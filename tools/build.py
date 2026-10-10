"""Builds the Comercio IA landing pages (es, en), the timbre patterns, and
refreshes header/footer/fonts/metadata on the hand-written pages, and writes the
privacy and accessibility pages and the sitemap. Usage: python3 build.py <site_dir>"""
import html, json, os, random, re, sys

SITE = sys.argv[1]
BASE = "https://comercioia.cl"
LASTMOD = "2026-10-09"
# Self-hosted (assets/fonts, OFL): no request leaves for a font CDN before consent.
FONTS = ('<link rel="preload" href="/assets/fonts/hanken-grotesk-400-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
         '<link rel="preload" href="/assets/fonts/hanken-grotesk-300-latin.woff2" as="font" type="font/woff2" crossorigin>')
ICON = ('<link rel="icon" href="/favicon.svg" type="image/svg+xml">\n'
        '<link rel="icon" href="/favicon-192.png" type="image/png" sizes="192x192">')

# ---------------------------------------------------------------- timbre (PDF417-like)
def pdf417_like(cols, rows, seed):
    rnd = random.Random(seed)
    def codeword():
        while True:
            w = [rnd.randint(1, 6) for _ in range(8)]
            if sum(w) == 17:
                return w
    start = [8, 1, 1, 1, 1, 1, 1, 3]
    stop = [7, 1, 1, 3, 1, 1, 1, 2, 1]
    out = []
    for r in range(rows):
        seq = start + sum((codeword() for _ in range(cols + 2)), []) + stop
        x = 0
        for i, w in enumerate(seq):
            if i % 2 == 0:
                out.append((x, r * 3, w))
            x += w
    width = 17 + (cols + 2) * 17 + 18
    return width, rows * 3, out

def svg_pattern(cols, rows, seed, fill):
    w, h, bars = pdf417_like(cols, rows, seed)
    rects = "".join(f'<rect x="{x}" y="{y}" width="{bw}" height="3"/>' for x, y, bw in bars)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" preserveAspectRatio="none" '
            f'shape-rendering="crispEdges"><g fill="{fill}">{rects}</g></svg>\n')

os.makedirs(os.path.join(SITE, "assets"), exist_ok=True)
open(os.path.join(SITE, "assets", "timbre-receipt.svg"), "w").write(svg_pattern(6, 9, 39, "#1b1914"))
open(os.path.join(SITE, "assets", "timbre-band.svg"), "w").write(svg_pattern(9, 7, 61, "#A30C24"))

# ---------------------------------------------------------------- sequence diagram
LANES_X = [90, 330, 560, 790, 1010]
STEPS = [  # from, to, ours, es, en
    (0, 1, False, "«Lo quiero»", "“I'll take it”"),
    (1, 2, True, "create_checkout · pide boleta", "create_checkout · asks for a boleta"),
    (2, 1, True, "totales, avisos legales, medios de pago", "totals, legal notices, payment methods"),
    (1, 2, True, "complete_checkout · Webpay Plus", "complete_checkout · Webpay Plus"),
    (2, 3, False, "crea el pago con la cuenta de la tienda", "creates the payment on the store's account"),
    (2, 1, False, "requires_escalation + continue_url", "requires_escalation + continue_url"),
    (0, 3, False, "paga en la página del proveedor", "pays on the provider's page"),
    (3, 2, False, "confirmación del pago", "payment confirmation"),
    (2, 4, True, "boleta 39, dentro de 1 hora", "boleta 39, within 1 hour"),
    (2, 0, True, "boleta + copia del contrato", "boleta + contract copy"),
    (2, 1, True, "pedido con tax_documents[]", "order with tax_documents[]"),
]

def seq_svg(lang):
    lanes = (["Comprador", "Agente de IA", "Tienda", "Proveedor de pago", "SII"] if lang == "es"
             else ["Buyer", "AI agent", "Store", "Payment provider", "SII"])
    y0, dy = 92, 44
    H = y0 + dy * (len(STEPS) - 1) + 40
    p = [f'<svg viewBox="0 0 1100 {H}" role="img" aria-labelledby="seq-title">']
    p.append(f'<title id="seq-title">{"Diagrama de secuencia de una compra" if lang == "es" else "Sequence diagram of one purchase"}</title>')
    for i, name in enumerate(lanes):
        x = LANES_X[i]
        p.append(f'<text class="lane" x="{x}" y="26" text-anchor="middle">{name}</text>')
        p.append(f'<line class="life" x1="{x}" y1="44" x2="{x}" y2="{H - 8}"/>')
        p.append(f'<rect x="{x - 3}" y="40" width="6" height="6" class="head"/>')
    for n, (a, b, ours, es, en) in enumerate(STEPS):
        y = y0 + n * dy
        x1, x2 = LANES_X[a], LANES_X[b]
        d = 1 if x2 > x1 else -1
        cls = " ours" if ours else ""
        p.append(f'<line class="msg{cls}" x1="{x1}" y1="{y}" x2="{x2 - d * 7}" y2="{y}"/>')
        p.append(f'<path class="head{cls}" d="M{x2} {y} L{x2 - d * 9} {y - 4.5} L{x2 - d * 9} {y + 4.5} Z"/>')
        label = (es if lang == "es" else en).replace("&", "&amp;")
        mid = (x1 + x2) / 2
        p.append(f'<text class="lbl{cls}" x="{mid:.0f}" y="{y - 9}" text-anchor="middle">'
                 f'<tspan class="num">{n + 1:02d}</tspan>  {label}</text>')
    p.append("</svg>")
    return "\n".join(p)

def seq_text(lang):
    lanes = (["Comprador", "Agente de IA", "Tienda", "Proveedor de pago", "SII"] if lang == "es"
             else ["Buyer", "AI agent", "Store", "Payment provider", "SII"])
    items = "\n".join(f'            <li>{lanes[a]} → {lanes[b]}: {(es if lang == "es" else en).replace("&", "&amp;")}</li>'
                      for a, b, _, es, en in STEPS)
    summary = "Ver los pasos como texto" if lang == "es" else "Show the steps as text"
    return f'''<details class="seq-text">
          <summary>{summary}</summary>
          <ol>
{items}
          </ol>
        </details>'''

# ---------------------------------------------------------------- shared chrome
# Universal access symbol. The button sits outside the header: the header's backdrop-filter
# would otherwise become the containing block of a position:fixed child.
A11Y_ICON = ('<svg viewBox="0 0 24 24" width="26" height="26" aria-hidden="true" focusable="false">'
             '<circle cx="12" cy="12" r="10.4" fill="none" stroke="currentColor" stroke-width="1.5"/>'
             '<circle cx="12" cy="6.7" r="1.6" fill="currentColor"/>'
             '<path d="M6.6 9.3l5.4 1.2 5.4-1.2M12 10.5v3.7m0 0l-2.5 4.9m2.5-4.9l2.5 4.9" fill="none" stroke="currentColor" '
             'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/></svg>')

def masthead(lang, current):
    if lang == "es":
        links = [("/spec/", "Especificación", "spec"), ("/spec/#esquemas", "Esquemas", "schemas"), ("/cumplimiento/", "Cumplimiento", "compliance"), ("/#participa", "Participa", "join")]
        other = {"spec": "/en/spec/", "compliance": "/en/compliance/", "privacy": "/en/privacy/", "accessibility": "/en/accessibility/"}.get(current, "/en/")
        home, other_label, other_lang = "/", "English", "en"
    else:
        links = [("/en/spec/", "Specification", "spec"), ("/en/spec/#schemas", "Schemas", "schemas"), ("/en/compliance/", "Compliance", "compliance"), ("/en/#participate", "Participate", "join")]
        other = {"spec": "/spec/", "compliance": "/cumplimiento/", "privacy": "/privacidad/", "accessibility": "/accesibilidad/"}.get(current, "/")
        home, other_label, other_lang = "/en/", "Español", "es-CL"
    cur = ' aria-current="page"'
    a11y_label = "Ajustes de accesibilidad" if lang == "es" else "Accessibility settings"
    nav = "\n      ".join(f'<a href="{h}"{cur if k == current else ""}>{t}</a>' for h, t, k in links)
    return f'''<a class="skip" href="#main">{"Saltar al contenido" if lang == "es" else "Skip to content"}</a>
<header class="masthead">
  <div class="wrap">
    <a class="logo" href="{home}" aria-label="Comercio IA"><span class="rut">cl.<b>comercioia</b></span></a>
    <nav class="nav" aria-label="{"Principal" if lang == "es" else "Main"}">
      {nav}
      <a class="ext" href="https://github.com/Pintor-Project/comercioia">GitHub</a>
      <a class="lang" href="{other}" hreflang="{other_lang}" lang="{other_lang}">{other_label}</a>
    </nav>
  </div>
</header>
<button type="button" class="a11y-fab" id="a11y-btn" aria-expanded="false" aria-label="{a11y_label}" title="{a11y_label}" hidden>{A11Y_ICON}</button>'''

def footer(lang):
    if lang == "es":
        return '''<footer class="footer">
  <div class="wrap">
    <p>Iniciativa abierta impulsada por <a href="https://pintorproject.cl">Pintor Project</a>. Implementación de referencia: <a href="https://synaptiktech.com/es/product/checkout-ia">Synaptik Checkout IA</a>, producto comercial de Pintor Project.</p>
    <p><a href="/spec/">Especificación</a> · <a href="/spec/#esquemas">Esquemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="links"><a href="/privacidad/">Privacidad</a> <a href="/accesibilidad/">Accesibilidad</a> <button type="button" class="linkish" data-cookie-settings hidden>Preferencias de cookies</button></p>
    <p class="legal">Especificación y esquemas bajo licencia Apache-2.0. No es asesoría legal. Comercio IA no está afiliado a Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, el SII ni el SERNAC, ni cuenta con su respaldo; las marcas pertenecen a sus dueños.</p>
  </div>
</footer>'''
    return '''<footer class="footer">
  <div class="wrap">
    <p>An open initiative led by <a href="https://pintorproject.cl">Pintor Project</a>. Reference implementation: <a href="https://synaptiktech.com/en/product/checkout-ia">Synaptik Checkout IA</a>, a commercial product of Pintor Project.</p>
    <p><a href="/en/spec/">Specification</a> · <a href="/en/spec/#schemas">Schemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="links"><a href="/en/privacy/">Privacy</a> <a href="/en/accessibility/">Accessibility</a> <button type="button" class="linkish" data-cookie-settings hidden>Cookie preferences</button></p>
    <p class="legal">Specification and schemas under the Apache-2.0 license. Not legal advice. Comercio IA is not affiliated with or endorsed by Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, the SII or SERNAC; trademarks belong to their owners.</p>
  </div>
</footer>'''

