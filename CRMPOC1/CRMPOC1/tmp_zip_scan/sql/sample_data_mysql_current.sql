-- Sample test data for current MySQL schema
-- Generated for the current app tables on 2026-08-11
-- Run this after create_tables_mysql_current.sql

START TRANSACTION;

INSERT INTO roles (id, name, description) VALUES
  (1, 'admin', 'Administrator with full access'),
  (2, 'engineer', 'Engineer access for installations and complaints'),
  (3, 'vendor', 'Vendor access for order visibility'),
  (4, 'callcenter', 'Call center operator'),
  (5, 'sales', 'Sales access')
ON DUPLICATE KEY UPDATE description = VALUES(description);

INSERT INTO permissions (
  id, role_id, module, sub_module, can_view, can_create, can_edit, can_delete, can_export
) VALUES
  (1, 1, 'dashboard', NULL, 1, 1, 1, 1, 1),
  (2, 1, 'orders', NULL, 1, 1, 1, 1, 1),
  (3, 1, 'installations', NULL, 1, 1, 1, 1, 1),
  (4, 1, 'complaints', NULL, 1, 1, 1, 1, 1),
  (5, 1, 'claims', NULL, 1, 1, 1, 1, 1),
  (6, 1, 'calls', NULL, 1, 1, 1, 1, 1),
  (7, 1, 'users', NULL, 1, 1, 1, 1, 1),
  (8, 2, 'installations', NULL, 1, 0, 1, 0, 0),
  (9, 2, 'complaints', NULL, 1, 0, 1, 0, 0),
  (10, 3, 'orders', NULL, 1, 1, 0, 0, 1),
  (11, 4, 'complaints', NULL, 1, 1, 1, 0, 1),
  (12, 4, 'calls', NULL, 1, 1, 1, 0, 1),
  (13, 5, 'dashboard', NULL, 1, 0, 0, 0, 1),
  (14, 5, 'complaints', 'Sales', 1, 1, 1, 0, 1)
ON DUPLICATE KEY UPDATE
  can_view = VALUES(can_view),
  can_create = VALUES(can_create),
  can_edit = VALUES(can_edit),
  can_delete = VALUES(can_delete),
  can_export = VALUES(can_export);

INSERT INTO users (id, name, email, password_hash, role, phone, is_active) VALUES
  (1, 'Administrator', 'admin@indcool.com', '$2b$12$osSHlqFYZiyKYITlut4wF.F6ccv..KEAOewWS03idG86v.DTnLTpO', 'admin', '9999999991', 1),
  (2, 'Ravi Kumar', 'ravi@indcool.com', '$2b$12$52d2e30tQWbqV71kk/XBuuPeb22LS/at1whsptlsviJFcKBlQLi3q', 'engineer', '9810000001', 1),
  (3, 'Sunita Patel', 'sunita@indcool.com', '$2b$12$52d2e30tQWbqV71kk/XBuuPeb22LS/at1whsptlsviJFcKBlQLi3q', 'engineer', '9810000002', 1),
  (4, 'Vendor One User', 'vendor1@indcool.com', '$2b$12$S9KOheh2yrVMJ88JMs1l/uaKwIhUh/qdvqGZAxtTiwTZrJJug.Shq', 'vendor', '9820000001', 1),
  (5, 'Call Center User', 'callcenter@indcool.com', '$2b$12$V6jVYi4e.H7cd0XY7m1yPeWln7BuGCLg1z6aJ66FnMCi8z7tLJATa', 'callcenter', '9830000001', 1),
  (6, 'Sales User', 'sales@indcool.com', '$2b$12$SqNeXIrENHB7mAdMe8aoD./4sM.f7XgXd4DevKOrXExOHL9PDHgvS', 'sales', '9840000001', 1)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  password_hash = VALUES(password_hash),
  phone = VALUES(phone),
  is_active = VALUES(is_active);

INSERT INTO couriers (id, courier_name, contact_name, contact_mobile, email, address) VALUES
  (1, 'BlueDart', 'Amit Singh', '9000000001', 'support@bluedart.test', 'Mumbai hub'),
  (2, 'Delhivery', 'Neha Shah', '9000000002', 'support@delhivery.test', 'Delhi hub')
ON DUPLICATE KEY UPDATE
  courier_name = VALUES(courier_name),
  contact_name = VALUES(contact_name),
  contact_mobile = VALUES(contact_mobile),
  email = VALUES(email),
  address = VALUES(address);

