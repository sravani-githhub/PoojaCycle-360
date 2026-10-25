# API overview

Run the FastAPI service and open `/docs` for interactive OpenAPI/Swagger documentation. Resources use plural kebab-case paths, for example `/api/waste-reports`.

| Method | Path | Behavior |
|---|---|---|
| GET | `/api/health` | Database connectivity status and database type. |
| GET | `/api/dashboard` | Saved collected/processed quantities, including a demo-seed disclosure. |
| GET | `/api/{resource}?limit=50&offset=0` | Paginated database rows and total count. |
| POST | `/api/{resource}` | Validated insert; returns saved row and 201. |
| GET | `/api/{resource}/{id}` | One saved row or 404. |
| PATCH | `/api/{resource}/{id}` | Validated update; 404 if missing, 409 on integrity conflict. |
| DELETE | `/api/{resource}/{id}` | Delete if no traceability constraint blocks it; 204 on success. |
| POST | `/api/checkout` | Atomically saves an order and item snapshots using current catalog prices, decrements stock, and marks payment simulated. |

`resource` may be `users`, `waste-sources`, `waste-types`, `waste-reports`, `collection-assignments`, `waste-batches`, `processing-records`, `artisans`, `material-requests`, `products`, `product-batches`, `orders`, `order-items`, or `impact-records`.

Invalid values return 422, missing records 404, duplicate/foreign-key conflicts 409, and database outages 503/500 without returning SQL or credentials. `users` responses never include `password_hash`. There is currently no login endpoint or authorization layer; sample organizer/customer records are used for the prototype forms.