ORG = {"@type": "Organization", "@id": BASE + "/#org", "name": "Pintor Project SpA", "alternateName": "Pintor Project",
       "url": "https://pintorproject.cl", "email": "contacto@comercioia.cl",
       "address": {"@type": "PostalAddress", "streetAddress": "San Pío X 2460", "addressLocality": "Providencia",
                   "addressRegion": "Región Metropolitana", "postalCode": "7510041", "addressCountry": "CL"}}
WEBSITE = {"@type": "WebSite", "@id": BASE + "/#website", "name": "Comercio IA", "url": BASE + "/",
           "inLanguage": ["es-CL", "en"], "publisher": {"@id": BASE + "/#org"}}
OG_ALT = {"es": "Comercio IA: boleta, retracto y medios de pago chilenos para agentes de IA",
          "en": "Comercio IA: Chilean tax receipts, withdrawal rights and payment methods for AI agents"}

def seo(lang, title, desc, url, kind):
    """kind: home | article | page. Wrapped in markers so the hand-written pages can be refreshed in place."""
    es = lang == "es"
    title_t, desc_t = html.unescape(title), html.unescape(desc)
    page = {"@type": {"home": "WebPage", "article": "TechArticle", "page": "WebPage"}[kind], "@id": url, "url": url,
            "name": title_t, "description": desc_t, "inLanguage": "es-CL" if es else "en",
            "isPartOf": {"@id": BASE + "/#website"}, "publisher": {"@id": BASE + "/#org"}}
    if kind == "article":
        page.update(headline=title_t.split(" · ")[0], datePublished="2026-10-09", dateModified=LASTMOD,
                    author={"@id": BASE + "/#org"}, license="https://www.apache.org/licenses/LICENSE-2.0")
    graph = [ORG, WEBSITE, page] if kind == "home" else [page]
    ld = json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False, separators=(",", ":"))
    return f'''<!-- seo -->
<meta property="og:type" content="{"article" if kind == "article" else "website"}">
<meta property="og:site_name" content="Comercio IA">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:locale" content="{"es_CL" if es else "en_US"}">
<meta property="og:locale:alternate" content="{"en_US" if es else "es_CL"}">
<meta property="og:image" content="{BASE}/assets/og-{lang}.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{OG_ALT[lang]}">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#FFFFFF">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<script type="application/ld+json">{ld}</script>
<script src="/assets/site.js" defer></script>
<!-- /seo -->'''

def head(lang, title, desc, canonical, alt_es, alt_en, kind="home", extra=""):
    return f'''<!doctype html>
<html lang="{"es-CL" if lang == "es" else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="alternate" hreflang="es-CL" href="{alt_es}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="alternate" hreflang="x-default" href="{alt_es}">
<link rel="canonical" href="{canonical}">
{seo(lang, title, desc, canonical, kind)}
{ICON}
{FONTS}
<link rel="stylesheet" href="/assets/site.css">{extra}
</head>'''

def ledger_row(prefix, key, title, text, source):
    return (f'<tr><td class="n">{prefix}<span class="k">{key}</span></td>'
            f'<td class="w"><b>{title}</b><span>{text}</span></td><td class="s">{source}</td></tr>')

# ---------------------------------------------------------------- plain-language introduction
INTRO = {
    "es": dict(
        h2='Cómo compra una IA, <span class="sub">y qué le falta en Chile.</span>',
        steps=[
            ("01", "Los asistentes de IA empiezan a comprar",
             "ChatGPT, Gemini o Claude ya no solo recomiendan productos: pueden buscar en una tienda, armar el carro y llevar al cliente a pagar. Para eso, el asistente y la tienda tienen que hablar el mismo idioma."),
            ("02", "Ese idioma ya existe: UCP y ACP",
             'Google y Shopify publicaron el <a href="https://ucp.dev">Universal Commerce Protocol (UCP)</a>; OpenAI y Stripe, el <a href="https://www.agenticcommerce.dev">Agentic Commerce Protocol (ACP)</a>. Son estándares abiertos: reglas públicas para que cualquier asistente pueda comprar en cualquier tienda, igual que una tarjeta funciona en cualquier máquina de pago.'),
            ("03", "Pero no conocen Chile",
             "Fueron pensados para Estados Unidos: no saben de boleta ni factura del SII, derecho a retracto, garantía legal ni Webpay. Comercio IA es una extensión: un complemento que se enchufa a esos estándares y agrega lo que exige la ley chilena. No los reemplaza, los completa."),
        ],
        terms_title="Palabras que vas a ver",
        terms=[
            ("Agente de IA", "Un asistente como ChatGPT, Gemini o Claude que hace tareas por una persona, como buscar y comprar."),
            ("Estándar o protocolo", "Reglas públicas y gratuitas que siguen todos los que quieren entenderse, como el formato de una factura electrónica."),
            ("Extensión", "Un agregado a un estándar para un caso que el estándar no cubre. Quien no la conoce sigue funcionando."),
            ("Esquema", "El archivo técnico que dice exactamente qué datos viajan y en qué formato. Es lo que leen los programadores."),
        ],
        who="Esta página es para quien implementa: plataformas de e-commerce, ERPs, proveedores de pago y equipos técnicos de tiendas. Si tienes una tienda y solo quieres vender por IA, tu plataforma o tu proveedor debería encargarse.",
    ),
    "en": dict(
        h2='How AI shopping works, <span class="sub">and what Chile adds.</span>',
        steps=[
            ("01", "AI assistants are starting to shop",
             "ChatGPT, Gemini and Claude no longer just recommend products: they can search a store, build a cart and take the buyer to pay. For that, the assistant and the store need to speak the same language."),
            ("02", "That language exists: UCP and ACP",
             'Google and Shopify published the <a href="https://ucp.dev">Universal Commerce Protocol (UCP)</a>; OpenAI and Stripe, the <a href="https://www.agenticcommerce.dev">Agentic Commerce Protocol (ACP)</a>. They are open standards: public rules so any assistant can buy from any store, the way a card works on any payment terminal.'),
            ("03", "But they don't know Chile",
             "They were designed for the United States: they know nothing about SII tax receipts (boleta and factura), the right of withdrawal, the legal warranty or Webpay. Comercio IA is an extension: an add-on that plugs into those standards and adds what Chilean law requires. It doesn't replace them; it completes them."),
        ],
        terms_title="Words you'll see",
        terms=[
            ("AI agent", "An assistant such as ChatGPT, Gemini or Claude that does tasks for a person, like finding and buying things."),
            ("Standard or protocol", "Free, public rules that everyone who wants to interoperate follows, like the format of an electronic invoice."),
            ("Extension", "An addition to a standard for a case the standard doesn't cover. Anyone who doesn't know it keeps working."),
            ("Schema", "The technical file that says exactly which data travels and in what format. It's what developers read."),
        ],
        who="This page is for implementers: e-commerce platforms, ERPs, payment providers and stores' technical teams. If you run a store and just want to sell through AI, your platform or provider should handle it.",
    ),
}

def intro_section(lang):
    d = INTRO[lang]
    ideas = "\n".join(f'          <div>\n            {ILL_IDEAS[i]}\n            <h3>{h}</h3>\n            <p>{t}</p>\n          </div>'
                      for i, (_, h, t) in enumerate(d["steps"]))
    terms = "\n".join(f"            <dt>{a}</dt><dd>{b}</dd>" for a, b in d["terms"])
    return f'''  <section class="section intro" id="{"que-es" if lang == "es" else "what-is-it"}">
    <div class="wrap">
      <h2>{d["h2"]}</h2>
      <div class="ideas">
{ideas}
      </div>
      <div class="glossary">
        <h3>{d["terms_title"]}</h3>
        <dl>
{terms}
        </dl>
      </div>
      <p class="fine">{d["who"]}</p>
    </div>
  </section>'''

