"""
analyze_with_polars.py

Data transformation and statistical analysis using Polars.

Performs:
    - Data aggregation and joining
    - Revenue analysis by state
    - Customer behavior metrics
    - Linear regression: Review score vs Delivery time
    - Product category performance analysis

Features:
    - Fast DataFrame operations with Polars
    - Statistical insights with scipy
    - Regression analysis
    - Export transformed data
"""

import os
import polars as pl
import psycopg2
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from scipy import stats

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': int(os.getenv('DB_PORT', 22446)),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'sslmode': 'require'
}


def get_connection():
    """Create PostgreSQL connection."""
    return psycopg2.connect(**DB_CONFIG)


def load_table_to_polars(table_name):
    """Load PostgreSQL table into Polars DataFrame."""
    conn = get_connection()
    query = f"SELECT * FROM {table_name}"
    
    with conn.cursor() as cur:
        cur.execute(query)
        columns = [desc[0] for desc in cur.description]
        data = cur.fetchall()
    
    conn.close()
    
    # Create Polars DataFrame
    df = pl.DataFrame(data, schema=columns, orient='row')
    print(f"✓ Loaded {len(df):,} rows from {table_name}")
    return df


def analyze_revenue_by_state():
    """
    Analysis 1: Revenue analysis by customer state.
    
    Joins: orders + order_items + order_payments + customers
    Aggregates: Total revenue, order count, avg order value by state
    """
    print("\n" + "="*70)
    print("ANALYSIS 1: Revenue by State")
    print("="*70)
    
    # Load tables
    orders = load_table_to_polars('orders_raw')
    order_items = load_table_to_polars('order_items_raw')
    payments = load_table_to_polars('order_payments_raw')
    customers = load_table_to_polars('customers_raw')
    
    # Join tables
    df = (
        orders
        .join(customers, on='customer_id', how='left')
        .join(order_items, on='order_id', how='left')
        .join(payments, on='order_id', how='left')
    )
    
    # Aggregate by state
    state_revenue = (
        df
        .group_by('customer_state')
        .agg([
            pl.col('payment_value').sum().alias('total_revenue'),
            pl.col('order_id').n_unique().alias('order_count'),
            pl.col('payment_value').mean().alias('avg_order_value')
        ])
        .sort('total_revenue', descending=True)
    )
    
    print("\nTop 10 States by Revenue:")
    print(state_revenue.head(10))
    
    # Statistical insights
    print(f"\nRevenue Statistics:")
    print(f"  Total Revenue: R$ {state_revenue['total_revenue'].sum():,.2f}")
    print(f"  Avg Revenue per State: R$ {state_revenue['total_revenue'].mean():,.2f}")
    print(f"  Std Dev: R$ {state_revenue['total_revenue'].std():,.2f}")
    
    return state_revenue


