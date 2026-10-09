"""Builds the Comercio IA landing pages (es, en), the timbre patterns, and
refreshes header/footer/fonts on the spec pages. Usage: python3 build.py <site_dir>"""
import os, random, re, sys

SITE = sys.argv[1]
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500;600&display=swap">')
ICON = ("<link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
        "%3Crect x='2' y='6' width='28' height='20' fill='white' stroke='%23C8102E' stroke-width='3'/%3E"
        "%3Ctext x='16' y='21' font-family='monospace' font-size='12' font-weight='700' fill='%23C8102E' text-anchor='middle'%3Ecl%3C/text%3E%3C/svg%3E\">")

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

# ---------------------------------------------------------------- shared chrome
def masthead(lang, current):
    if lang == "es":
        links = [("/spec/", "Especificación", "spec"), ("/spec/#esquemas", "Esquemas", "schemas"), ("/#participa", "Participa", "join")]
        home, other, other_label, other_lang = "/", "/en/" if current != "spec" else "/en/spec/", "English", "en"
    else:
        links = [("/en/spec/", "Specification", "spec"), ("/en/spec/#schemas", "Schemas", "schemas"), ("/en/#participate", "Participate", "join")]
        home, other, other_label, other_lang = "/en/", "/" if current != "spec" else "/spec/", "Español", "es-CL"
    cur = ' aria-current="page"'
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
</header>'''

def footer(lang):
    if lang == "es":
        return '''<footer class="footer">
  <div class="wrap">
    <p>Iniciativa abierta impulsada por <a href="https://pintorproject.cl">Pintor Project</a>. Implementación de referencia: <a href="https://synaptiktech.com">Synaptik Checkout</a>.</p>
    <p class="mono"><a href="/spec/">Especificación</a> · <a href="/spec/#esquemas">Esquemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="legal">Especificación y esquemas bajo licencia Apache-2.0. No es asesoría legal. Comercio IA no está afiliado a Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu ni al SII, ni cuenta con su respaldo; las marcas pertenecen a sus dueños.</p>
  </div>
</footer>'''
    return '''<footer class="footer">
  <div class="wrap">
    <p>An open initiative led by <a href="https://pintorproject.cl">Pintor Project</a>. Reference implementation: <a href="https://synaptiktech.com">Synaptik Checkout</a>.</p>
    <p class="mono"><a href="/en/spec/">Specification</a> · <a href="/en/spec/#schemas">Schemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="legal">Specification and schemas under the Apache-2.0 license. Not legal advice. Comercio IA is not affiliated with or endorsed by Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu or the SII; trademarks belong to their owners.</p>
  </div>
</footer>'''

RECEIPT_LINES = [
    '<div class="rutbox"><span>R.U.T.: 76.123.456-0</span><span>BOLETA ELECTRÓNICA</span><span>N° 4512330</span><span>EJEMPLO</span></div>',
    '<div class="c">TIENDA EJEMPLO SPA</div>',
    '<div class="c sm">Av. Ejemplo 123, Santiago</div>',
    '<div class="hr"></div>',
    '<div class="r"><span>09/10/26 14:22</span><span>vía agente IA</span></div>',
    '<div class="hr"></div>',
    '<div class="r"><span>Teclado 61 teclas</span><span>$189.990</span></div>',
    '<div class="r"><span>Despacho RM</span><span>$4.990</span></div>',
    '<div class="hr"></div>',
    '<div class="r tot"><span>TOTAL</span><span>$194.980</span></div>',
    '<div class="r sm"><span>IVA incluido</span><span>$31.131</span></div>',
    '<div class="r sm"><span>Webpay Plus</span><span>aprobado</span></div>',
    '<div class="hr"></div>',
    '<div class="sm">Derecho a retracto: 10 días</div>',
    '<div class="sm">Garantía legal: 6 meses</div>',
    '<img src="/assets/timbre-receipt.svg" alt="">',
    '<div class="c sm">Timbre electrónico · ejemplo</div>',
    '<div class="c sm ns">cl.comercioia.shopping.tax_document</div>',
]

def receipt(lang):
    out = []
    for i, l in enumerate(RECEIPT_LINES):
        if l.startswith('<img'):
            out.append(l.replace('<img ', f'<img class="ln" style="--i:{i}" ', 1))
        else:
            m = re.match(r'<div class="([^"]*)"', l)
            out.append(l.replace(f'<div class="{m.group(1)}"', f'<div class="{m.group(1)} ln" style="--i:{i}"', 1))
    aria = ("Ejemplo de boleta electrónica emitida después de una compra hecha a través de un agente de IA" if lang == "es"
            else "Example of a Chilean electronic receipt issued after a purchase made through an AI agent")
    note = ("Ejemplo ilustrativo. La tienda emite la boleta y el agente la recibe en el pedido." if lang == "es"
            else "Illustrative example, in Spanish as a Chilean store would issue it. The agent receives it on the order.")
    return f'''<figure class="receipt-wrap" role="img" aria-label="{aria}">
        <div class="receipt">
{chr(10).join("          " + l for l in out)}
        </div>
        <figcaption class="receipt-note">{note}</figcaption>
      </figure>'''

def head(lang, title, desc, canonical, alt_es, alt_en):
    return f'''<!doctype html>
