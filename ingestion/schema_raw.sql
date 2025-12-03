
-- 1. olist_customers_dataset.csv
CREATE TABLE IF NOT EXISTS customers_raw (
    customer_id              VARCHAR(50) PRIMARY KEY,
    customer_unique_id       VARCHAR(50),
    customer_zip_code_prefix INTEGER,
    customer_city            VARCHAR(100),
    customer_state           VARCHAR(2)
);

-- 2. olist_geolocation_dataset.csv
CREATE TABLE IF NOT EXISTS geolocation_raw (
    geolocation_zip_code_prefix INTEGER,
    geolocation_lat             DOUBLE PRECISION,
    geolocation_lng             DOUBLE PRECISION,
    geolocation_city            VARCHAR(100),
    geolocation_state           VARCHAR(2)
);

-- 3. olist_sellers_dataset.csv
CREATE TABLE IF NOT EXISTS sellers_raw (
    seller_id              VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city            VARCHAR(100),
    seller_state           VARCHAR(2)
);

-- 4. olist_products_dataset.csv
CREATE TABLE IF NOT EXISTS products_raw (
    product_id                  VARCHAR(50) PRIMARY KEY,
    product_category_name       VARCHAR(100),
    product_name_lenght         DOUBLE PRECISION,
    product_description_lenght  DOUBLE PRECISION,
    product_photos_qty          DOUBLE PRECISION,
    product_weight_g            DOUBLE PRECISION,
    product_length_cm           DOUBLE PRECISION,
    product_height_cm           DOUBLE PRECISION,
    product_width_cm            DOUBLE PRECISION
);

-- 5. product_category_name_translation.csv
CREATE TABLE IF NOT EXISTS product_category_name_translation_raw (
    product_category_name         VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100)
);

-- 6. olist_orders_dataset.csv
CREATE TABLE IF NOT EXISTS orders_raw (
    order_id                     VARCHAR(50) PRIMARY KEY,
    customer_id                  VARCHAR(50),
    order_status                 VARCHAR(20),
    order_purchase_timestamp     TIMESTAMP,
    order_approved_at            TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

ALTER TABLE orders_raw
ADD CONSTRAINT fk_orders_customer
FOREIGN KEY (customer_id)
REFERENCES customers_raw (customer_id);

-- 7. olist_order_items_dataset.csv
CREATE TABLE IF NOT EXISTS order_items_raw (
    order_id           VARCHAR(50),
    order_item_id      INTEGER,
    product_id         VARCHAR(50),
    seller_id          VARCHAR(50),
    shipping_limit_date TIMESTAMP,
    price              DOUBLE PRECISION,
    freight_value      DOUBLE PRECISION,
    CONSTRAINT pk_order_items PRIMARY KEY (order_id, order_item_id)
);

ALTER TABLE order_items_raw
ADD CONSTRAINT fk_items_order
FOREIGN KEY (order_id)
REFERENCES orders_raw (order_id);

ALTER TABLE order_items_raw
ADD CONSTRAINT fk_items_product
FOREIGN KEY (product_id)
REFERENCES products_raw (product_id);

ALTER TABLE order_items_raw
ADD CONSTRAINT fk_items_seller
FOREIGN KEY (seller_id)
REFERENCES sellers_raw (seller_id);

-- 8. olist_order_payments_dataset.csv
CREATE TABLE IF NOT EXISTS order_payments_raw (
    order_id            VARCHAR(50),
    payment_sequential  INTEGER,
    payment_type        VARCHAR(30),
    payment_installments INTEGER,
    payment_value       DOUBLE PRECISION,
    CONSTRAINT pk_order_payments PRIMARY KEY (order_id, payment_sequential)
);

ALTER TABLE order_payments_raw
ADD CONSTRAINT fk_payments_order
FOREIGN KEY (order_id)
REFERENCES orders_raw (order_id);

-- 9. olist_order_reviews_dataset.csv
CREATE TABLE IF NOT EXISTS order_reviews_raw (
    review_id               VARCHAR(50) PRIMARY KEY,
    order_id                VARCHAR(50),
    review_score            INTEGER,
    review_comment_title    TEXT,
    review_comment_message  TEXT,
    review_creation_date    TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

ALTER TABLE order_reviews_raw
ADD CONSTRAINT fk_reviews_order
FOREIGN KEY (order_id)
REFERENCES orders_raw (order_id);