INSERT INTO item_masters (
  id, item_code, item_name, category, description, brand, unit, hsn_code, mrp, is_active
) VALUES
  (1, '8908012210474', 'AIR COOLER IDCCLR40L', 'Cooler', 'Sample cooler item', 'Indcool', 'Piece', '847989', 15999.00, 1),
  (2, '8908012210481', 'SPLIT AC IDCACS24K5', 'AC', 'Sample split AC item', 'Indcool', 'Piece', '841510', 42999.00, 1),
  (3, '8908012210436', 'SPLIT AC IDCACS18K5', 'AC', 'Additional test item', 'Indcool', 'Piece', '841510', 36999.00, 1)
ON DUPLICATE KEY UPDATE
  item_name = VALUES(item_name),
  category = VALUES(category),
  mrp = VALUES(mrp),
  is_active = VALUES(is_active);

INSERT INTO vendors (
  id, vendor_code, name_of_firm, contact_name, contact_mobile, email, gst_no, address, state, district, pincode, latitude, longitude, is_active
) VALUES
  (1, 'VEND001', 'Vendor One Pvt Ltd', 'Rajesh Verma', '9100000001', 'vendor1@test.com', '27ABCDE1234F1Z5', 'Sector 21, Noida', 'Uttar Pradesh', 'Gautam Buddha Nagar', '201301', 28.53550000, 77.39100000, 1),
  (2, 'VEND002', 'Vendor Two Appliances', 'Pooja Mehra', '9100000002', 'vendor2@test.com', '07ABCDE1234F1Z5', 'Rohini, Delhi', 'Delhi', 'North West', '110085', 28.73830000, 77.08290000, 1)
ON DUPLICATE KEY UPDATE
  name_of_firm = VALUES(name_of_firm),
  contact_name = VALUES(contact_name),
  contact_mobile = VALUES(contact_mobile),
  is_active = VALUES(is_active);

INSERT INTO payment_transactions (
  id, payment_type, total_amount, request_count, recorded_by_user_id, engineer_user_id, recorded_at
) VALUES
  (1, 'UPI', 1250.00, 1, 1, 2, '2026-08-09 10:30:00'),
  (2, 'Cash', 2200.00, 2, 1, 3, '2026-08-10 11:45:00')
ON DUPLICATE KEY UPDATE
  total_amount = VALUES(total_amount),
  request_count = VALUES(request_count),
  recorded_by_user_id = VALUES(recorded_by_user_id),
  engineer_user_id = VALUES(engineer_user_id);

INSERT INTO projects (id, title, description, status, owner_id) VALUES
  (1, 'Advisor Onboarding Pilot', 'Sample workflow project for testing', 'Active', 1),
  (2, 'Retail Campaign Setup', 'Secondary sample workflow project', 'Draft', 6)
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  status = VALUES(status),
  owner_id = VALUES(owner_id);

INSERT INTO workflow_tasks (
  id, project_id, task_name, task_type, sequence, status, advisor_id, input_data, output_data, error_message, started_at, completed_at
) VALUES
  (1, 1, 'Add advisor record', 'Add Advisor', 1, 'Completed', 'ADV-001', '{"name":"Advisor One"}', '{"result":"ok"}', NULL, '2026-08-08T09:00:00Z', '2026-08-08T09:03:00Z'),
  (2, 1, 'Send survey', 'Send Survey', 2, 'Running', 'ADV-001', '{"channel":"email"}', NULL, NULL, '2026-08-08T09:05:00Z', NULL),
  (3, 2, 'Gather responses', 'Gather Responses', 1, 'Pending', NULL, NULL, NULL, NULL, NULL, NULL)
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  advisor_id = VALUES(advisor_id),
  input_data = VALUES(input_data),
  output_data = VALUES(output_data);

INSERT INTO orders (
  id, order_no, order_date, oem_bill_no, vendor_id, customer_name, customer_contact, customer_email, customer_city, customer_state,
  customer_address, courier_id, lrn_no, vendor_bill_no, vendor_bill_date, status, expected_delivery_date, actual_delivery_date, order_file_path, created_by
) VALUES
  (1, 'V1-ORDER-10ROWS-20260801', '2026-08-01', 'OEM-1001', 1, 'Vendor1 Customer', '9876543210', 'customer1@test.com', 'Noida', 'Uttar Pradesh',
   'Tower A, Noida', 1, 'LRN-0001', 'VB-001', '2026-08-01', 'Delivered', '2026-08-02', '2026-08-03', '/uploads/orders/order1.pdf', 1),
  (2, 'V2-ORDER-AC-20260805', '2026-08-05', 'OEM-1002', 2, 'Test Customer Two', '9876543211', 'customer2@test.com', 'Delhi', 'Delhi',
   'Pitampura, Delhi', 2, 'LRN-0002', 'VB-002', '2026-08-05', 'In Transit', '2026-08-12', NULL, '/uploads/orders/order2.pdf', 1)
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  expected_delivery_date = VALUES(expected_delivery_date),
  actual_delivery_date = VALUES(actual_delivery_date);

