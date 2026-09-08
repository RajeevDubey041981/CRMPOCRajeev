-- Generated from current SQLAlchemy models for SQL Server
-- Date: 2026-08-11


CREATE TABLE couriers (
	id INTEGER NOT NULL IDENTITY, 
	courier_name VARCHAR(255) NOT NULL, 
	contact_name VARCHAR(255) NULL, 
	contact_mobile VARCHAR(20) NULL, 
	email VARCHAR(255) NULL, 
	address TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE item_masters (
	id INTEGER NOT NULL IDENTITY, 
	item_code VARCHAR(100) NOT NULL, 
	item_name VARCHAR(255) NOT NULL, 
	category VARCHAR(100) NULL, 
	description TEXT NULL, 
	brand VARCHAR(100) NULL, 
	unit VARCHAR(50) NULL, 
	hsn_code VARCHAR(20) NULL, 
	mrp NUMERIC(10, 2) NULL, 
	is_active BIT NOT NULL DEFAULT 'true', 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE market_categories (
	id INTEGER NOT NULL IDENTITY, 
	name VARCHAR(255) NOT NULL, 
	parent_id INTEGER NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES market_categories (id)
);


CREATE TABLE market_users (
	id INTEGER NOT NULL IDENTITY, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20) NULL, 
	address TEXT NULL, 
	city VARCHAR(100) NULL, 
	state VARCHAR(100) NULL, 
	role VARCHAR(50) NOT NULL DEFAULT 'Retailer', 
	status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	fee_status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	onboarding_fee NUMERIC(10, 2) NULL, 
	joined_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id)
);


CREATE TABLE roles (
	id INTEGER NOT NULL IDENTITY, 
	name VARCHAR(100) NOT NULL, 
	description TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);


CREATE TABLE users (
	id INTEGER NOT NULL IDENTITY, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	role VARCHAR(100) NOT NULL, 
	phone VARCHAR(20) NULL, 
	is_active BIT NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE vendors (
	id INTEGER NOT NULL IDENTITY, 
	vendor_code VARCHAR(50) NOT NULL, 
	name_of_firm VARCHAR(255) NOT NULL, 
	contact_name VARCHAR(255) NULL, 
	contact_mobile VARCHAR(20) NULL, 
	email VARCHAR(255) NULL, 
	gst_no VARCHAR(20) NULL, 
	address TEXT NULL, 
	state VARCHAR(100) NULL, 
	district VARCHAR(100) NULL, 
	pincode VARCHAR(10) NULL, 
	latitude NUMERIC(10, 8) NULL, 
	longitude NUMERIC(11, 8) NULL, 
	is_active BIT NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id)
);


CREATE TABLE market_items (
	id INTEGER NOT NULL IDENTITY, 
	sku VARCHAR(100) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	company VARCHAR(100) NULL, 
	category_id INTEGER NULL, 
	base_price NUMERIC(10, 2) NULL, 
	mrp NUMERIC(10, 2) NULL, 
	image_path VARCHAR(500) NULL, 
	status VARCHAR(20) NOT NULL DEFAULT 'Active', 
	stock_count INTEGER NOT NULL DEFAULT '0', 
	description TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES market_categories (id)
);


CREATE TABLE market_orders (
	id INTEGER NOT NULL IDENTITY, 
	order_no VARCHAR(50) NOT NULL, 
	retailer_id INTEGER NULL, 
	distributor_id INTEGER NULL, 
	total_amount NUMERIC(12, 2) NULL, 
	status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	notes TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(retailer_id) REFERENCES market_users (id), 
	FOREIGN KEY(distributor_id) REFERENCES market_users (id)
);


CREATE TABLE orders (
	id INTEGER NOT NULL IDENTITY, 
	order_no VARCHAR(255) NULL, 
	order_date DATETIME NOT NULL, 
	oem_bill_no VARCHAR(100) NULL, 
	vendor_id INTEGER NULL, 
	customer_name VARCHAR(255) NULL, 
	customer_contact VARCHAR(20) NULL, 
	customer_email VARCHAR(255) NULL, 
	customer_city VARCHAR(100) NULL, 
	customer_state VARCHAR(100) NULL, 
	customer_address TEXT NULL, 
	courier_id INTEGER NULL, 
	lrn_no VARCHAR(100) NULL, 
	vendor_bill_no VARCHAR(100) NULL, 
	vendor_bill_date DATETIME NULL, 
	status VARCHAR(50) NOT NULL, 
	expected_delivery_date DATETIME NULL, 
	actual_delivery_date DATETIME NULL, 
	order_file_path VARCHAR(500) NULL, 
	created_by INTEGER NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vendor_id) REFERENCES vendors (id), 
	FOREIGN KEY(courier_id) REFERENCES couriers (id), 
	FOREIGN KEY(created_by) REFERENCES users (id)
);


