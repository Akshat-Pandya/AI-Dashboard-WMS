CREATE TABLE inbound_asns (
  id VARCHAR(10) PRIMARY KEY,
  asnNumber VARCHAR(30),
  status VARCHAR(20),
  supplierName VARCHAR(100),
  expectedDate DATETIME,
  actualDate DATETIME,
  totalLines INT,
  receivedLines INT,
  totalUnits INT,
  receivedUnits INT,
  dock VARCHAR(20),
  poNumber VARCHAR(20),
  isOverdue BOOLEAN
);

INSERT INTO inbound_asns VALUES
('ASN001','ASN-2026-1201','receiving','Siemens Industrial Supply','2026-02-17 10:00:00','2026-02-17 09:45:00',4,2,200,120,'Dock 3','PO-8834',false),
('ASN002','ASN-2026-1198','expected','Bosch Automation Parts','2026-02-16 14:00:00',NULL,6,0,450,0,'Dock 1','PO-8820',true),
('ASN003','ASN-2026-1202','received','ABB Industrial Supplies','2026-02-16 10:00:00','2026-02-16 09:40:00',5,5,320,320,'Dock 2','PO-8838',false),
('ASN004','ASN-2026-1203','receiving','Schneider Electric India','2026-02-17 12:00:00','2026-02-17 11:50:00',7,3,540,210,'Dock 4','PO-8841',false),
('ASN005','ASN-2026-1204','expected','Delta Automation Ltd','2026-02-18 09:30:00',NULL,4,0,260,0,'Dock 1','PO-8845',false),
('ASN006','ASN-2026-1205','overdue','Yaskawa Robotics','2026-02-16 15:00:00',NULL,6,0,410,0,'Dock 5','PO-8848',true),
('ASN007','ASN-2026-1206','received','Panasonic Industrial','2026-02-17 08:30:00','2026-02-17 08:20:00',3,3,180,180,'Dock 2','PO-8851',false),
('ASN008','ASN-2026-1207','receiving','Mitsubishi Electric','2026-02-17 13:00:00','2026-02-17 12:45:00',8,4,600,300,'Dock 3','PO-8854',false);


CREATE TABLE inventory_items (
  id VARCHAR(10) PRIMARY KEY,
  sku VARCHAR(20),
  productName VARCHAR(100),
  zone VARCHAR(20),
  location VARCHAR(20),
  quantityOnHand INT,
  quantityReserved INT,
  quantityAvailable INT,
  reorderPoint INT,
  status VARCHAR(20),
  lastUpdated DATETIME,
  unitOfMeasure VARCHAR(10),
  weight DECIMAL(6,2),
  category VARCHAR(50)
);

INSERT INTO inventory_items VALUES
('INV001','SKU-A1001','Industrial Bearing 6205','Zone A','A-01-03',5,2,3,20,'available','2026-02-17 08:30:00','EA',0.12,'Bearings'),
('INV002','SKU-A1002','Conveyor Belt Section 2M','Zone A','A-02-07',150,30,120,25,'available','2026-02-17 09:15:00','EA',4.50,'Conveyors'),
('INV003','SKU-B2001','Servo Motor SM-400','Zone B','B-01-01',8,8,0,10,'reserved','2026-02-17 07:45:00','EA',3.20,'Motors'),
('INV004','SKU-B2002','PLC Controller Unit X200','Zone B','B-03-05',45,10,35,15,'available','2026-02-17 10:00:00','EA',1.80,'Controllers'),
('INV005','SKU-C3001','Safety Light Curtain SLC-80','Zone C','C-02-02',2,0,2,5,'available','2026-02-16 14:30:00','EA',0.90,'Safety'),
('INV006','SKU-A1003','Pneumatic Cylinder PC-50','Zone A','A-04-01',0,0,0,12,'available','2026-02-15 16:00:00','EA',2.10,'Pneumatics'),
('INV007','SKU-A1004','Hydraulic Pump HP-20','Zone A','A-05-02',18,4,14,10,'available','2026-02-17 11:10:00','EA',6.40,'Hydraulics'),
('INV008','SKU-A1005','Linear Guide Rail LG-300','Zone A','A-06-01',60,12,48,20,'available','2026-02-17 11:25:00','EA',3.60,'Motion'),
('INV009','SKU-A1006','Industrial Coupling IC-90','Zone A','A-02-03',22,5,17,15,'available','2026-02-17 10:40:00','EA',0.80,'Mechanical'),
('INV010','SKU-A1007','Air Filter Cartridge AF-10','Zone A','A-03-06',95,20,75,30,'available','2026-02-17 09:55:00','EA',0.30,'Maintenance');


