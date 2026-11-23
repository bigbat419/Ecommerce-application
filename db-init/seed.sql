-- ═══════════════════════════════════════════════════════════════════
-- FLAMINGOS ECOMMERCE PLATFORM — Full Database Schema + Seed Data
-- ═══════════════════════════════════════════════════════════════════

CREATE DATABASE IF NOT EXISTS flamingos_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE flamingos_db;

-- ─────────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(120)  NOT NULL,
  email      VARCHAR(255)  UNIQUE NOT NULL,
  password   VARCHAR(255)  NOT NULL,
  role       VARCHAR(50)   DEFAULT 'user',
  is_admin   TINYINT(1)    DEFAULT 0,
  created_at TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────────
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
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- CART ITEMS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS cart_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT  NOT NULL,
  product_id INT  NOT NULL,
  quantity   INT  DEFAULT 1,
  added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- ORDERS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS orders (
  id                  INT AUTO_INCREMENT PRIMARY KEY,
  user_id             INT           NOT NULL,
  total               DECIMAL(10,2) NOT NULL,
  status              VARCHAR(50)   DEFAULT 'pending',
  paystack_reference  VARCHAR(100)  DEFAULT NULL,
  created_at          TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- ORDER ITEMS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_items (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  order_id   INT           NOT NULL,
  product_id INT           NOT NULL,
  price      DECIMAL(10,2) NOT NULL,
  quantity   INT           NOT NULL,
  FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- ADDRESSES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS addresses (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT          NOT NULL,
  label      VARCHAR(100),
  line1      VARCHAR(255) NOT NULL,
  city       VARCHAR(100) NOT NULL,
  country    VARCHAR(100) NOT NULL,
  created_at TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- WISHLIST  (new — Flamingos)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS wishlist (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  user_id    INT NOT NULL,
  product_id INT NOT NULL,
  added_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uq_wish (user_id, product_id),
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- REVIEWS  (new — Flamingos)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS reviews (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT        NOT NULL,
  user_id    INT        NOT NULL,
  rating     TINYINT    NOT NULL DEFAULT 5,
  title      VARCHAR(160),
  body       TEXT,
  created_at TIMESTAMP  DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users(id)    ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- COUPONS  (new — Flamingos)
-- ─────────────────────────────────────────────
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

-- ═══════════════════════════════════════════════════════════════════
-- SEED DATA
-- ═══════════════════════════════════════════════════════════════════

-- ── Admin user (password: Admin@1234 — bcrypt hash placeholder)
-- Replace the hash below with a real bcrypt hash generated at startup.
-- The set_admin.py script handles this automatically via ADMIN_PASSWORD env var.
INSERT IGNORE INTO users (name, email, password, role, is_admin)
VALUES ('Flamingos Admin', 'admin@flamingos.com',
        '$2b$12$PLACEHOLDER_REPLACE_WITH_REAL_BCRYPT_HASH', 'admin', 1);

-- ── Sample customers
INSERT IGNORE INTO users (name, email, password, role, is_admin)
VALUES
  ('Amara Okonkwo',  'amara@example.com',  '$2b$12$PLACEHOLDER', 'user', 0),
  ('Chidi Ezenwachi', 'chidi@example.com', '$2b$12$PLACEHOLDER', 'user', 0),
  ('Ngozi Adeyemi',  'ngozi@example.com',  '$2b$12$PLACEHOLDER', 'user', 0);

-- ── Sample products — Women
INSERT IGNORE INTO products (name, slug, category, description, price, stock)
VALUES
  ('Flamingos Floral Wrap Dress',
   'flamingos-floral-wrap-dress', 'Women',
   'A stunning floral wrap dress crafted from lightweight chiffon. Perfect for brunch, garden parties, or a casual day out. Available in vibrant coral and soft ivory.',
   18500.00, 42),

  ('Classic High-Waist Trousers',
   'classic-high-waist-trousers', 'Women',
   'Tailored high-waist trousers in a premium stretch-woven fabric. The wide-leg silhouette elongates the figure and pairs beautifully with both crop tops and tucked blouses.',
   15200.00, 28),

  ('Off-Shoulder Ruffle Blouse',
   'off-shoulder-ruffle-blouse', 'Women',
   'An elegant off-shoulder blouse with delicate ruffles at the neckline. Made from 100% cotton voile, it is breathable and effortlessly chic.',
   9800.00, 55),

  ('Linen Co-ord Set',
   'linen-co-ord-set', 'Women',
   'A matching linen blazer and straight-leg trouser set in natural linen. Breathable, sustainable, and infinitely versatile — dress it up or down.',
   32000.00, 15);

-- ── Sample products — Men
INSERT IGNORE INTO products (name, slug, category, description, price, stock)
VALUES
  ('Premium Slim-Fit Oxford Shirt',
   'premium-slim-fit-oxford-shirt', 'Men',
   'A timeless slim-fit Oxford shirt woven from 100% combed cotton. Soft-washed for comfort, perfect for business casual or smart-casual styling.',
   12500.00, 60),

  ('Heritage Chino Trousers',
   'heritage-chino-trousers', 'Men',
   'Classic straight-cut chinos in a durable twill fabric. Features two front pockets, two back patch pockets, and a comfortable mid-rise waistband.',
   14000.00, 38),

  ('Relaxed Linen Shirt',
   'relaxed-linen-shirt', 'Men',
   'An easy-going linen shirt with a relaxed fit and camp collar. Ideal for warm-weather weekends and tropical getaways.',
   10500.00, 47),

  ('Technical Stretch Joggers',
   'technical-stretch-joggers', 'Men',
   'Modern tapered joggers crafted from a 4-way stretch performance fabric. Moisture-wicking, quick-dry, and stylish enough for athleisure wear.',
   16000.00, 33);

-- ── Sample products — Accessories
INSERT IGNORE INTO products (name, slug, category, description, price, stock)
VALUES
  ('Leather Crossbody Bag',
   'leather-crossbody-bag', 'Accessories',
   'A compact crossbody bag in full-grain vegan leather. Features a main zip compartment, interior card slots, and an adjustable strap.',
   27500.00, 20),

  ('Woven Straw Hat',
   'woven-straw-hat', 'Accessories',
   'A wide-brim straw hat with a grosgrain ribbon trim. Handwoven from natural raffia for superior UV protection and effortless beach style.',
   8500.00, 65),

  ('Silk Scarf — Flamingo Print',
   'silk-scarf-flamingo-print', 'Accessories',
   'Our signature 100% silk twill scarf featuring an exclusive flamingo-and-botanical print. Wear it as a hair wrap, neck scarf, or bag accessory.',
   13500.00, 50);

-- ── Sample products — Footwear
INSERT IGNORE INTO products (name, slug, category, description, price, stock)
VALUES
  ('Block Heel Mules',
   'block-heel-mules', 'Footwear',
   'Sophisticated block-heel mules in supple vegan suede. A 6 cm heel provides height without sacrificing comfort. Available in nude, black, and terracotta.',
   22000.00, 25),

  ('Canvas Low-Top Sneakers',
   'canvas-low-top-sneakers', 'Footwear',
   'Clean, minimal canvas sneakers with a vulcanised rubber sole. A wardrobe essential that pairs with absolutely everything.',
   11000.00, 70),

  ('Artisan Leather Sandals',
   'artisan-leather-sandals', 'Footwear',
   'Handcrafted flat sandals with woven leather straps and a padded footbed. Inspired by Mediterranean craftsmanship, made for all-day wear.',
   19500.00, 30);

-- ── Sample kids product
INSERT IGNORE INTO products (name, slug, category, description, price, stock)
VALUES
  ('Mini Me Ruffle Dress',
   'mini-me-ruffle-dress', 'Kids',
   'An adorable ruffled mini dress for little ones. Soft cotton fabric, easy-on snap buttons, and a joyful floral print.',
   7500.00, 80);

-- ── Launch coupons
INSERT IGNORE INTO coupons (code, discount_pct, max_uses, active)
VALUES
  ('FLAMINGO10', 10.00, 1000, 1),
  ('SAVE20',     20.00, 500,  1),
  ('WELCOME15',  15.00, 250,  1);

-- ── Sample address for demo user
INSERT IGNORE INTO addresses (user_id, label, line1, city, country)
SELECT u.id, 'Home', '14 Admiralty Way', 'Lagos', 'Nigeria'
FROM users u WHERE u.email = 'amara@example.com' LIMIT 1;

-- ═══════════════════════════════════════════════════════════════════
-- FLAMINGOS — Extended Schema (Phase 2)
-- ═══════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────
-- BRANDS
-- ─────────────────────────────────────────────
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

-- ─────────────────────────────────────────────
-- CATEGORIES (standalone — not just VARCHAR on products)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS categories (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(120)  NOT NULL,
  slug        VARCHAR(120)  UNIQUE NOT NULL,
  parent_id   INT           DEFAULT NULL,
  description TEXT,
  image       VARCHAR(255),
  active      TINYINT(1)    DEFAULT 1,
  sort_order  INT           DEFAULT 0,
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
);

-- ─────────────────────────────────────────────
-- Add brand_id to products
-- ─────────────────────────────────────────────
ALTER TABLE products ADD COLUMN IF NOT EXISTS brand_id INT DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS compare_at_price DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS sku VARCHAR(100) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS weight DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_featured TINYINT(1) DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS cost_price DECIMAL(10,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS barcode VARCHAR(100) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS short_description TEXT DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS specifications TEXT DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS length DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS width DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS height DECIMAL(8,2) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INT DEFAULT 5;
ALTER TABLE products ADD COLUMN IF NOT EXISTS manage_stock TINYINT(1) DEFAULT 1;
ALTER TABLE products ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'active';
ALTER TABLE products ADD COLUMN IF NOT EXISTS taxable TINYINT(1) DEFAULT 1;
ALTER TABLE products ADD COLUMN IF NOT EXISTS tags VARCHAR(255) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_title VARCHAR(255) DEFAULT NULL;
ALTER TABLE products ADD COLUMN IF NOT EXISTS meta_description TEXT DEFAULT NULL;

-- ─────────────────────────────────────────────
-- SHIPPING METHODS
-- ─────────────────────────────────────────────
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

-- ─────────────────────────────────────────────
-- ORDER TRACKING EVENTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS order_tracking (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  order_id    INT           NOT NULL,
  status      VARCHAR(80)   NOT NULL,
  note        VARCHAR(255),
  location    VARCHAR(120),
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- RETURN REQUESTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS return_requests (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  order_id      INT          NOT NULL,
  user_id       INT          NOT NULL,
  reason        VARCHAR(200) NOT NULL,
  details       TEXT,
  status        VARCHAR(50)  DEFAULT 'pending',
  admin_note    TEXT,
  created_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
  updated_at    TIMESTAMP    DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)  REFERENCES users(id)  ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- LOYALTY POINTS
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS loyalty_points (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  user_id     INT           NOT NULL,
  points      INT           NOT NULL DEFAULT 0,
  event_type  VARCHAR(80)   NOT NULL,
  reference   VARCHAR(120),
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────
-- STORE SETTINGS  (key-value store)
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS store_settings (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  key_name    VARCHAR(100)  UNIQUE NOT NULL,
  value       TEXT,
  updated_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ─────────────────────────────────────────────
-- STAFF ROLES
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS staff_roles (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  name        VARCHAR(80)   NOT NULL,
  permissions TEXT,
  created_at  TIMESTAMP     DEFAULT CURRENT_TIMESTAMP
);

-- Add role_id to users
ALTER TABLE users ADD COLUMN IF NOT EXISTS staff_role_id INT DEFAULT NULL;

-- ─────────────────────────────────────────────
-- SEED: Default store settings
-- ─────────────────────────────────────────────
INSERT IGNORE INTO store_settings (key_name, value) VALUES
  ('site_name',           'Flamingos'),
  ('site_tagline',        'Shop Smarter. Live Better.'),
  ('currency',            'NGN'),
  ('currency_symbol',     '₦'),
  ('free_shipping_above', '25000'),
  ('contact_email',       'support@flamingos.com'),
  ('contact_phone',       '+234 801 234 5678'),
  ('address',             'Lagos, Nigeria'),
  ('loyalty_points_rate', '1'),
  ('meta_description',    'Flamingos — Premium fashion and lifestyle products at unbeatable prices.');

-- SEED: Default shipping methods
INSERT IGNORE INTO shipping_methods (name, description, price, min_days, max_days, free_above) VALUES
  ('Standard Delivery',  'Delivered in 3-5 business days',       1500.00, 3, 5, 25000.00),
  ('Express Delivery',   'Next-day delivery',                    3500.00, 1, 2, NULL),
  ('Same-Day Delivery',  'Delivered within 4 hours (Lagos only)', 5000.00, 0, 0, NULL),
  ('Pickup',             'Collect from our Lagos office',            0.00, 0, 1, NULL);

-- SEED: Default staff roles
INSERT IGNORE INTO staff_roles (name, permissions) VALUES
  ('Super Admin',   '["all"]'),
  ('Store Manager', '["products","orders","users","reports"]'),
  ('Support Agent', '["orders","returns","customers"]'),
  ('Catalog Editor','["products","categories","brands"]');

-- SEED: Sample brands
INSERT IGNORE INTO brands (name, slug, description) VALUES
  ('Flamingos Originals', 'flamingos-originals', 'Our exclusive in-house label'),
  ('UrbanThread',         'urbanthread',          'Contemporary streetwear'),
  ('LuxWear',             'luxwear',              'Premium luxury fashion'),
  ('ActiveFit',           'activefit',            'Performance sportswear');

-- SEED: Default categories
INSERT IGNORE INTO categories (name, slug, sort_order) VALUES
  ('Men',         'men',         1),
  ('Women',       'women',       2),
  ('Kids',        'kids',        3),
  ('Accessories', 'accessories', 4),
  ('Footwear',    'footwear',    5),
  ('Sale',        'sale',        6);
