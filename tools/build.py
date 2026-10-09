"""Builds the Comercio IA landing pages (es, en), the timbre patterns, and
refreshes header/footer/fonts/metadata on the hand-written pages, and writes the
privacy and accessibility pages and the sitemap. Usage: python3 build.py <site_dir>"""
import html, json, os, random, re, sys

SITE = sys.argv[1]
BASE = "https://comercioia.cl"
LASTMOD = "2026-10-09"
# Self-hosted (assets/fonts, OFL): no request leaves for a font CDN before consent.
FONTS = ('<link rel="preload" href="/assets/fonts/geist-400-latin.woff2" as="font" type="font/woff2" crossorigin>\n'
         '<link rel="preload" href="/assets/fonts/geist-mono-400-latin.woff2" as="font" type="font/woff2" crossorigin>')
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
    <p class="mono"><a href="/spec/">Especificación</a> · <a href="/spec/#esquemas">Esquemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="links"><a href="/privacidad/">Privacidad</a> <a href="/accesibilidad/">Accesibilidad</a> <button type="button" class="linkish" data-cookie-settings hidden>Preferencias de cookies</button></p>
    <p class="legal">Especificación y esquemas bajo licencia Apache-2.0. No es asesoría legal. Comercio IA no está afiliado a Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, el SII ni el SERNAC, ni cuenta con su respaldo; las marcas pertenecen a sus dueños.</p>
  </div>
</footer>'''
    return '''<footer class="footer">
  <div class="wrap">
    <p>An open initiative led by <a href="https://pintorproject.cl">Pintor Project</a>. Reference implementation: <a href="https://synaptiktech.com/en/product/checkout-ia">Synaptik Checkout IA</a>, a commercial product of Pintor Project.</p>
    <p class="mono"><a href="/en/spec/">Specification</a> · <a href="/en/spec/#schemas">Schemas</a> · <a href="https://github.com/Pintor-Project/comercioia">GitHub</a> · <a href="mailto:contacto@comercioia.cl">contacto@comercioia.cl</a></p>
    <p class="links"><a href="/en/privacy/">Privacy</a> <a href="/en/accessibility/">Accessibility</a> <button type="button" class="linkish" data-cookie-settings hidden>Cookie preferences</button></p>
    <p class="legal">Specification and schemas under the Apache-2.0 license. Not legal advice. Comercio IA is not affiliated with or endorsed by Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, the SII or SERNAC; trademarks belong to their owners.</p>
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
    return f'''<figure class="receipt-wrap">
        <div class="receipt" role="img" aria-label="{aria}">
{chr(10).join("          " + l for l in out)}
        </div>
        <figcaption class="receipt-note">{note}</figcaption>
      </figure>'''

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

def head(lang, title, desc, canonical, alt_es, alt_en, kind="home"):
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
            desc="Chilean tax receipts, withdrawal rights, legal warranty, credit notes and payment methods, so any AI agent can make a legal sale in Chile. On UCP and ACP.",
            label="Open proposal · version 2026-10-09",
            h1="Comercio IA", h1sub="A boleta for consumers, a factura for businesses. For any AI agent.",
            lead="An open extension to UCP (Google and Shopify) and ACP (OpenAI and Stripe). It adds what Chilean law requires and the standards don't cover: an SII boleta or factura depending on who buys, the right of withdrawal and legal warranty in consumer sales, credit notes and local payment methods.",
            cta="Read the specification", cta_href="/en/spec/", alt_link="See the schemas", alt_href="/en/spec/#schemas",
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
                  ("In design", "", "Reference implementation", "Synaptik Checkout IA: the three extensions and Webpay Plus, with automatic boleta."),
                  ("Pending", "", "First real sales", "At least one boleta, one factura and one withdrawal with a credit note."),
                  ("In progress", "", "Legal review and outside validation", "Answers to the open questions and one co-signer or outside implementer.")],
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
        {seq_text(lang)}
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
                     r'|<link rel="preload" href="/assets/fonts/geist-400-latin.woff2"[^>]*>\s*<link rel="preload" href="/assets/fonts/geist-mono-400-latin.woff2"[^>]*>)', re.S)
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
