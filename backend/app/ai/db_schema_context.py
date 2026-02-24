# app/ai/db_schema_context.py

DB_SCHEMA = """
DATABASE SCHEMA (MySQL):

TABLE: warehouse_alerts
  id VARCHAR PK, severity ENUM('low','medium','high','critical'),
  title VARCHAR, message TEXT, category VARCHAR, timestamp DATETIME,
  acknowledged TINYINT(1), zone VARCHAR

TABLE: inventory_items
  id VARCHAR PK, sku VARCHAR UNIQUE, product_name VARCHAR,
  zone VARCHAR, location VARCHAR,
  quantity_on_hand INT, quantity_reserved INT, quantity_available INT,
  reorder_point INT, status VARCHAR,
  last_updated DATETIME, unit_of_measure VARCHAR,
  weight DECIMAL, category VARCHAR

TABLE: orders
  id VARCHAR PK, order_number VARCHAR UNIQUE,
  status ENUM('pending','processing','picking','packing','shipped','cancelled','on_hold'),
  priority ENUM('low','medium','high','urgent'),
  customer_name VARCHAR, total_lines INT, picked_lines INT, packed_lines INT,
  total_units INT, created_at DATETIME, due_date DATETIME,
  wave_id VARCHAR, carrier VARCHAR, staging_zone VARCHAR

TABLE: warehouse_tasks
  id VARCHAR PK,
  task_type ENUM('pick','pack','putaway','replenishment','cycle_count','transfer'),
  status ENUM('pending','active','blocked','completed','cancelled'),
  priority ENUM('low','medium','high','urgent'),
  assigned_to VARCHAR, assignee_name VARCHAR, zone VARCHAR,
  source_location VARCHAR, destination_location VARCHAR,
  reference_id VARCHAR, created_at DATETIME, started_at DATETIME,
  completed_at DATETIME, estimated_minutes INT,
  is_blocked TINYINT(1), block_reason VARCHAR

TABLE: asn_headers  (Advance Shipment Notices)
  id VARCHAR PK, asn_number VARCHAR UNIQUE,
  status ENUM('pending','in_transit','receiving','completed','cancelled'),
  supplier_name VARCHAR, expected_date DATE, actual_date DATE,
  total_lines INT, received_lines INT, total_units INT, received_units INT,
  dock VARCHAR, po_number VARCHAR,
  is_overdue TINYINT(1)

TABLE: kpis
  id VARCHAR PK, label VARCHAR, value DECIMAL,
  previous_value DECIMAL, unit VARCHAR,
  trend ENUM('up','down','stable'),
  change_percent DECIMAL, category VARCHAR,
  target DECIMAL, is_on_target TINYINT(1)
"""