-- INDcool CRM database table and relationship mapping
-- Usage:
--   mysql -u USER -p DATABASE < database_table_mapping.sql
--
-- The first three queries return the live schema mapping. The final query lists
-- the main CRM business relationships in a compact ER-style format.

-- 1. Tables and columns
SELECT
    c.TABLE_NAME,
    c.ORDINAL_POSITION,
    c.COLUMN_NAME,
    c.COLUMN_TYPE,
    c.IS_NULLABLE,
    c.COLUMN_DEFAULT,
    c.COLUMN_KEY,
    c.EXTRA
FROM information_schema.COLUMNS c
WHERE c.TABLE_SCHEMA = DATABASE()
ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION;

-- 2. Primary keys
SELECT
    k.TABLE_NAME,
    k.COLUMN_NAME,
    k.ORDINAL_POSITION
FROM information_schema.KEY_COLUMN_USAGE k
WHERE k.TABLE_SCHEMA = DATABASE()
  AND k.CONSTRAINT_NAME = 'PRIMARY'
ORDER BY k.TABLE_NAME, k.ORDINAL_POSITION;

-- 3. Foreign-key mappings
SELECT
    k.TABLE_NAME AS child_table,
    k.COLUMN_NAME AS child_column,
    k.CONSTRAINT_NAME AS constraint_name,
    k.REFERENCED_TABLE_NAME AS parent_table,
    k.REFERENCED_COLUMN_NAME AS parent_column,
    r.UPDATE_RULE,
    r.DELETE_RULE
FROM information_schema.KEY_COLUMN_USAGE k
JOIN information_schema.REFERENTIAL_CONSTRAINTS r
  ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
 AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
 AND r.TABLE_NAME = k.TABLE_NAME
WHERE k.TABLE_SCHEMA = DATABASE()
  AND k.REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY k.TABLE_NAME, k.CONSTRAINT_NAME, k.ORDINAL_POSITION;

-- 4. Compact relationship mapping
SELECT CONCAT(
    k.TABLE_NAME, '.', k.COLUMN_NAME,
    ' -> ', k.REFERENCED_TABLE_NAME, '.', k.REFERENCED_COLUMN_NAME,
    ' [', r.DELETE_RULE, ']'
) AS relationship
FROM information_schema.KEY_COLUMN_USAGE k
JOIN information_schema.REFERENTIAL_CONSTRAINTS r
  ON r.CONSTRAINT_SCHEMA = k.CONSTRAINT_SCHEMA
 AND r.CONSTRAINT_NAME = k.CONSTRAINT_NAME
 AND r.TABLE_NAME = k.TABLE_NAME
WHERE k.TABLE_SCHEMA = DATABASE()
  AND k.REFERENCED_TABLE_NAME IS NOT NULL
ORDER BY k.TABLE_NAME, k.COLUMN_NAME;

-- Main CRM relationship map
-- users
--   -> vendors.email is the application-level vendor-account mapping
--   -> orders.created_by, complaints.created_by, service_requests.created_by
--   -> assignments, approvals, payments, notifications, and audit logs
--
-- vendors
--   -> orders.vendor_id
--   -> service_requests.assigned_vendor_id
--   -> user_pending_actions.recipient_vendor_id
--
-- orders
--   -> order_items.order_id
--   -> complaints.order_id, installations.order_id, service_requests.order_id
--
-- order_items
--   -> complaints.order_item_id, installations.order_item_id,
--      serial_history_events.order_item_id, service_request_items.order_item_id
--
-- complaints
--   -> complaint_status_logs.complaint_id
--   -> installation_requests.complaint_id
--   -> service_requests.complaint_id
--
-- installation_requests
--   -> installation_documents.installation_request_id
--   -> installation_engineer_serials.installation_request_id
--   -> installation_status_logs.installation_request_id
--
-- service_requests
--   -> service_request_items.service_request_id
--   -> service_request_units.service_request_id
--   -> service_assignments.service_request_id
--   -> service_documents.service_request_id
--   -> service_observations.service_request_id
--   -> service_approvals.service_request_id
--   -> service_completions.service_request_id
--   -> service_payment_requests.service_request_id
--   -> service_notifications.service_request_id
--
-- partner_registrations
--   -> users.id through created_by
--   -> users.email and vendors.email are application-level onboarding mappings
--
-- market_categories
--   -> market_items.category_id
--
-- market_orders
--   -> market_order_items.order_id
--   -> market_order_items.item_id -> market_items.id
--
-- projects
--   -> workflow_tasks.project_id
--
-- roles
--   -> permissions.role_id