# ---------------------------------------------------------------- own line illustrations (one style, one red accent)
ILL_IDEAS = [
    # a chat bubble with a cart: assistants start to shop
    '<svg viewBox="0 0 132 96" aria-hidden="true" focusable="false">'
    '<rect class="ill-fill" x="10" y="12" width="84" height="50" rx="14"/>'
    '<path class="ill" d="M24 12h56a14 14 0 0 1 14 14v22a14 14 0 0 1-14 14H46l-14 12v-12h-8a14 14 0 0 1-14-14V26a14 14 0 0 1 14-14z"/>'
    '<path class="ill" d="M36 30h8l5 18h20l4-12H47"/><circle class="ill-dot" cx="52" cy="53" r="2.2"/><circle class="ill-dot" cx="66" cy="53" r="2.2"/>'
    '<path class="ill-red" d="M108 20v12M102 26h12M116 48v8M112 52h8"/></svg>',
    # UCP and ACP speaking the same language
    '<svg viewBox="0 0 132 96" aria-hidden="true" focusable="false">'
    '<rect class="ill-fill" x="8" y="26" width="46" height="44" rx="8"/>'
    '<rect class="ill" x="8" y="26" width="46" height="44" rx="8"/><text class="ill-t" x="31" y="51" text-anchor="middle">UCP</text>'
    '<rect class="ill" x="78" y="26" width="46" height="44" rx="8"/><text class="ill-t" x="101" y="51" text-anchor="middle">ACP</text>'
    '<path class="ill" d="M54 40h24M54 56h24" stroke-dasharray="3 4"/><path class="ill" d="M72 36l6 4-6 4M60 52l-6 4 6 4"/></svg>',
    # a plug-in piece with the red cl. box: the extension
    '<svg viewBox="0 0 132 96" aria-hidden="true" focusable="false">'
    '<rect class="ill-fill" x="8" y="22" width="60" height="52" rx="8"/>'
    '<path class="ill" d="M16 22h44a8 8 0 0 1 8 8v12h-6a6 6 0 0 0 0 12h6v12a8 8 0 0 1-8 8H16a8 8 0 0 1-8-8V30a8 8 0 0 1 8-8z"/>'
    '<text class="ill-t" x="34" y="52" text-anchor="middle">UCP</text>'
    '<rect class="ill-red" x="78" y="30" width="46" height="36"/>'
    '<text class="ill-tr" x="101" y="46" text-anchor="middle">cl.</text><text class="ill-tr" x="101" y="58" text-anchor="middle">SII</text>'
    '<path class="ill-red" d="M62 48h16"/></svg>',
]
ILL_WHO = [
    # a storefront
    '<svg viewBox="0 0 96 72" aria-hidden="true" focusable="false"><rect class="ill-fill" x="14" y="30" width="68" height="34"/>'
    '<path class="ill" d="M10 30h76M14 30v34h68V30M10 30l6-18h64l6 18M40 64V44h16v20"/><path class="ill-red" d="M26 12v18M42 12v18M58 12v18M74 12v18"/></svg>',
    # stacked layers: a platform or ERP
    '<svg viewBox="0 0 96 72" aria-hidden="true" focusable="false"><path class="ill-fill" d="M48 42l34-14-34-14-34 14z"/>'
    '<path class="ill" d="M48 42l34-14-34-14-34 14zM14 38l34 14 34-14M14 48l34 14 34-14"/><path class="ill-red" d="M48 14v28"/></svg>',
    # a chat bubble: an AI agent
    '<svg viewBox="0 0 96 72" aria-hidden="true" focusable="false"><rect class="ill-fill" x="12" y="14" width="56" height="36" rx="12"/>'
    '<path class="ill" d="M24 14h32a12 12 0 0 1 12 12v12a12 12 0 0 1-12 12H36l-10 9v-9h-2a12 12 0 0 1-12-12V26a12 12 0 0 1 12-12z"/>'
    '<path class="ill-red" d="M80 18v10M75 23h10M84 40v6M81 43h6"/><path class="ill" d="M28 32h24"/></svg>',
    # a card and a payment terminal: a payment provider
    '<svg viewBox="0 0 96 72" aria-hidden="true" focusable="false"><rect class="ill-fill" x="10" y="20" width="52" height="34" rx="5"/>'
    '<rect class="ill" x="10" y="20" width="52" height="34" rx="5"/><path class="ill" d="M10 30h52M18 44h14"/>'
    '<rect class="ill-red" x="58" y="10" width="28" height="52" rx="5"/><path class="ill-red" d="M64 20h16M64 28h16"/></svg>',
]
SPARK = ('<svg viewBox="0 0 22 22" aria-hidden="true" focusable="false"><circle cx="11" cy="11" r="11" fill="var(--bg-3)"/>'
         '<path d="M11 5.5l1.4 4.1 4.1 1.4-4.1 1.4-1.4 4.1-1.4-4.1-4.1-1.4 4.1-1.4z" fill="var(--ink-2)"/></svg>')
KEYBOARD = ('<svg viewBox="0 0 34 20" aria-hidden="true" focusable="false"><rect x="1" y="1" width="32" height="18" rx="3" fill="none" stroke="currentColor" stroke-width="1.4"/>'
            '<path d="M5 6h3M10 6h3M15 6h3M20 6h3M25 6h3M5 10h3M10 10h3M15 10h3M20 10h3M25 10h3M9 14h16" stroke="currentColor" stroke-width="1.4"/></svg>')

# ---------------------------------------------------------------- hero object: the RUT box in volume, with its timbre
def timbre_symbol():
    w, h, bars = pdf417_like(6, 9, 39)  # same pattern as /assets/timbre-receipt.svg
    d = "".join(f"M{x} {y}h{bw}v3h-{bw}z" for x, y, bw in bars)
    return (f'<svg class="sprite" width="0" height="0" aria-hidden="true" focusable="false">'
            f'<symbol id="timbre" viewBox="0 0 {w} {h}" preserveAspectRatio="none"><path d="{d}"/></symbol></svg>')

def hero_art(lang, version):
    es = lang == "es"
    title = ("El recuadro del RUT de los documentos tributarios chilenos, en volumen, con su timbre electrónico: boleta electrónica, factura electrónica y nota de crédito."
             if es else "The RUT box printed on Chilean tax documents, as a solid block with its electronic stamp: electronic boleta, electronic factura and credit note.")
    caption = ("El recuadro del RUT, presente en todo documento tributario chileno." if es
               else "The RUT box, printed on every Chilean tax document.")
    stamp = f"Timbre electrónico · versión {version}" if es else f"Electronic stamp · version {version}"
    return f'''<figure class="hero-art">
          <svg class="block" viewBox="0 0 520 450" role="img" aria-labelledby="block-t">
            <title id="block-t">{title}</title>
            <g class="lift">
              <path class="face" d="M40 140 L400 140 L470 90 L110 90 Z"/>
              <path class="hatch" d="M70 140 L140 90 M110 140 L180 90 M150 140 L220 90 M190 140 L260 90 M230 140 L300 90 M270 140 L340 90 M310 140 L380 90 M350 140 L420 90"/>
              <path class="solid" d="M400 140 L470 90 L470 370 L400 420 Z"/>
            </g>
            <rect class="face" x="40" y="140" width="360" height="280"/>
            <rect class="frame" x="76" y="170" width="288" height="146"/>
            <text class="t-big" x="220" y="218" text-anchor="middle">cl.<tspan>comercioia</tspan></text>
            <text class="t" x="220" y="250" text-anchor="middle">BOLETA ELECTRÓNICA</text>
            <text class="t" x="220" y="273" text-anchor="middle">FACTURA ELECTRÓNICA</text>
            <text class="t" x="220" y="296" text-anchor="middle">NOTA DE CRÉDITO</text>
            <use class="timbre" href="#timbre" x="76" y="336" width="288" height="50"/>
            <text class="t-dim" x="220" y="406" text-anchor="middle">{stamp}</text>
          </svg>
          <figcaption class="block-caption">{caption}</figcaption>
        </figure>'''

# ---------------------------------------------------------------- purchase demo: what the buyer sees, next to the JSON
# The JSON in each step is cut from the validated examples in /examples (… marks what is left out),
# so the demo never shows a field the current schemas don't define.
EX = {n: json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "examples", n + ".json")))
      for n in ("checkout-response", "order-after-withdrawal", "profile")}

def pick(d, *keys):
    return {k: d[k] for k in keys}

def json_lines(value, ours, width=60):
    """Compact JSON as highlighted lines. Keys in `ours` (at any depth) mark their whole member as added by Comercio IA."""
    esc = lambda t: html.escape(t, quote=False)
    def scalar(v):
        return '<span class="d">…</span>' if v is Ellipsis else f'<span class="s">{esc(json.dumps(v, ensure_ascii=False))}</span>'
    def plain(v):  # text length of the one-line form
        if v is Ellipsis: return "…"
        if isinstance(v, dict): return "{ " + ", ".join(f'"{k}": {plain(x)}' for k, x in v.items()) + " }"
        if isinstance(v, list): return "[ " + ", ".join(plain(x) for x in v) + " ]"
        return json.dumps(v, ensure_ascii=False)
    def inline(v):
        if isinstance(v, dict): return "{ " + ", ".join(f'<span class="k">"{esc(k)}"</span>: {inline(x)}' for k, x in v.items()) + " }"
        if isinstance(v, list): return "[ " + ", ".join(inline(x) for x in v) + " ]"
        return scalar(v)
    out = []
    def emit(v, ind, prefix, prefix_len, o, tail):
        """Render v after `prefix` at indent `ind`; `tail` is "," or ""."""
        if prefix_len + len(plain(v)) + ind + len(tail) <= width or not isinstance(v, (dict, list)) or not v:
            out.append((" " * ind + prefix + inline(v) + tail, o)); return
        opn, cls = ("{", "}") if isinstance(v, dict) else ("[", "]")
        out.append((" " * ind + prefix + opn, o))
        items = list(v.items()) if isinstance(v, dict) else [(None, x) for x in v]
        line, line_len, line_o = None, 0, o
        for i, (k, x) in enumerate(items):
            t = "," if i < len(items) - 1 else ""
            xo = o or (k in ours)
            p = f'<span class="k">"{esc(k)}"</span>: ' if k is not None else ""
            pl = len(f'"{k}": ') if k is not None else 0
            small = not isinstance(x, (dict, list)) or pl + len(plain(x)) <= 28
            piece, piece_len = p + inline(x) + t, pl + len(plain(x)) + len(t)
            if small and line is not None and line_o == xo and ind + 2 + line_len + 1 + piece_len <= width:
                line, line_len = line + " " + piece, line_len + 1 + piece_len
                continue
            if line is not None: out.append((" " * (ind + 2) + line, line_o)); line = None
            if small:
                line, line_len, line_o = piece, piece_len, xo
            else:
                emit(x, ind + 2, p, pl, xo, t)
        if line is not None: out.append((" " * (ind + 2) + line, line_o))
        out.append((" " * ind + cls + tail, o))
    emit(value, 0, "", 0, False, "")
    return "".join(f'<span class="l{" o" if o else ""}">{t}</span>' for t, o in out)

def code_block(op, direction, blocks, legend):
    """blocks: [(subtitle or None, value, ours_keys)]"""
    parts = []
    for sub, value, ours in blocks:
        if sub: parts.append(f'<p class="code-sub">{sub}</p>')
        parts.append(f'<pre tabindex="0"><code>{json_lines(value, ours)}</code></pre>')
    return (f'<figure class="code"><figcaption><span><b>{op}</b> · {direction}</span><span>UCP</span></figcaption>\n'
            + "\n".join(parts) + f'\n<p class="code-legend">{legend}</p></figure>')

def phone(time, chat, lang):
    head_ = "Asistente de IA" if lang == "es" else "AI assistant"
    typing = "Escribe un mensaje" if lang == "es" else "Type a message"
    return (f'<div class="phone"><div class="screen">'
            f'<div class="bar" aria-hidden="true"><span>{time}</span><span>5G</span></div>'
            f'<div class="ahead">{SPARK}<span>{head_}</span></div>'
            f'<div class="chat">{chat}</div>'
            f'<div class="input" aria-hidden="true">{typing}</div></div></div>')

