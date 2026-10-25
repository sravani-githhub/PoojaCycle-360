-- Generated from backend/app/models.py using the SQLAlchemy PostgreSQL dialect.

-- Prefer `python -m alembic upgrade head` for managed schema updates.


CREATE TABLE users (
	id SERIAL NOT NULL, 
	full_name VARCHAR(160) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash VARCHAR(255), 
	role VARCHAR(32) NOT NULL, 
	phone_number VARCHAR(32), 
	location VARCHAR(200), 
	account_status VARCHAR(20) DEFAULT 'active' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_users_role CHECK (role IN ('admin','organizer','collector','artisan','processing_partner','customer')), 
	CONSTRAINT ck_users_status CHECK (account_status IN ('active','inactive','suspended'))
)

;

CREATE UNIQUE INDEX ix_users_email ON users (email);


CREATE TABLE waste_sources (
	id SERIAL NOT NULL, 
	source_name VARCHAR(180) NOT NULL, 
	source_type VARCHAR(24) NOT NULL, 
	address TEXT NOT NULL, 
	contact_name VARCHAR(160), 
	contact_phone VARCHAR(32), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_sources_type CHECK (source_type IN ('temple','festival','community_site'))
)

;


CREATE TABLE waste_types (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	description TEXT NOT NULL, 
	handling_notes TEXT NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;


CREATE TABLE artisans (
	user_id INTEGER, 
	id SERIAL NOT NULL, 
	display_name VARCHAR(160) NOT NULL, 
	skills TEXT NOT NULL, 
	preferred_materials TEXT NOT NULL, 
	location VARCHAR(200) NOT NULL, 
	availability_status VARCHAR(20) NOT NULL, 
	contact_visibility VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_artisans_availability CHECK (availability_status IN ('available','busy','inactive')), 
	CONSTRAINT ck_artisans_visibility CHECK (contact_visibility IN ('private','platform_only','public')), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE SET NULL
)

;


CREATE TABLE orders (
	id SERIAL NOT NULL, 
	customer_user_id INTEGER NOT NULL, 
	order_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	payment_mode VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_orders_total_nonnegative CHECK (total_amount >= 0), 
	CONSTRAINT ck_orders_status CHECK (status IN ('pending','confirmed','shipped','completed','cancelled')), 
	CONSTRAINT ck_orders_simulated_payment CHECK (payment_mode = 'simulated'), 
	FOREIGN KEY(customer_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_orders_customer_user_id ON orders (customer_user_id);


CREATE TABLE waste_reports (
	id SERIAL NOT NULL, 
	source_id INTEGER NOT NULL, 
	waste_type_id INTEGER NOT NULL, 
	quantity NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	contamination_level NUMERIC(5, 2), 
	contamination_notes TEXT, 
	availability_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	collection_status VARCHAR(16) NOT NULL, 
	reported_by_user_id INTEGER NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_waste_reports_quantity_positive CHECK (quantity > 0), 
	CONSTRAINT ck_waste_reports_unit CHECK (unit IN ('kg','g','tonne','item')), 
	CONSTRAINT ck_waste_reports_status CHECK (collection_status IN ('pending','assigned','scheduled','collected','cancelled','failed')), 
	CONSTRAINT ck_waste_reports_contamination CHECK (contamination_level IS NULL OR (contamination_level >= 0 AND contamination_level <= 100)), 
	FOREIGN KEY(source_id) REFERENCES waste_sources (id) ON DELETE RESTRICT, 
	FOREIGN KEY(waste_type_id) REFERENCES waste_types (id) ON DELETE RESTRICT, 
	FOREIGN KEY(reported_by_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_waste_reports_source_id ON waste_reports (source_id);

CREATE INDEX ix_waste_reports_status_availability ON waste_reports (collection_status, availability_at);

CREATE INDEX ix_waste_reports_waste_type_id ON waste_reports (waste_type_id);


CREATE TABLE artisan_material_requests (
	id SERIAL NOT NULL, 
	artisan_id INTEGER NOT NULL, 
	waste_type_id INTEGER NOT NULL, 
	required_quantity NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	request_date TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_material_request_quantity_positive CHECK (required_quantity > 0), 
	CONSTRAINT ck_material_request_unit CHECK (unit IN ('kg','g','tonne','item')), 
	CONSTRAINT ck_material_request_status CHECK (status IN ('open','matched','fulfilled','cancelled')), 
	FOREIGN KEY(artisan_id) REFERENCES artisans (id) ON DELETE CASCADE, 
	FOREIGN KEY(waste_type_id) REFERENCES waste_types (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_artisan_material_requests_artisan_id ON artisan_material_requests (artisan_id);


CREATE TABLE collection_assignments (
	id SERIAL NOT NULL, 
	waste_report_id INTEGER NOT NULL, 
	collector_user_id INTEGER, 
	scheduled_pickup_at TIMESTAMP WITH TIME ZONE, 
	actual_pickup_at TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(16) NOT NULL, 
	notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_assignments_status CHECK (status IN ('pending','assigned','scheduled','collected','cancelled','failed')), 
	FOREIGN KEY(waste_report_id) REFERENCES waste_reports (id) ON DELETE CASCADE, 
	FOREIGN KEY(collector_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_assignments_status_pickup ON collection_assignments (status, scheduled_pickup_at);

CREATE INDEX ix_collection_assignments_collector_user_id ON collection_assignments (collector_user_id);

CREATE INDEX ix_collection_assignments_waste_report_id ON collection_assignments (waste_report_id);


CREATE TABLE products (
	id SERIAL NOT NULL, 
	artisan_id INTEGER, 
	product_name VARCHAR(180) NOT NULL, 
	description TEXT NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	price NUMERIC(10, 2) NOT NULL, 
	available_stock INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_products_price_nonnegative CHECK (price >= 0), 
	CONSTRAINT ck_products_stock_nonnegative CHECK (available_stock >= 0), 
	CONSTRAINT ck_products_status CHECK (status IN ('draft','active','out_of_stock','archived')), 
	FOREIGN KEY(artisan_id) REFERENCES artisans (id) ON DELETE SET NULL
)

;

CREATE INDEX ix_products_artisan_id ON products (artisan_id);


CREATE TABLE waste_batches (
	id SERIAL NOT NULL, 
	batch_code VARCHAR(32) NOT NULL, 
	waste_report_id INTEGER NOT NULL, 
	waste_type_id INTEGER NOT NULL, 
	received_quantity NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	current_stage VARCHAR(20) NOT NULL, 
	quality_notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_batches_quantity_positive CHECK (received_quantity > 0), 
	CONSTRAINT ck_batches_unit CHECK (unit IN ('kg','g','tonne','item')), 
	CONSTRAINT ck_batches_stage CHECK (current_stage IN ('received','sorted','in_processing','processed','composted','reused','recycled','rejected')), 
	CONSTRAINT uq_batch_report UNIQUE (waste_report_id), 
	FOREIGN KEY(waste_report_id) REFERENCES waste_reports (id) ON DELETE RESTRICT, 
	FOREIGN KEY(waste_type_id) REFERENCES waste_types (id) ON DELETE RESTRICT
)

;

CREATE UNIQUE INDEX ix_waste_batches_batch_code ON waste_batches (batch_code);


CREATE TABLE order_items (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(10, 2) NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_order_items_quantity_positive CHECK (quantity > 0), 
	CONSTRAINT ck_order_items_amounts_nonnegative CHECK (unit_price >= 0 AND subtotal >= 0), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_order_items_order_id ON order_items (order_id);


CREATE TABLE processing_records (
	id SERIAL NOT NULL, 
	batch_id INTEGER NOT NULL, 
	processing_partner_user_id INTEGER NOT NULL, 
	processing_method VARCHAR(40) NOT NULL, 
	input_quantity NUMERIC(12, 3) NOT NULL, 
	input_unit VARCHAR(10) NOT NULL, 
	output_quantity NUMERIC(12, 3), 
	output_unit VARCHAR(10), 
	output_description TEXT, 
	processing_date TIMESTAMP WITH TIME ZONE NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	evidence_notes TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_processing_input_positive CHECK (input_quantity > 0), 
	CONSTRAINT ck_processing_input_unit CHECK (input_unit IN ('kg','g','tonne','item')), 
	CONSTRAINT ck_processing_output_nonnegative CHECK (output_quantity IS NULL OR output_quantity >= 0), 
	CONSTRAINT ck_processing_output_unit CHECK (output_unit IS NULL OR output_unit IN ('kg','g','tonne','item')), 
	CONSTRAINT ck_processing_output_unit_required CHECK ((output_quantity IS NULL AND output_unit IS NULL) OR (output_quantity IS NOT NULL AND output_unit IS NOT NULL)), 
	CONSTRAINT ck_processing_status CHECK (status IN ('planned','in_progress','completed','failed')), 
	CONSTRAINT ck_processing_method CHECK (processing_method IN ('composting','coir_production','craft_production','paper_making','reuse_upcycling','authorized_recycling','sorting','other')), 
	FOREIGN KEY(batch_id) REFERENCES waste_batches (id) ON DELETE CASCADE, 
	FOREIGN KEY(processing_partner_user_id) REFERENCES users (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_processing_records_batch_id ON processing_records (batch_id);


CREATE TABLE product_batches (
	id SERIAL NOT NULL, 
	product_id INTEGER NOT NULL, 
	batch_id INTEGER NOT NULL, 
	quantity_used NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_product_batch UNIQUE (product_id, batch_id), 
	CONSTRAINT ck_product_batches_quantity_positive CHECK (quantity_used > 0), 
	CONSTRAINT ck_product_batches_unit CHECK (unit IN ('kg','g','tonne','item')), 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE CASCADE, 
	FOREIGN KEY(batch_id) REFERENCES waste_batches (id) ON DELETE RESTRICT
)

;

CREATE INDEX ix_product_batches_batch_id ON product_batches (batch_id);

CREATE INDEX ix_product_batches_product_id ON product_batches (product_id);


CREATE TABLE impact_records (
	id SERIAL NOT NULL, 
	batch_id INTEGER, 
	processing_record_id INTEGER, 
	measured_quantity NUMERIC(12, 3) NOT NULL, 
	unit VARCHAR(10) NOT NULL, 
	quantity_basis VARCHAR(16) NOT NULL, 
	outcome_category VARCHAR(50) NOT NULL, 
	verification_status VARCHAR(24) NOT NULL, 
	evidence_reference TEXT, 
	recorded_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	notes TEXT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(batch_id) REFERENCES waste_batches (id) ON DELETE CASCADE, 
	FOREIGN KEY(processing_record_id) REFERENCES processing_records (id) ON DELETE CASCADE
)

;

CREATE INDEX ix_impact_records_batch_id ON impact_records (batch_id);

CREATE INDEX ix_impact_records_processing_record_id ON impact_records (processing_record_id);
