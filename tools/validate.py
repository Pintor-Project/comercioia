"""Validates the Comercio IA schemas and examples.

Checks:
  1. Every schema is valid JSON Schema 2020-12.
  2. UCP self-description: $id on https://comercioia.cl/, name under cl.comercioia., YYYY-MM-DD version,
     file path matches name and version, requires.capabilities keys are a subset of $defs.
  3. Every example validates against the matching definitions (UCP base schemas are fetched from ucp.dev).
  4. Every RUT in the examples has a valid modulo 11 check digit.
  5. The profile example declares each schema at its canonical comercioia.cl URL.
  6. Backward compatibility: an example valid under the previous version of a schema stays valid under the latest.

Examples are checked against the latest version of each schema.

Usage: python tools/validate.py            (run from the repository root)
"""
import glob
import json
import os
import re
import sys
import urllib.request

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")
EXAMPLES = os.path.join(ROOT, "examples")
errors = []


def fail(msg):
    errors.append(msg)
    print("FAIL", msg)


_cache = {}


def retrieve(uri):
    if uri.startswith("https://comercioia.cl/"):
        path = os.path.join(SITE, uri[len("https://comercioia.cl/"):])
        return Resource.from_contents(json.load(open(path)))
    if uri not in _cache:
        with urllib.request.urlopen(uri, timeout=30) as r:
            _cache[uri] = json.load(r)
    return Resource.from_contents(_cache[uri])


registry = Registry(retrieve=retrieve)

# 1 + 2: schemas
schemas = {}    # name -> (doc, rel) of the latest version
previous = {}   # name -> (doc, rel) of the version before it
for path in sorted(glob.glob(os.path.join(SITE, "ucp", "**", "*.json"), recursive=True)):
    rel = os.path.relpath(path, SITE)
    doc = json.load(open(path))
    try:
        Draft202012Validator.check_schema(doc)
    except Exception as e:  # noqa: BLE001
        fail(f"{rel}: not a valid 2020-12 schema: {e}")
        continue
    if doc.get("$id") != "https://comercioia.cl/" + rel.replace(os.sep, "/"):
        fail(f"{rel}: $id {doc.get('$id')} does not match its path")
    name, version = doc.get("name", ""), doc.get("version", "")
    if not name.startswith("cl.comercioia."):
        fail(f"{rel}: name {name} is outside cl.comercioia.")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", version) or not rel.endswith(f"{version}.json"):
        fail(f"{rel}: version {version} does not match the file name")
    caps = set(doc.get("requires", {}).get("capabilities", {}))
    if not caps <= set(doc.get("$defs", {})):
        fail(f"{rel}: requires.capabilities {caps - set(doc['$defs'])} missing from $defs")
    if name in schemas and schemas[name][0]["version"] < version:
        previous[name] = schemas[name]
    if name not in schemas or schemas[name][0]["version"] < version:
        schemas[name] = (doc, rel)
    print("ok  ", rel, name)


def errors_for(doc, defname, instance):
    schema = {"$ref": f"{doc['$id']}#/$defs/{defname}"}
    return sorted(Draft202012Validator(schema, registry=registry).iter_errors(instance), key=str)


def check(name, defname, instance, label):
    doc, rel = schemas[name]
    errs = errors_for(doc, defname, instance)
    for e in errs:
        fail(f"{label}: {defname}: {e.message} at {list(e.absolute_path)}")
    if not errs:
        print("ok  ", label, "->", defname, doc["version"])
    if name in previous and defname in previous[name][0]["$defs"]:
        old = previous[name][0]
        if errs and not errors_for(old, defname, instance):
            fail(f"{label}: valid under {name} {old['version']} but not under {doc['version']} (breaks backward compatibility)")


def rejects(name, defname, instance, label):
    if errors_for(schemas[name][0], defname, instance):
        print("ok  ", label, "is rejected")
    else:
        fail(f"{label} must be rejected")


def ex(name):
    return json.load(open(os.path.join(EXAMPLES, name)))


# 3: examples
co = ex("checkout-response.json")
check("cl.comercioia.shopping.tax_document", "tax_document_request", co["tax_document"], "checkout-response.tax_document")
check("cl.comercioia.shopping.consumer_terms", "checkout_terms", co["consumer_terms"], "checkout-response.consumer_terms")
for i, pol in enumerate(co["policies"]):
    defname = {"cl.comercioia.policy.retracto": "retracto_policy",
               "cl.comercioia.policy.garantia_legal": "garantia_legal_policy"}[pol["type"]]
    check("cl.comercioia.shopping.consumer_terms", defname, pol, f"checkout-response.policies[{i}]")
