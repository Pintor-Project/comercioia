import json, os, sys
root = sys.argv[1]
V = "2026-10-09"
UCP = "https://ucp.dev/2026-08-25/schemas"
H = [
 ("webpay_plus", "Webpay Plus (Transbank)", "webpay-plus", "Transbank",
  "Redirect payment. The business creates the transaction with its own Transbank commerce code; Webpay Plus requires an HTML form POST of token_ws, so continue_url points to a business page that auto-posts it. Confirmation is by commit on return (approved only when response_code = 0 and status = AUTHORIZED); there is no webhook, so businesses MUST sweep abandoned transactions by status query.",
  {"token_ttl_seconds": {"type": "integer", "examples": [300], "description": "Lifetime of the Webpay token."},
   "payment_window_seconds": {"type": "integer", "examples": [240], "description": "Time the buyer has on the Webpay form in production."}}),
 ("oneclick_mall", "Oneclick Mall (Transbank)", "oneclick-mall", "Transbank",
  "Saved-card payment. The buyer enrolls a card once on Transbank's page; later charges are server-to-server with the enrollment's tbk_user and a store commerce code under the business's Mall. PROPOSED: whether charges initiated through an AI agent fit Transbank's Oneclick terms must be confirmed with Transbank before use.",
  {"enrollment_required": {"type": "boolean", "description": "True when the buyer has no active enrollment and must be sent to enroll via continue_url."},
   "daily_limit_clp": {"type": "integer", "description": "Per-buyer daily limit set at affiliation, if the business chooses to disclose it."}}),
 ("mercadopago", "Mercado Pago Checkout", "mercadopago", "Mercado Pago",
  "Redirect payment. The business creates an order or preference with its own Mercado Pago credentials (unit prices are integers in Chile, with an idempotency key); the buyer pays at the returned checkout URL. Confirmation is by signed webhook plus reconciliation.",
  {"checkout_expires_at": {"type": "string", "format": "date-time", "description": "When the payment link stops accepting payments, if set."}}),
 ("getnet", "Getnet Web Checkout", "getnet", "Getnet",
  "Redirect payment on Getnet's Web Checkout (PlacetoPay platform). The business creates a session with its own credentials; the buyer pays at the returned processUrl. The notification is sent once, so businesses MUST also poll the session status. Features enabled for Chile must be confirmed with Getnet.",
  {"session_ttl_seconds": {"type": "integer", "examples": [1800], "description": "Session lifetime; the platform default is 30 minutes."}}),
 ("khipu", "Khipu (bank transfer)", "khipu", "Khipu",
  "Bank-transfer payment initiated by Khipu. The business creates the payment with its own Khipu API key; the buyer pays from their bank account at the returned payment_url. Confirmation is by signed webhook (retried by Khipu) and status query. Khipu, not the handler author, carries any registration required for payment initiation.",
  {"payment_expires_at": {"type": "string", "format": "date-time", "description": "When the payment link expires, if set."}}),
]
for key, title, anchor, provider, desc, resp_extra in H:
    name = f"cl.comercioia.{key}"
    doc = {
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      "$id": f"https://comercioia.cl/ucp/handlers/{key}/{V}.json",
      "name": name,
      "version": V,
      "title": f"{title} payment handler",
      "description": (f"OPEN PROPOSAL, ready to implement and open for comment. Not yet stable. {desc} "
                      f"Funds go from the buyer to the business's own {provider} account and never pass through the handler author. "
                      f"Published by the Comercio IA initiative until {provider} publishes its own handler; {provider} is invited to review, co-sign or take it over. "
                      f"Not affiliated with or endorsed by {provider}. Spec: https://comercioia.cl/spec/#{anchor}"),
      "$defs": {
        name: {
          "payment_instrument": {
            "allOf": [
              {"$ref": f"{UCP}/common/types/payment_instrument.json"},
              {"type": "object", "properties": {"type": {"const": "redirect"}}}
            ]
          },
          "business_schema": {"allOf": [{"$ref": f"{UCP}/payment_handler.json#/$defs/business_schema"},
                                        {"type": "object", "properties": {"config": {"$ref": "#/$defs/business_config"}}}]},
          "platform_schema": {"allOf": [{"$ref": f"{UCP}/payment_handler.json#/$defs/platform_schema"},
                                        {"type": "object", "properties": {"config": {"$ref": "#/$defs/platform_config"}}}]},
          "response_schema": {"allOf": [{"$ref": f"{UCP}/payment_handler.json#/$defs/response_schema"},
                                        {"type": "object", "properties": {"config": {"$ref": "#/$defs/response_config"}}}]}
        },
        "business_config": {
          "type": "object",
          "description": "Public configuration only. Credentials and API keys MUST NOT appear in profiles or responses.",
          "properties": {"environment": {"type": "string", "examples": ["production", "integration"]}}
        },
        "platform_config": {"type": "object", "description": "No platform configuration is required: the platform only follows continue_url."},
        "response_config": {
          "type": "object",
          "properties": dict({"environment": {"type": "string", "examples": ["production", "integration"]}}, **resp_extra)
        }
      }
    }
    d = os.path.join(root, "ucp", "handlers", key)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{V}.json"), "w") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2); f.write("\n")
    print("wrote", key)