CREATE TABLE payment_transactions (
	id INTEGER NOT NULL IDENTITY, 
	payment_type VARCHAR(20) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	request_count INTEGER NOT NULL, 
	recorded_by_user_id INTEGER NULL, 
	engineer_user_id INTEGER NULL, 
	recorded_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(recorded_by_user_id) REFERENCES users (id), 
	FOREIGN KEY(engineer_user_id) REFERENCES users (id)
);


CREATE TABLE permissions (
	id INTEGER NOT NULL IDENTITY, 
	role_id INTEGER NOT NULL, 
	module VARCHAR(100) NOT NULL, 
	sub_module VARCHAR(100) NULL, 
	can_view BIT NOT NULL, 
	can_create BIT NOT NULL, 
	can_edit BIT NOT NULL, 
	can_delete BIT NOT NULL, 
	can_export BIT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE
);


CREATE TABLE projects (
	id INTEGER NOT NULL IDENTITY, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NULL, 
	status VARCHAR(30) NOT NULL, 
	owner_id INTEGER NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(owner_id) REFERENCES users (id)
);


CREATE TABLE market_order_items (
	id INTEGER NOT NULL IDENTITY, 
	order_id INTEGER NOT NULL, 
	item_id INTEGER NULL, 
	qty INTEGER NOT NULL DEFAULT '1', 
	unit_price NUMERIC(10, 2) NULL, 
	subtotal NUMERIC(12, 2) NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES market_orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(item_id) REFERENCES market_items (id)
);


CREATE TABLE order_items (
	id INTEGER NOT NULL IDENTITY, 
	order_id INTEGER NOT NULL, 
	item_id INTEGER NULL, 
	item_code VARCHAR(100) NULL, 
	serial_no VARCHAR(100) NULL, 
	serial_no_2 VARCHAR(100) NULL, 
	item_qty INTEGER NOT NULL, 
	pcb_warranty_years INTEGER NULL, 
	component_warranty_years INTEGER NULL, 
	machine_warranty_years INTEGER NULL, 
	free_service_count INTEGER NOT NULL, 
	service_consume_count INTEGER NOT NULL, 
	installation_status VARCHAR(50) NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id) ON DELETE CASCADE, 
	FOREIGN KEY(item_id) REFERENCES item_masters (id)
);


CREATE TABLE workflow_tasks (
	id INTEGER NOT NULL IDENTITY, 
	project_id INTEGER NOT NULL, 
	task_name VARCHAR(255) NOT NULL, 
	task_type VARCHAR(50) NOT NULL, 
	sequence INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	advisor_id VARCHAR(100) NULL, 
	input_data TEXT NULL, 
	output_data TEXT NULL, 
	error_message TEXT NULL, 
	started_at VARCHAR(50) NULL, 
	completed_at VARCHAR(50) NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES projects (id) ON DELETE CASCADE
);


CREATE TABLE claims (
	id INTEGER NOT NULL IDENTITY, 
	claim_id VARCHAR(100) NOT NULL, 
	order_no VARCHAR(255) NULL, 
	serial_number VARCHAR(100) NULL, 
	order_item_id INTEGER NULL, 
	customer_name VARCHAR(255) NULL, 
	customer_contact VARCHAR(20) NULL, 
	customer_email VARCHAR(255) NULL, 
	status VARCHAR(50) NOT NULL, 
	submitted_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	processed_by INTEGER NULL, 
	notes TEXT NULL, 
	bank_name VARCHAR(100) NULL, 
	account_holder_name VARCHAR(255) NULL, 
	account_number VARCHAR(100) NULL, 
	ifsc_code VARCHAR(20) NULL, 
	admin_remark TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_item_id) REFERENCES order_items (id), 
	FOREIGN KEY(processed_by) REFERENCES users (id)
);