def analyze_delivery_performance():
    """
    Analysis 2: Delivery performance vs Review scores.
    
    Calculates:
        - Delivery time (days)
        - Correlation with review scores
        - Linear regression
    """
    print("\n" + "="*70)
    print("ANALYSIS 2: Delivery Performance & Reviews (Regression)")
    print("="*70)
    
    # Load tables
    orders = load_table_to_polars('orders_raw')
    reviews = load_table_to_polars('order_reviews_raw')
    
    # Join and calculate delivery time
    df = (
        orders
        .join(reviews, on='order_id', how='inner')
        .filter(
            (pl.col('order_delivered_customer_date').is_not_null()) &
            (pl.col('order_purchase_timestamp').is_not_null()) &
            (pl.col('review_score').is_not_null())
        )
        .with_columns([
            # Calculate delivery time in days
            (
                (pl.col('order_delivered_customer_date').cast(pl.Datetime) - 
                 pl.col('order_purchase_timestamp').cast(pl.Datetime))
                .dt.total_days()
            ).alias('delivery_days')
        ])
        .filter(pl.col('delivery_days') > 0)  # Remove invalid data
    )
    
    print(f"\n✓ Analyzed {len(df):,} orders with complete data")
    
    # Convert to numpy for regression
    delivery_days = df['delivery_days'].to_numpy()
    review_scores = df['review_score'].to_numpy()
    
    # Linear Regression: review_score = β0 + β1 * delivery_days
    slope, intercept, r_value, p_value, std_err = stats.linregress(delivery_days, review_scores)
    
    print(f"\n📊 REGRESSION ANALYSIS:")
    print(f"   Model: review_score = {intercept:.4f} + ({slope:.4f}) * delivery_days")
    print(f"   R-squared: {r_value**2:.4f}")
    print(f"   P-value: {p_value:.4e}")
    print(f"   Standard Error: {std_err:.4f}")
    print(f"   Correlation: {r_value:.4f}")
    
    if p_value < 0.05:
        print(f"\n✓ SIGNIFICANT: Delivery time significantly impacts review scores (p < 0.05)")
    else:
        print(f"\n⚠ NOT SIGNIFICANT: No significant relationship (p >= 0.05)")
    
    # Interpretation
    print(f"\n📈 INTERPRETATION:")
    print(f"   - For each additional day of delivery, review score changes by {slope:.4f} points")
    print(f"   - {abs(r_value**2)*100:.2f}% of review score variation explained by delivery time")
    
    # Aggregate stats
    delivery_stats = (
        df
        .group_by(pl.col('delivery_days').cast(pl.Int32))
        .agg([
            pl.col('review_score').mean().alias('avg_review'),
            pl.col('review_score').count().alias('order_count')
        ])
        .sort('delivery_days')
    )
    
    print(f"\nDelivery Time vs Avg Review Score (first 10 days):")
    print(delivery_stats.head(10))
    
    return df, slope, intercept, r_value**2


def analyze_product_categories():
    """
    Analysis 3: Product category performance.
    
    Metrics:
        - Sales volume by category
        - Average price by category
        - Review scores by category
    """
    print("\n" + "="*70)
    print("ANALYSIS 3: Product Category Performance")
    print("="*70)
    
    # Load tables
    order_items = load_table_to_polars('order_items_raw')
    products = load_table_to_polars('products_raw')
    reviews = load_table_to_polars('order_reviews_raw')
    translations = load_table_to_polars('product_category_name_translation_raw')
    
    # Join tables
    df = (
        order_items
        .join(products, on='product_id', how='left')
        .join(translations, on='product_category_name', how='left')
        .join(reviews, on='order_id', how='left')
    )
    
    # Aggregate by category
    category_stats = (
        df
        .group_by('product_category_name_english')
        .agg([
            pl.col('order_item_id').count().alias('items_sold'),
            pl.col('price').sum().alias('total_revenue'),
            pl.col('price').mean().alias('avg_price'),
            pl.col('review_score').mean().alias('avg_review')
        ])
        .sort('total_revenue', descending=True)
        .filter(pl.col('product_category_name_english').is_not_null())
    )
    
    print("\nTop 15 Product Categories:")
    print(category_stats.head(15))
    
    # Best rated categories (with sufficient data)
    best_rated = (
        category_stats
        .filter(pl.col('items_sold') >= 100)  # At least 100 sales
        .sort('avg_review', descending=True)
    )
    
    print("\n⭐ Top 10 Best Rated Categories (min 100 sales):")
    print(best_rated.head(10))
    
    return category_stats


def export_transformed_data(df, filename):
    """Export transformed data to CSV."""
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, filename)
    df.write_csv(output_path)
    print(f"\n✓ Exported to: {output_path}")


def main():
    """Run all analyses."""
    print("\n" + "="*70)
    print("POLARS DATA TRANSFORMATION & STATISTICAL ANALYSIS")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Analysis 1: Revenue by state
        state_revenue = analyze_revenue_by_state()
        export_transformed_data(state_revenue, 'revenue_by_state.csv')
        
        # Analysis 2: Delivery performance (REGRESSION)
        delivery_df, slope, intercept, r2 = analyze_delivery_performance()
        
        # Analysis 3: Product categories
        category_stats = analyze_product_categories()
        export_transformed_data(category_stats, 'category_performance.csv')
        
        # Summary
        print("\n" + "="*70)
        print("ANALYSIS COMPLETE")
        print("="*70)
        print(f"✓ Revenue analysis exported")
        print(f"✓ Regression model: R² = {r2:.4f}, β₁ = {slope:.4f}")
        print(f"✓ Category analysis exported")
        print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        raise


if __name__ == "__main__":
    main()
