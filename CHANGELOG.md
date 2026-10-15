# Changelog

## 2026-10-15 · Propuesta abierta · Open proposal

Correcciones de contenido tras una revisión legal. La `2026-10-09` no se modifica y sigue publicada; esta versión la reemplaza como vigente. Sin cambios de estructura: no se agregan, quitan ni renombran campos. · Content corrections after a legal review. `2026-10-09` is not modified and stays published; this version replaces it as the current one. No structural change: no fields are added, removed or renamed.

- Se publican de nuevo, con el mismo contenido estructural, las tres extensiones y los cinco medios de pago, para que una sola fecha identifique la especificación. · The three extensions and the five payment handlers are republished with the same structure, so one date identifies the specification.
- `tax_document`: la elección de boleta o factura depende de la operación y de la calidad tributaria del comprador; el momento de emisión (`issue_trigger`) sigue el art. 55 del DL 825 y `payment_confirmed` es solo una opción operativa; el RUT genérico `66666666-6` solo en los casos que admite el formato del SII. · Boleta or factura depends on the operation and the buyer's tax status; the issuance event (`issue_trigger`) follows art. 55 of DL 825 and `payment_confirmed` is only an operational option; the generic RUT `66666666-6` only in the cases the SII format allows.
- `consumer_terms`: confirmación escrita con copia íntegra del contrato, sin un número general de horas; exclusión del retracto limitada a las categorías legales y con aviso en español junto al precio; garantía legal «según corresponda». · Written confirmation with a full copy of the contract, with no general number of hours; withdrawal exclusion limited to the legal categories and disclosed in Spanish next to the price; legal warranty "as applicable".
- `credit_note`: los efectos tributarios dependen de la causal; el plazo de seis meses (DL 825 arts. 21 y 70) no es una regla general. · Tax effects depend on the cause; the six-month period (DL 825 arts. 21 and 70) is not a general rule.
- Medios de pago: la iniciación de pagos queda sujeta a la Ley 21.521 y a la normativa CMF, con su calendario gradual (Khipu); Oneclick Mall se describe como un flujo propuesto y distinto del de redirección; publicar los esquemas no equivale por sí solo a operar un servicio financiero. · Payment initiation is subject to Ley 21.521 and CMF regulation on its phased calendar (Khipu); Oneclick Mall is described as a proposed flow different from the redirect flows; publishing the schemas is not, by itself, operating a financial service.
- Especificación: «Preguntas abiertas» pasa a «Aspectos que dependen de cada implementación». Guía de cumplimiento revisada al 15 de octubre de 2026 (reglas 1, 2, 4, 5 y 6). · Specification: "Open questions" becomes "Aspects that depend on each implementation". Compliance guide reviewed as of 15 October 2026 (rules 1, 2, 4, 5 and 6).
- Sitio: política de privacidad con la identificación completa del responsable; Google Analytics se detiene al retirar el consentimiento, también en otras pestañas, y no recibe direcciones de correo ni parámetros de URL; el aviso de no afiliación se mantiene y las integraciones propuestas se identifican como tales. · Site: privacy policy with the controller's full identification; Google Analytics stops when consent is withdrawn, including in other tabs, and receives no email addresses or URL parameters; the non-affiliation notice stays and proposed integrations are labelled as such.

## 2026-10-09 · Propuesta abierta · Open proposal

Primera versión pública. First public version.

- Extensiones · Extensions: `cl.comercioia.shopping.tax_document`, `cl.comercioia.shopping.consumer_terms`, `cl.comercioia.shopping.credit_note`.
- Tipos de política · Policy types: `cl.comercioia.policy.retracto`, `cl.comercioia.policy.garantia_legal`.
- Medios de pago · Payment handlers: `cl.comercioia.webpay_plus`, `cl.comercioia.oneclick_mall` (propuesto · proposed), `cl.comercioia.mercadopago`, `cl.comercioia.getnet`, `cl.comercioia.khipu`.
- Requiere UCP `2026-08-25`. Equivalencias para ACP `2026-04-17`.
- Mismo día de publicación: la descripción de los esquemas pasó de «draft» a «open proposal». Sin cambios de estructura. · Same day as publication: schema descriptions changed from "draft" to "open proposal". No structural change.
- Mismo día: la descripción de `cl.comercioia.khipu` deja de afirmar que Khipu tiene un registro de iniciador de pagos (régimen CMF desde julio de 2027). Sin cambios de estructura. · Same day: the `cl.comercioia.khipu` description no longer states that Khipu holds a payment-initiation registration (CMF regime from July 2027). No structural change.