CREATE TABLE outbound_orders (
  id VARCHAR(10) PRIMARY KEY,
  orderNumber VARCHAR(30),
  status VARCHAR(20),
  priority VARCHAR(20),
  customerName VARCHAR(100),
  totalLines INT,
  pickedLines INT,
  packedLines INT,
  totalUnits INT,
  createdAt DATETIME,
  dueDate DATETIME,
  waveId VARCHAR(20),
  carrier VARCHAR(30),
  stagingZone VARCHAR(20)
);

INSERT INTO outbound_orders VALUES
('ORD001','WO-2026-0451','picking','high','AutoTech Manufacturing',5,2,0,48,'2026-02-17 06:00:00','2026-02-17 18:00:00','WAVE-042','DHL Express','Zone D'),
('ORD002','WO-2026-0452','pending','urgent','RoboSys India Pvt Ltd',3,0,0,12,'2026-02-17 07:30:00','2026-02-17 14:00:00',NULL,'BlueDart','Zone D'),
('ORD003','WO-2026-0453','picking','medium','Precision Auto Components',6,3,1,72,'2026-02-17 08:10:00','2026-02-18 12:00:00','WAVE-043','Delhivery','Zone D');


CREATE TABLE warehouse_alerts (
  id VARCHAR(10) PRIMARY KEY,
  severity VARCHAR(20),
  title VARCHAR(100),
  message TEXT,
  category VARCHAR(30),
  timestamp DATETIME,
  acknowledged BOOLEAN,
  zone VARCHAR(20)
);

INSERT INTO warehouse_alerts VALUES
('ALT001','critical','Zone C Temperature Rising','Cold storage Zone C temperature at -15°C, threshold is -18°C. Compressor check required.','environmental','2026-02-17 10:30:00',false,'Zone C'),
('ALT002','error','4 Tasks Blocked in Zone B','Put-away tasks blocked due to occupied destination locations. Replenishment cycle needed.','operations','2026-02-17 09:55:00',false,'Zone B');



CREATE TABLE warehouse_kpis (
  id VARCHAR(10) PRIMARY KEY,
  label VARCHAR(50),
  value DECIMAL(10,2),
  previousValue DECIMAL(10,2),
  unit VARCHAR(20),
  trend VARCHAR(10),
  changePercent DECIMAL(6,2),
  category VARCHAR(30),
  target DECIMAL(10,2),
  isOnTarget BOOLEAN
);

INSERT INTO warehouse_kpis VALUES
('KPI001','Orders Fulfilled Today',156,142,'orders','up',9.9,'throughput',150,true),
('KPI002','Pick Accuracy',99.2,98.8,'%', 'up',0.4,'accuracy',99.5,false);




CREATE TABLE warehouse_tasks (
  id VARCHAR(10) PRIMARY KEY,
  taskType VARCHAR(30),
  status VARCHAR(20),
  priority VARCHAR(20),
  assignedTo VARCHAR(20),
  assigneeName VARCHAR(50),
  zone VARCHAR(20),
  sourceLocation VARCHAR(30),
  destinationLocation VARCHAR(30),
  referenceId VARCHAR(20),
  createdAt DATETIME,
  startedAt DATETIME,
  completedAt DATETIME,
  estimatedMinutes INT,
  isBlocked BOOLEAN,
  blockReason TEXT
);

INSERT INTO warehouse_tasks VALUES
('TSK001','picking','in-progress','high','OP-101','Rajesh Kumar','Zone A','A-01-03','D-STAGE-01','ORD001','2026-02-17 08:00:00','2026-02-17 08:15:00',NULL,25,false,NULL),
('TSK002','put-away','blocked','medium','OP-103','Priya Singh','Zone B','DOCK-3','B-05-02','ASN001','2026-02-17 09:50:00',NULL,NULL,15,true,'Destination location occupied');


CREATE TABLE zone_utilization (
  zoneId VARCHAR(20) PRIMARY KEY,
  zoneName VARCHAR(50),
  zoneType VARCHAR(30),
  totalCapacity INT,
  usedCapacity INT,
  utilizationPercent DECIMAL(5,2),
  activeTasks INT,
  activeWorkers INT,
  temperature INT,
  status VARCHAR(20)
);

INSERT INTO zone_utilization VALUES
('zone-a','Zone A','ambient',500,420,84,12,5,NULL,'active'),
('zone-b','Zone B','ambient',400,280,70,8,3,NULL,'active'),
('zone-c','Zone C','cold-storage',200,185,92.5,4,2,-18,'active');
