-- =========================================================
-- PharmaDB - High-Quality Refactor v5
-- DDL + DML + VIEWS + TRIGGERS + PROC + FUNC
--
-- Changes:
-- - Added a manual data correction step to guarantee order totals.
-- - Added realistic, multi-week sample data for better analytics.
-- - Added role-based views for Customer, Supplier, and Pharmacist.
-- - Added stock management logic to Purchase Item triggers.
-- =========================================================

-- Start with a clean slate
DROP DATABASE IF EXISTS PharmaDB;
CREATE DATABASE PharmaDB
  DEFAULT CHARACTER SET utf8mb4
  DEFAULT COLLATE utf8mb4_unicode_ci;
USE PharmaDB;

SET sql_mode = 'STRICT_ALL_TABLES';

-- =========================================================
-- 1) MASTER TABLES (DDL)
-- =========================================================

CREATE TABLE Category (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL UNIQUE,
    Description VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE Supplier (
    SupplierID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL UNIQUE,
    Contact VARCHAR(100),
    Address VARCHAR(255),
    Email VARCHAR(100) UNIQUE,
    Phone VARCHAR(25)
) ENGINE=InnoDB;

CREATE TABLE Customer (
    CustomerID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(100) UNIQUE,
    Phone VARCHAR(25),
    Address VARCHAR(255)
) ENGINE=InnoDB;

CREATE TABLE Medicine (
    MedicineID INT PRIMARY KEY AUTO_INCREMENT,
    Name VARCHAR(100) NOT NULL,
    Manufacturer VARCHAR(100),
    Price DECIMAL(10,2) NOT NULL CHECK (Price >= 0),
    StockQty INT NOT NULL DEFAULT 0 CHECK (StockQty >= 0),
    ReorderLevel INT NOT NULL DEFAULT 0 CHECK (ReorderLevel >= 0),
    CategoryID INT,
    CONSTRAINT fk_med_category
        FOREIGN KEY (CategoryID) REFERENCES Category(CategoryID)
        ON UPDATE CASCADE ON DELETE SET NULL,
    INDEX idx_med_name (Name)
) ENGINE=InnoDB;

CREATE TABLE Purchase_Order (
    POID INT PRIMARY KEY AUTO_INCREMENT,
    PODate DATE NOT NULL,
    Status VARCHAR(50) DEFAULT 'Pending',
    TotalCost DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (TotalCost >= 0),
    SupplierID INT NOT NULL,
    CONSTRAINT fk_po_supplier
        FOREIGN KEY (SupplierID) REFERENCES Supplier(SupplierID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_po_date (PODate)
) ENGINE=InnoDB;

CREATE TABLE Purchase_Item (
    POID INT,
    MedicineID INT,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    CostPrice DECIMAL(10,2) NOT NULL CHECK (CostPrice >= 0),
    LineTotal DECIMAL(12,2) GENERATED ALWAYS AS (Quantity * CostPrice) STORED,
    PRIMARY KEY (POID, MedicineID),
    CONSTRAINT fk_pi_po
        FOREIGN KEY (POID) REFERENCES Purchase_Order(POID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_pi_med
        FOREIGN KEY (MedicineID) REFERENCES Medicine(MedicineID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE Sales_Order (
    SOID INT PRIMARY KEY AUTO_INCREMENT,
    SODate DATE NOT NULL,
    Status VARCHAR(50) DEFAULT 'Pending',
    TotalAmount DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (TotalAmount >= 0),
    CustomerID INT NOT NULL,
    CONSTRAINT fk_so_customer
        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    INDEX idx_so_date (SODate)
) ENGINE=InnoDB;

CREATE TABLE Sales_Item (
    SOID INT,
    MedicineID INT,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    SellingPrice DECIMAL(10,2) NOT NULL CHECK (SellingPrice >= 0),
    LineTotal DECIMAL(12,2) GENERATED ALWAYS AS (Quantity * SellingPrice) STORED,
    PRIMARY KEY (SOID, MedicineID),
    CONSTRAINT fk_si_so
        FOREIGN KEY (SOID) REFERENCES Sales_Order(SOID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_si_med
        FOREIGN KEY (MedicineID) REFERENCES Medicine(MedicineID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE Stock_Alert (
    AlertID INT AUTO_INCREMENT PRIMARY KEY,
    AlertType VARCHAR(50) NOT NULL,
    DateInitiated DATE NOT NULL,
    Notes VARCHAR(255),
    Resolved BOOLEAN DEFAULT FALSE,
    MedicineID INT NOT NULL,
    CONSTRAINT fk_alert_med
        FOREIGN KEY (MedicineID) REFERENCES Medicine(MedicineID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    INDEX idx_alert_med_resolved (MedicineID, Resolved)
) ENGINE=InnoDB;

CREATE TABLE Prescription (
    PrescriptionID INT PRIMARY KEY AUTO_INCREMENT,
    PrescDate DATE NOT NULL,
    DoctorName VARCHAR(100) NOT NULL,
    CustomerID INT,
    CONSTRAINT fk_presc_customer
        FOREIGN KEY (CustomerID) REFERENCES Customer(CustomerID)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB;

CREATE TABLE Prescription_Item (
    PrescriptionID INT,
    MedicineID INT,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    Dosage VARCHAR(100),
    PRIMARY KEY (PrescriptionID, MedicineID),
    CONSTRAINT fk_presci_presc
        FOREIGN KEY (PrescriptionID) REFERENCES Prescription(PrescriptionID)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT fk_presci_med
        FOREIGN KEY (MedicineID) REFERENCES Medicine(MedicineID)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;


-- =========================================================
-- 2) ROLE-BASED VIEWS
-- =========================================================

CREATE OR REPLACE VIEW Available_Medicines_View AS
SELECT m.Name, m.Manufacturer, m.Price, c.Name AS Category
FROM Medicine m LEFT JOIN Category c ON m.CategoryID = c.CategoryID;

CREATE OR REPLACE VIEW Customer_Order_History_View AS
SELECT so.CustomerID, c.Name AS CustomerName, so.SOID AS OrderID, so.SODate AS OrderDate, m.Name AS MedicineName, si.Quantity, si.SellingPrice, si.LineTotal
FROM Sales_Order so
JOIN Sales_Item si ON so.SOID = si.SOID
JOIN Customer c ON so.CustomerID = c.CustomerID
JOIN Medicine m ON si.MedicineID = m.MedicineID;

CREATE OR REPLACE VIEW Supplier_Purchase_History_View AS
SELECT po.SupplierID, s.Name AS SupplierName, po.POID AS OrderID, po.PODate AS OrderDate, m.Name AS MedicineName, pi.Quantity, pi.CostPrice, pi.LineTotal
FROM Purchase_Order po
JOIN Purchase_Item pi ON po.POID = pi.POID
JOIN Supplier s ON po.SupplierID = s.SupplierID
JOIN Medicine m ON pi.MedicineID = m.MedicineID;


-- =========================================================
-- 3) SAMPLE DATA (DML) - V2 (3-week realistic data)
-- =========================================================

INSERT INTO Category (Name, Description) VALUES
('Analgesic', 'Pain relieving medicines'), ('Antibiotic', 'Treats bacterial infections'), ('Antipyretic', 'Reduces fever'),
('Antiseptic', 'Prevents infections on skin'), ('Antiviral', 'Treats viral infections'), ('Supplement', 'Nutritional supplements'),
('Antihistamine', 'Treats allergies');

INSERT INTO Supplier (Name, Contact, Address, Email, Phone) VALUES
('Global Pharma', 'Ravi Shankar', 'Mumbai, MH', 'contact@globalpharma.com', '9876543210'),
('MediSource Inc.', 'Priya Patel', 'Ahmedabad, GJ', 'sales@medisource.com', '8899776655'),
('HealthWave Drugs', 'Amit Singh', 'Delhi, DL', 'support@healthwave.com', '9988776655');

INSERT INTO Customer (Name, Email, Phone, Address) VALUES
('Aarav Sharma', 'aarav.sharma@example.com', '9123456780', 'Koramangala, Bangalore'),
('Diya Mehta', 'diya.mehta@example.com', '9234567891', 'Bandra, Mumbai'),
('Rohan Gupta', 'rohan.gupta@example.com', '9345678902', 'Indiranagar, Bangalore'),
('Priya Singh', 'priya.singh@example.com', '9456789013', 'Jubilee Hills, Hyderabad'),
('Aditya Kumar', 'aditya.kumar@example.com', '9567890124', 'Anna Nagar, Chennai'),
('Ananya Reddy', 'ananya.reddy@example.com', '9678901235', 'HSR Layout, Bangalore'),
('Vikram Rathore', 'vikram.rathore@example.com', '9789012346', 'Powai, Mumbai'),
('Isha Verma', 'isha.verma@example.com', '9890123457', 'Kondapur, Hyderabad'),
('Arjun Desai', 'arjun.desai@example.com', '9901234568', 'Whitefield, Bangalore'),
('Saanvi Joshi', 'saanvi.joshi@example.com', '9012345679', 'Kalyani Nagar, Pune');

INSERT INTO Medicine (Name, Manufacturer, Price, StockQty, ReorderLevel, CategoryID) VALUES
('Paracetamol 500mg', 'GSK', 20.00, 200, 50, 1),
('Ibuprofen 200mg', 'Dr. Reddy''s', 35.00, 150, 50, 1),
('Amoxicillin 250mg', 'Cipla', 75.00, 80, 30, 2),
('Cetirizine 10mg', 'Sun Pharma', 30.00, 100, 40, 7),
('Vitamin C 500mg', 'Abbott', 120.00, 250, 100, 6),
('Dettol Liquid 1L', 'Reckitt', 290.00, 60, 20, 4),
('Oseltamivir 75mg', 'Roche', 450.00, 40, 15, 5),
('Azithromycin 500mg', 'Pfizer', 118.00, 25, 20, 2),
('Multivitamin Tablets', 'Himalaya', 250.00, 180, 75, 6),
('Loratadine 10mg', 'Bayer', 55.00, 70, 30, 7);

-- Purchases to stock up
INSERT INTO Purchase_Order (PODate, Status, SupplierID) VALUES
('2025-09-28', 'Received', 1), ('2025-10-12', 'Received', 2);

INSERT INTO Purchase_Item (POID, MedicineID, Quantity, CostPrice) VALUES
(1, 1, 100, 15.00), (1, 2, 100, 28.00), (1, 3, 50, 60.00), (1, 4, 60, 22.00),
(1, 5, 150, 90.00), (1, 6, 40, 250.00), (1, 9, 100, 200.00),
(2, 8, 30, 90.00), (2, 2, 50, 29.00), (2, 10, 40, 45.00);

-- Week 1 Sales Data (Oct 1 - Oct 7)
INSERT INTO Sales_Order (SODate, Status, CustomerID) VALUES
('2025-10-01', 'Completed', 1), ('2025-10-01', 'Completed', 2), ('2025-10-02', 'Completed', 3),
('2025-10-03', 'Completed', 4), ('2025-10-04', 'Completed', 5), ('2025-10-04', 'Completed', 1),
('2025-10-05', 'Completed', 6), ('2025-10-06', 'Completed', 7), ('2025-10-07', 'Completed', 8);
INSERT INTO Sales_Item (SOID, MedicineID, Quantity, SellingPrice) VALUES
(1, 1, 2, 20.00), (1, 5, 1, 120.00), (2, 4, 3, 30.00), (3, 2, 2, 35.00), (4, 9, 1, 250.00),
(5, 1, 5, 20.00), (6, 6, 1, 290.00), (7, 5, 2, 120.00), (8, 3, 1, 75.00), (9, 1, 3, 20.00), (9, 2, 3, 35.00);

-- Week 2 Sales Data (Oct 8 - Oct 14)
INSERT INTO Sales_Order (SODate, Status, CustomerID) VALUES
('2025-10-08', 'Completed', 9), ('2025-10-09', 'Completed', 10), ('2025-10-09', 'Completed', 1),
('2025-10-10', 'Completed', 2), ('2025-10-11', 'Completed', 5), ('2025-10-12', 'Completed', 3),
('2025-10-13', 'Completed', 7), ('2025-10-14', 'Completed', 4), ('2025-10-14', 'Completed', 6);
INSERT INTO Sales_Item (SOID, MedicineID, Quantity, SellingPrice) VALUES
(10, 7, 1, 450.00), (11, 10, 2, 55.00), (12, 1, 10, 20.00), (13, 2, 5, 35.00), (14, 8, 5, 118.00),
(15, 5, 3, 120.00), (16, 9, 2, 250.00), (17, 4, 4, 30.00), (18, 1, 4, 20.00);

-- Week 3 Sales Data (Oct 15 - Oct 21)
INSERT INTO Sales_Order (SODate, Status, CustomerID) VALUES
('2025-10-15', 'Completed', 8), ('2025-10-16', 'Completed', 2), ('2025-10-17', 'Completed', 5),
('2025-10-18', 'Completed', 10), ('2025-10-18', 'Completed', 9), ('2025-10-19', 'Completed', 3),
('2025-10-20', 'Completed', 1), ('2025-10-21', 'Completed', 7), ('2025-10-21', 'Completed', 5);
INSERT INTO Sales_Item (SOID, MedicineID, Quantity, SellingPrice) VALUES
(19, 2, 8, 35.00), (20, 5, 4, 120.00), (21, 1, 5, 20.00), (22, 10, 3, 55.00), (23, 9, 1, 250.00),
(24, 4, 2, 30.00), (25, 6, 1, 290.00), (26, 1, 10, 20.00), (27, 2, 10, 35.00);

-- =========================================================
-- 4) DATA CORRECTION (Post-DML)
-- =========================================================
-- Manually update order totals to ensure data integrity,
-- in case triggers did not fire during bulk insert.
UPDATE Sales_Order so SET so.TotalAmount = (SELECT SUM(si.LineTotal) FROM Sales_Item si WHERE si.SOID = so.SOID) WHERE so.SOID > 0;
UPDATE Purchase_Order po SET po.TotalCost = (SELECT SUM(pi.LineTotal) FROM Purchase_Item pi WHERE pi.POID = po.POID) WHERE po.POID > 0;

-- =========================================================
-- 5) TRIGGERS
-- =========================================================

DELIMITER $$
CREATE TRIGGER trg_low_stock_alert AFTER UPDATE ON Medicine FOR EACH ROW
BEGIN
    IF NEW.StockQty <= NEW.ReorderLevel AND NEW.StockQty < OLD.StockQty THEN
        IF NOT EXISTS (SELECT 1 FROM Stock_Alert WHERE MedicineID = NEW.MedicineID AND Resolved = FALSE) THEN
            INSERT INTO Stock_Alert (AlertType, DateInitiated, Notes, MedicineID)
            VALUES ('Low Stock', CURDATE(), CONCAT('Stock for "', NEW.Name, '" is low (', NEW.StockQty, '). Reorder level is ', NEW.ReorderLevel, '.'), NEW.MedicineID);
        END IF;
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_resolve_stock_alert AFTER UPDATE ON Medicine FOR EACH ROW
BEGIN
    IF NEW.StockQty > NEW.ReorderLevel AND OLD.StockQty <= OLD.ReorderLevel THEN
        UPDATE Stock_Alert SET Resolved = TRUE, Notes = CONCAT(Notes, ' (Auto-resolved on ', CURDATE(), ' due to stock replenishment.)')
         WHERE MedicineID = NEW.MedicineID AND Resolved = FALSE;
    END IF;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_pi_after_insert AFTER INSERT ON Purchase_Item FOR EACH ROW
BEGIN
    UPDATE Purchase_Order SET TotalCost = (SELECT SUM(LineTotal) FROM Purchase_Item WHERE POID = NEW.POID) WHERE POID = NEW.POID;
    UPDATE Medicine SET StockQty = StockQty + NEW.Quantity WHERE MedicineID = NEW.MedicineID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_pi_after_update AFTER UPDATE ON Purchase_Item FOR EACH ROW
BEGIN
    UPDATE Purchase_Order SET TotalCost = (SELECT SUM(LineTotal) FROM Purchase_Item WHERE POID = NEW.POID) WHERE POID = NEW.POID;
    UPDATE Medicine SET StockQty = StockQty + (NEW.Quantity - OLD.Quantity) WHERE MedicineID = NEW.MedicineID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_pi_after_delete AFTER DELETE ON Purchase_Item FOR EACH ROW
BEGIN
    UPDATE Purchase_Order SET TotalCost = IFNULL((SELECT SUM(LineTotal) FROM Purchase_Item WHERE POID = OLD.POID), 0) WHERE POID = OLD.POID;
    UPDATE Medicine SET StockQty = GREATEST(0, StockQty - OLD.Quantity) WHERE MedicineID = OLD.MedicineID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_si_after_insert AFTER INSERT ON Sales_Item FOR EACH ROW
BEGIN
    UPDATE Sales_Order SET TotalAmount = (SELECT SUM(LineTotal) FROM Sales_Item WHERE SOID = NEW.SOID) WHERE SOID = NEW.SOID;
    UPDATE Medicine SET StockQty = GREATEST(0, StockQty - NEW.Quantity) WHERE MedicineID = NEW.MedicineID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_si_after_update AFTER UPDATE ON Sales_Item FOR EACH ROW
BEGIN
    UPDATE Sales_Order SET TotalAmount = (SELECT SUM(LineTotal) FROM Sales_Item WHERE SOID = NEW.SOID) WHERE SOID = NEW.SOID;
    UPDATE Medicine SET StockQty = StockQty - (NEW.Quantity - OLD.Quantity) WHERE MedicineID = NEW.MedicineID;
END$$
DELIMITER ;

DELIMITER $$
CREATE TRIGGER trg_si_after_delete AFTER DELETE ON Sales_Item FOR EACH ROW
BEGIN
    UPDATE Sales_Order SET TotalAmount = IFNULL((SELECT SUM(LineTotal) FROM Sales_Item WHERE SOID = OLD.SOID), 0) WHERE SOID = OLD.SOID;
    UPDATE Medicine SET StockQty = StockQty + OLD.Quantity WHERE MedicineID = OLD.MedicineID;
END$$
DELIMITER ;

-- =========================================================
-- 6) PROCEDURE & FUNCTION
-- =========================================================
DELIMITER $$
CREATE PROCEDURE GetMedicineDetailsByCategory(IN category_name VARCHAR(100))
BEGIN
    SELECT m.MedicineID, m.Name, m.Price, m.StockQty, c.Name AS Category
      FROM Medicine m JOIN Category c ON m.CategoryID = c.CategoryID
     WHERE c.Name = category_name;
END$$
DELIMITER ;

DELIMITER $$
CREATE FUNCTION GetStockValue() RETURNS DECIMAL(14,2) DETERMINISTIC READS SQL DATA
BEGIN
    DECLARE total_value DECIMAL(14,2);
    SELECT SUM(StockQty * Price) INTO total_value FROM Medicine;
    RETURN IFNULL(total_value, 0);
END$$
DELIMITER ;
