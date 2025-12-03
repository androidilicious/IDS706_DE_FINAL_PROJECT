-- ============================================
-- Olist E-Commerce Business Intelligence Queries
-- ============================================

-- Query 1: Monthly Revenue Trend
-- Shows revenue growth over time
SELECT 
    DATE_TRUNC('month', order_purchase_timestamp) AS month,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(p.payment_value) AS total_revenue,
    AVG(p.payment_value) AS avg_order_value,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM orders_raw o
JOIN order_payments_raw p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY month
ORDER BY month;

-- Query 2: Top 10 Sellers by Revenue
-- Identify best performing sellers
SELECT 
    s.seller_id,
    s.seller_city,
    s.seller_state,
    COUNT(DISTINCT oi.order_id) AS orders_fulfilled,
    SUM(oi.price) AS total_revenue,
    AVG(oi.price) AS avg_item_price,
    AVG(r.review_score) AS avg_review_score
FROM sellers_raw s
JOIN order_items_raw oi ON s.seller_id = oi.seller_id
LEFT JOIN order_reviews_raw r ON oi.order_id = r.order_id
GROUP BY s.seller_id, s.seller_city, s.seller_state
ORDER BY total_revenue DESC
LIMIT 10;

-- Query 3: Customer Satisfaction by Product Category
-- Which categories have best/worst reviews?
SELECT 
    t.product_category_name_english AS category,
    COUNT(DISTINCT oi.order_id) AS total_orders,
    AVG(r.review_score) AS avg_review_score,
    SUM(oi.price) AS total_revenue,
    AVG(oi.price) AS avg_price
FROM order_items_raw oi
JOIN products_raw p ON oi.product_id = p.product_id
LEFT JOIN product_category_name_translation_raw t ON p.product_category_name = t.product_category_name
LEFT JOIN order_reviews_raw r ON oi.order_id = r.order_id
WHERE t.product_category_name_english IS NOT NULL
GROUP BY t.product_category_name_english
HAVING COUNT(DISTINCT oi.order_id) >= 100  -- At least 100 orders
ORDER BY avg_review_score DESC;

-- Query 4: Delivery Performance Analysis
-- Average delivery time by state
SELECT 
    c.customer_state,
    COUNT(o.order_id) AS total_orders,
    AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400) AS avg_delivery_days,
    AVG(EXTRACT(EPOCH FROM (o.order_estimated_delivery_date - o.order_delivered_customer_date))/86400) AS avg_early_delivery_days,
    AVG(r.review_score) AS avg_review_score
FROM orders_raw o
JOIN customers_raw c ON o.customer_id = c.customer_id
LEFT JOIN order_reviews_raw r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
  AND o.order_status = 'delivered'
GROUP BY c.customer_state
ORDER BY avg_delivery_days;

-- Query 5: Payment Method Analysis
-- Which payment methods are most popular and their average values?
SELECT 
    payment_type,
    COUNT(*) AS transaction_count,
    SUM(payment_value) AS total_value,
    AVG(payment_value) AS avg_value,
    AVG(payment_installments) AS avg_installments
FROM order_payments_raw
GROUP BY payment_type
ORDER BY transaction_count DESC;

-- Query 6: Customer Repeat Purchase Rate
-- How many customers make multiple purchases?
SELECT 
    order_count,
    COUNT(*) AS customer_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) AS percentage
FROM (
    SELECT customer_id, COUNT(DISTINCT order_id) AS order_count
    FROM orders_raw
    GROUP BY customer_id
) customer_orders
GROUP BY order_count
ORDER BY order_count;

-- Query 7: Late Delivery Impact on Reviews
-- Do late deliveries correlate with lower review scores?
SELECT 
    CASE 
        WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
        WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Late'
        ELSE 'Unknown'
    END AS delivery_status,
    COUNT(o.order_id) AS order_count,
    AVG(r.review_score) AS avg_review_score,
    STDDEV(r.review_score) AS review_score_stddev
FROM orders_raw o
LEFT JOIN order_reviews_raw r ON o.order_id = r.order_id
WHERE o.order_delivered_customer_date IS NOT NULL
  AND o.order_estimated_delivery_date IS NOT NULL
  AND r.review_score IS NOT NULL
GROUP BY delivery_status;

-- Query 8: Top Product Combinations (Frequently Bought Together)
-- Products often purchased in the same order
SELECT 
    p1.product_category_name AS category_1,
    p2.product_category_name AS category_2,
    COUNT(*) AS times_bought_together
FROM order_items_raw oi1
JOIN order_items_raw oi2 ON oi1.order_id = oi2.order_id AND oi1.order_item_id < oi2.order_item_id
JOIN products_raw p1 ON oi1.product_id = p1.product_id
JOIN products_raw p2 ON oi2.product_id = p2.product_id
WHERE p1.product_category_name IS NOT NULL 
  AND p2.product_category_name IS NOT NULL
GROUP BY category_1, category_2
ORDER BY times_bought_together DESC
LIMIT 20;

-- Query 9: Geographic Sales Distribution
-- Which regions generate most revenue?
SELECT 
    c.customer_state,
    c.customer_city,
    COUNT(DISTINCT o.order_id) AS total_orders,
    SUM(p.payment_value) AS total_revenue,
    AVG(p.payment_value) AS avg_order_value,
    COUNT(DISTINCT o.customer_id) AS unique_customers
FROM customers_raw c
JOIN orders_raw o ON c.customer_id = o.customer_id
JOIN order_payments_raw p ON o.order_id = p.order_id
WHERE o.order_status = 'delivered'
GROUP BY c.customer_state, c.customer_city
HAVING COUNT(DISTINCT o.order_id) >= 10
ORDER BY total_revenue DESC
LIMIT 20;

-- Query 10: Product Size & Weight Impact on Price
-- Correlation between product dimensions and pricing
SELECT 
    CASE 
        WHEN product_weight_g < 500 THEN 'Light (< 500g)'
        WHEN product_weight_g < 2000 THEN 'Medium (500g-2kg)'
        WHEN product_weight_g < 5000 THEN 'Heavy (2kg-5kg)'
        ELSE 'Very Heavy (> 5kg)'
    END AS weight_category,
    COUNT(*) AS product_count,
    AVG(oi.price) AS avg_price,
    AVG(oi.freight_value) AS avg_freight
FROM products_raw p
JOIN order_items_raw oi ON p.product_id = oi.product_id
WHERE p.product_weight_g IS NOT NULL
GROUP BY weight_category
ORDER BY avg_price DESC;