def demo_steps(lang):
    es = lang == "es"
    co, order, prof = EX["checkout-response"], EX["order-after-withdrawal"], EX["profile"]["ucp"]
    retracto, garantia = co["policies"]
    step1 = {"line_items": [Ellipsis], "tax_document": co["tax_document"],
             "consumer_terms": pick(co["consumer_terms"], "ai_disclosure")}
    step2 = {"currency": co["currency"], "totals": [Ellipsis, co["totals"][-1]],
             "policies": [pick(retracto, "type", "window_days", "refund_within_days"), pick(garantia, "type", "months")],
             "messages": [dict(pick(co["messages"][0], "type", "code", "presentation"), content=Ellipsis), Ellipsis],
             "consumer_terms": dict(seller=pick(co["consumer_terms"]["seller"], "razon_social", "rut", "domicilio"),
                                    ai_disclosure=Ellipsis, price_includes_tax=co["consumer_terms"]["price_includes_tax"])}
    step3 = dict(pick(co, "id", "status", "continue_url"), messages=[Ellipsis, co["messages"][-1]])
    step3_profile = {"payment_handlers": {"cl.comercioia.webpay_plus": [pick(prof["payment_handlers"]["cl.comercioia.webpay_plus"][0], "id", "available_instruments")]}}
    doc = order["tax_documents"][0]
    step4 = {"id": order["id"],
             "tax_documents": [pick(doc, "type", "folio", "issuer_rut", "issued_at", "total", "iva", "sii_status", "representation_url")],
             "consumer_terms": {"confirmation": pick(order["consumer_terms"]["confirmation"], "channel", "contract_copy_url")}}
    adj = order["adjustments"][0]
    step5 = {"id": order["id"], "adjustments": [dict(pick(adj, "id", "type", "status", "description"),
             tax_document=pick(adj["tax_document"], "type", "folio", "ref_type", "ref_folio", "cod_ref", "razon"))]}
    legend = "Lo que agrega Comercio IA" if es else "What Comercio IA adds"
    a2s, s2a = ("agente → tienda", "tienda → agente") if es else ("agent → store", "store → agent")
    order_op = "pedido" if es else "order"
    profile_sub = "perfil de la tienda · /.well-known/ucp" if es else "store profile · /.well-known/ucp"
    product = (f'<div class="card prod"><div class="img">{KEYBOARD}</div><div><b>{"Teclado 61 teclas" if es else "61-key keyboard"}</b>'
               f'<div class="dim">{"Despacho RM · 3 días hábiles" if es else "Delivery in Santiago · 3 business days"}</div><div>$189.990</div></div></div>')
    totals = (f'<div class="card"><div class="row"><span>{"Teclado 61 teclas" if es else "61-key keyboard"}</span><span>$189.990</span></div>'
              f'<div class="row"><span>{"Despacho RM" if es else "Delivery (Santiago)"}</span><span>$4.990</span></div>'
              f'<div class="row tot"><span>Total</span><span>$194.980</span></div>'
              f'<div class="dim">{"IVA incluido · boleta electrónica" if es else "VAT included · electronic boleta"}</div></div>')
    receipt = ('<div class="mini-receipt" role="img" aria-label="' + ("Boleta electrónica N° 4512330 de Tienda Ejemplo SpA por $194.980" if es else "Electronic boleta No. 4512330 from Tienda Ejemplo SpA for $194.980") + '">'
               '<div class="rb">R.U.T.: 76.123.456-0<br>BOLETA ELECTRÓNICA<br>N° 4512330</div>'
               '<div class="row"><span>Teclado 61 teclas</span><span>$189.990</span></div>'
               '<div class="row"><span>Despacho RM</span><span>$4.990</span></div>'
               '<div class="row"><b>TOTAL</b><b>$194.980</b></div>'
               '<img src="/assets/timbre-receipt.svg" alt=""></div>')
    if es:
        S = [
            ("«Lo quiero», con boleta", "El agente pide boleta al crear el checkout.",
             "Y declara que es un asistente de IA. La tienda lo repite en su respuesta, para que el comprador sepa que compra a través de un agente.",
             phone("14:21", '<div class="me">Busco un teclado de 61 teclas que llegue esta semana.</div><div class="ai">Encontré este en Tienda Ejemplo:</div>'
                   + product + '<div class="ai">¿Lo quieres con boleta o con factura?</div><div class="me">Con boleta.</div>', lang),
             code_block("create_checkout", a2s, [(None, step1, {"tax_document", "consumer_terms"})], legend)),
            ("Totales y avisos legales", "La tienda responde con el total en pesos y los avisos legales.",
             "Quién vende, con RUT y domicilio; el derecho a retracto y la garantía legal. Los avisos también llegan como mensajes del núcleo de UCP, así que hasta un agente que no conoce la extensión debe mostrarlos sin ocultarlos.",
             phone("14:21", totals
                   + '<div class="notice"><b>Vende</b>Tienda Ejemplo SpA · RUT 76.123.456-0 · Av. Ejemplo 123, Santiago</div>'
                   + '<div class="notice"><b>Derecho a retracto</b>Tienes derecho a retracto por 10 días desde que recibes el producto.</div>'
                   + '<div class="notice"><b>Garantía legal</b>Garantía legal de 6 meses: reparación, cambio o devolución, a tu elección.</div>'
                   + '<div class="ai small">Estás comprando a través de un asistente de IA.</div>', lang),
             code_block("checkout", s2a, [(None, step2, {"policies", "consumer_terms"})], legend)),
            ("Pago en la página del proveedor", "El comprador paga fuera del chat, en la página del proveedor.",
             "La tienda crea el pago con su propia cuenta de Webpay Plus y responde con un enlace (<code>continue_url</code>). El asistente solo abre ese enlace; el dinero va directo a la cuenta de la tienda.",
             phone("14:22", '<div class="me">Listo, lo compro.</div><div class="ai">Para pagar, abre la página de pago. Ahí pagas con Webpay Plus.</div>'
                   + '<div class="card"><b>Total a pagar: $194.980</b><div class="dim">Webpay Plus · tienda-ejemplo.cl</div><span class="paybtn">Abrir la página de pago ↗</span></div>'
                   + '<div class="ai small">El pago se hace en la página del proveedor, no en este chat.</div>', lang),
             code_block("complete_checkout", s2a, [(None, step3, set()), (profile_sub, step3_profile, {"cl.comercioia.webpay_plus"})], legend)),
            ("Boleta emitida al SII", "Con el pago confirmado, la tienda emite la boleta y la envía al SII.",
             "La tienda confirma el pago directamente con el proveedor. El pedido le devuelve al agente el folio, el RUT del emisor y el estado en el SII; el comprador recibe la boleta y la copia del contrato por correo.",
             phone("14:23", '<div class="ai">Tienda Ejemplo confirmó tu pago y emitió tu boleta:</div>' + receipt
                   + '<div class="ai small">Te llegó la copia del contrato por correo.</div>', lang),
             code_block(order_op, s2a, [(None, step4, {"tax_documents", "consumer_terms"})], legend)),
            ("Retracto y nota de crédito", "Si el comprador se retracta, la devolución lleva su nota de crédito.",
             "La tienda registra la devolución en el pedido con una nota de crédito electrónica (DTE 61) que hace referencia a la boleta original.",
             phone("10:05", '<div class="me">Me arrepentí del teclado. ¿Lo puedo devolver?</div>'
                   + '<div class="ai">Sí: estás dentro de los 10 días del derecho a retracto. Tienda Ejemplo explica cómo devolverlo en tienda-ejemplo.cl/retracto.</div>'
                   + '<div class="card"><b>Devolución completada</b><div class="row"><span>Nota de crédito</span><span>N° 88213</span></div>'
                   + '<div class="row"><span>Anula boleta</span><span>N° 4512330</span></div><div class="row tot"><span>Devuelto</span><span>$194.980</span></div></div>', lang),
             code_block(order_op, s2a, [(None, step5, {"tax_document"})], legend)),
        ]
    else:
        S = [
            ("“I'll take it”, with a boleta", "The agent asks for a boleta when it creates the checkout.",
             "It also declares that it is an AI assistant. The store echoes that back in its response, so the buyer knows they are buying through an agent.",
             phone("14:21", "<div class=\"me\">I'm looking for a 61-key keyboard that arrives this week.</div><div class=\"ai\">I found this one at Tienda Ejemplo:</div>"
                   + product + '<div class="ai">Do you want a boleta (consumer receipt) or a factura (business invoice)?</div><div class="me">A boleta, please.</div>', lang),
             code_block("create_checkout", a2s, [(None, step1, {"tax_document", "consumer_terms"})], legend)),
            ("Totals and legal notices", "The store answers with the total in pesos and the legal notices.",
             "Who sells, with RUT and address; the right of withdrawal and the legal warranty. The notices also arrive as core UCP messages, so even an agent that doesn't know the extension must show them without hiding them.",
             phone("14:21", totals
                   + '<div class="notice"><b>Seller</b>Tienda Ejemplo SpA · RUT 76.123.456-0 · Av. Ejemplo 123, Santiago</div>'
                   + '<div class="notice"><b>Right of withdrawal</b>You can withdraw within 10 days of receiving the product.</div>'
                   + '<div class="notice"><b>Legal warranty</b>6-month legal warranty: repair, replacement or refund, your choice.</div>'
                   + '<div class="ai small">You are buying through an AI assistant.</div>', lang),
             code_block("checkout", s2a, [(None, step2, {"policies", "consumer_terms"})], legend)),
            ("Payment on the provider's page", "The buyer pays outside the chat, on the provider's page.",
             "The store creates the payment with its own Webpay Plus account and answers with a link (<code>continue_url</code>). The assistant only opens that link; the money goes straight to the store's account.",
             phone("14:22", "<div class=\"me\">OK, I'll buy it.</div><div class=\"ai\">To pay, open the payment page. You'll pay there with Webpay Plus.</div>"
                   + '<div class="card"><b>Total to pay: $194.980</b><div class="dim">Webpay Plus · tienda-ejemplo.cl</div><span class="paybtn">Open the payment page ↗</span></div>'
                   + "<div class=\"ai small\">Payment happens on the provider's page, not in this chat.</div>", lang),
             code_block("complete_checkout", s2a, [(None, step3, set()), (profile_sub, step3_profile, {"cl.comercioia.webpay_plus"})], legend)),
            ("Boleta issued to the SII", "Once payment is confirmed, the store issues the boleta and sends it to the SII.",
             "The store confirms the payment directly with the provider. The order gives the agent the folio, the issuer's RUT and the SII status; the buyer gets the boleta and a copy of the contract by email.",
             phone("14:23", '<div class="ai">Tienda Ejemplo confirmed your payment and issued your boleta:</div>' + receipt
                   + '<div class="ai small">A copy of the contract was sent to your email.</div>', lang),
             code_block(order_op, s2a, [(None, step4, {"tax_documents", "consumer_terms"})], legend)),
            ("Withdrawal and credit note", "If the buyer withdraws, the refund carries its credit note.",
             "The store records the refund on the order with an electronic credit note (DTE 61) that references the original boleta.",
             phone("10:05", '<div class="me">I changed my mind about the keyboard. Can I return it?</div>'
                   + "<div class=\"ai\">Yes: you're within the 10-day right of withdrawal. Tienda Ejemplo explains how to return it at tienda-ejemplo.cl/retracto.</div>"
                   + '<div class="card"><b>Refund completed</b><div class="row"><span>Credit note</span><span>No. 88213</span></div>'
                   + '<div class="row"><span>Cancels boleta</span><span>No. 4512330</span></div><div class="row tot"><span>Refunded</span><span>$194.980</span></div></div>', lang),
             code_block(order_op, s2a, [(None, step5, {"tax_document"})], legend)),
        ]
    return S

