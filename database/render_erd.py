"""Render the ER model to a self-contained SVG; no browser or third-party library required."""
from html import escape
from pathlib import Path

OUT = Path(__file__).with_name("ER_diagram.svg")
nodes = {
    "users": (40, 110, "USERS", ["PK id", "UK email", "role, status, timestamps"]),
    "sources": (40, 300, "WASTE_SOURCES", ["PK id", "source_name, source_type", "address, contact fields"]),
    "types": (40, 490, "WASTE_TYPES", ["PK id", "UK name", "description, handling_notes"]),
    "artisans": (40, 680, "ARTISANS", ["PK id", "FK user_id (optional)", "skills, materials, availability"]),
    "products": (40, 870, "PRODUCTS", ["PK id", "FK artisan_id (optional)", "price, stock, status"]),
    "orders": (40, 1060, "ORDERS", ["PK id", "FK customer_user_id", "order_date, status, total"]),
    "reports": (420, 110, "WASTE_REPORTS", ["PK id", "FK source_id, waste_type_id", "FK reported_by_user_id", "quantity, unit, status"]),
    "assignments": (420, 300, "COLLECTION_ASSIGNMENTS", ["PK id", "FK waste_report_id", "FK collector_user_id", "pickup times, status"]),
    "requests": (420, 490, "MATERIAL_REQUESTS", ["PK id", "FK artisan_id, waste_type_id", "required_quantity, unit", "status"]),
    "items": (420, 680, "ORDER_ITEMS", ["PK id", "FK order_id, product_id", "quantity, unit_price, subtotal"]),
    "product_batches": (420, 870, "PRODUCT_BATCHES", ["PK id; unique product + batch", "FK product_id, batch_id", "quantity_used, unit"]),
    "batches": (420, 1060, "WASTE_BATCHES", ["PK id", "FK waste_report_id (unique)", "FK waste_type_id", "received quantity, stage"]),
    "processing": (800, 300, "PROCESSING_RECORDS", ["PK id", "FK batch_id, partner_user_id", "method, input/output", "status, evidence"]),
    "impact": (800, 680, "IMPACT_RECORDS", ["PK id", "FK batch_id / processing_record_id", "measured quantity, basis", "verification status"]),
}
edges = [
    ("users", "reports", "1:N"), ("sources", "reports", "1:N"), ("types", "reports", "1:N"),
    ("reports", "assignments", "1:N"), ("users", "assignments", "1:N"),
    ("reports", "batches", "1:0..1"), ("types", "batches", "1:N"),
    ("batches", "processing", "1:N"), ("users", "processing", "partner"),
    ("users", "artisans", "1:0..1"), ("artisans", "requests", "1:N"), ("types", "requests", "1:N"),
    ("artisans", "products", "1:N"), ("products", "product_batches", "1:N"), ("batches", "product_batches", "1:N"),
    ("users", "orders", "1:N"), ("orders", "items", "1:N"), ("products", "items", "1:N"),
    ("batches", "impact", "0..1:N"), ("processing", "impact", "0..1:N"),
]
svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1160" height="1320" viewBox="0 0 1160 1320">',
       '<rect width="1160" height="1320" fill="#f7f5ef"/>',
       '<text x="40" y="48" font-family="Arial,sans-serif" font-size="25" font-weight="700" fill="#2c4a3e">PoojaCycle 360 — relational data model</text>',
       '<text x="40" y="76" font-family="Arial,sans-serif" font-size="13" fill="#526259">FK relationships and cardinalities · PostgreSQL / SQLAlchemy</text>',
       '<defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#789183"/></marker></defs>']
for src, dst, label in edges:
    x1, y1, *_ = nodes[src]; x2, y2, *_ = nodes[dst]
    w, h = 320, 132
    if x2 > x1:
        sx, sy, ex, ey = x1 + w, y1 + h / 2, x2, y2 + h / 2
        dx = max(45, (ex - sx) * .48)
        path = f'M {sx} {sy} C {sx+dx} {sy}, {ex-dx} {ey}, {ex} {ey}'
        tx, ty = (sx + ex) / 2, (sy + ey) / 2 - 6
    elif x2 == x1:
        sx, sy, ex, ey = x1 + w, y1 + h / 2, x2 + w, y2 + h / 2
        channel = x1 + w + 18
        path = f'M {sx} {sy} C {channel} {sy}, {channel} {ey}, {ex} {ey}'
        tx, ty = channel + 2, (sy + ey) / 2
    else:
        sx, sy, ex, ey = x1 + w, y1 + h / 2, x2 + w, y2 + h / 2
        path = f'M {sx} {sy} C {sx+65} {sy-20}, {ex+65} {ey-20}, {ex} {ey}'
        tx, ty = sx + 25, sy - 12
    svg.append(f'<path d="{path}" fill="none" stroke="#789183" stroke-width="1.5" opacity=".7" marker-end="url(#arrow)"/>')
    svg.append(f'<text x="{tx}" y="{ty}" font-family="Arial,sans-serif" font-size="10" fill="#526259">{escape(label)}</text>')
for key, (x, y, title, fields) in nodes.items():
    svg.append(f'<rect x="{x}" y="{y}" width="320" height="132" rx="12" fill="#fff" stroke="#9bad9d" stroke-width="1.5"/>')
    svg.append(f'<path d="M{x+12} {y} H{x+308} Q{x+320} {y} {x+320} {y+12} V{y+38} H{x} V{y+12} Q{x} {y} {x+12} {y}" fill="#dce8dd"/>')
    svg.append(f'<text x="{x+14}" y="{y+25}" font-family="Arial,sans-serif" font-size="13" font-weight="700" fill="#2c4a3e">{escape(title)}</text>')
    for i, field in enumerate(fields):
        svg.append(f'<text x="{x+14}" y="{y+59+i*18}" font-family="Arial,sans-serif" font-size="11" fill="#34433a">{escape(field)}</text>')
svg.append('<text x="40" y="1260" font-family="Arial,sans-serif" font-size="11" fill="#526259">Amounts use explicit units; prices use decimal currency; demo records are fictional and unverified.</text>')
svg.append('</svg>')
OUT.write_text('\n'.join(svg), encoding='utf-8')
print("Rendered ER diagram SVG.")
