# Changelog

## 2026-10-16 · Propuesta abierta · Open proposal

Nueva versión de `cl.comercioia.shopping.tax_document`. Solo agrega campos opcionales: todo lo válido en `2026-10-09` sigue siendo válido. `consumer_terms`, `credit_note` y los medios de pago siguen en `2026-10-09`, y la versión `2026-10-09` de `tax_document` sigue publicada sin cambios.

New version of `cl.comercioia.shopping.tax_document`. It only adds optional fields: everything valid under `2026-10-09` remains valid. `consumer_terms`, `credit_note` and the payment handlers stay at `2026-10-09`, and version `2026-10-09` of `tax_document` stays published unchanged.

- Referencias B2B ([#1](https://github.com/Pintor-Project/comercioia/issues/1)) · B2B references: `tax_document.references[]` en el checkout y `tax_documents[].references[]` en el pedido, con `type` (`TpoDocRef` del SII: `801` orden de compra, `802` nota de pedido, `803` contrato, `52` guía de despacho, o un código alfabético como `HES`), `number` (`FolioRef`, ≤18), `date` (`FchRef`, obligatoria en factura · mandatory on a factura) y `reason` (`RazonRef`, ≤90). Hasta 40 · Up to 40.
- Boletas sobre 135 UF (Código Tributario art. 92 ter; Res. Ex. SII 44/2025) · Boletas above 135 UF: `tax_document.receiver` sirve también para boleta, con solo `rut` y `razon_social` obligatorios; `giro`, `direccion` y `comuna` siguen siendo obligatorios en factura · `tax_document.receiver` now also works for a boleta, with only `rut` and `razon_social` required; `giro`, `direccion` and `comuna` remain required on a factura.
- Medio de pago · Payment method: `payment_method` en `tax_document` y en `tax_documents[]`, con los códigos `MedioPago` del Formato Boletas Electrónicas v4.2 · with the SII boleta `MedioPago` codes: `1` efectivo · cash, `2` pago electrónico · electronic payment, `3` transferencia electrónica · electronic transfer, `4` cheque, `5` otro · other.
- Mensaje de error · Error message: `cl.comercioia.tax_document.receiver_required`, cuando falta el receptor de una factura o de una boleta sobre 135 UF · when the receiver of a factura or of a boleta above 135 UF is missing.
- Ejemplos · Examples: factura con orden de compra y HES, boleta sobre 135 UF · factura with purchase order and HES, boleta above 135 UF. `tools/validate.py` valida contra la última versión y comprueba la compatibilidad con la anterior · validates against the latest version and checks compatibility with the previous one.

## 2026-10-09 · Propuesta abierta · Open proposal

Primera versión pública. First public version.

- Extensiones · Extensions: `cl.comercioia.shopping.tax_document`, `cl.comercioia.shopping.consumer_terms`, `cl.comercioia.shopping.credit_note`.
- Tipos de política · Policy types: `cl.comercioia.policy.retracto`, `cl.comercioia.policy.garantia_legal`.
- Medios de pago · Payment handlers: `cl.comercioia.webpay_plus`, `cl.comercioia.oneclick_mall` (propuesto · proposed), `cl.comercioia.mercadopago`, `cl.comercioia.getnet`, `cl.comercioia.khipu`.
- Requiere UCP `2026-08-25`. Equivalencias para ACP `2026-04-17`.
- Mismo día de publicación: la descripción de los esquemas pasó de «draft» a «open proposal». Sin cambios de estructura. · Same day as publication: schema descriptions changed from "draft" to "open proposal". No structural change.
- Mismo día: la descripción de `cl.comercioia.khipu` deja de afirmar que Khipu tiene un registro de iniciador de pagos (régimen CMF desde julio de 2027). Sin cambios de estructura. · Same day: the `cl.comercioia.khipu` description no longer states that Khipu holds a payment-initiation registration (CMF regime from July 2027). No structural change.