def demo(lang):
    es = lang == "es"
    steps = demo_steps(lang)
    pid = "paso" if es else "step"
    n = len(steps)
    tabs = "\n".join(f'            <button type="button" id="tab-{i}" aria-controls="{pid}-{i}"><span class="n">{i:02d}</span><span>{t}</span></button>'
                     for i, (t, *_rest) in enumerate(steps, 1))
    panels = "\n".join(
        f'''          <div class="panel" id="{pid}-{i}">
            <div class="panel-copy"><p class="panel-n">{"Paso" if es else "Step"} {i} {"de" if es else "of"} {n}</p><h3>{h}</h3><p>{p}</p></div>
            {ph}
            {code}
          </div>''' for i, (_t, h, p, ph, code) in enumerate(steps, 1))
    return f'''<div class="demo-band">
      <div class="wrap">
        <div class="demo" data-demo>
          <div>
            <div class="steps" data-demo-tabs aria-label="{"Pasos de una compra" if es else "Steps of a purchase"}" hidden>
{tabs}
            </div>
            <p class="demo-note">{"Ejemplo ilustrativo con datos de prueba." if es else "Illustrative example with test data."}</p>
          </div>
          <div>
{panels}
          </div>
        </div>
      </div>
    </div>'''

# ---------------------------------------------------------------- landing pages
def landing(lang):
    es = lang == "es"
    T = {}
    if es:
        T.update(
            title="Comercio IA · La extensión chilena abierta para UCP y ACP",
            desc="Boleta, retracto, garantía legal, notas de crédito y medios de pago chilenos para que cualquier agente de IA cierre una venta legal en Chile, sobre UCP y ACP.",
            label="Propuesta abierta · versión 2026-10-09",
            h1="Comercio IA", h1sub="Boleta para personas, factura para empresas. Para cualquier agente de IA.",
            lead="Cuando un asistente de IA vende por una tienda chilena, la venta tiene que cumplir la ley: boleta o factura del SII, derecho a retracto, garantía legal y medios de pago locales. Comercio IA son las reglas abiertas para hacerlo, como complemento de los estándares de compra por IA de Google, Shopify, OpenAI y Stripe.",
            cta="Leer la especificación", cta_href="/spec/", alt_link="Ver una compra paso a paso", alt_href="#demo",
            covers=(("Extiende", ["UCP", "ACP"]), ("Medios de pago", ["Webpay Plus", "Oneclick Mall", "Mercado Pago", "Getnet", "Khipu"])),
            facts=[("Abierta", "Licencia Apache-2.0, como UCP y ACP. Cualquiera la implementa sin pedir permiso."),
                   ("La tienda vende", "El pago llega a la cuenta de la propia tienda. La especificación nunca toca los fondos."),
                   ("Compatible", "Un agente que no la conoce sigue funcionando, y los avisos legales igual le llegan.")],
        )
    else:
        T.update(
            title="Comercio IA · The open Chilean extension for UCP and ACP",
            desc="Chilean tax receipts, withdrawal rights, legal warranty, credit notes and payment methods, so any AI agent can make a legal sale in Chile. On UCP and ACP.",
            label="Open proposal · version 2026-10-09",
            h1="Comercio IA", h1sub="A boleta for consumers, a factura for businesses. For any AI agent.",
            lead="When an AI assistant sells on behalf of a Chilean store, the sale has to follow Chilean law: an SII tax receipt (boleta or factura), the right of withdrawal, the legal warranty and local payment methods. Comercio IA is the open set of rules to do that, as an add-on to the AI shopping standards from Google, Shopify, OpenAI and Stripe.",
            cta="Read the specification", cta_href="/en/spec/", alt_link="See a purchase step by step", alt_href="#demo",
            covers=(("Extends", ["UCP", "ACP"]), ("Payment methods", ["Webpay Plus", "Oneclick Mall", "Mercado Pago", "Getnet", "Khipu"])),
            facts=[("Open", "Apache-2.0 license, like UCP and ACP. Anyone can implement it without asking."),
                   ("The store sells", "Payment goes to the store's own account. The specification never touches funds."),
                   ("Compatible", "An agent that doesn't know it keeps working, and the legal notices still reach it.")],
        )
    facts = "\n".join(f'        <div><h2>{a}</h2><p>{b}</p></div>' for a, b in T["facts"])

    if es:
        gap_left = ["Catálogo y búsqueda", "Carro y checkout", "Pedido y ajustes", "Políticas y avisos", "Medios de pago enchufables"]
        gap_right = ["Boleta para personas, factura para empresas", "Derecho a retracto", "Garantía legal", "Notas de crédito", "Webpay, Mercado Pago, Getnet y Khipu"]
        rows = [
            ledger_row("cl.comercioia.shopping.", "tax_document", "Boleta o factura", "Boleta para personas; factura con RUT y giro para empresas. El pedido devuelve folio, RUT del emisor y estado en el SII.", "DL 825 · Res. SII 74/2020"),
            ledger_row("cl.comercioia.shopping.", "consumer_terms", "Información al consumidor", "En ventas a personas: identidad del vendedor, aviso de que compra a través de IA, despacho, cuotas con CAE y confirmación escrita.", "Ley 19.496 · DS 6/2021 · Res. SERNAC 33/2022"),
            ledger_row("cl.comercioia.shopping.", "credit_note", "Notas de crédito", "Cada devolución o retracto lleva su DTE 61, con referencia al documento original.", "DL 825 arts. 21 y 70"),
            ledger_row("cl.comercioia.policy.", "retracto", "Derecho a retracto", "10 días desde la recepción, 90 sin confirmación escrita, devolución en 45 días.", "Ley 19.496 art. 3 bis"),
            ledger_row("cl.comercioia.policy.", "garantia_legal", "Garantía legal", "6 meses desde la recepción: reparación, cambio o devolución, a elección del comprador.", "Ley 19.496 arts. 20 y 21"),
            ledger_row("cl.comercioia.", "webpay_plus · oneclick_mall · mercadopago · getnet · khipu", "Medios de pago chilenos", "La tienda cobra con su propia cuenta y el comprador paga en la página del proveedor.", "Documentación de cada proveedor"),
        ]
        who = [("/.well-known/ucp", "Tiendas y proveedores", "Vendas a personas o a empresas, declara la extensión y tus medios de pago en tu perfil. Si tu plataforma o ERP ya la implementa, solo la activas."),
               ("UCP · ACP", "Plataformas y ERP", "Implementa los esquemas en tus endpoints y ofrécelo a todas tus tiendas con tu propia marca."),
               ("document_choice", "Agentes de IA", "Asistentes personales y agentes de compra de empresas: anuncia las extensiones que soportas, pide boleta o factura y muestra cada aviso legal sin ocultarlo."),
               ("payment_handlers", "Proveedores de pago", "Publicamos tu medio de pago hasta que publiques el tuyo. Revísalo, cofírmalo o asúmelo.")]
        kv = [("Versión", "<code>2026-10-09</code>"), ("Estado", "Propuesta abierta: lista para implementar y comentar"), ("Espacio de nombres", "<code>cl.comercioia.*</code>"),
              ("Requiere", "UCP <code>2026-08-25</code> o posterior"), ("Licencia", "Apache-2.0"), ("Versión estable", "Enero de 2027, al cumplir el camino a la 1.0"), ("Próxima versión", '<code>2026-10-16</code>: <a href="https://github.com/Pintor-Project/comercioia/issues/1">referencias B2B</a> (orden de compra, HES, contrato)'),
              ("Contacto", '<a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a>')]
        asks = [("Comenta.", "Errores, campos que faltan, casos de tu negocio. Todo comentario se responde antes de la versión estable."),
                ("Cofirma.", "Plataformas, ERP, proveedores de pago y gremios pueden aparecer como cofirmantes de la versión estable."),
                ("Implementa.", "Gratis y sin pedir permiso. Si la implementas, avísanos y te listamos.")]
        S = dict(
            s1h='Los estándares llegan hasta donde <span class="sub">empieza la ley chilena.</span>',
            s1a="UCP y ACP traen", s1b="Comercio IA agrega",
            s2h='Tres extensiones, dos políticas <span class="sub">y cinco medios de pago.</span>',
            th=("Nombre", "Qué hace", "Base legal"),
            s3h='De «lo quiero» a una boleta <span class="sub">que el SII ya recibió.</span>',
            s3p="Lo que ve el comprador en su asistente, junto a lo que viaja entre el agente y la tienda. En rojo, lo que agrega Comercio IA.",
            seq_cap="La misma compra, como diagrama de secuencia",
            leg=("Núcleo de UCP/ACP y proveedor de pago", "Lo que agrega Comercio IA"),
            fine="Ningún estándar define todavía cómo devolver al comprador al agente después de pagar en una página externa (propuesta UCP #486), así que el agente se entera del pago por el pedido. Si compra una empresa, el paso 02 pide factura con su RUT y giro, el paso 09 emite una factura (33) y, en general, el retracto no aplica, salvo cuando la compradora es micro o pequeña empresa (Ley 20.416).",
            s4h='Cada uno implementa <span class="sub">su parte.</span>',
            s5h='Lista para implementar. <span class="sub">Estable tras la primera venta real.</span>', s5id="participa",
            s6h='Cinco condiciones <span class="sub">para declararla estable.</span>',
            road=[("Hecho", "done", "Especificación y esquemas publicados", "9 de octubre de 2026, en comercioia.cl."),
                  ("Hecho", "done", "Repositorio público y periodo de comentarios", "Comentarios abiertos hasta el 30 de noviembre de 2026."),
                  ("En diseño", "", "Implementación de referencia", "Synaptik Checkout IA: las tres extensiones y Webpay Plus, con boleta automática."),
                  ("Pendiente", "", "Primeras ventas reales", "Al menos una boleta, una factura y un retracto con nota de crédito."),
                  ("En curso", "", "Revisión legal y validación externa", "Respuesta a las preguntas abiertas y un cofirmante o implementador externo.")],
            road_note="Las extensiones y los medios de pago se versionan por separado: Oneclick Mall, Getnet y Khipu pueden seguir como propuesta cuando el resto ya sea estable.",
        )
    else:
        gap_left = ["Catalog and search", "Cart and checkout", "Order and adjustments", "Policies and notices", "Pluggable payment methods"]
        gap_right = ["A boleta for consumers, a factura for businesses", "Right of withdrawal (retracto)", "Legal warranty", "Credit notes", "Webpay, Mercado Pago, Getnet and Khipu"]
        rows = [
            ledger_row("cl.comercioia.shopping.", "tax_document", "Boleta or factura", "A boleta for consumers; a factura with RUT and line of business for companies. The order returns the folio, issuer RUT and SII status.", "DL 825 · SII Res. 74/2020"),
            ledger_row("cl.comercioia.shopping.", "consumer_terms", "Consumer information", "In consumer sales: seller identity, notice that the purchase is made through AI, delivery, installments with CAE and written confirmation.", "Ley 19.496 · DS 6/2021 · SERNAC Res. 33/2022"),
            ledger_row("cl.comercioia.shopping.", "credit_note", "Credit notes", "Every refund or withdrawal carries its DTE 61, referencing the original document.", "DL 825 arts. 21 and 70"),
            ledger_row("cl.comercioia.policy.", "retracto", "Right of withdrawal", "10 days from receipt, 90 without written confirmation, refund within 45 days.", "Ley 19.496 art. 3 bis"),
            ledger_row("cl.comercioia.policy.", "garantia_legal", "Legal warranty", "6 months from receipt: repair, replacement or refund, at the buyer's choice.", "Ley 19.496 arts. 20 and 21"),
            ledger_row("cl.comercioia.", "webpay_plus · oneclick_mall · mercadopago · getnet · khipu", "Chilean payment methods", "The store charges with its own account and the buyer pays on the provider's page.", "Each provider's documentation"),
        ]
        who = [("/.well-known/ucp", "Stores and suppliers", "Whether you sell to consumers or to companies, declare the extension and your payment methods in your profile. If your platform or ERP already implements it, just turn it on."),
               ("UCP · ACP", "Platforms and ERPs", "Implement the schemas in your endpoints and offer it to all your stores under your own brand."),
               ("document_choice", "AI agents", "Personal assistants and corporate purchasing agents: announce the extensions you support, ask for a boleta or factura, and show every legal notice without hiding it."),
               ("payment_handlers", "Payment providers", "We publish your payment method until you publish your own. Review it, co-sign it or take it over.")]
        kv = [("Version", "<code>2026-10-09</code>"), ("Status", "Open proposal: ready to implement and comment on"), ("Namespace", "<code>cl.comercioia.*</code>"),
              ("Requires", "UCP <code>2026-08-25</code> or later"), ("License", "Apache-2.0"), ("Stable release", "January 2027, once the path to 1.0 is complete"), ("Next version", '<code>2026-10-16</code>: <a href="https://github.com/Pintor-Project/comercioia/issues/1">B2B references</a> (purchase order, HES, contract)'),
              ("Contact", '<a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a>')]
        asks = [("Comment.", "Errors, missing fields, cases from your business. Every comment gets an answer before the stable release."),
                ("Co-sign.", "Platforms, ERPs, payment providers and trade associations can be listed as co-signers of the stable release."),
                ("Implement.", "Free and without asking. If you implement it, tell us and we'll list you.")]
        S = dict(
            s1h='The standards stop <span class="sub">where Chilean law starts.</span>',
            s1a="UCP and ACP cover", s1b="Comercio IA adds",
            s2h='Three extensions, two policies <span class="sub">and five payment methods.</span>',
            th=("Name", "What it does", "Legal basis"),
            s3h='From “I\'ll take it” to a boleta <span class="sub">the SII has received.</span>',
            s3p="What the buyer sees in their assistant, next to what travels between the agent and the store. In red, what Comercio IA adds.",
            seq_cap="The same purchase, as a sequence diagram",
            leg=("UCP/ACP core and payment provider", "What Comercio IA adds"),
            fine="Neither standard yet defines how to return the buyer to the agent after paying on an external page (UCP proposal #486), so the agent learns about the payment from the order. When a company buys, step 02 asks for a factura with its RUT and line of business, step 09 issues a factura (33), and the right of withdrawal generally does not apply, except when the buyer is a micro or small business (Ley 20.416).",
            s4h='Everyone implements <span class="sub">their part.</span>',
            s5h='Ready to implement. <span class="sub">Stable after the first real sale.</span>', s5id="participate",
            s6h='Five conditions <span class="sub">before we call it stable.</span>',
            road=[("Done", "done", "Specification and schemas published", "9 October 2026, at comercioia.cl."),
                  ("Done", "done", "Public repository and comment period", "Comments open until 30 November 2026."),
                  ("In design", "", "Reference implementation", "Synaptik Checkout IA: the three extensions and Webpay Plus, with automatic boleta."),
                  ("Pending", "", "First real sales", "At least one boleta, one factura and one withdrawal with a credit note."),
                  ("In progress", "", "Legal review and outside validation", "Answers to the open questions and one co-signer or outside implementer.")],
            road_note="Extensions and payment methods are versioned separately: Oneclick Mall, Getnet and Khipu can stay as proposals once the rest is stable.",
        )
    li = lambda xs: "\n".join(f"            <li>{x}</li>" for x in xs)
    who_html = "\n".join(f'        <div>\n          {ILL_WHO[i]}\n          <p class="tag">{t}</p><h3>{h}</h3><p>{p}</p>\n        </div>' for i, (t, h, p) in enumerate(who))
    kv_html = "\n".join(f"          <dt>{a}</dt><dd>{b}</dd>" for a, b in kv)
    asks_html = "\n".join(f"          <li><b>{a}</b><span>{b}</span></li>" for a, b in asks)
    rows_html = "\n".join("          " + r for r in rows)
    road_html = "\n".join(f'          <li class="{c}"><span class="st">{st}</span><b>{t}</b><span class="d">{d}</span></li>' for st, c, t, d in S["road"])
    covers_html = "\n".join(f'        <dt>{a}</dt><dd>{"".join(f"<span>{x}</span>" for x in xs)}</dd>' for a, xs in T["covers"])
    version = re.search(r"\d{4}-\d{2}-\d{2}", T["label"]).group(0)
    canonical = "https://comercioia.cl/" if es else "https://comercioia.cl/en/"
    return f'''{head(lang, T["title"], T["desc"], canonical, "https://comercioia.cl/", "https://comercioia.cl/en/", extra=chr(10) + '<script src="/assets/demo.js" defer></script>')}
<body>
{masthead(lang, "home")}
{timbre_symbol()}

<main id="main">
  <section class="hero">
    <div class="wrap">
      <div class="hero-grid">
        <div>
          <p class="status">{T["label"]}</p>
          <h1>{T["h1"]}<span class="sub">{T["h1sub"]}</span></h1>
          <p class="lead">{T["lead"]}</p>
          <div class="actions">
            <a class="btn" href="{T["cta_href"]}">{T["cta"]} <span aria-hidden="true">→</span></a>
            <a class="btn ghost" href="{T["alt_href"]}">{T["alt_link"]}</a>
          </div>
        </div>
        {hero_art(lang, version)}
      </div>
      <dl class="covers">
{covers_html}
      </dl>
      <div class="facts">
{facts}
      </div>
    </div>
  </section>

{intro_section(lang)}

  <section class="section" id="demo">
    <div class="wrap center">
      <h2>{S["s3h"]}</h2>
      <p class="intro-p">{S["s3p"]}</p>
    </div>
    {demo(lang)}
    <div class="wrap">
      <h3 class="seq-head">{S["seq_cap"]}</h3>
      <div class="seq">
{seq_svg(lang)}
      </div>
      {seq_text(lang)}
      <p class="legend"><span>{S["leg"][0]}</span><span class="ours">{S["leg"][1]}</span></p>
      <p class="fine">{S["fine"]}</p>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{S["s1h"]}</h2>
      <div class="gap">
        <div>
          <h3>{S["s1a"]}</h3>
          <ul>
{li(gap_left)}
          </ul>
        </div>
        <div class="ours">
          <h3>{S["s1b"]}</h3>
          <ul>
{li(gap_right)}
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{S["s2h"]}</h2>
      <table class="ledger">
        <thead><tr><th>{S["th"][0]}</th><th>{S["th"][1]}</th><th>{S["th"][2]}</th></tr></thead>
        <tbody>
{rows_html}
        </tbody>
      </table>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{S["s4h"]}</h2>
      <div class="who">
{who_html}
      </div>
    </div>
  </section>

  <section class="section" id="{S["s5id"]}">
    <div class="wrap">
      <h2>{S["s5h"]}</h2>
      <div class="status-grid">
        <dl class="kv">
{kv_html}
        </dl>
        <ul class="asks">
{asks_html}
        </ul>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <h2>{S["s6h"]}</h2>
      <ol class="road">
{road_html}
      </ol>
      <p class="fine">{S["road_note"]}</p>
    </div>
  </section>
</main>

{footer(lang)}
</body>
</html>
'''

