# app/ai/db_schema_context.py
# ⚠️ Keep this in sync with schema.sql — wrong table/column names cause SQL errors

DB_SCHEMA = """
DATABASE: wms (MySQL)

TABLE: warehouse_alerts
  id           VARCHAR(10) PK
  severity     VARCHAR(20)       -- values: 'critical', 'warning', 'error', 'info'
  title        VARCHAR(255)
  message      TEXT
  category     VARCHAR(50)
  timestamp    DATETIME
  acknowledged BOOLEAN
  zone         VARCHAR(50)

TABLE: inventory_items
  id                 VARCHAR(10) PK
  sku                VARCHAR(50)
  product_name       VARCHAR(255)
  zone               VARCHAR(50)   -- e.g. 'Zone A', 'Zone B'
  location           VARCHAR(50)
  quantity_on_hand   INT
  quantity_reserved  INT
  quantity_available INT
  reorder_point      INT
  status             VARCHAR(20)
  last_updated       DATETIME
  unit_of_measure    VARCHAR(10)
  weight             DECIMAL(10,2)
  category           VARCHAR(100)

TABLE: outbound_orders              -- outbound customer orders
  id            VARCHAR(10) PK
  order_number  VARCHAR(50)
  status        VARCHAR(20)         -- 'pending','processing','picking','packing','shipped','cancelled','on_hold'
  priority      VARCHAR(20)         -- 'low','medium','high','urgent'
  customer_name VARCHAR(255)
  total_lines   INT
  picked_lines  INT
  packed_lines  INT
  total_units   INT
  created_at    DATETIME
  due_date      DATETIME
  wave_id       VARCHAR(50)
  carrier       VARCHAR(100)
  staging_zone  VARCHAR(50)

TABLE: warehouse_tasks
  id                   VARCHAR(10) PK
  task_type            VARCHAR(50)   -- 'pick','pack','putaway','replenishment','cycle_count','transfer'
  status               VARCHAR(20)   -- 'pending','active','blocked','completed','cancelled'
  priority             VARCHAR(20)   -- 'low','medium','high','urgent'
  assigned_to          VARCHAR(20)
  assignee_name        VARCHAR(100)
  zone                 VARCHAR(50)
  source_location      VARCHAR(50)
  destination_location VARCHAR(50)
  reference_id         VARCHAR(50)
  created_at           DATETIME
  started_at           DATETIME
  completed_at         DATETIME
  estimated_minutes    INT
  is_blocked           BOOLEAN
  block_reason         TEXT

TABLE: inbound_asns                 -- Advance Shipment Notices from suppliers
  id              VARCHAR(10) PK
  asn_number      VARCHAR(50)
  status          VARCHAR(20)       -- 'pending','in_transit','receiving','completed','cancelled'
  supplier_name   VARCHAR(255)
  expected_date   DATETIME
  actual_date     DATETIME NULL
  total_lines     INT
  received_lines  INT
  total_units     INT
  received_units  INT
  dock            VARCHAR(50)
  po_number       VARCHAR(50)
  is_overdue      BOOLEAN

TABLE: warehouse_kpis
  id              VARCHAR(10) PK
  label           VARCHAR(255)
  value           DECIMAL(10,2)
  previous_value  DECIMAL(10,2)
  unit            VARCHAR(20)
  trend           VARCHAR(10)       -- 'up','down','stable'
  change_percent  DECIMAL(10,2)
  category        VARCHAR(50)
  target          DECIMAL(10,2)
  is_on_target    BOOLEAN

TABLE: zone_utilization
  zone_id             VARCHAR(20) PK
  zone_name           VARCHAR(100)
  zone_type           VARCHAR(50)
  total_capacity      INT
  used_capacity       INT
  utilization_percent DECIMAL(5,2)
  active_tasks        INT
  active_workers      INT
  temperature         DECIMAL(5,2) NULL 
  status              VARCHAR(20)
"""