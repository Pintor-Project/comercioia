# Comercio IA

**La extensión chilena abierta para UCP y ACP.** Boleta y factura del SII, derecho a retracto, garantía legal, notas de crédito y medios de pago chilenos, para que cualquier agente de IA pueda cerrar una venta legal en Chile.

**The open Chilean extension for UCP and ACP.** SII tax receipts, the right of withdrawal, the legal warranty, credit notes and Chilean payment methods, so any AI agent can complete a legal sale in Chile.

[comercioia.cl](https://comercioia.cl) · [Especificación](https://comercioia.cl/spec/) · [Specification (English)](https://comercioia.cl/en/spec/)

> **Estado: propuesta abierta, versión `2026-10-09`.** Lista para implementar y abierta a comentarios hasta el 30 de noviembre de 2026. La primera versión estable está prevista para enero de 2027, al cumplir el [camino a la 1.0](https://comercioia.cl/#participa).
>
> **Status: open proposal, version `2026-10-09`.** Ready to implement and open for comment until 30 November 2026. The first stable release is planned for January 2027, once the [path to 1.0](https://comercioia.cl/en/#participate) is complete.

## Qué contiene · What's inside

| Nombre · Name | Qué hace · What it does | Esquema · Schema |
|---|---|---|
| `cl.comercioia.shopping.tax_document` | Boleta o factura en el checkout; documentos del SII en el pedido | [2026-10-09](site/ucp/schemas/tax_document/2026-10-09.json) |
| `cl.comercioia.shopping.consumer_terms` | Identidad del vendedor, aviso de IA, despacho, cuotas, confirmación escrita; políticas de retracto y garantía legal | [2026-10-09](site/ucp/schemas/consumer_terms/2026-10-09.json) |
| `cl.comercioia.shopping.credit_note` | Nota de crédito (DTE 61) en cada ajuste del pedido | [2026-10-09](site/ucp/schemas/credit_note/2026-10-09.json) |
| `cl.comercioia.webpay_plus` | Webpay Plus (Transbank) | [2026-10-09](site/ucp/handlers/webpay_plus/2026-10-09.json) |
| `cl.comercioia.oneclick_mall` | Oneclick Mall (Transbank), propuesto | [2026-10-09](site/ucp/handlers/oneclick_mall/2026-10-09.json) |
| `cl.comercioia.mercadopago` | Mercado Pago Checkout | [2026-10-09](site/ucp/handlers/mercadopago/2026-10-09.json) |
| `cl.comercioia.getnet` | Getnet Web Checkout | [2026-10-09](site/ucp/handlers/getnet/2026-10-09.json) |
| `cl.comercioia.khipu` | Khipu (transferencia bancaria) | [2026-10-09](site/ucp/handlers/khipu/2026-10-09.json) |

Los esquemas se sirven desde `https://comercioia.cl/ucp/…`, el dominio que corresponde al espacio de nombres `cl.comercioia.*`, sin redirecciones, como exige UCP. Ejemplos completos en [`examples/`](examples/).

The schemas are served from `https://comercioia.cl/ucp/…`, the domain that matches the `cl.comercioia.*` namespace, with no redirects, as UCP requires. Full examples in [`examples/`](examples/).

## Participa · Participate

- **Comentar · Comment:** abre un [issue](../../issues/new/choose) con un error, un campo que falta o un caso de tu negocio.
- **Proponer un cambio · Propose a change:** issue con la plantilla «Propuesta de cambio», y después un pull request.
- **Cofirmar o implementar · Co-sign or implement:** escríbenos a [contacto@comercioia.cl](mailto:contacto@comercioia.cl).

Detalles en [CONTRIBUTING.md](CONTRIBUTING.md). Historial en [CHANGELOG.md](CHANGELOG.md).

## Estructura · Layout

```
site/                 comercioia.cl (HTML estático + esquemas en site/ucp/)
  ucp/schemas/…       extensiones, una carpeta por nombre y un archivo por versión
  ucp/handlers/…      medios de pago
tools/build.py        genera las portadas, el timbre y el diagrama de secuencia
tools/gen_handlers.py genera los esquemas de los medios de pago
tools/validate.py     valida esquemas y ejemplos (lo corre la CI)
examples/             perfil, checkout y pedido de ejemplo
```

Cada push a `main` valida y publica el sitio en comercioia.cl.

## Aviso · Notice

Esta especificación describe reglas tributarias y de protección al consumidor de Chile, pero no es asesoría legal. Comercio IA no está afiliado a Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu ni al SII, ni cuenta con su respaldo; las marcas pertenecen a sus dueños.

This specification describes Chilean tax and consumer-protection rules, but it is not legal advice. Comercio IA is not affiliated with or endorsed by Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu or the SII; trademarks belong to their owners.

Iniciativa abierta impulsada por [Pintor Project](https://pintorproject.cl). Implementación de referencia: [Synaptik Checkout](https://synaptiktech.com). Licencia [Apache-2.0](LICENSE).
