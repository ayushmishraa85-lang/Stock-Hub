-- ============================================================================
-- sql_queries.sql
-- ----------------------------------------------------------------------------
-- Reference SQL for the Inventory Management System.
--
-- These are the raw queries that power analytics.py, inventory.py, and
-- sales.py (Python uses parameterized versions of these via pandas /
-- sqlite3 -- this file is for reference, learning, and easy porting to
-- MySQL/PostgreSQL).
--
-- Schema: SQLite (see database.py for the authoritative CREATE TABLE
-- statements). Minor syntax notes for porting to MySQL are included
-- inline where relevant.
-- ============================================================================


-- ----------------------------------------------------------------------------
-- SCHEMA (for reference -- database.py is the source of truth)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS Suppliers (
    SupplierID      INTEGER PRIMARY KEY AUTOINCREMENT,   -- MySQL: AUTO_INCREMENT
    SupplierName    TEXT NOT NULL,
    ContactNumber   TEXT,
    Email           TEXT
);

CREATE TABLE IF NOT EXISTS Products (
    ProductID       INTEGER PRIMARY KEY AUTOINCREMENT,
    ProductName     TEXT NOT NULL,
    Category        TEXT NOT NULL,
    Price           REAL NOT NULL CHECK (Price >= 0),
    CurrentStock    INTEGER NOT NULL DEFAULT 0 CHECK (CurrentStock >= 0),
    ReorderLevel    INTEGER NOT NULL DEFAULT 10,
    SupplierID      INTEGER,
    IsActive        INTEGER NOT NULL DEFAULT 1,           -- soft-delete flag
    FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS Sales (
    SaleID          INTEGER PRIMARY KEY AUTOINCREMENT,
    ProductID       INTEGER NOT NULL,
    QuantitySold    INTEGER NOT NULL CHECK (QuantitySold > 0),
    SaleDate        TEXT NOT NULL,                        -- 'YYYY-MM-DD'
    UnitPriceAtSale REAL NOT NULL,                         -- price snapshot at time of sale
    FOREIGN KEY (ProductID) REFERENCES Products(ProductID) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS Users (
    UserID          INTEGER PRIMARY KEY AUTOINCREMENT,
    Username        TEXT NOT NULL UNIQUE,
    PasswordHash    TEXT NOT NULL,
    Role            TEXT NOT NULL DEFAULT 'staff'
);

CREATE INDEX IF NOT EXISTS idx_sales_date     ON Sales(SaleDate);
CREATE INDEX IF NOT EXISTS idx_sales_product  ON Sales(ProductID);
CREATE INDEX IF NOT EXISTS idx_products_category ON Products(Category);


-- ============================================================================
-- BUSINESS QUESTION 1: Which products sell the fastest?
-- (Total units sold, all-time -- simplest version of "top sellers")
-- ============================================================================

SELECT
    p.ProductName,
    p.Category,
    SUM(sa.QuantitySold) AS TotalUnitsSold,
    SUM(sa.QuantitySold * sa.UnitPriceAtSale) AS TotalRevenue
FROM Sales sa
JOIN Products p ON sa.ProductID = p.ProductID
GROUP BY p.ProductID, p.ProductName, p.Category
ORDER BY TotalUnitsSold DESC
LIMIT 10;

-- A more rigorous "velocity" version: average units/day over the last 30 days
-- (normalizes for how long a product has been selling).
SELECT
    p.ProductName,
    p.Category,
    SUM(sa.QuantitySold) * 1.0 / 30 AS AvgUnitsPerDay
FROM Sales sa
JOIN Products p ON sa.ProductID = p.ProductID
WHERE sa.SaleDate >= date('now', '-30 days')   -- MySQL: DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY p.ProductID, p.ProductName, p.Category
ORDER BY AvgUnitsPerDay DESC
LIMIT 10;


-- ============================================================================
-- BUSINESS QUESTION 2: Which products need reordering?
-- (Current stock at or below the configured reorder level)
-- ============================================================================

SELECT
    p.ProductID,
    p.ProductName,
    p.Category,
    p.CurrentStock,
    p.ReorderLevel,
    s.SupplierName,
    s.ContactNumber
FROM Products p
LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
WHERE p.CurrentStock <= p.ReorderLevel
  AND p.IsActive = 1
ORDER BY (p.CurrentStock * 1.0 / NULLIF(p.ReorderLevel, 0)) ASC;


-- ============================================================================
-- BUSINESS QUESTION 3: Which categories generate the highest revenue?
-- ============================================================================

SELECT
    p.Category,
    SUM(sa.QuantitySold * sa.UnitPriceAtSale) AS Revenue,
    SUM(sa.QuantitySold) AS QuantitySold
FROM Sales sa
JOIN Products p ON sa.ProductID = p.ProductID
GROUP BY p.Category
ORDER BY Revenue DESC;


-- ============================================================================
-- BUSINESS QUESTION 4: Which products have not sold in the last 30 days?
-- ============================================================================

SELECT
    p.ProductID,
    p.ProductName,
    p.Category,
    p.CurrentStock,
    p.Price
FROM Products p
WHERE p.IsActive = 1
  AND p.ProductID NOT IN (
        SELECT DISTINCT ProductID
        FROM Sales
        WHERE SaleDate >= date('now', '-30 days')
  );


-- ============================================================================
-- BUSINESS QUESTION 5: What is the current inventory value?
-- ============================================================================

-- Overall total
SELECT SUM(Price * CurrentStock) AS TotalInventoryValue
FROM Products
WHERE IsActive = 1;

-- Broken down by category (for the pie chart)
SELECT
    Category,
    SUM(Price * CurrentStock) AS InventoryValue
FROM Products
WHERE IsActive = 1
GROUP BY Category
ORDER BY InventoryValue DESC;


-- ============================================================================
-- BUSINESS QUESTION 6: Which supplier provides the most products?
-- ============================================================================

SELECT
    s.SupplierName,
    COUNT(p.ProductID) AS ProductCount
FROM Suppliers s
LEFT JOIN Products p ON s.SupplierID = p.SupplierID AND p.IsActive = 1
GROUP BY s.SupplierID, s.SupplierName
ORDER BY ProductCount DESC;


-- ============================================================================
-- SUPPORTING QUERIES used elsewhere in the dashboard
-- ============================================================================

-- Monthly sales trend (for the line chart)
SELECT
    strftime('%Y-%m', SaleDate) AS Month,         -- MySQL: DATE_FORMAT(SaleDate, '%Y-%m')
    SUM(QuantitySold * UnitPriceAtSale) AS Revenue,
    SUM(QuantitySold) AS QuantitySold
FROM Sales
GROUP BY Month
ORDER BY Month;

-- Daily sales trend, last 60 days (for the dashboard area chart)
SELECT
    SaleDate,
    SUM(QuantitySold * UnitPriceAtSale) AS Revenue,
    SUM(QuantitySold) AS QuantitySold
FROM Sales
WHERE SaleDate >= date('now', '-60 days')
GROUP BY SaleDate
ORDER BY SaleDate;

-- Full sales history with product details (for the Sales History tab)
SELECT
    sa.SaleID,
    p.ProductName,
    p.Category,
    sa.QuantitySold,
    sa.UnitPriceAtSale,
    (sa.QuantitySold * sa.UnitPriceAtSale) AS LineTotal,
    sa.SaleDate
FROM Sales sa
JOIN Products p ON sa.ProductID = p.ProductID
ORDER BY sa.SaleDate DESC, sa.SaleID DESC
LIMIT 500;

-- Search products by keyword + category filter
SELECT
    p.ProductID, p.ProductName, p.Category, p.Price,
    p.CurrentStock, p.ReorderLevel, s.SupplierName
FROM Products p
LEFT JOIN Suppliers s ON p.SupplierID = s.SupplierID
WHERE p.IsActive = 1
  AND p.ProductName LIKE '%' || :keyword || '%'     -- MySQL: LIKE CONCAT('%', :keyword, '%')
  AND (:category = 'All' OR p.Category = :category)
ORDER BY p.ProductName;

-- Record a sale, then decrement stock (two statements -- wrap in a
-- transaction in application code; see sales.py:record_sale)
INSERT INTO Sales (ProductID, QuantitySold, SaleDate, UnitPriceAtSale)
VALUES (:product_id, :quantity, :sale_date, :unit_price);

UPDATE Products
SET CurrentStock = CurrentStock - :quantity
WHERE ProductID = :product_id
  AND CurrentStock >= :quantity;   -- guards against overselling