INSERT INTO order_items (
  id, order_id, item_id, item_code, serial_no, serial_no_2, item_qty, pcb_warranty_years, component_warranty_years, machine_warranty_years,
  free_service_count, service_consume_count, installation_status
) VALUES
  (1, 1, 1, '8908012210474', '8908012210474-A1', '8908012210474-A2', 1, 1, 1, 2, 2, 1, 'Completed'),
  (2, 1, 2, '8908012210481', '8908012210481-B1', '8908012210481-B2', 1, 1, 1, 2, 2, 0, 'Requested'),
  (3, 2, 3, '8908012210436', '8908012210436-C1', NULL, 1, 1, 1, 1, 1, 0, 'Not Requested')
ON DUPLICATE KEY UPDATE
  installation_status = VALUES(installation_status),
  service_consume_count = VALUES(service_consume_count);

INSERT INTO complaints (
  id, comp_no, comp_date, customer_name, customer_mobile, customer_email, customer_address, model_details, problem_description, query_type,
  status, status_date, assigned_engineer, remark, service_proof_path, access_code, send_sms, created_by, order_item_id, serial_no, source
) VALUES
  (1, 'COMP-2026-0001', '2026-08-07', 'Vendor1 Customer', '9876543210', 'customer1@test.com', 'Tower A, Noida', 'AIR COOLER IDCCLR40L',
   'Cooling issue after installation', 'Service', 'Resolved', '2026-08-09 15:00:00', 2, 'Fan motor checked and cleaned',
   '/uploads/complaints/service-proof-1.pdf', 'ACC1001', 1, 5, 1, '8908012210474-A1', 'callcenter'),
  (2, 'COMP-2026-0002', '2026-08-10', 'Test Customer Two', '9876543211', 'customer2@test.com', 'Pitampura, Delhi', 'SPLIT AC IDCACS18K5',
   'Installation delay complaint', 'Installation', 'Pending', '2026-08-10 11:00:00', 3, 'Waiting for engineer assignment',
   NULL, 'ACC1002', 1, 5, 3, '8908012210436-C1', 'public')
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  assigned_engineer = VALUES(assigned_engineer),
  remark = VALUES(remark);

INSERT INTO complaint_status_logs (
  id, complaint_id, old_status, new_status, changed_by, remark, document_path, action_taken, changed_at
) VALUES
  (1, 1, 'Pending', 'In Process', 5, 'Assigned to Ravi Kumar', NULL, 'Assigned engineer', '2026-08-08 10:00:00'),
  (2, 1, 'In Process', 'Resolved', 2, 'Problem resolved on site', '/uploads/complaints/resolution1.pdf', 'Service completed', '2026-08-09 15:00:00'),
  (3, 2, 'Pending', 'Pending', 5, 'Fresh complaint logged', NULL, 'Complaint created', '2026-08-10 11:00:00')
ON DUPLICATE KEY UPDATE
  new_status = VALUES(new_status),
  remark = VALUES(remark),
  action_taken = VALUES(action_taken);

INSERT INTO calls (
  id, ref_no, customer_name, customer_email, phone, call_type, status, priority, assigned_to, transferred_to, is_transferred,
  duration_secs, call_datetime, followup_date, notes, follow_up_notes, follow_up_status, complaint_id
) VALUES
  (1, 'CALL-2026-0001', 'Vendor1 Customer', 'customer1@test.com', '9876543210', 'Inbound', 'Closed', 'high', 5, NULL, 0,
   420, '2026-08-07 09:15:00', '2026-08-08 10:00:00', 'Customer reported cooler issue', 'Issue tracked under complaint', 'Done', 1),
  (2, 'CALL-2026-0002', 'Test Customer Two', 'customer2@test.com', '9876543211', 'Outbound', 'Open', 'medium', 5, 6, 1,
   180, '2026-08-10 12:30:00', '2026-08-12 12:00:00', 'Follow-up on installation delay', 'Need status update from engineer', 'Scheduled', 2)
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  assigned_to = VALUES(assigned_to),
  follow_up_status = VALUES(follow_up_status);

