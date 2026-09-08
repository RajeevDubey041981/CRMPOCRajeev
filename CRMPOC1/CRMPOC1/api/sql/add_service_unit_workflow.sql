-- Per-unit serial verification and observations (local / manual apply)
ALTER TABLE service_request_units
  ADD COLUMN serial_verified_at DATETIME NULL,
  ADD COLUMN warranty_status VARCHAR(50) NULL,
  ADD COLUMN service_type VARCHAR(50) NULL;

ALTER TABLE service_observations
  ADD COLUMN service_request_unit_id INT NULL,
  ADD INDEX ix_service_observations_service_request_unit_id (service_request_unit_id),
  ADD CONSTRAINT service_observations_service_request_unit_id_fkey
    FOREIGN KEY (service_request_unit_id) REFERENCES service_request_units (id);
