-- ═══════════════════════════════════════════════════════════════════
-- FLAMINGOS MIGRATION — Run this against your existing database
-- Works on ecommerce_db OR flamingos_db (whichever you have)
--
-- Usage in phpMyAdmin:
--   1. Select your database (ecommerce_db or flamingos_db)
--   2. Click "Import" → choose this file → Go
--
-- Usage in MySQL CLI:
--   mysql -u root -p ecommerce_db < migrate_flamingos.sql
-- ═══════════════════════════════════════════════════════════════════

-- ─── If you want to use the new database name, uncomment these:
-- CREATE DATABASE IF NOT EXISTS flamingos_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE flamingos_db;

-- ─── Core tables (safe — won't overwrite existing data) ──────────

CREATE TABLE IF NOT EXISTS users (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(120)  NOT NULL,
  email      VARCHAR(255)  UNIQUE NOT NULL,
  password   VARCHAR(255)  NOT NULL,
  role       VARCHAR(50)   DEFAULT 'user',
  is_admin   TINYINT(1)    DEFAULT 0,
  created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(255)   NOT NULL,
  slug        VARCHAR(255)   UNIQUE NOT NULL,
  category    VARCHAR(100),
  description TEXT,
  price       DECIMAL(10,2)  NOT NULL,
  stock       INT            DEFAULT 0,
  image       VARCHAR(255),
  created_at  TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS product_images (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  product_id  INT NOT NULL,
  image       VARCHAR(255) NOT NULL,
  sort_order  INT DEFAULT 0,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS cart_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT  NOT NULL,
  product_id INT  NOT NULL,
  quantity   INT  DEFAULT 1,
  added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  user_id             INT           NOT NULL,
  total               DECIMAL(10,2) NOT NULL,
  status              VARCHAR(50)   DEFAULT 'pending',
  paystack_reference  VARCHAR(100)  DEFAULT NULL,
  created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT           NOT NULL,
  product_id INT           NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  quantity   INT           NOT NULL
);

CREATE TABLE IF NOT EXISTS addresses (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT          NOT NULL,
  label      VARCHAR(100),
  line1      VARCHAR(255) NOT NULL,
  city       VARCHAR(100) NOT NULL,
  country    VARCHAR(100) NOT NULL,
  created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─── Add paystack_reference if missing ───────────────────────────
SET @dbname = DATABASE();
SET @tablename = 'orders';
SET @colname = 'paystack_reference';
SET @preparedStatement = (
  SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
     WHERE table_schema = @dbname AND table_name = @tablename AND column_name = @colname) > 0,
    'SELECT 1',
    CONCAT('ALTER TABLE orders ADD COLUMN paystack_reference VARCHAR(100) DEFAULT NULL')
  )
);
PREPARE stmt FROM @preparedStatement;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- ─── Flamingos new tables ─────────────────────────────────────────

CREATE TABLE IF NOT EXISTS wishlist (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_wish (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS reviews (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT        NOT NULL,
  user_id    INT        NOT NULL,
  rating     TINYINT    NOT NULL DEFAULT 5,
  title      VARCHAR(160),
  body       TEXT,
  created_at TIMESTAMP  DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS coupons (
  id           INT AUTO_INCREMENT PRIMARY KEY,
  code         VARCHAR(50)    UNIQUE NOT NULL,
  discount_pct DECIMAL(5,2)   NOT NULL DEFAULT 0,
  max_uses     INT            DEFAULT NULL,
  uses         INT            DEFAULT 0,
  active       TINYINT(1)     DEFAULT 1,
  expires_at   DATE           DEFAULT NULL,
  created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS brands (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(120)  NOT NULL,
  slug        VARCHAR(120)  UNIQUE NOT NULL,
  description TEXT,
  logo        VARCHAR(255),
  website     VARCHAR(255),
  active      TINYINT(1)    DEFAULT 1,
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(120)  NOT NULL,
  slug        VARCHAR(120)  UNIQUE NOT NULL,
  parent_id   INT           DEFAULT NULL,
  description TEXT,
  image       VARCHAR(255),
  active      TINYINT(1)    DEFAULT 1,
  sort_order  INT           DEFAULT 0,
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS shipping_methods (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(120)   NOT NULL,
  description   VARCHAR(255),
  price         DECIMAL(10,2)  NOT NULL DEFAULT 0,
  min_days      INT            DEFAULT 1,
  max_days      INT            DEFAULT 7,
  free_above    DECIMAL(10,2)  DEFAULT NULL,
  active        TINYINT(1)     DEFAULT 1,
  sort_order    INT            DEFAULT 0,
  created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_tracking (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  order_id    INT           NOT NULL,
  status      VARCHAR(80)   NOT NULL,
  note        VARCHAR(255),
  location    VARCHAR(120),
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS return_requests (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  order_id      INT          NOT NULL,
  user_id       INT          NOT NULL,
  reason        VARCHAR(200) NOT NULL,
  details       TEXT,
  status        VARCHAR(50)  DEFAULT 'pending',
  admin_note    TEXT,
  created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loyalty_points (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT           NOT NULL,
  points      INT           NOT NULL DEFAULT 0,
  event_type  VARCHAR(80)   NOT NULL,
  reference   VARCHAR(120),
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS store_settings (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  key_name    VARCHAR(100)  UNIQUE NOT NULL,
  value       TEXT,
  updated_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staff_roles (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(80)   NOT NULL,
  permissions TEXT,
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ─── New columns on existing tables (safe — ignore if present) ───

-- products
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand_id        INT          DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS compare_at_price DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS sku             VARCHAR(100) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured     TINYINT(1)   DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price      DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode         VARCHAR(100) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description TEXT DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS specifications  TEXT DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS weight          DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS length          DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS width           DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS height          DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INT DEFAULT 5;
ALTER TABLE products ADD COLUMN IF NOT EXISTS manage_stock    TINYINT(1) DEFAULT 1;
ALTER TABLE products ADD COLUMN IF NOT EXISTS status          VARCHAR(20) DEFAULT 'active';
ALTER TABLE products ADD COLUMN IF NOT EXISTS taxable         TINYINT(1) DEFAULT 1;
ALTER TABLE products ADD COLUMN IF NOT EXISTS tags            VARCHAR(255) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_title      VARCHAR(255) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_description TEXT DEFAULT NULL;

-- users
ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_role_id INT DEFAULT NULL;

-- orders
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_method_id INT          DEFAULT NULL;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS tracking_number    VARCHAR(100) DEFAULT NULL;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS shipping_address   TEXT         DEFAULT NULL;

-- ─── Default store settings ───────────────────────────────────────
INSERT IGNORE INTO store_settings (key_name, value) VALUES
  ('site_name',           'Flamingos'),
  ('site_tagline',        'Shop Smarter. Live Better.'),
  ('currency',            'NGN'),
  ('currency_symbol',     '₦'),
  ('free_shipping_above', '25000'),
  ('contact_email',       'support@flamingos.com'),
  ('contact_phone',       '+234 801 234 5678'),
  ('loyalty_points_rate', '1'),
  ('meta_description',    'Flamingos — Premium fashion at unbeatable prices.');

-- ─── Default shipping methods ─────────────────────────────────────
INSERT IGNORE INTO shipping_methods (name, description, price, min_days, max_days, free_above) VALUES
  ('Standard Delivery', 'Delivered in 3–5 business days', 1500.00, 3, 5, 25000.00),
  ('Express Delivery',  'Next-day delivery',              3500.00, 1, 2, NULL),
  ('Same-Day Delivery', '4 hours (Lagos only)',           5000.00, 0, 0, NULL),
  ('Store Pickup',      'Collect from our office',            0.00, 0, 1, NULL);

-- ─── Default staff roles ──────────────────────────────────────────
INSERT IGNORE INTO staff_roles (name, permissions) VALUES
  ('Super Admin',   '["all"]'),
  ('Store Manager', '["products","orders","users","reports"]'),
  ('Support Agent', '["orders","returns","customers"]'),
  ('Catalog Editor','["products","categories","brands"]');

-- ─── Default categories ───────────────────────────────────────────
INSERT IGNORE INTO categories (name, slug, sort_order) VALUES
  ('Men',         'men',         1),
  ('Women',       'women',       2),
  ('Kids',        'kids',        3),
  ('Accessories', 'accessories', 4),
  ('Footwear',    'footwear',    5),
  ('Sale',        'sale',        6);

-- ─── Default coupons ──────────────────────────────────────────────
INSERT IGNORE INTO coupons (code, discount_pct, max_uses, active) VALUES
  ('FLAMINGO10', 10.00, 1000, 1),
  ('SAVE20',     20.00,  500, 1),
  ('WELCOME15',  15.00,  250, 1);

-- ═══════════════════════════════════════════════════════════════════
-- Migration complete. All Flamingos tables are now ready.
-- ═══════════════════════════════════════════════════════════════════