for i, msg in enumerate(co["messages"]):
    if msg.get("presentation") == "disclosure" and msg["code"] not in {p["type"] for p in co["policies"]}:
        fail(f"checkout-response.messages[{i}]: disclosure code {msg['code']} has no matching policy")

req = ex("checkout-request-factura.json")
check("cl.comercioia.shopping.tax_document", "tax_document_request", req["tax_document"], "checkout-request-factura.tax_document")
check("cl.comercioia.shopping.consumer_terms", "checkout_terms", req["consumer_terms"], "checkout-request-factura.consumer_terms")
TD = "cl.comercioia.shopping.tax_document"
rcv = req["tax_document"]["receiver"]
rejects(TD, "tax_document_request", {"document_choice": "factura"}, "factura without receiver")
rejects(TD, "tax_document_request", {"document_choice": "factura", "receiver": {"rut": rcv["rut"], "razon_social": rcv["razon_social"]}},
        "factura receiver without giro, direccion and comuna")
rejects(TD, "tax_document_request", dict(req["tax_document"], references=[{"type": "801", "number": "4500195544"}]),
        "factura reference without date")
rejects(TD, "tax_document_request", {"references": [{"type": "8010", "number": "1"}]}, "reference type longer than 3 characters")
rejects(TD, "tax_document_request", {"document_choice": "boleta", "receiver": {"rut": "15987654-3"}}, "boleta receiver without razon_social")

b135 = ex("checkout-request-boleta-135uf.json")
check(TD, "tax_document_request", b135["tax_document"], "checkout-request-boleta-135uf.tax_document")
check("cl.comercioia.shopping.consumer_terms", "checkout_terms", b135["consumer_terms"], "checkout-request-boleta-135uf.consumer_terms")

order = ex("order-after-withdrawal.json")
for i, d in enumerate(order["tax_documents"]):
    check("cl.comercioia.shopping.tax_document", "issued_document", d, f"order.tax_documents[{i}]")
check("cl.comercioia.shopping.consumer_terms", "order_terms", order["consumer_terms"], "order.consumer_terms")
for i, adj in enumerate(order["adjustments"]):
    check("cl.comercioia.shopping.credit_note", "adjustment_with_document", adj, f"order.adjustments[{i}]")

UF135_CLP = 5186253  # 135 UF in CLP for 2025 (SII Res. Ex. 44/2025); the SII updates it every December
for fname in ("order-boleta-135uf.json", "order-factura.json"):
    for i, d in enumerate(ex(fname)["tax_documents"]):
        check(TD, "issued_document", d, f"{fname[:-5]}.tax_documents[{i}]")
        if d["type"] in (39, 41) and d["total"] > UF135_CLP and (d.get("receiver_rut") in (None, "66666666-6") or "payment_method" not in d):
            fail(f"{fname}: a boleta above 135 UF must carry the buyer's RUT and the payment method")


# 4: RUT check digits
def dv(body):
    s, m = 0, 2
    for c in reversed(body):
        s += int(c) * m
        m = 2 if m == 7 else m + 1
    r = 11 - s % 11
    return "0" if r == 11 else "K" if r == 10 else str(r)


for path in sorted(glob.glob(os.path.join(EXAMPLES, "*.json"))):
    for rut in re.findall(r'"(\d{1,8}-[\dkK])"', open(path).read()):
        body, d = rut.split("-")
        if dv(body) != d.upper():
            fail(f"{os.path.basename(path)}: RUT {rut} has a wrong check digit (expected {dv(body)})")

# 5: profile URLs
prof = ex("profile.json")["ucp"]
for section in ("capabilities", "payment_handlers"):
    for name, decls in prof[section].items():
        if name in schemas:
            for d in decls:
                want = schemas[name][0]["$id"]
                if d.get("schema") != want:
                    fail(f"profile.{section}.{name}: schema {d.get('schema')} != {want}")

print()
if errors:
    print(f"{len(errors)} problem(s)")
    sys.exit(1)
print("all checks passed")