CREATE TABLE complaints (
	id INTEGER NOT NULL IDENTITY, 
	comp_no VARCHAR(100) NOT NULL, 
	comp_date DATETIME NOT NULL DEFAULT GETDATE(), 
	customer_name VARCHAR(255) NOT NULL, 
	customer_mobile VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255) NULL, 
	customer_address TEXT NULL, 
	model_details VARCHAR(255) NULL, 
	problem_description TEXT NULL, 
	query_type VARCHAR(50) NULL, 
	status VARCHAR(50) NOT NULL, 
	status_date DATETIMEOFFSET NULL, 
	assigned_engineer INTEGER NULL, 
	remark TEXT NULL, 
	service_proof_path VARCHAR(500) NULL, 
	access_code VARCHAR(100) NULL, 
	send_sms BIT NOT NULL, 
	created_by INTEGER NULL, 
	order_item_id INTEGER NULL, 
	serial_no VARCHAR(100) NULL, 
	source VARCHAR(50) NOT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	deleted_at DATETIMEOFFSET NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assigned_engineer) REFERENCES users (id), 
	FOREIGN KEY(created_by) REFERENCES users (id), 
	FOREIGN KEY(order_item_id) REFERENCES order_items (id)
);


CREATE TABLE installation_requests (
	id INTEGER NOT NULL IDENTITY, 
	customer_name VARCHAR(255) NOT NULL, 
	contact_number VARCHAR(20) NOT NULL, 
	address TEXT NULL, 
	order_item_id INTEGER NULL, 
	product_name VARCHAR(255) NULL, 
	serial_no VARCHAR(100) NULL, 
	serial_no_2 VARCHAR(100) NULL, 
	request_date DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	assigned_engineer INTEGER NULL, 
	status VARCHAR(50) NOT NULL, 
	installation_date DATETIMEOFFSET NULL, 
	work_report TEXT NULL, 
	work_report_file_path VARCHAR(500) NULL, 
	settlement_approved_by INTEGER NULL, 
	payment_amount_requested NUMERIC(10, 2) NULL, 
	payment_type_requested VARCHAR(20) NULL, 
	payment_qr_code_path VARCHAR(500) NULL, 
	payment_qr_code_blob IMAGE NULL, 
	payment_qr_code_filename VARCHAR(255) NULL, 
	payment_qr_code_content_type VARCHAR(100) NULL, 
	payment_qr_code_size_bytes INTEGER NULL, 
	payment_proof_file_path VARCHAR(500) NULL, 
	payment_requested_at DATETIMEOFFSET NULL, 
	payment_amount_paid NUMERIC(10, 2) NULL, 
	payment_type_paid VARCHAR(20) NULL, 
	payment_recorded_at DATETIMEOFFSET NULL, 
	payment_recorded_by INTEGER NULL, 
	payment_transaction_id INTEGER NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_item_id) REFERENCES order_items (id), 
	FOREIGN KEY(assigned_engineer) REFERENCES users (id), 
	FOREIGN KEY(settlement_approved_by) REFERENCES users (id), 
	FOREIGN KEY(payment_recorded_by) REFERENCES users (id), 
	FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id)
);


CREATE TABLE serial_history_events (
	id INTEGER NOT NULL IDENTITY, 
	order_item_id INTEGER NULL, 
	serial_no VARCHAR(100) NOT NULL, 
	serial_no_2 VARCHAR(100) NULL, 
	event_type VARCHAR(50) NOT NULL, 
	event_subtype VARCHAR(100) NULL, 
	event_at DATETIMEOFFSET NOT NULL, 
	performed_by_user_id INTEGER NULL, 
	performed_by_name VARCHAR(255) NULL, 
	source_table VARCHAR(100) NULL, 
	source_id INTEGER NULL, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	remarks TEXT NULL, 
	metadata_json TEXT NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_serial_history_source_event UNIQUE (source_table, source_id, event_type, serial_no), 
	FOREIGN KEY(order_item_id) REFERENCES order_items (id), 
	FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
);