<html lang="{"es-CL" if lang == "es" else "en"}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="alternate" hreflang="es-CL" href="{alt_es}">
<link rel="alternate" hreflang="en" href="{alt_en}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
{ICON}
{FONTS}
<link rel="stylesheet" href="/assets/site.css">
</head>'''

def ledger_row(prefix, key, title, text, source):
    return (f'<tr><td class="n">{prefix}<span class="k">{key}</span></td>'
            f'<td class="w"><b>{title}</b><span>{text}</span></td><td class="s">{source}</td></tr>')

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
            lead="Una extensión abierta de UCP (Google y Shopify) y ACP (OpenAI y Stripe). Agrega lo que la ley chilena exige y los estándares no traen: boleta o factura del SII según quién compra, derecho a retracto y garantía legal en ventas a personas, notas de crédito y medios de pago locales.",
            cta="Leer la especificación", cta_href="/spec/", alt_link="Ver los esquemas", alt_href="/spec/#esquemas",
            facts=[("Abierta", "Licencia Apache-2.0, como UCP y ACP. Cualquiera la implementa sin pedir permiso."),
                   ("La tienda vende", "El pago llega a la cuenta de la propia tienda. La especificación nunca toca los fondos."),
                   ("Compatible", "Un agente que no la conoce sigue funcionando, y los avisos legales igual le llegan.")],
        )
    else:
        T.update(
            title="Comercio IA · The open Chilean extension for UCP and ACP",
            desc="Chilean tax receipts, right of withdrawal, legal warranty, credit notes and payment methods, so any AI agent can complete a legal sale in Chile, on top of UCP and ACP.",
            label="Open proposal · version 2026-10-09",
            h1="Comercio IA", h1sub="A boleta for consumers, a factura for businesses. For any AI agent.",
            lead="An open extension to UCP (Google and Shopify) and ACP (OpenAI and Stripe). It adds what Chilean law requires and the standards don't cover: an SII boleta or factura depending on who buys, the right of withdrawal and legal warranty in consumer sales, credit notes and local payment methods.",
            cta="Read the specification", cta_href="/en/spec/", alt_link="See the schemas", alt_href="/en/spec/#schemas",
            facts=[("Open", "Apache-2.0 license, like UCP and ACP. Anyone can implement it without asking."),
                   ("The store sells", "Payment goes to the store's own account. The specification never touches funds."),
                   ("Compatible", "An agent that doesn't know it keeps working, and the legal notices still reach it.")],
        )
    facts = "\n".join(f'        <div><h3>{a}</h3><p>{b}</p></div>' for a, b in T["facts"])

    if es:
        gap_left = ["Catálogo y búsqueda", "Carro y checkout", "Pedido y ajustes", "Políticas y avisos", "Medios de pago enchufables"]
        gap_right = ["Boleta para personas, factura para empresas", "Derecho a retracto", "Garantía legal", "Notas de crédito", "Webpay, Mercado Pago, Getnet y Khipu"]
        rows = [
            ledger_row("cl.comercioia.shopping.", "tax_document", "Boleta o factura", "Boleta para personas; factura con RUT y giro para empresas. El pedido devuelve folio, RUT del emisor y estado en el SII.", "DL 825 · Res. SII 74/2020"),
            ledger_row("cl.comercioia.shopping.", "consumer_terms", "Información al consumidor", "En ventas a personas: identidad del vendedor, aviso de que compra a través de IA, despacho, cuotas con CAE y confirmación escrita.", "Ley 19.496 · DS 6/2021"),
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
            s1l="01 · El vacío", s1h='Los estándares llegan hasta donde <span class="sub">empieza la ley chilena.</span>',
            s1a="UCP y ACP traen", s1b="Comercio IA agrega",
            s2l="02 · Qué contiene", s2h='Tres extensiones, dos políticas <span class="sub">y cinco medios de pago.</span>',
            th=("Nombre", "Qué hace", "Base legal"),
            s3l="03 · Una compra", s3h='De «lo quiero» a una boleta <span class="sub">que el SII ya recibió.</span>',
            leg=("Núcleo de UCP/ACP y proveedor de pago", "Lo que agrega Comercio IA"),
            fine="Ningún estándar define todavía cómo devolver al comprador al agente después de pagar en una página externa (propuesta UCP #486), así que el agente se entera del pago por el pedido. Si compra una empresa, el paso 02 pide factura con su RUT y giro, el paso 09 emite una factura (33) y, en general, el retracto no aplica, salvo cuando la compradora es micro o pequeña empresa (Ley 20.416).",
            s4l="04 · Para quién", s4h='Cada uno implementa <span class="sub">su parte.</span>',
            s5l="05 · Estado", s5h='Lista para implementar. <span class="sub">Estable tras la primera venta real.</span>', s5id="participa",
            s6l="06 · Camino a la 1.0", s6h='Cinco condiciones <span class="sub">para declararla estable.</span>',
            road=[("Hecho", "done", "Especificación y esquemas publicados", "9 de octubre de 2026, en comercioia.cl."),
                  ("Hecho", "done", "Repositorio público y periodo de comentarios", "Comentarios abiertos hasta el 30 de noviembre de 2026."),
                  ("En diseño", "", "Implementación de referencia", "Synaptik Checkout: las tres extensiones y Webpay Plus, con boleta automática."),
                  ("Pendiente", "", "Primeras ventas reales", "Al menos una boleta, una factura y un retracto con nota de crédito."),
                  ("Pendiente", "", "Revisión legal y validación externa", "Respuesta a las preguntas abiertas y un cofirmante o implementador externo.")],
            road_note="Las extensiones y los medios de pago se versionan por separado: Oneclick Mall, Getnet y Khipu pueden seguir como propuesta cuando el resto ya sea estable.",
        )
    else:
        gap_left = ["Catalog and search", "Cart and checkout", "Order and adjustments", "Policies and notices", "Pluggable payment methods"]
        gap_right = ["A boleta for consumers, a factura for businesses", "Right of withdrawal (retracto)", "Legal warranty", "Credit notes", "Webpay, Mercado Pago, Getnet and Khipu"]
        rows = [
            ledger_row("cl.comercioia.shopping.", "tax_document", "Boleta or factura", "A boleta for consumers; a factura with RUT and line of business for companies. The order returns the folio, issuer RUT and SII status.", "DL 825 · SII Res. 74/2020"),
            ledger_row("cl.comercioia.shopping.", "consumer_terms", "Consumer information", "In consumer sales: seller identity, notice that the purchase is made through AI, delivery, installments with CAE and written confirmation.", "Ley 19.496 · DS 6/2021"),
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
            s1l="01 · The gap", s1h='The standards stop <span class="sub">where Chilean law starts.</span>',
            s1a="UCP and ACP cover", s1b="Comercio IA adds",
            s2l="02 · What's inside", s2h='Three extensions, two policies <span class="sub">and five payment methods.</span>',
            th=("Name", "What it does", "Legal basis"),
            s3l="03 · One purchase", s3h='From “I\'ll take it” to a boleta <span class="sub">the SII has received.</span>',
            leg=("UCP/ACP core and payment provider", "What Comercio IA adds"),
            fine="Neither standard yet defines how to return the buyer to the agent after paying on an external page (UCP proposal #486), so the agent learns about the payment from the order. When a company buys, step 02 asks for a factura with its RUT and line of business, step 09 issues a factura (33), and the right of withdrawal generally does not apply, except when the buyer is a micro or small business (Ley 20.416).",
            s4l="04 · Who it's for", s4h='Everyone implements <span class="sub">their part.</span>',
            s5l="05 · Status", s5h='Ready to implement. <span class="sub">Stable after the first real sale.</span>', s5id="participate",
            s6l="06 · Path to 1.0", s6h='Five conditions <span class="sub">before we call it stable.</span>',
            road=[("Done", "done", "Specification and schemas published", "9 October 2026, at comercioia.cl."),
                  ("Done", "done", "Public repository and comment period", "Comments open until 30 November 2026."),
                  ("In design", "", "Reference implementation", "Synaptik Checkout: the three extensions and Webpay Plus, with automatic boleta."),
                  ("Pending", "", "First real sales", "At least one boleta, one factura and one withdrawal with a credit note."),
                  ("Pending", "", "Legal review and outside validation", "Answers to the open questions and one co-signer or outside implementer.")],
            road_note="Extensions and payment methods are versioned separately: Oneclick Mall, Getnet and Khipu can stay as proposals once the rest is stable.",
        )
    li = lambda xs: "\n".join(f"            <li>{x}</li>" for x in xs)
    who_html = "\n".join(f'        <div><p class="tag">{t}</p><h3>{h}</h3><p>{p}</p></div>' for t, h, p in who)
    kv_html = "\n".join(f"          <dt>{a}</dt><dd>{b}</dd>" for a, b in kv)
    asks_html = "\n".join(f"          <li><b>{a}</b><span>{b}</span></li>" for a, b in asks)
    rows_html = "\n".join("          " + r for r in rows)
    road_html = "\n".join(f'          <li class="{c}"><span class="st">{st}</span><b>{t}</b><span class="d">{d}</span></li>' for st, c, t, d in S["road"])
    canonical = "https://comercioia.cl/" if es else "https://comercioia.cl/en/"
    return f'''{head(lang, T["title"], T["desc"], canonical, "https://comercioia.cl/", "https://comercioia.cl/en/")}
