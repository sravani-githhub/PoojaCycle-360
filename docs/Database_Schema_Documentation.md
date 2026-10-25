# Database schema documentation

The project models users, sources, controlled material types, reports, assignments, traceable batches, processing outcomes, artisan profiles/requests, products, product-to-batch provenance, orders, items, and impact records. Authoritative SQLAlchemy definitions are `backend/app/models.py`; Alembic migration `0001_initial` applies the same metadata. `database/schema.sql` is PostgreSQL DDL for review and manual setup.

See [`../database/data_dictionary.md`](../database/data_dictionary.md) for column definitions and [`../database/ER_diagram.mmd`](../database/ER_diagram.mmd) for the ER model.

## Integrity rules

- Foreign keys preserve traceability; deletes cascade only for dependent child rows.
- Material amounts are positive fixed-precision decimals with units; currency uses fixed-precision decimals.
- Pydantic validation and DB check constraints cover role, status, quantity, order values and impact basis.
- `product_batches` stores actual provenance instead of inferring recycled content.
- Processing output remains absent until recorded. Impact amount basis and verification status are separate.
- Plastic packaging includes sorting and local acceptance notes; no material is presumed recyclable from its label.
- Seed rows are `DEMO ONLY`; dashboard values are DB-derived and disclose when fictional rows are present.

## Authentication and payments

Login and role authorization are not implemented. The optional password hash field is nullable, cannot be set by the public CRUD API, and is always omitted from responses. Roles are validated as values but do not grant access. Orders use simulated payment only; no payment provider or card fields exist.