open(os.path.join(SITE, "index.html"), "w").write(landing("es"))
os.makedirs(os.path.join(SITE, "en"), exist_ok=True)
open(os.path.join(SITE, "en", "index.html"), "w").write(landing("en"))

# ---------------------------------------------------------------- privacy + accessibility pages
GA_COOKIE = "_ga_CCFR41KLL9"
DOCS = {
    ("es", "privacy"): dict(
        path="privacidad/index.html", url=BASE + "/privacidad/", alt=BASE + "/en/privacy/",
        title="Política de privacidad · Comercio IA",
        desc="Qué datos trata comercioia.cl, para qué, con qué proveedores y cómo ejercer tus derechos. Analítica solo con tu consentimiento.",
        status="Vigente desde el 9 de octubre de 2026", h1="Política de privacidad", sub="Sin cookies hasta que digas que sí.",
        lede="Este sitio publica una especificación técnica. No tiene cuentas, formularios ni publicidad. Solo usamos analítica para saber qué páginas se leen, y solo si la aceptas.",
        sections=[
            ("responsable", "Quién es responsable",
             "<p>Pintor Project SpA, San Pío X 2460, Providencia, Santiago, Chile, impulsa Comercio IA y es responsable de los datos que se tratan en comercioia.cl. Escríbenos a <a href=\"mailto:contacto@comercioia.cl\">contacto@comercioia.cl</a>.</p>"),
            ("datos", "Qué datos tratamos",
             "<dl class=\"kv\">"
             "<dt>Al visitar el sitio</dt><dd>Nuestro proveedor de alojamiento, Microsoft Azure, procesa tu dirección IP y los datos técnicos de cada solicitud para entregarte las páginas y proteger el servicio. Nosotros no guardamos registros de visitas.</dd>"
             "<dt>Si aceptas la analítica</dt><dd>Google Analytics 4 registra las páginas que ves, el desplazamiento, los clics en enlaces externos, de dónde llegaste, tu tipo de dispositivo, navegador e idioma, y tu ubicación aproximada (país y ciudad). Google Analytics 4 no registra ni guarda direcciones IP. Desactivamos Google Signals y la personalización de anuncios.</dd>"
             "<dt>Tus preferencias</dt><dd>Tu decisión sobre la analítica y tus ajustes de lectura se guardan en tu propio navegador (<code>cia-consent</code> y <code>cia-a11y</code>). No se envían a nadie.</dd>"
             "<dt>Si nos escribes</dt><dd>Usamos tu correo y lo que nos cuentes para responderte y dar seguimiento a tus comentarios sobre la especificación. El correo está alojado en Microsoft 365.</dd>"
             "<dt>En GitHub</dt><dd>Los issues y pull requests del repositorio son públicos y se rigen por la política de privacidad de GitHub.</dd>"
             "</dl>"),
            ("cookies", "Cookies",
             "<p>Sin tu consentimiento el sitio no instala cookies. Si aceptas la analítica, Google Analytics instala estas dos:</p>"
             "<dl class=\"kv\">"
             f"<dt><code>_ga</code></dt><dd>Distingue visitantes de forma anónima. Dura 2 años.</dd>"
             f"<dt><code>{GA_COOKIE}</code></dt><dd>Mantiene el estado de la sesión. Dura 2 años.</dd>"
             "</dl>"
             "<p>Puedes cambiar tu decisión cuando quieras: <button type=\"button\" class=\"linkish\" data-cookie-settings hidden>preferencias de cookies</button>. Si la retiras, borramos estas cookies de tu navegador.</p>"),
            ("finalidad", "Para qué y con qué base",
             "<dl class=\"kv\">"
             "<dt>Analítica</dt><dd>Saber qué partes de la especificación se leen y mejorarlas. Base: tu consentimiento, que puedes retirar.</dd>"
             "<dt>Funcionamiento y seguridad</dt><dd>Entregar las páginas y protegerlas de abusos. Base: es necesario para prestar el servicio.</dd>"
             "<dt>Correos</dt><dd>Responderte. Base: tu propia solicitud.</dd>"
             "</dl>"
             "<p>No vendemos ni cedemos datos, no hacemos perfiles y no tomamos decisiones automatizadas sobre ti.</p>"),
            ("proveedores", "Proveedores y transferencias",
             "<p>Google LLC (analítica) y Microsoft Corporation (alojamiento y correo) pueden tratar los datos fuera de Chile, incluso en Estados Unidos, bajo sus términos de tratamiento de datos. Conservamos los datos de analítica durante 14 meses, y los correos mientras sean necesarios para responder y dar seguimiento a la especificación.</p>"),
            ("derechos", "Tus derechos",
             "<p>Puedes pedir acceso, rectificación, cancelación o bloqueo de tus datos (Ley 19.628). Desde el 1 de diciembre de 2026, con la Ley 21.719, se suman la portabilidad, la oposición y los derechos frente a decisiones automatizadas, y podrás reclamar ante la Agencia de Protección de Datos Personales. Escribe a <a href=\"mailto:contacto@comercioia.cl\">contacto@comercioia.cl</a>; respondemos dentro de los plazos legales.</p>"),
            ("cambios", "Cambios",
             "<p>Si cambiamos esta política, publicaremos aquí la nueva versión con su fecha. El historial completo está en el <a href=\"https://github.com/Pintor-Project/comercioia\">repositorio público</a>.</p>"),
        ]),
    ("en", "privacy"): dict(
        path="en/privacy/index.html", url=BASE + "/en/privacy/", alt=BASE + "/privacidad/",
        title="Privacy policy · Comercio IA",
        desc="What data comercioia.cl processes, why, with which providers and how to exercise your rights. Analytics only with your consent.",
        status="In force from 9 October 2026", h1="Privacy policy", sub="No cookies until you say yes.",
        lede="This site publishes a technical specification. It has no accounts, forms or ads. We only use analytics to learn which pages are read, and only if you accept it.",
        sections=[
            ("controller", "Who is responsible",
             "<p>Pintor Project SpA, San Pío X 2460, Providencia, Santiago, Chile, leads Comercio IA and is responsible for the data processed on comercioia.cl. Write to us at <a href=\"mailto:contacto@comercioia.cl\">contacto@comercioia.cl</a>.</p>"),
            ("data", "What data we process",
             "<dl class=\"kv\">"
             "<dt>When you visit</dt><dd>Our hosting provider, Microsoft Azure, processes your IP address and the technical data of each request to serve the pages and protect the service. We keep no visit logs ourselves.</dd>"
             "<dt>If you accept analytics</dt><dd>Google Analytics 4 records the pages you view, scrolling, clicks on outbound links, where you came from, your device type, browser and language, and your approximate location (country and city). Google Analytics 4 does not log or store IP addresses. We turned off Google Signals and ad personalization.</dd>"
             "<dt>Your preferences</dt><dd>Your analytics choice and your reading settings are stored in your own browser (<code>cia-consent</code> and <code>cia-a11y</code>). They are not sent anywhere.</dd>"
             "<dt>If you email us</dt><dd>We use your address and what you tell us to reply and follow up on your comments about the specification. Email is hosted on Microsoft 365.</dd>"
             "<dt>On GitHub</dt><dd>Issues and pull requests in the repository are public and governed by GitHub's privacy policy.</dd>"
             "</dl>"),
            ("cookies", "Cookies",
             "<p>Without your consent the site sets no cookies. If you accept analytics, Google Analytics sets these two:</p>"
             "<dl class=\"kv\">"
             f"<dt><code>_ga</code></dt><dd>Tells visitors apart anonymously. Lasts 2 years.</dd>"
             f"<dt><code>{GA_COOKIE}</code></dt><dd>Keeps the session state. Lasts 2 years.</dd>"
             "</dl>"
             "<p>You can change your choice at any time: <button type=\"button\" class=\"linkish\" data-cookie-settings hidden>cookie preferences</button>. If you withdraw it, we delete these cookies from your browser.</p>"),
            ("purpose", "Why, and on what basis",
             "<dl class=\"kv\">"
             "<dt>Analytics</dt><dd>To learn which parts of the specification are read and improve them. Basis: your consent, which you can withdraw.</dd>"
             "<dt>Operation and security</dt><dd>To serve the pages and protect them from abuse. Basis: necessary to provide the service.</dd>"
             "<dt>Email</dt><dd>To reply to you. Basis: your own request.</dd>"
             "</dl>"
             "<p>We do not sell or share data, build profiles, or make automated decisions about you.</p>"),
            ("providers", "Providers and transfers",
             "<p>Google LLC (analytics) and Microsoft Corporation (hosting and email) may process data outside Chile, including in the United States, under their data processing terms. We keep analytics data for 14 months, and emails for as long as needed to reply and follow up on the specification.</p>"),
            ("rights", "Your rights",
             "<p>You can request access to, correction, deletion or blocking of your data (Chilean Ley 19.628). From 1 December 2026, Ley 21.719 adds portability, objection and rights regarding automated decisions, and you will be able to complain to the Chilean Personal Data Protection Agency. Write to <a href=\"mailto:contacto@comercioia.cl\">contacto@comercioia.cl</a>; we reply within the legal deadlines.</p>"),
            ("changes", "Changes",
             "<p>If we change this policy, we will publish the new version here with its date. The full history is in the <a href=\"https://github.com/Pintor-Project/comercioia\">public repository</a>.</p>"),
        ]),
    ("es", "accessibility"): dict(
        path="accesibilidad/index.html", url=BASE + "/accesibilidad/", alt=BASE + "/en/accessibility/",
        title="Accesibilidad · Comercio IA",
        desc="Cómo hacemos que comercioia.cl se pueda leer con cualquier capacidad: ajustes de lectura, pautas WCAG 2.2 AA, limitaciones conocidas y contacto.",
        status="Evaluación propia del 9 de octubre de 2026", h1="Accesibilidad", sub="Una especificación abierta tiene que poder leerla cualquiera.",
        lede="Seguimos las pautas WCAG 2.2 nivel AA y agregamos ajustes de lectura propios, sin herramientas de terceros. Si algo no te funciona, cuéntanos.",
        sections=[
            ("ajustes", "Ajustes de lectura",
             "<p>El botón redondo con el símbolo de accesibilidad, abajo a la izquierda, abre estos ajustes. Se guardan en tu navegador y se aplican en todas las páginas.</p>"
             "<dl class=\"kv\">"
             "<dt>Tamaño del texto</dt><dd>Agranda el texto un 15 % o un 30 %, además del zoom del navegador.</dd>"
             "<dt>Fuente más legible</dt><dd>Cambia a Atkinson Hyperlegible, diseñada por el Braille Institute para personas con baja visión.</dd>"
             "<dt>Más espacio</dt><dd>Aumenta el interlineado y el espacio entre letras y palabras.</dd>"
             "<dt>Subrayar enlaces</dt><dd>Marca todos los enlaces, sin depender del color.</dd>"
             "<dt>Alto contraste</dt><dd>Lleva todo el texto secundario al color principal.</dd>"
             "<dt>Detener animaciones</dt><dd>Quita todo movimiento. El sitio ya respeta la opción «reducir movimiento» de tu sistema.</dd>"
             "</dl>"
             "<p>No usamos superposiciones de accesibilidad de terceros. Estos ajustes son parte del sitio y no reemplazan las herramientas de tu sistema, como el lector de pantalla o la lupa.</p>"),
            ("como", "Qué hicimos",
             "<ul>"
             "<li>HTML semántico con encabezados en orden, regiones y un enlace para saltar al contenido.</li>"
             "<li>Todo se puede usar con teclado, con el foco siempre visible.</li>"
             "<li>Contraste de al menos 4,5:1 en el texto, en modo claro y oscuro.</li>"
             "<li>Idioma declarado en cada página y en las frases en otro idioma.</li>"
             "<li>Texto alternativo en las imágenes y el diagrama de una compra también como lista de pasos.</li>"
             "<li>Se lee bien con zoom de 200 % y en pantallas de 320 px de ancho.</li>"
             "<li>Fuentes alojadas en el propio sitio: nada se carga desde terceros antes de tu consentimiento.</li>"
             "</ul>"),
            ("limites", "Limitaciones conocidas",
             "<ul>"
             "<li>Los esquemas JSON son archivos técnicos para programas; su explicación está en la especificación.</li>"
             "<li>Algunos bloques de código de la especificación son anchos y se desplazan horizontalmente.</li>"
             "<li>Esta declaración se basa en una evaluación propia, sin auditoría externa todavía.</li>"
             "</ul>"),
            ("marco", "Marco de referencia",
             "<p>En Chile, la Ley 20.422 establece normas sobre igualdad de oportunidades e inclusión social de personas con discapacidad, y la norma técnica para sitios web del Estado (DS N° 1 de 2015) se basa en las pautas WCAG. Comercio IA no es un sitio del Estado, pero sigue esas pautas de forma voluntaria.</p>"),
            ("contacto", "Cuéntanos",
             "<p>Si encuentras una barrera o necesitas el contenido en otro formato, escribe a <a href=\"mailto:contacto@comercioia.cl?subject=Accesibilidad\">contacto@comercioia.cl</a> con el asunto «Accesibilidad». Te respondemos en un máximo de 10 días hábiles.</p>"),
        ]),
    ("en", "accessibility"): dict(
        path="en/accessibility/index.html", url=BASE + "/en/accessibility/", alt=BASE + "/accesibilidad/",
        title="Accessibility · Comercio IA",
        desc="How we make comercioia.cl readable for everyone: reading settings, WCAG 2.2 AA, known limitations and contact.",
        status="Self-assessed on 9 October 2026", h1="Accessibility", sub="An open specification has to be readable by anyone.",
        lede="We follow WCAG 2.2 level AA and add our own reading settings, with no third-party tools. If something doesn't work for you, tell us.",
        sections=[
            ("settings", "Reading settings",
             "<p>The round button with the accessibility symbol, bottom left, opens these settings. They are stored in your browser and apply on every page.</p>"
             "<dl class=\"kv\">"
             "<dt>Text size</dt><dd>Enlarges text by 15% or 30%, on top of browser zoom.</dd>"
             "<dt>More legible font</dt><dd>Switches to Atkinson Hyperlegible, designed by the Braille Institute for people with low vision.</dd>"
             "<dt>More spacing</dt><dd>Increases line, letter and word spacing.</dd>"
             "<dt>Underline links</dt><dd>Marks every link without relying on color.</dd>"
             "<dt>High contrast</dt><dd>Brings all secondary text to the main text color.</dd>"
             "<dt>Stop animations</dt><dd>Removes all motion. The site already respects your system's “reduce motion” setting.</dd>"
             "</dl>"
             "<p>We use no third-party accessibility overlays. These settings are part of the site and don't replace your system's tools, such as a screen reader or magnifier.</p>"),
            ("how", "What we did",
             "<ul>"
             "<li>Semantic HTML with headings in order, landmarks and a skip-to-content link.</li>"
             "<li>Everything works with a keyboard, with focus always visible.</li>"
             "<li>Text contrast of at least 4.5:1, in light and dark mode.</li>"
             "<li>Language declared on every page and on phrases in another language.</li>"
             "<li>Alternative text on images, and the purchase diagram also as a list of steps.</li>"
             "<li>Reads well at 200% zoom and on 320 px wide screens.</li>"
             "<li>Fonts hosted on the site itself: nothing loads from third parties before your consent.</li>"
             "</ul>"),
            ("limits", "Known limitations",
             "<ul>"
             "<li>The JSON schemas are technical files for programs; the specification explains them.</li>"
             "<li>Some code blocks in the specification are wide and scroll horizontally.</li>"
             "<li>The example receipt on the home page is in Spanish, as a Chilean store would issue it.</li>"
             "<li>This statement is based on a self-assessment, with no external audit yet.</li>"
             "</ul>"),
            ("framework", "Framework",
             "<p>In Chile, Ley 20.422 sets rules on equal opportunities and social inclusion for people with disabilities, and the technical standard for government websites (DS No. 1 of 2015) is based on WCAG. Comercio IA is not a government site, but follows those guidelines voluntarily.</p>"),
            ("contact", "Tell us",
             "<p>If you find a barrier or need the content in another format, write to <a href=\"mailto:contacto@comercioia.cl?subject=Accessibility\">contacto@comercioia.cl</a> with the subject “Accessibility”. We reply within 10 business days.</p>"),
        ]),
}