<body>
{masthead(lang, "home")}

<main id="main">
  <section class="hero">
    <div class="wrap">
      <div class="hero-grid">
        <div>
          <p class="label"><span class="dot"></span>{T["label"]}</p>
          <h1>{T["h1"]}<span class="sub">{T["h1sub"]}</span></h1>
          <p class="lead" style="margin-top:28px">{T["lead"]}</p>
          <div class="actions">
            <a class="btn" href="{T["cta_href"]}">{T["cta"]} <span aria-hidden="true">→</span></a>
            <a class="link-arrow" href="{T["alt_href"]}">{T["alt_link"]}</a>
          </div>
        </div>
      {receipt(lang)}
      </div>
      <div class="facts">
{facts}
      </div>
    </div>
    <div class="band" role="presentation"></div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="label">{S["s1l"]}</p><h2>{S["s1h"]}</h2></div>
      <div class="section-body cols-2">
        <div>
          <p class="col-title">{S["s1a"]}</p>
          <ul class="list-plain">
{li(gap_left)}
          </ul>
        </div>
        <div>
          <p class="col-title red">{S["s1b"]}</p>
          <ul class="list-plain red">
{li(gap_right)}
          </ul>
        </div>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="label">{S["s2l"]}</p><h2>{S["s2h"]}</h2></div>
      <div class="section-body">
        <table class="ledger">
          <thead><tr><th>{S["th"][0]}</th><th>{S["th"][1]}</th><th>{S["th"][2]}</th></tr></thead>
          <tbody>
{rows_html}
          </tbody>
        </table>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="label">{S["s3l"]}</p><h2>{S["s3h"]}</h2></div>
      <div class="section-body wide">
        <div class="seq">
{seq_svg(lang)}
        </div>
        <p class="legend"><span>{S["leg"][0]}</span><span class="ours">{S["leg"][1]}</span></p>
        <p class="fine">{S["fine"]}</p>
      </div>
    </div>
  </section>

  <section class="section">
    <div class="wrap">
      <div class="section-head"><p class="label">{S["s4l"]}</p><h2>{S["s4h"]}</h2></div>
      <div class="section-body who">
{who_html}
      </div>
    </div>
  </section>

  <section class="section" id="{S["s5id"]}">
    <div class="wrap">
      <div class="section-head"><p class="label">{S["s5l"]}</p><h2>{S["s5h"]}</h2></div>
      <div class="section-body status-grid">
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
      <div class="section-head"><p class="label">{S["s6l"]}</p><h2>{S["s6h"]}</h2></div>
      <div class="section-body">
        <ol class="road">
{road_html}
        </ol>
        <p class="fine">{S["road_note"]}</p>
      </div>
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

# ---------------------------------------------------------------- spec pages + 404: new chrome
FONT_RE = re.compile(r'<link rel="preconnect" href="https://fonts.googleapis.com">\s*<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\s*<link rel="stylesheet" href="https://fonts.googleapis.com/css2\?[^"]+">', re.S)
ICON_RE = re.compile(r'<link rel="icon" href="data:image/svg\+xml,[^"]+">')
for rel, lang in (("spec/index.html", "es"), ("en/spec/index.html", "en")):
    path = os.path.join(SITE, rel)
    s = open(path).read()
    s = FONT_RE.sub(lambda m: FONTS, s)
    s = ICON_RE.sub(lambda m: ICON, s)
    s = re.sub(r'<a class="skip".*?</header>', lambda m: masthead(lang, "spec"), s, flags=re.S)
    s = re.sub(r'<footer class="[^"]*">.*?</footer>', lambda m: footer(lang), s, flags=re.S)
    open(path, "w").write(s)

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