CREATE TABLE calls (
	id INTEGER NOT NULL IDENTITY, 
	ref_no VARCHAR(100) NOT NULL, 
	customer_name VARCHAR(255) NULL, 
	customer_email VARCHAR(255) NULL, 
	phone VARCHAR(20) NULL, 
	call_type VARCHAR(20) NULL, 
	status VARCHAR(30) NULL, 
	priority VARCHAR(20) NOT NULL, 
	assigned_to INTEGER NULL, 
	transferred_to INTEGER NULL, 
	is_transferred BIT NOT NULL, 
	duration_secs INTEGER NULL, 
	call_datetime DATETIMEOFFSET NOT NULL, 
	followup_date DATETIMEOFFSET NULL, 
	notes TEXT NULL, 
	follow_up_notes TEXT NULL, 
	follow_up_status VARCHAR(30) NULL, 
	complaint_id INTEGER NULL, 
	created_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	updated_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assigned_to) REFERENCES users (id), 
	FOREIGN KEY(transferred_to) REFERENCES users (id), 
	FOREIGN KEY(complaint_id) REFERENCES complaints (id)
);


CREATE TABLE claim_photos (
	id INTEGER NOT NULL IDENTITY, 
	claim_id INTEGER NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	uploaded_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(claim_id) REFERENCES claims (id) ON DELETE CASCADE
);


CREATE TABLE complaint_status_logs (
	id INTEGER NOT NULL IDENTITY, 
	complaint_id INTEGER NOT NULL, 
	old_status VARCHAR(50) NULL, 
	new_status VARCHAR(50) NULL, 
	changed_by INTEGER NULL, 
	remark TEXT NULL, 
	document_path VARCHAR(500) NULL, 
	action_taken VARCHAR(100) NULL, 
	changed_at DATETIMEOFFSET NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(complaint_id) REFERENCES complaints (id), 
	FOREIGN KEY(changed_by) REFERENCES users (id)
);

CREATE UNIQUE INDEX ix_item_masters_item_code ON item_masters (item_code);

CREATE UNIQUE INDEX ix_market_users_email ON market_users (email);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE INDEX ix_vendors_name_of_firm ON vendors (name_of_firm);

CREATE UNIQUE INDEX ix_vendors_vendor_code ON vendors (vendor_code);

CREATE UNIQUE INDEX ix_market_items_sku ON market_items (sku);

CREATE UNIQUE INDEX ix_market_orders_order_no ON market_orders (order_no);

CREATE INDEX ix_orders_status ON orders (status);

CREATE INDEX ix_orders_customer_contact ON orders (customer_contact);

CREATE INDEX ix_orders_customer_name ON orders (customer_name);

CREATE INDEX ix_orders_oem_bill_no ON orders (oem_bill_no);

CREATE INDEX ix_orders_vendor_id ON orders (vendor_id);

CREATE UNIQUE INDEX ix_orders_order_no ON orders (order_no);

CREATE INDEX ix_projects_status ON projects (status);

CREATE INDEX ix_order_items_item_code ON order_items (item_code);

CREATE INDEX ix_order_items_serial_no ON order_items (serial_no);

CREATE INDEX ix_workflow_tasks_project_id ON workflow_tasks (project_id);

CREATE UNIQUE INDEX ix_claims_claim_id ON claims (claim_id);

CREATE UNIQUE INDEX ix_complaints_comp_no ON complaints (comp_no);

CREATE INDEX ix_complaints_customer_mobile ON complaints (customer_mobile);

CREATE INDEX ix_complaints_order_item_id ON complaints (order_item_id);

CREATE INDEX ix_complaints_assigned_engineer ON complaints (assigned_engineer);

CREATE INDEX ix_complaints_serial_no ON complaints (serial_no);

CREATE INDEX ix_complaints_status ON complaints (status);

CREATE INDEX ix_installation_requests_status ON installation_requests (status);

CREATE INDEX ix_installation_requests_request_date ON installation_requests (request_date);

CREATE INDEX ix_serial_history_events_event_at ON serial_history_events (event_at);

CREATE INDEX ix_serial_history_events_serial_no ON serial_history_events (serial_no);

CREATE INDEX ix_serial_history_events_order_item_id ON serial_history_events (order_item_id);

CREATE UNIQUE INDEX ix_calls_ref_no ON calls (ref_no);

CREATE INDEX ix_calls_followup_date ON calls (followup_date);

CREATE INDEX ix_calls_status ON calls (status);
