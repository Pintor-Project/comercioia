# Comercio IA

**La extensión chilena abierta para UCP y ACP.** Boleta o factura del SII, derecho a retracto, garantía legal, notas de crédito y medios de pago chilenos, para que cualquier agente de IA pueda cerrar una venta legal en Chile.

**The open Chilean extension for UCP and ACP.** SII tax receipts, the right of withdrawal, the legal warranty, credit notes and Chilean payment methods, so any AI agent can complete a legal sale in Chile.

[comercioia.cl](https://comercioia.cl) · [Especificación](https://comercioia.cl/spec/) · [Specification (English)](https://comercioia.cl/en/spec/)

> **Estado: propuesta abierta, versión `2026-10-30`.** Lista para implementar y abierta a comentarios hasta el 30 de noviembre de 2026. La primera versión estable está prevista para enero de 2027, al cumplir el [camino a la 1.0](https://comercioia.cl/#participa).
>
> **Status: open proposal, version `2026-10-30`.** Ready to implement and open for comment until 30 November 2026. The first stable release is planned for January 2027, once the [path to 1.0](https://comercioia.cl/en/#participate) is complete.

## Qué contiene · What's inside

| Nombre · Name | Qué hace · What it does | Esquema · Schema |
|---|---|---|
| `cl.comercioia.shopping.tax_document` | Boleta o factura según la operación y el comprador, en el checkout, con referencias B2B y comprador identificado sobre 135 UF, modelo de emisión declarado y comprobante de pago electrónico como documento de la venta; documentos del SII en el pedido | [2026-10-30](site/ucp/schemas/tax_document/2026-10-30.json) · anteriores · previous: [2026-10-16](site/ucp/schemas/tax_document/2026-10-16.json), [2026-10-15](site/ucp/schemas/tax_document/2026-10-15.json) |
| `cl.comercioia.shopping.consumer_terms` | Identidad del vendedor, aviso de IA, despacho, cuotas, confirmación escrita; políticas de retracto y garantía legal | [2026-10-15](site/ucp/schemas/consumer_terms/2026-10-15.json) |
| `cl.comercioia.shopping.credit_note` | Nota de crédito (DTE 61) en cada ajuste del pedido | [2026-10-15](site/ucp/schemas/credit_note/2026-10-15.json) |
| `cl.comercioia.webpay_plus` | Webpay Plus (Transbank) | [2026-10-15](site/ucp/handlers/webpay_plus/2026-10-15.json) |
| `cl.comercioia.oneclick_mall` | Oneclick Mall (Transbank), propuesto; flujo distinto al de redirección | [2026-10-15](site/ucp/handlers/oneclick_mall/2026-10-15.json) |
| `cl.comercioia.mercadopago` | Mercado Pago Checkout | [2026-10-15](site/ucp/handlers/mercadopago/2026-10-15.json) |
| `cl.comercioia.getnet` | Getnet Web Checkout | [2026-10-15](site/ucp/handlers/getnet/2026-10-15.json) |
| `cl.comercioia.khipu` | Khipu (transferencia bancaria) | [2026-10-15](site/ucp/handlers/khipu/2026-10-15.json) |

La versión anterior, `2026-10-09`, sigue publicada en sus direcciones (`…/2026-10-09.json`); la `2026-10-15` la corrige tras una revisión legal, ver el [CHANGELOG](CHANGELOG.md).

The previous version, `2026-10-09`, stays published at its addresses (`…/2026-10-09.json`); `2026-10-15` corrects it after a legal review, see the [CHANGELOG](CHANGELOG.md).

La `2026-10-30` solo agrega a `tax_document`: el modelo de emisión que declara la tienda (`issuance_model`) y el comprobante de un pago electrónico como documento de la venta (`payment_receipt`), que el art. 54 de la Ley del IVA y la Res. Ex. SII 176/2020 equiparan a la boleta. La `2026-10-16` (referencias B2B y boletas sobre 135 UF) añadió solo campos opcionales a la `2026-10-15`. Las demás extensiones y los medios de pago siguen en `2026-10-15`, y las versiones anteriores de `tax_document` también siguen publicadas.

`2026-10-30` only adds to `tax_document`: the emission model the store declares (`issuance_model`) and the receipt of an electronic payment as the document of a sale (`payment_receipt`), which art. 54 of the Ley del IVA and SII Res. Ex. 176/2020 treat as a boleta. `2026-10-16` (B2B references and boletas above 135 UF) had only added optional fields to `2026-10-15`. The other extensions and the payment handlers stay at `2026-10-15`, and the earlier `tax_document` versions also stay published.

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

Esta especificación describe reglas tributarias y de protección al consumidor de Chile, pero no es asesoría legal. Comercio IA no está afiliado a Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, el SII ni el SERNAC, ni cuenta con su respaldo; las marcas pertenecen a sus dueños.

This specification describes Chilean tax and consumer-protection rules, but it is not legal advice. Comercio IA is not affiliated with or endorsed by Google, Shopify, OpenAI, Stripe, Transbank, Mercado Pago, Getnet, Khipu, the SII or SERNAC; trademarks belong to their owners.

Iniciativa abierta impulsada por [Pintor Project](https://pintorproject.cl). Implementación de referencia: [Synaptik Checkout IA](https://synaptiktech.com/es/product/checkout-ia), producto comercial de Pintor Project. Licencia [Apache-2.0](LICENSE).
