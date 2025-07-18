-- Costco Database Schema
-- This schema stores scraped data from Costco.ca including categories, products, and relationships

-- Drop tables if they exist (for development)
DROP TABLE IF EXISTS category_products;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS scraping_sessions;

-- Scraping sessions to track when data was collected
CREATE TABLE scraping_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    status TEXT DEFAULT 'running', -- running, completed, failed
    total_categories INTEGER DEFAULT 0,
    total_products INTEGER DEFAULT 0,
    ai_enabled BOOLEAN DEFAULT TRUE,
    metadata JSON, -- Store additional session info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Categories table based on our standardized CategoryInterface
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    category_type TEXT NOT NULL, -- leaf_product, leaf_service, etc.
    description TEXT,
    parent_category_id INTEGER NULL,
    is_leaf BOOLEAN NOT NULL DEFAULT FALSE,
    level INTEGER DEFAULT 0, -- Hierarchy level (0 = root)
    path TEXT, -- Full category path like "Electronics/Computers/Laptops"
    metadata JSON, -- Store additional category-specific data
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (parent_category_id) REFERENCES categories(id),
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(session_id),
    UNIQUE(session_id, name, url) -- Prevent duplicates within session
);

-- Products table for actual Costco products
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    name TEXT NOT NULL,
    item_number TEXT, -- Costco item number
    price DECIMAL(10,2),
    original_price DECIMAL(10,2), -- For sale items
    currency TEXT DEFAULT 'CAD',
    description TEXT,
    brand TEXT,
    model TEXT,
    availability TEXT, -- in_stock, out_of_stock, limited, etc.
    rating DECIMAL(2,1), -- Product rating (1.0-5.0)
    review_count INTEGER DEFAULT 0,
    image_url TEXT,
    product_url TEXT,
    warehouse_only BOOLEAN DEFAULT FALSE,
    online_only BOOLEAN DEFAULT FALSE,
    member_exclusive BOOLEAN DEFAULT FALSE,
    metadata JSON, -- Store additional product data
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (session_id) REFERENCES scraping_sessions(session_id),
    UNIQUE(session_id, item_number) -- Prevent duplicate products per session
);

-- Many-to-many relationship between categories and products
CREATE TABLE category_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    position INTEGER, -- Position of product within category
    featured BOOLEAN DEFAULT FALSE, -- Is this a featured product in the category
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
    UNIQUE(category_id, product_id) -- Prevent duplicate relationships
);

-- Indexes for better query performance
CREATE INDEX idx_categories_session_id ON categories(session_id);
CREATE INDEX idx_categories_parent_id ON categories(parent_category_id);
CREATE INDEX idx_categories_type ON categories(category_type);
CREATE INDEX idx_categories_path ON categories(path);

CREATE INDEX idx_products_session_id ON products(session_id);
CREATE INDEX idx_products_item_number ON products(item_number);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_brand ON products(brand);

CREATE INDEX idx_category_products_category ON category_products(category_id);
CREATE INDEX idx_category_products_product ON category_products(product_id);

CREATE INDEX idx_sessions_status ON scraping_sessions(status);
CREATE INDEX idx_sessions_start_time ON scraping_sessions(start_time);

-- Views for common queries
CREATE VIEW category_hierarchy AS
WITH RECURSIVE category_tree AS (
    -- Base case: root categories
    SELECT 
        id,
        session_id,
        name,
        url,
        category_type,
        parent_category_id,
        is_leaf,
        level,
        name as path,
        CAST(id AS TEXT) as id_path
    FROM categories 
    WHERE parent_category_id IS NULL
    
    UNION ALL
    
    -- Recursive case: child categories
    SELECT 
        c.id,
        c.session_id,
        c.name,
        c.url,
        c.category_type,
        c.parent_category_id,
        c.is_leaf,
        c.level,
        ct.path || ' > ' || c.name as path,
        ct.id_path || ',' || CAST(c.id AS TEXT) as id_path
    FROM categories c
    JOIN category_tree ct ON c.parent_category_id = ct.id
)
SELECT * FROM category_tree;

-- View for product counts per category
CREATE VIEW category_product_counts AS
SELECT 
    c.id as category_id,
    c.session_id,
    c.name as category_name,
    c.category_type,
    c.is_leaf,
    COUNT(cp.product_id) as product_count,
    COUNT(CASE WHEN cp.featured = TRUE THEN 1 END) as featured_count
FROM categories c
LEFT JOIN category_products cp ON c.id = cp.category_id
GROUP BY c.id, c.session_id, c.name, c.category_type, c.is_leaf;

-- View for session statistics
CREATE VIEW session_stats AS
SELECT 
    s.session_id,
    s.start_time,
    s.end_time,
    s.status,
    s.ai_enabled,
    COUNT(DISTINCT c.id) as categories_found,
    COUNT(DISTINCT p.id) as products_found,
    COUNT(DISTINCT CASE WHEN c.is_leaf = TRUE THEN c.id END) as leaf_categories,
    COUNT(DISTINCT CASE WHEN c.is_leaf = FALSE THEN c.id END) as navigation_categories,
    AVG(p.price) as avg_product_price,
    MIN(p.price) as min_product_price,
    MAX(p.price) as max_product_price
FROM scraping_sessions s
LEFT JOIN categories c ON s.session_id = c.session_id
LEFT JOIN products p ON s.session_id = p.session_id
GROUP BY s.session_id, s.start_time, s.end_time, s.status, s.ai_enabled;
