# Cómo participar · How to participate

## Comentarios · Comments

El periodo de comentarios de la versión `2026-10-09` está abierto hasta el **30 de noviembre de 2026**. Abre un issue con la plantilla «Comentario». Todo comentario recibe respuesta antes de la versión estable.

The comment period for version `2026-10-09` is open until **30 November 2026**. Open an issue with the "Comentario" template. Every comment gets an answer before the stable release.

## Cambios · Changes

1. Abre un issue con la plantilla «Propuesta de cambio»: qué cambia, por qué, y qué regla chilena o caso real lo justifica.
2. Si hay acuerdo, envía un pull request que modifique el esquema, la especificación en español y en inglés, y los ejemplos.
3. `tools/validate.py` debe pasar. La CI lo corre en cada pull request.

## Reglas de versionado · Versioning rules

- Cada versión tiene fecha (`AAAA-MM-DD`) y vive en su propio archivo: `site/ucp/schemas/<nombre>/<versión>.json`.
- **Una versión publicada no se modifica.** Un cambio de campos se publica en una versión nueva; la anterior queda disponible.
- Los esquemas no cierran objetos (`additionalProperties`) ni usan listas cerradas (`enum`), como pide UCP. Los códigos van como `examples`.
- Las extensiones y los medios de pago se versionan por separado.
- Si un proveedor publica su propio medio de pago, lo adoptamos y marcamos el nuestro como obsoleto.

## Dominio y autoridad · Domain authority

Los esquemas `cl.comercioia.*` deben servirse desde `https://comercioia.cl`, sin redirecciones ni CDN con otro nombre. Si no, los agentes los ignoran.

## Gobernanza · Governance

Pintor Project mantiene la especificación durante la etapa de propuesta. Los cofirmantes de la versión estable se listan en el sitio y en este repositorio, y participan en las decisiones de cambio. Cuando haya adopción amplia, el repositorio puede pasar a una organización neutral.

Pintor Project maintains the specification during the proposal stage. Co-signers of the stable release are listed on the site and in this repository, and take part in change decisions. Once adoption is broad, the repository can move to a neutral organization.

## Contacto · Contact

[contacto@comercioia.cl](mailto:contacto@comercioia.cl)
