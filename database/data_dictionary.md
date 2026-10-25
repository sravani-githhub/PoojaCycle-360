# Data dictionary

All main entities use integer primary keys. Material amounts use `Numeric(12,3)` plus a controlled unit; currency uses fixed precision `Numeric`. Changing records include UTC `created_at` and `updated_at` timestamps.

| Table | Purpose and important columns |
|---|---|
| `users` | Account/contact directory. Unique `email`; constrained `role`; `account_status`; nullable `password_hash` (never returned by API). API omits email, phone and location from unauthenticated responses. Authentication is not implemented. |
| `waste_sources` | Temple, festival or community collection location, address and optional contact; private contact fields are omitted from unauthenticated API responses. |
| `waste_types` | Five reference material types with description and handling notes. Plastic is not presumed recyclable. |
| `waste_reports` | Reported amount, unit, source/type, availability date, preferred pickup window, festival flag, contamination, collection status, and reporter. Quantity positive; contamination 0–100 if supplied. |
| `collection_assignments` | Collector and scheduled/actual pickup details for a waste report. |
| `waste_batches` | Traceability record for received material with quantity, type, stage and quality notes. One batch per report in this prototype. |
| `processing_records` | Partner, method, input/output quantity, processing date, status and evidence notes. Output is nullable until recorded. |
| `artisans` | Maker profile optionally linked to a user; skills, materials, location, private contact email, monthly capacity in kg, availability and contact visibility. |
| `artisan_material_requests` | Artisan request for a material type, amount and status. |
| `products` | Eco Store listing, optional artisan, decimal price, integer stock and status. |
| `product_batches` | Many-to-many provenance junction from products to actual waste batches, with amount used. |
| `orders` | Customer order, status and total. `payment_mode` is simulated only; no card data exists. |
| `order_items` | Product, quantity, price-at-order and subtotal. Quantity must be positive. |
| `impact_records` | Recorded outcome linked to a batch or processing record. `quantity_basis` distinguishes reported, estimated, processed and verified; verification is separate. No carbon/water multipliers are used. |

## Relationships

- Users report many waste reports; each report points to one source, one waste type and one reporting user.
- A report can have multiple collection attempts. It has at most one batch in this prototype; a batch can have multiple processing records.
- Collector and processing partner are users. Their role is validated as data but API authorization is not implemented.
- Artisan profiles optionally link to a user. Artisans request waste types and list products. Products and tracked batches link through `product_batches`.
- Customers place orders. Orders contain order-item rows that snapshot price and subtotal.
- Impact records require a batch or processing record. Recorded quantities are not automatically presented as verified outcomes.
