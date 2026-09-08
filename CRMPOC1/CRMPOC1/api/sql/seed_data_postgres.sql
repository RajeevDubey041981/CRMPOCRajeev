-- Optional seed data for PostgreSQL
-- Run after create_tables_postgres.sql

INSERT INTO roles (name, description) VALUES
    ('admin', 'Administrator — full access to all modules'),
    ('callcenter', 'Call Center — create/view complaints, log calls'),
    ('engineer', 'Engineer — view assigned complaints/installations, update status & work reports'),
    ('vendor', 'Vendor — read-only access to own orders'),
    ('public', 'Public User — submit complaint via public form (no login UI)')
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (name, email, password_hash, role, phone, is_active) VALUES
    ('Administrator', 'admin@indcool.com', '$2b$12$4gQwV4lM5bQkPKD8RkY1Y.aqI0R8K5v6KpAxq6P6n4bX6J0NfREbW', 'admin', '9999999999', TRUE),
    ('Ravi Kumar', 'ravi@indcool.com', '$2b$12$4gQwV4lM5bQkPKD8RkY1Y.aqI0R8K5v6KpAxq6P6n4bX6J0NfREbW', 'engineer', '9810000001', TRUE),
    ('Sunita Patel', 'sunita@indcool.com', '$2b$12$4gQwV4lM5bQkPKD8RkY1Y.aqI0R8K5v6KpAxq6P6n4bX6J0NfREbW', 'engineer', '9810000002', TRUE)
ON CONFLICT (email) DO NOTHING;

INSERT INTO item_masters (item_code, item_name, category, is_active) VALUES
    ('8908012210436', 'SPLIT AC IDCACS18K5', 'AC', TRUE),
    ('8908012210443', 'WINDOW AC IDCACW15K3', 'AC', TRUE),
    ('8908012210450', 'GEYSER IDCGYS25L', 'Geyser', TRUE),
    ('8908012210467', 'FRIDGE IDCFRD250L', 'Fridge', TRUE),
    ('8908012210474', 'AIR COOLER IDCCLR40L', 'Cooler', TRUE)
ON CONFLICT (item_code) DO NOTHING;