INSERT INTO claims (
  id, claim_id, order_no, serial_number, order_item_id, customer_name, customer_contact, customer_email, status, submitted_at,
  processed_by, notes, bank_name, account_holder_name, account_number, ifsc_code, admin_remark
) VALUES
  (1, 'CLM-2026-0001', 'V1-ORDER-10ROWS-20260801', '8908012210474-A1', 1, 'Vendor1 Customer', '9876543210', 'customer1@test.com',
   'Approved', '2026-08-09 13:00:00', 1, 'Approved after inspection', 'State Bank of India', 'Vendor1 Customer', '12345678901', 'SBIN0000123', 'Amount approved'),
  (2, 'CLM-2026-0002', 'V2-ORDER-AC-20260805', '8908012210436-C1', 3, 'Test Customer Two', '9876543211', 'customer2@test.com',
   'Processing', '2026-08-10 16:00:00', 1, 'Awaiting final review', 'HDFC Bank', 'Test Customer Two', '98765432101', 'HDFC0000456', 'Review in progress')
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  processed_by = VALUES(processed_by),
  admin_remark = VALUES(admin_remark);

INSERT INTO claim_photos (id, claim_id, file_path, uploaded_at) VALUES
  (1, 1, '/uploads/claims/claim1-photo1.jpg', '2026-08-09 13:05:00'),
  (2, 1, '/uploads/claims/claim1-photo2.jpg', '2026-08-09 13:06:00'),
  (3, 2, '/uploads/claims/claim2-photo1.jpg', '2026-08-10 16:05:00')
ON DUPLICATE KEY UPDATE
  file_path = VALUES(file_path);

INSERT INTO market_categories (id, name, parent_id) VALUES
  (1, 'Cooling Appliances', NULL),
  (2, 'Air Conditioners', 1),
  (3, 'Air Coolers', 1)
ON DUPLICATE KEY UPDATE
  name = VALUES(name),
  parent_id = VALUES(parent_id);

INSERT INTO market_items (
  id, sku, name, company, category_id, base_price, mrp, image_path, status, stock_count, description
) VALUES
  (1, 'SKU-AC-24K5', 'SPLIT AC IDCACS24K5', 'Indcool', 2, 35000.00, 42999.00, '/uploads/market/ac24k5.jpg', 'Active', 25, 'Marketplace sample AC item'),
  (2, 'SKU-CLR-40L', 'AIR COOLER IDCCLR40L', 'Indcool', 3, 12000.00, 15999.00, '/uploads/market/cooler40l.jpg', 'Active', 40, 'Marketplace sample cooler item')
ON DUPLICATE KEY UPDATE
  stock_count = VALUES(stock_count),
  mrp = VALUES(mrp),
  status = VALUES(status);

INSERT INTO market_users (
  id, name, email, phone, address, city, state, role, status, fee_status, onboarding_fee, joined_at
) VALUES
  (1, 'Retailer One', 'retailer1@test.com', '9900000001', 'Shop 1, Noida', 'Noida', 'Uttar Pradesh', 'Retailer', 'Approved', 'Paid', 5000.00, '2026-08-01 09:00:00'),
  (2, 'Distributor One', 'distributor1@test.com', '9900000002', 'Warehouse 4, Delhi', 'Delhi', 'Delhi', 'Distributor', 'Approved', 'Paid', 10000.00, '2026-08-02 10:00:00')
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  fee_status = VALUES(fee_status),
  onboarding_fee = VALUES(onboarding_fee);

INSERT INTO market_orders (id, order_no, retailer_id, distributor_id, total_amount, status, notes) VALUES
  (1, 'MKT-ORD-0001', 1, 2, 85998.00, 'Confirmed', 'Marketplace sample order')
ON DUPLICATE KEY UPDATE
  total_amount = VALUES(total_amount),
  status = VALUES(status),
  notes = VALUES(notes);

INSERT INTO market_order_items (id, order_id, item_id, qty, unit_price, subtotal) VALUES
  (1, 1, 1, 1, 42999.00, 42999.00),
  (2, 1, 2, 3, 14333.00, 42999.00)
ON DUPLICATE KEY UPDATE
  qty = VALUES(qty),
  unit_price = VALUES(unit_price),
  subtotal = VALUES(subtotal);

