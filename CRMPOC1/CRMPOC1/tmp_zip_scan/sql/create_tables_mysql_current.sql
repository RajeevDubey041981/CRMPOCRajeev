-- Generated from live MySQL database: indcool
-- Date: 2026-08-21


CREATE TABLE alembic_version (
	version_num VARCHAR(128) NOT NULL, 
	PRIMARY KEY (version_num)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE calls (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	ref_no VARCHAR(100) NOT NULL, 
	customer_name VARCHAR(255), 
	customer_email VARCHAR(255), 
	phone VARCHAR(20), 
	call_type VARCHAR(20), 
	status VARCHAR(30), 
	priority VARCHAR(20) NOT NULL DEFAULT 'medium', 
	assigned_to INTEGER, 
	transferred_to INTEGER, 
	is_transferred TINYINT(1) NOT NULL DEFAULT '0', 
	duration_secs INTEGER, 
	call_datetime DATETIME(6) NOT NULL, 
	followup_date DATETIME(6), 
	notes LONGTEXT, 
	follow_up_notes LONGTEXT, 
	follow_up_status VARCHAR(30), 
	complaint_id INTEGER, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE claim_photos (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	claim_id INTEGER NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	uploaded_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE claims (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	claim_id VARCHAR(100) NOT NULL, 
	order_no VARCHAR(255), 
	serial_number VARCHAR(100), 
	order_item_id INTEGER, 
	customer_name VARCHAR(255), 
	customer_contact VARCHAR(20), 
	customer_email VARCHAR(255), 
	status VARCHAR(50) NOT NULL DEFAULT 'Processing', 
	submitted_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	processed_by INTEGER, 
	notes LONGTEXT, 
	bank_name VARCHAR(100), 
	account_holder_name VARCHAR(255), 
	account_number VARCHAR(100), 
	ifsc_code VARCHAR(20), 
	admin_remark LONGTEXT, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE complaint_status_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	complaint_id INTEGER NOT NULL, 
	old_status VARCHAR(50), 
	new_status VARCHAR(50), 
	changed_by INTEGER, 
	remark LONGTEXT, 
	document_path VARCHAR(500), 
	action_taken VARCHAR(100), 
	changed_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE couriers (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	courier_name VARCHAR(255) NOT NULL, 
	contact_name VARCHAR(255), 
	contact_mobile VARCHAR(20), 
	email VARCHAR(255), 
	address LONGTEXT, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE item_masters (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	item_code VARCHAR(100) NOT NULL, 
	item_name VARCHAR(255) NOT NULL, 
	category VARCHAR(100), 
	description LONGTEXT, 
	brand VARCHAR(100), 
	unit VARCHAR(50), 
	hsn_code VARCHAR(20), 
	mrp DECIMAL(10, 2), 
	is_active TINYINT(1) NOT NULL DEFAULT '1', 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE market_categories (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	parent_id INTEGER, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE market_items (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	sku VARCHAR(100) NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	company VARCHAR(100), 
	category_id INTEGER, 
	base_price DECIMAL(10, 2), 
	mrp DECIMAL(10, 2), 
	image_path VARCHAR(500), 
	status VARCHAR(20) NOT NULL DEFAULT 'Active', 
	stock_count INTEGER NOT NULL DEFAULT '0', 
	description LONGTEXT, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE market_order_items (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	item_id INTEGER, 
	qty INTEGER NOT NULL DEFAULT '1', 
	unit_price DECIMAL(10, 2), 
	subtotal DECIMAL(12, 2), 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE market_orders (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_no VARCHAR(50) NOT NULL, 
	retailer_id INTEGER, 
	distributor_id INTEGER, 
	total_amount DECIMAL(12, 2), 
	status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	notes LONGTEXT, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE market_users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(20), 
	address LONGTEXT, 
	city VARCHAR(100), 
	state VARCHAR(100), 
	`role` VARCHAR(50) NOT NULL DEFAULT 'Retailer', 
	status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	fee_status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	onboarding_fee DECIMAL(10, 2), 
	joined_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE order_items (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_id INTEGER NOT NULL, 
	item_id INTEGER, 
	serial_no VARCHAR(100), 
	serial_no_2 VARCHAR(100), 
	item_qty INTEGER NOT NULL DEFAULT '1', 
	pcb_warranty_years INTEGER, 
	component_warranty_years INTEGER, 
	machine_warranty_years INTEGER, 
	free_service_count INTEGER NOT NULL DEFAULT '0', 
	service_consume_count INTEGER NOT NULL DEFAULT '0', 
	installation_status VARCHAR(50) NOT NULL DEFAULT 'Not Requested', 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	item_code VARCHAR(100), 
	dry_free_service_count INTEGER NOT NULL DEFAULT '0', 
	wet_free_service_count INTEGER NOT NULL DEFAULT '0', 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE orders (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_no VARCHAR(255), 
	order_date DATE NOT NULL, 
	oem_bill_no VARCHAR(100), 
	vendor_id INTEGER, 
	customer_name VARCHAR(255), 
	customer_contact VARCHAR(20), 
	customer_email VARCHAR(255), 
	customer_city VARCHAR(100), 
	customer_state VARCHAR(100), 
	customer_address LONGTEXT, 
	courier_id INTEGER, 
	lrn_no VARCHAR(100), 
	vendor_bill_no VARCHAR(100), 
	vendor_bill_date DATE, 
	status VARCHAR(50) NOT NULL DEFAULT 'Pending', 
	expected_delivery_date DATE, 
	actual_delivery_date DATE, 
	order_file_path VARCHAR(500), 
	created_by INTEGER, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE permissions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	role_id INTEGER NOT NULL, 
	module VARCHAR(100) NOT NULL, 
	sub_module VARCHAR(100), 
	can_view TINYINT(1) NOT NULL DEFAULT '0', 
	can_create TINYINT(1) NOT NULL DEFAULT '0', 
	can_edit TINYINT(1) NOT NULL DEFAULT '0', 
	can_delete TINYINT(1) NOT NULL DEFAULT '0', 
	can_export TINYINT(1) NOT NULL DEFAULT '0', 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE projects (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	title VARCHAR(255) NOT NULL, 
	description LONGTEXT, 
	status VARCHAR(30) NOT NULL DEFAULT 'Draft', 
	owner_id INTEGER, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE roles (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(100) NOT NULL, 
	description LONGTEXT, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_document_rules (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_type VARCHAR(50), 
	warranty_status VARCHAR(50), 
	query_type VARCHAR(50), 
	document_type VARCHAR(100) NOT NULL, 
	is_required TINYINT(1) NOT NULL DEFAULT '1', 
	is_active TINYINT(1) NOT NULL DEFAULT '1', 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	`role` VARCHAR(100) NOT NULL DEFAULT 'callcenter', 
	phone VARCHAR(20), 
	is_active TINYINT(1) NOT NULL DEFAULT '1', 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE vendors (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	vendor_code VARCHAR(50) NOT NULL, 
	name_of_firm VARCHAR(255) NOT NULL, 
	contact_name VARCHAR(255), 
	contact_mobile VARCHAR(20), 
	email VARCHAR(255), 
	gst_no VARCHAR(20), 
	address LONGTEXT, 
	state VARCHAR(100), 
	district VARCHAR(100), 
	pincode VARCHAR(10), 
	latitude DECIMAL(10, 8), 
	longitude DECIMAL(11, 8), 
	is_active TINYINT(1) NOT NULL DEFAULT '1', 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE workflow_tasks (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	project_id INTEGER NOT NULL, 
	task_name VARCHAR(255) NOT NULL, 
	task_type VARCHAR(50) NOT NULL, 
	sequence INTEGER NOT NULL DEFAULT '1', 
	status VARCHAR(20) NOT NULL DEFAULT 'Pending', 
	advisor_id VARCHAR(100), 
	input_data LONGTEXT, 
	output_data LONGTEXT, 
	error_message LONGTEXT, 
	started_at VARCHAR(50), 
	completed_at VARCHAR(50), 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	PRIMARY KEY (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE complaints (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	comp_no VARCHAR(100) NOT NULL, 
	comp_date DATE NOT NULL DEFAULT (curdate()), 
	customer_name VARCHAR(255) NOT NULL, 
	customer_mobile VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255), 
	customer_address LONGTEXT, 
	model_details VARCHAR(255), 
	problem_description LONGTEXT, 
	query_type VARCHAR(50), 
	status VARCHAR(50) NOT NULL DEFAULT 'Pending', 
	status_date DATETIME(6), 
	assigned_engineer INTEGER, 
	remark LONGTEXT, 
	service_proof_path VARCHAR(500), 
	access_code VARCHAR(100), 
	send_sms TINYINT(1) NOT NULL DEFAULT '1', 
	created_by INTEGER, 
	source VARCHAR(50) NOT NULL DEFAULT 'callcenter', 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	deleted_at DATETIME(6), 
	order_item_id INTEGER, 
	serial_no VARCHAR(100), 
	PRIMARY KEY (id), 
	CONSTRAINT fk_complaints_order_item_id_order_items FOREIGN KEY(order_item_id) REFERENCES order_items (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE payment_transactions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	payment_type VARCHAR(20) NOT NULL, 
	total_amount DECIMAL(12, 2) NOT NULL, 
	request_count INTEGER NOT NULL, 
	recorded_by_user_id INTEGER, 
	engineer_user_id INTEGER, 
	recorded_at DATETIME NOT NULL DEFAULT (now()), 
	PRIMARY KEY (id), 
	CONSTRAINT payment_transactions_ibfk_1 FOREIGN KEY(recorded_by_user_id) REFERENCES users (id), 
	CONSTRAINT payment_transactions_ibfk_2 FOREIGN KEY(engineer_user_id) REFERENCES users (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE serial_history_events (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	order_item_id INTEGER, 
	serial_no VARCHAR(100) NOT NULL, 
	serial_no_2 VARCHAR(100), 
	event_type VARCHAR(50) NOT NULL, 
	event_subtype VARCHAR(100), 
	event_at DATETIME NOT NULL, 
	performed_by_user_id INTEGER, 
	performed_by_name VARCHAR(255), 
	source_table VARCHAR(100), 
	source_id INTEGER, 
	title VARCHAR(255) NOT NULL, 
	description TEXT NOT NULL, 
	remarks TEXT, 
	metadata_json JSON, 
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_serial_history_order_item FOREIGN KEY(order_item_id) REFERENCES order_items (id), 
	CONSTRAINT fk_serial_history_performed_by FOREIGN KEY(performed_by_user_id) REFERENCES users (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE installation_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	customer_name VARCHAR(255) NOT NULL, 
	contact_number VARCHAR(20) NOT NULL, 
	address LONGTEXT, 
	order_item_id INTEGER, 
	product_name VARCHAR(255), 
	serial_no VARCHAR(100), 
	serial_no_2 VARCHAR(100), 
	request_date DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	assigned_engineer INTEGER, 
	status VARCHAR(50) NOT NULL DEFAULT 'Pending', 
	installation_date DATETIME(6), 
	work_report LONGTEXT, 
	work_report_file_path VARCHAR(500), 
	settlement_approved_by INTEGER, 
	created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	updated_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6), 
	payment_amount_requested DECIMAL(10, 2), 
	payment_type_requested VARCHAR(20), 
	payment_qr_code_path VARCHAR(500), 
	payment_requested_at DATETIME, 
	payment_amount_paid DECIMAL(10, 2), 
	payment_type_paid VARCHAR(20), 
	payment_recorded_at DATETIME, 
	payment_recorded_by INTEGER, 
	payment_proof_file_path VARCHAR(500), 
	payment_qr_code_blob LONGBLOB, 
	payment_qr_code_filename VARCHAR(255), 
	payment_qr_code_content_type VARCHAR(100), 
	payment_qr_code_size_bytes INTEGER, 
	payment_transaction_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_installation_requests_payment_recorded_by_users FOREIGN KEY(payment_recorded_by) REFERENCES users (id), 
	CONSTRAINT fk_installation_requests_payment_transaction_id FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	request_no VARCHAR(100) NOT NULL, 
	request_date DATE NOT NULL, 
	query_type VARCHAR(50) NOT NULL, 
	customer_name VARCHAR(255) NOT NULL, 
	customer_mobile VARCHAR(20) NOT NULL, 
	customer_email VARCHAR(255), 
	customer_address TEXT, 
	model_details VARCHAR(255), 
	problem_description TEXT, 
	additional_remarks TEXT, 
	status VARCHAR(50) NOT NULL, 
	status_date DATETIME, 
	source VARCHAR(50) NOT NULL, 
	created_by INTEGER, 
	order_id INTEGER, 
	order_item_id INTEGER, 
	serial_no VARCHAR(100), 
	service_type VARCHAR(50), 
	warranty_status VARCHAR(50), 
	assigned_engineer_id INTEGER, 
	assigned_vendor_id INTEGER, 
	requires_documents TINYINT(1) NOT NULL DEFAULT '0', 
	ask_for_documents TINYINT(1) NOT NULL DEFAULT '0', 
	document_request_sent_at DATETIME, 
	document_access_token VARCHAR(120), 
	customer_identified_at DATETIME, 
	approved_at DATETIME, 
	completed_at DATETIME, 
	closed_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	deleted_at DATETIME, 
	complaint_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT service_requests_ibfk_1 FOREIGN KEY(assigned_engineer_id) REFERENCES users (id), 
	CONSTRAINT service_requests_ibfk_2 FOREIGN KEY(assigned_vendor_id) REFERENCES vendors (id), 
	CONSTRAINT service_requests_ibfk_3 FOREIGN KEY(created_by) REFERENCES users (id), 
	CONSTRAINT service_requests_ibfk_4 FOREIGN KEY(order_id) REFERENCES orders (id), 
	CONSTRAINT service_requests_ibfk_5 FOREIGN KEY(order_item_id) REFERENCES order_items (id), 
	CONSTRAINT service_requests_ibfk_6 FOREIGN KEY(complaint_id) REFERENCES complaints (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_assignments (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	assignee_type VARCHAR(20) NOT NULL, 
	assignee_user_id INTEGER, 
	assignee_vendor_id INTEGER, 
	assigned_by INTEGER, 
	assigned_at DATETIME NOT NULL, 
	remarks TEXT, 
	is_active TINYINT(1) NOT NULL DEFAULT '1', 
	PRIMARY KEY (id), 
	CONSTRAINT service_assignments_ibfk_1 FOREIGN KEY(assigned_by) REFERENCES users (id), 
	CONSTRAINT service_assignments_ibfk_2 FOREIGN KEY(assignee_user_id) REFERENCES users (id), 
	CONSTRAINT service_assignments_ibfk_3 FOREIGN KEY(assignee_vendor_id) REFERENCES vendors (id), 
	CONSTRAINT service_assignments_ibfk_4 FOREIGN KEY(service_request_id) REFERENCES service_requests (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_completions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	performed_by_type VARCHAR(20) NOT NULL, 
	performed_by_user_id INTEGER, 
	performed_by_vendor_id INTEGER, 
	work_performed TEXT, 
	parts_replaced_json TEXT, 
	service_notes TEXT, 
	service_date DATE, 
	before_photos_json TEXT, 
	after_photos_json TEXT, 
	customer_acknowledgement_path VARCHAR(500), 
	final_amount DECIMAL(12, 2), 
	completion_remarks TEXT, 
	completed_at DATETIME NOT NULL, 
	old_part_serial_no VARCHAR(100), 
	new_part_serial_no VARCHAR(100), 
	PRIMARY KEY (id), 
	CONSTRAINT service_completions_ibfk_1 FOREIGN KEY(performed_by_user_id) REFERENCES users (id), 
	CONSTRAINT service_completions_ibfk_2 FOREIGN KEY(performed_by_vendor_id) REFERENCES vendors (id), 
	CONSTRAINT service_completions_ibfk_3 FOREIGN KEY(service_request_id) REFERENCES service_requests (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_documents (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	document_type VARCHAR(100) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	uploaded_by_type VARCHAR(50) NOT NULL, 
	uploaded_by_user_id INTEGER, 
	uploaded_by_customer_name VARCHAR(255), 
	status VARCHAR(50) NOT NULL, 
	reviewed_by INTEGER, 
	reviewed_at DATETIME, 
	review_remarks TEXT, 
	uploaded_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT service_documents_ibfk_1 FOREIGN KEY(reviewed_by) REFERENCES users (id), 
	CONSTRAINT service_documents_ibfk_2 FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	CONSTRAINT service_documents_ibfk_3 FOREIGN KEY(uploaded_by_user_id) REFERENCES users (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_notifications (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	recipient_user_id INTEGER, 
	recipient_vendor_id INTEGER, 
	title VARCHAR(255) NOT NULL, 
	message TEXT NOT NULL, 
	notification_type VARCHAR(50) NOT NULL, 
	is_read TINYINT(1) NOT NULL DEFAULT '0', 
	read_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT service_notifications_ibfk_1 FOREIGN KEY(recipient_user_id) REFERENCES users (id), 
	CONSTRAINT service_notifications_ibfk_2 FOREIGN KEY(recipient_vendor_id) REFERENCES vendors (id), 
	CONSTRAINT service_notifications_ibfk_3 FOREIGN KEY(service_request_id) REFERENCES service_requests (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_observations (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	submitted_by_user_id INTEGER, 
	serial_no VARCHAR(100), 
	warranty_status VARCHAR(50), 
	service_type VARCHAR(50), 
	problem_found TEXT, 
	observation TEXT, 
	recommended_action TEXT, 
	parts_required_json TEXT, 
	estimated_service_charge DECIMAL(12, 2), 
	estimated_parts_charge DECIMAL(12, 2), 
	remarks TEXT, 
	submitted_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT service_observations_ibfk_1 FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	CONSTRAINT service_observations_ibfk_2 FOREIGN KEY(submitted_by_user_id) REFERENCES users (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_payment_requests (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	requested_by_type VARCHAR(20) NOT NULL, 
	requested_by_user_id INTEGER, 
	requested_by_vendor_id INTEGER, 
	service_type VARCHAR(50), 
	customer_charge_amount DECIMAL(12, 2), 
	settlement_service_amount DECIMAL(12, 2), 
	settlement_parts_amount DECIMAL(12, 2), 
	total_requested_amount DECIMAL(12, 2), 
	payment_type VARCHAR(50), 
	remarks TEXT, 
	status VARCHAR(50) NOT NULL, 
	processed_at DATETIME, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	processed_by_user_id INTEGER, 
	payment_transaction_id INTEGER, 
	payment_qr_code_path VARCHAR(500), 
	approved_amount DECIMAL(12, 2), 
	PRIMARY KEY (id), 
	CONSTRAINT service_payment_requests_ibfk_1 FOREIGN KEY(requested_by_user_id) REFERENCES users (id), 
	CONSTRAINT service_payment_requests_ibfk_2 FOREIGN KEY(requested_by_vendor_id) REFERENCES vendors (id), 
	CONSTRAINT service_payment_requests_ibfk_3 FOREIGN KEY(service_request_id) REFERENCES service_requests (id), 
	CONSTRAINT service_payment_requests_ibfk_4 FOREIGN KEY(processed_by_user_id) REFERENCES users (id), 
	CONSTRAINT service_payment_requests_ibfk_5 FOREIGN KEY(payment_transaction_id) REFERENCES payment_transactions (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_status_logs (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	action VARCHAR(100) NOT NULL, 
	old_status VARCHAR(50), 
	new_status VARCHAR(50), 
	performed_by INTEGER, 
	performed_role VARCHAR(100), 
	remarks TEXT, 
	metadata_json TEXT, 
	created_at DATETIME NOT NULL, 
	serial_history_source_id INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT service_status_logs_ibfk_1 FOREIGN KEY(performed_by) REFERENCES users (id), 
	CONSTRAINT service_status_logs_ibfk_2 FOREIGN KEY(service_request_id) REFERENCES service_requests (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;


CREATE TABLE service_approvals (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	service_request_id INTEGER NOT NULL, 
	observation_id INTEGER, 
	decision VARCHAR(20) NOT NULL, 
	remarks TEXT, 
	approved_by INTEGER, 
	approved_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT service_approvals_ibfk_1 FOREIGN KEY(approved_by) REFERENCES users (id), 
	CONSTRAINT service_approvals_ibfk_2 FOREIGN KEY(observation_id) REFERENCES service_observations (id), 
	CONSTRAINT service_approvals_ibfk_3 FOREIGN KEY(service_request_id) REFERENCES service_requests (id)
)DEFAULT CHARSET=utf8mb4 ENGINE=InnoDB COLLATE utf8mb4_0900_ai_ci;

CREATE INDEX ix_order_items_item_code ON order_items (item_code);

CREATE INDEX ix_complaints_order_item_id ON complaints (order_item_id);

CREATE INDEX ix_complaints_serial_no ON complaints (serial_no);

CREATE INDEX engineer_user_id ON payment_transactions (engineer_user_id);

CREATE INDEX recorded_by_user_id ON payment_transactions (recorded_by_user_id);

CREATE INDEX fk_serial_history_performed_by ON serial_history_events (performed_by_user_id);

CREATE INDEX ix_serial_history_events_event_at ON serial_history_events (event_at);

CREATE INDEX ix_serial_history_events_order_item_id ON serial_history_events (order_item_id);

CREATE INDEX ix_serial_history_events_serial_no ON serial_history_events (serial_no);

CREATE INDEX fk_installation_requests_payment_recorded_by_users ON installation_requests (payment_recorded_by);

CREATE INDEX fk_installation_requests_payment_transaction_id ON installation_requests (payment_transaction_id);

CREATE INDEX created_by ON service_requests (created_by);

CREATE INDEX ix_service_requests_assigned_engineer_id ON service_requests (assigned_engineer_id);

CREATE INDEX ix_service_requests_assigned_vendor_id ON service_requests (assigned_vendor_id);

CREATE INDEX ix_service_requests_complaint_id ON service_requests (complaint_id);

CREATE INDEX ix_service_requests_customer_mobile ON service_requests (customer_mobile);

CREATE INDEX ix_service_requests_document_access_token ON service_requests (document_access_token);

CREATE INDEX ix_service_requests_order_id ON service_requests (order_id);

CREATE INDEX ix_service_requests_order_item_id ON service_requests (order_item_id);

CREATE INDEX ix_service_requests_serial_no ON service_requests (serial_no);

CREATE INDEX ix_service_requests_service_type ON service_requests (service_type);

CREATE INDEX ix_service_requests_status ON service_requests (status);

CREATE INDEX assigned_by ON service_assignments (assigned_by);

CREATE INDEX ix_service_assignments_assignee_user_id ON service_assignments (assignee_user_id);

CREATE INDEX ix_service_assignments_assignee_vendor_id ON service_assignments (assignee_vendor_id);

CREATE INDEX ix_service_assignments_service_request_id ON service_assignments (service_request_id);

CREATE INDEX ix_service_completions_service_request_id ON service_completions (service_request_id);

CREATE INDEX performed_by_user_id ON service_completions (performed_by_user_id);

CREATE INDEX performed_by_vendor_id ON service_completions (performed_by_vendor_id);

CREATE INDEX ix_service_documents_service_request_id ON service_documents (service_request_id);

CREATE INDEX reviewed_by ON service_documents (reviewed_by);

CREATE INDEX uploaded_by_user_id ON service_documents (uploaded_by_user_id);

CREATE INDEX ix_service_notifications_recipient_user_id ON service_notifications (recipient_user_id);

CREATE INDEX ix_service_notifications_recipient_vendor_id ON service_notifications (recipient_vendor_id);

CREATE INDEX ix_service_notifications_service_request_id ON service_notifications (service_request_id);

CREATE INDEX ix_service_observations_service_request_id ON service_observations (service_request_id);

CREATE INDEX submitted_by_user_id ON service_observations (submitted_by_user_id);

CREATE INDEX ix_service_payment_requests_service_request_id ON service_payment_requests (service_request_id);

CREATE INDEX payment_transaction_id ON service_payment_requests (payment_transaction_id);

CREATE INDEX processed_by_user_id ON service_payment_requests (processed_by_user_id);

CREATE INDEX requested_by_user_id ON service_payment_requests (requested_by_user_id);

CREATE INDEX requested_by_vendor_id ON service_payment_requests (requested_by_vendor_id);

CREATE INDEX ix_service_status_logs_service_request_id ON service_status_logs (service_request_id);

CREATE INDEX performed_by ON service_status_logs (performed_by);

CREATE INDEX approved_by ON service_approvals (approved_by);

CREATE INDEX ix_service_approvals_service_request_id ON service_approvals (service_request_id);

CREATE INDEX observation_id ON service_approvals (observation_id);
