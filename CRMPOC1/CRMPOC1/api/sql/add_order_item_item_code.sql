-- Direct SQL script to add item_code to order_items and backfill from item_masters
-- Run this directly against the target database.

IF COL_LENGTH('dbo.order_items', 'item_code') IS NULL
BEGIN
    ALTER TABLE dbo.order_items ADD item_code NVARCHAR(100) NULL;
END;
GO

-- Backfill existing rows from the linked item master when available
UPDATE oi
SET item_code = im.item_code
FROM dbo.order_items AS oi
LEFT JOIN dbo.item_masters AS im ON im.id = oi.item_id
WHERE oi.item_code IS NULL OR oi.item_code = '';
GO

-- Optional: add an index for faster lookups
IF NOT EXISTS (
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_order_items_item_code' AND object_id = OBJECT_ID('dbo.order_items')
)
BEGIN
    CREATE INDEX IX_order_items_item_code ON dbo.order_items (item_code);
END;
GO