INSERT INTO installation_requests (
  id, customer_name, contact_number, address, order_item_id, product_name, serial_no, serial_no_2, request_date, assigned_engineer, status,
  installation_date, work_report, work_report_file_path, settlement_approved_by, payment_amount_requested, payment_type_requested, payment_qr_code_path,
  payment_qr_code_filename, payment_qr_code_content_type, payment_qr_code_size_bytes, payment_proof_file_path, payment_requested_at,
  payment_amount_paid, payment_type_paid, payment_recorded_at, payment_recorded_by, payment_transaction_id
) VALUES
  (1, 'Vendor1 Customer', '9876543210', 'Tower A, Noida', 1, 'AIR COOLER IDCCLR40L', '8908012210474-A1', '8908012210474-A2',
   '2026-08-06 13:11:31', 2, 'Completed', '2026-08-10 12:00:00', 'Installation completed successfully',
   '/uploads/installations/work-report-1.pdf', 1, 1250.00, 'UPI', '/uploads/installations/qr-1.png',
   'qr-1.png', 'image/png', 20480, '/uploads/installations/payment-proof-1.pdf', '2026-08-09 09:30:00',
   1250.00, 'UPI', '2026-08-09 10:30:00', 1, 1),
  (2, 'Vendor1 Customer', '9876543210', 'Tower A, Noida', 2, 'SPLIT AC IDCACS24K5', '8908012210481-B1', '8908012210481-B2',
   '2026-08-06 11:00:00', 2, 'Assigned', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
  (3, 'Test Customer Two', '9876543211', 'Pitampura, Delhi', 3, 'SPLIT AC IDCACS18K5', '8908012210436-C1', NULL,
   '2026-08-10 15:00:00', 3, 'Payment Pending', '2026-08-10 17:00:00', 'Site visit done, awaiting payment approval',
   '/uploads/installations/work-report-3.pdf', 1, 2200.00, 'Cash', NULL, NULL, NULL, NULL, '/uploads/installations/payment-proof-3.pdf',
   '2026-08-10 17:10:00', 2200.00, 'Cash', '2026-08-10 18:00:00', 1, 2)
ON DUPLICATE KEY UPDATE
  status = VALUES(status),
  assigned_engineer = VALUES(assigned_engineer),
  installation_date = VALUES(installation_date),
  payment_transaction_id = VALUES(payment_transaction_id);

INSERT INTO serial_history_events (
  id, order_item_id, serial_no, serial_no_2, event_type, event_subtype, event_at, performed_by_user_id, performed_by_name, source_table, source_id,
  title, description, remarks, metadata_json, created_at
) VALUES
  (1, 1, '8908012210474-A1', '8908012210474-A2', 'ORDER', 'ORDER_CREATED', '2026-08-01 08:47:49', 4, 'vendor1', 'orders', 1,
   'Order created', 'Order V1-ORDER-10ROWS-20260801 created for Vendor1 Customer.', NULL, '{"order_no":"V1-ORDER-10ROWS-20260801","status":"Delivered"}', '2026-08-01 08:47:49'),
  (2, 1, '8908012210474-A1', '8908012210474-A2', 'ORDER', 'EXPECTED_DELIVERY', '2026-08-02 00:00:00', NULL, NULL, 'orders', 1000001,
   'Expected delivery scheduled', 'Expected delivery date set to 2026-08-02.', NULL, '{"expected_delivery_date":"2026-08-02"}', '2026-08-01 09:00:00'),
  (3, 1, '8908012210474-A1', '8908012210474-A2', 'INSTALLATION', 'REQUEST_CREATED', '2026-08-06 13:11:31', 2, 'Ravi Kumar', 'installation_requests', 1,
   'Installation request created', 'Installation request 1 created with status Completed.', NULL, '{"status":"Completed","product_name":"AIR COOLER IDCCLR40L"}', '2026-08-06 13:11:31'),
  (4, 1, '8908012210474-A1', '8908012210474-A2', 'INSTALLATION', 'COMPLETED', '2026-08-10 12:00:00', 2, 'Ravi Kumar', 'installation_requests', 1000001,
   'Installation completed', 'Installation completed with status Completed.', 'Installation completed successfully', '{"status":"Completed"}', '2026-08-10 12:00:00'),
  (5, 1, '8908012210474-A1', '8908012210474-A2', 'COMPLAINT', 'STATUS_RESOLVED', '2026-08-09 15:00:00', 2, 'Ravi Kumar', 'complaints', 1,
   'Complaint resolved', 'Complaint COMP-2026-0001 marked as Resolved.', 'Fan motor checked and cleaned', '{"complaint_no":"COMP-2026-0001"}', '2026-08-09 15:00:00')
ON DUPLICATE KEY UPDATE
  title = VALUES(title),
  description = VALUES(description),
  remarks = VALUES(remarks);

COMMIT;

-- Test login users created by this script:
-- admin@indcool.com / admin123
-- ravi@indcool.com / engineer123
-- vendor1@indcool.com / vendor123
-- callcenter@indcool.com / call123
-- sales@indcool.com / sales123
