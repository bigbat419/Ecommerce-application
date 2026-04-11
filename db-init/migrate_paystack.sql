-- Run this once if your orders table already exists without paystack_reference
ALTER TABLE orders ADD COLUMN IF NOT EXISTS paystack_reference VARCHAR(100) DEFAULT NULL;
