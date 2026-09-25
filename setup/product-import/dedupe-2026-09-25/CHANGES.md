# Duplicate products removed, 25 Sep 2026

`before.json` is the full state of all four products before any change: fields,
variant, images (with CDN URLs), tags, collections, publications and event history.
`ck-men-50ml-edt-spr-old-600px.jpg` is the image replaced on Ck Men.

## Calvin Klein Eternity

- **Deleted** `calvin-klein-eternity-for-men-50ml-edt-spr` (product 16024784666955).
  Created 23 Sep 2026 19:12 UTC by the custom app **Anas-product-image-upload**, which
  set it active and added it to Point of Sale on 24 Sep. Never on the Online Store.
  Same item as Ck Men 50Ml Edt Spr: same barcode 031655644295, price, description.
- **Ck Men 50Ml Edt Spr** (15671298261323): the deleted product's image was the same
  picture at 1080px against Ck Men's 600px. Added it to Ck Men (alt "Ck Men 50Ml Edt
  Spr"), then removed the 600px one, so Ck Men has one image, the 1080px one.
  Nothing else changed on Ck Men.

## Murine Irritation & Redness

- **Kept** `murine-irritation-redness-eye-drops-10ml` (15671329161547): valid barcode
  5060018880204, real product photo. Title changed from "Murine Irritation & Redness
  Eye Drops 10Ml" to "Murine Irritation & Redness Relief Eye Drops 10Ml" (the box's
  wording). Its description already covered everything the other's did; kept as is.
- **Deleted** `murine-irritation-redness-relief-eye-drops` (15671257596235): broken
  SKU 50600188802040, no barcode, one render uploaded twice.
- **Redirect** /products/murine-irritation-redness-relief-eye-drops →
  /products/murine-irritation-redness-eye-drops-10ml (UrlRedirect 1220668784971).

Both products had been published to the Online Store, POS and Shop.