def doc_page(lang, kind, d):
    es = lang == "es"
    toc = "\n".join(f'      <li><a href="#{i}">{h}</a></li>' for i, h, _ in d["sections"])
    body = "\n".join(f'    <section id="{i}">\n      <h2>{h}</h2>\n      {b}\n    </section>' for i, h, b in d["sections"])
    alt_es, alt_en = (d["url"], d["alt"]) if es else (d["alt"], d["url"])
    return f'''{head(lang, d["title"], d["desc"], d["url"], alt_es, alt_en, "page")}
<body>
{masthead(lang, kind)}

<div class="wrap spec">
  <nav class="toc" aria-label="{"Contenido" if es else "Contents"}">
    <ol>
{toc}
    </ol>
  </nav>

  <main id="main" class="spec-body">
    <section id="intro">
      <p class="status">{d["status"]}</p>
      <h1>{d["h1"]}<span class="sub">{d["sub"]}</span></h1>
      <p class="lede">{d["lede"]}</p>
    </section>
{body}
  </main>
</div>

{footer(lang)}
</body>
</html>
'''

for (lang, kind), d in DOCS.items():
    path = os.path.join(SITE, d["path"])
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w").write(doc_page(lang, kind, d))

# ---------------------------------------------------------------- hand-written pages: chrome + metadata
FONT_RE = re.compile(r'(?:<link rel="preconnect" href="https://fonts.googleapis.com">\s*<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\s*<link rel="stylesheet" href="https://fonts.googleapis.com/css2\?[^"]+">'
                     r'|<link rel="preload" href="/assets/fonts/[^"]+\.woff2"[^>]*>(?:\s*<link rel="preload" href="/assets/fonts/[^"]+\.woff2"[^>]*>)*)', re.S)
