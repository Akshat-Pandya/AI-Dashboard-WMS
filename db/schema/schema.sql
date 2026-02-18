CREATE DATABASE IF NOT EXISTS wms;
USE wms;

-- =========================
-- Inventory
-- =========================
CREATE TABLE inventory_items (
    id VARCHAR(10) PRIMARY KEY,
    sku VARCHAR(50),
    product_name VARCHAR(255),
    zone VARCHAR(50),
    location VARCHAR(50),
    quantity_on_hand INT,
    quantity_reserved INT,
    quantity_available INT,
    reorder_point INT,
    status VARCHAR(20),
    last_updated DATETIME,
    unit_of_measure VARCHAR(10),
    weight DECIMAL(10,2),
    category VARCHAR(100)
);

-- =========================
-- Outbound Orders
-- =========================
CREATE TABLE outbound_orders (
    id VARCHAR(10) PRIMARY KEY,
    order_number VARCHAR(50),
    status VARCHAR(20),
    priority VARCHAR(20),
    customer_name VARCHAR(255),
    total_lines INT,
    picked_lines INT,
    packed_lines INT,
    total_units INT,
    created_at DATETIME,
    due_date DATETIME,
    wave_id VARCHAR(50),
    carrier VARCHAR(100),
    staging_zone VARCHAR(50)
);

-- =========================
-- Inbound ASNs
-- =========================
CREATE TABLE inbound_asns (
    id VARCHAR(10) PRIMARY KEY,
    asn_number VARCHAR(50),
    status VARCHAR(20),
    supplier_name VARCHAR(255),
    expected_date DATETIME,
    actual_date DATETIME NULL,
    total_lines INT,
    received_lines INT,
    total_units INT,
    received_units INT,
    dock VARCHAR(50),
    po_number VARCHAR(50),
    is_overdue BOOLEAN
);

-- =========================
-- Warehouse Tasks
-- =========================
CREATE TABLE warehouse_tasks (
    id VARCHAR(10) PRIMARY KEY,
    task_type VARCHAR(50),
    status VARCHAR(20),
    priority VARCHAR(20),
    assigned_to VARCHAR(20),
    assignee_name VARCHAR(100),
    zone VARCHAR(50),
    source_location VARCHAR(50),
    destination_location VARCHAR(50),
    reference_id VARCHAR(50),
    created_at DATETIME,
    started_at DATETIME NULL,
    completed_at DATETIME NULL,
    estimated_minutes INT,
    is_blocked BOOLEAN,
    block_reason TEXT
);

-- =========================
-- KPIs
-- =========================
CREATE TABLE warehouse_kpis (
    id VARCHAR(10) PRIMARY KEY,
    label VARCHAR(255),
    value DECIMAL(10,2),
    previous_value DECIMAL(10,2),
    unit VARCHAR(20),
    trend VARCHAR(10),
    change_percent DECIMAL(10,2),
    category VARCHAR(50),
    target DECIMAL(10,2),
    is_on_target BOOLEAN
);

-- =========================
-- Zone Utilization
-- =========================
CREATE TABLE zone_utilization (
    zone_id VARCHAR(20) PRIMARY KEY,
    zone_name VARCHAR(100),
    zone_type VARCHAR(50),
    total_capacity INT,
    used_capacity INT,
    utilization_percent DECIMAL(5,2),
    active_tasks INT,
    active_workers INT,
    temperature DECIMAL(5,2) NULL,
    status VARCHAR(20)
);

-- =========================
-- Alerts
-- =========================
CREATE TABLE warehouse_alerts (
    id VARCHAR(10) PRIMARY KEY,
    severity VARCHAR(20),
    title VARCHAR(255),
    message TEXT,
    category VARCHAR(50),
    timestamp DATETIME,
    acknowledged BOOLEAN,
    zone VARCHAR(50)
);