ICON_RE = re.compile(r'<link rel="icon" href="data:image/svg\+xml,[^"]+">|<link rel="icon" href="/favicon\.svg"[^>]*>\s*<link rel="icon" href="/favicon-192\.png"[^>]*>')
SEO_RE = re.compile(r'<!-- seo -->.*?<!-- /seo -->', re.S)
for rel, lang, cur in (("spec/index.html", "es", "spec"), ("en/spec/index.html", "en", "spec"), ("cumplimiento/index.html", "es", "compliance"), ("en/compliance/index.html", "en", "compliance")):
    path = os.path.join(SITE, rel)
    s = open(path).read()
    s = FONT_RE.sub(lambda m: FONTS, s)
    s = ICON_RE.sub(lambda m: ICON, s)
    title = re.search(r"<title>(.*?)</title>", s).group(1)
    desc = re.search(r'<meta name="description" content="([^"]*)">', s).group(1)
    url = re.search(r'<link rel="canonical" href="([^"]+)">', s).group(1)
    block = seo(lang, title, desc, url, "article")
    if SEO_RE.search(s):
        s = SEO_RE.sub(lambda m: block, s)
    else:
        s = re.sub(r'(<link rel="canonical" href="[^"]+">)', lambda m: m.group(1) + "\n" + block, s, count=1)
    if 'hreflang="x-default"' not in s:
        es_alt = re.search(r'<link rel="alternate" hreflang="es-CL" href="([^"]+)">', s).group(1)
        s = s.replace('<link rel="canonical"', f'<link rel="alternate" hreflang="x-default" href="{es_alt}">\n<link rel="canonical"', 1)
    s = re.sub(r'<a class="skip".*?</header>(?:\s*<button type="button" class="a11y-fab".*?</button>)?', lambda m: masthead(lang, cur), s, flags=re.S)
    s = re.sub(r'<footer class="[^"]*">.*?</footer>', lambda m: footer(lang), s, flags=re.S)
    open(path, "w").write(s)

# ---------------------------------------------------------------- sitemap
PAIRS = [("/", "/en/"), ("/spec/", "/en/spec/"), ("/cumplimiento/", "/en/compliance/"),
         ("/privacidad/", "/en/privacy/"), ("/accesibilidad/", "/en/accessibility/")]
urls = []
for es_p, en_p in PAIRS:
    alts = (f'    <xhtml:link rel="alternate" hreflang="es-CL" href="{BASE}{es_p}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="en" href="{BASE}{en_p}"/>\n'
            f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{es_p}"/>')
    for loc in (es_p, en_p):
        urls.append(f"  <url>\n    <loc>{BASE}{loc}</loc>\n    <lastmod>{LASTMOD}</lastmod>\n{alts}\n  </url>")
open(os.path.join(SITE, "sitemap.xml"), "w").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
    + "\n".join(urls) + "\n</urlset>\n")

nf = f'''<!doctype html>
<html lang="es-CL">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página no encontrada · Comercio IA</title>
<meta name="robots" content="noindex">
{ICON}
{FONTS}
<link rel="stylesheet" href="/assets/site.css">
<script src="/assets/site.js" defer></script>
</head>
<body>
{masthead("es", "")}
<main id="main" class="wrap" style="padding-top:96px;padding-bottom:120px">
  <p class="label"><span class="dot"></span>404</p>
  <h1 style="margin-top:20px">Página no encontrada.<span class="sub" lang="en">Page not found.</span></h1>
  <p class="lead" style="margin-top:28px"><a href="/">Inicio</a> · <a href="/spec/">Especificación</a> · <a href="/en/" lang="en">English</a></p>
</main>
{footer("es")}
</body>
</html>
'''
open(os.path.join(SITE, "404.html"), "w").write(nf)
print("built")
