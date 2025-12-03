"""
app.py

Streamlit Dashboard for Olist E-Commerce Analytics

Interactive web application displaying:
    - Revenue metrics and trends
    - Geographic sales distribution
    - Product category performance
    - Delivery performance insights
    - Regression analysis visualization
    - Real-time data quality metrics

Features:
    - Multi-page navigation
    - Interactive charts with Plotly
    - Real-time database queries
    - Export functionality
    - Responsive design

Run:
    streamlit run dashboard/app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime
import numpy as np
from scipy import stats

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Olist E-Commerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_connection():
    """Create cached database connection."""
    return psycopg2.connect(
        host=os.getenv('DB_HOST'),
        port=int(os.getenv('DB_PORT', 22446)),
        dbname=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        sslmode='require'
    )

@st.cache_data(ttl=600)  # Cache for 10 minutes
def run_query(query):
    """Execute SQL query and return DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(query, conn)
    return df

# Sidebar
st.sidebar.title("🛒 Olist Analytics")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["📈 Overview", "🌍 Geographic Analysis", "📦 Product Insights", 
     "🚚 Delivery Performance", "📊 Statistical Analysis", "✅ Data Quality"]
)

st.sidebar.markdown("---")
st.sidebar.info("""
**Data Source**: Brazilian E-Commerce  
**Period**: 2016-2018  
**Records**: 1.5M+ rows  
**Last Updated**: Real-time
""")

# ===== PAGE 1: OVERVIEW =====
if page == "📈 Overview":
    st.title("📈 Olist E-Commerce Dashboard")
    st.markdown("### Key Performance Indicators")
    
    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Orders
    total_orders = run_query("SELECT COUNT(DISTINCT order_id) FROM orders_raw WHERE order_status = 'delivered'")
    col1.metric("Total Orders", f"{total_orders.iloc[0, 0]:,}")
    
    # Total Revenue
    total_revenue = run_query("SELECT SUM(payment_value) FROM order_payments_raw")
    col2.metric("Total Revenue", f"R$ {total_revenue.iloc[0, 0]:,.2f}")
    
    # Avg Order Value
    avg_order = run_query("SELECT AVG(payment_value) FROM order_payments_raw")
    col3.metric("Avg Order Value", f"R$ {avg_order.iloc[0, 0]:,.2f}")
    
    # Unique Customers
    unique_customers = run_query("SELECT COUNT(DISTINCT customer_id) FROM customers_raw")
    col4.metric("Unique Customers", f"{unique_customers.iloc[0, 0]:,}")
    
    st.markdown("---")
    
    # Monthly Revenue Trend
    st.subheader("📅 Monthly Revenue Trend")
    monthly_revenue = run_query("""
        SELECT 
            DATE_TRUNC('month', order_purchase_timestamp) AS month,
            SUM(p.payment_value) AS revenue,
            COUNT(DISTINCT o.order_id) AS orders
        FROM orders_raw o
        JOIN order_payments_raw p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY month
        ORDER BY month
    """)
    
    fig_revenue = go.Figure()
    fig_revenue.add_trace(go.Scatter(
        x=monthly_revenue['month'], 
        y=monthly_revenue['revenue'],
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#1f77b4', width=3),
        fill='tozeroy'
    ))
    fig_revenue.update_layout(
        title="Monthly Revenue Growth",
        xaxis_title="Month",
        yaxis_title="Revenue (R$)",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_revenue, use_container_width=True)
    
    # Top Products and States
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Top 10 Product Categories")
        top_categories = run_query("""
            SELECT 
                t.product_category_name_english AS category,
                COUNT(DISTINCT oi.order_id) AS orders,
                SUM(oi.price) AS revenue
            FROM order_items_raw oi
            JOIN products_raw p ON oi.product_id = p.product_id
            LEFT JOIN product_category_name_translation_raw t 
                ON p.product_category_name = t.product_category_name
            WHERE t.product_category_name_english IS NOT NULL
            GROUP BY category
            ORDER BY revenue DESC
            LIMIT 10
        """)
        
        fig_cat = px.bar(
            top_categories, 
            x='revenue', 
            y='category',
            orientation='h',
            color='revenue',
            color_continuous_scale='Blues'
        )
        fig_cat.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col2:
        st.subheader("🌎 Top 10 States by Revenue")
        top_states = run_query("""
            SELECT 
                c.customer_state AS state,
                COUNT(DISTINCT o.order_id) AS orders,
                SUM(p.payment_value) AS revenue
            FROM customers_raw c
            JOIN orders_raw o ON c.customer_id = o.customer_id
            JOIN order_payments_raw p ON o.order_id = p.order_id
            WHERE o.order_status = 'delivered'
            GROUP BY state
            ORDER BY revenue DESC
            LIMIT 10
        """)
        
        fig_states = px.bar(
            top_states,
            x='revenue',
            y='state',
            orientation='h',
            color='revenue',
            color_continuous_scale='Greens'
        )
        fig_states.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_states, use_container_width=True)

# ===== PAGE 2: GEOGRAPHIC ANALYSIS =====
elif page == "🌍 Geographic Analysis":
    st.title("🌍 Geographic Sales Distribution")
    
    # State-level analysis
    state_data = run_query("""
        SELECT 
            c.customer_state AS state,
            c.customer_city AS city,
            COUNT(DISTINCT o.order_id) AS orders,
            SUM(p.payment_value) AS revenue,
            AVG(p.payment_value) AS avg_order_value,
            COUNT(DISTINCT c.customer_id) AS customers
        FROM customers_raw c
        JOIN orders_raw o ON c.customer_id = o.customer_id
        JOIN order_payments_raw p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY state, city
        ORDER BY revenue DESC
    """)
    
    # Aggregate by state
    state_summary = state_data.groupby('state').agg({
        'orders': 'sum',
        'revenue': 'sum',
        'customers': 'sum',
        'avg_order_value': 'mean'
    }).reset_index()
    
    # Map visualization
    st.subheader("📍 Revenue by State")
    fig_map = px.scatter_geo(
        state_summary,
        locations='state',
        locationmode='country names',
        size='revenue',
        color='revenue',
        hover_name='state',
        hover_data={'orders': True, 'customers': True, 'revenue': ':,.2f'},
        color_continuous_scale='Viridis',
        title="Sales Distribution Across Brazil"
    )
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Top cities
    st.subheader("🏙️ Top 20 Cities by Revenue")
    top_cities = state_data.nlargest(20, 'revenue')
    
    fig_cities = px.treemap(
        top_cities,
        path=['state', 'city'],
        values='revenue',
        color='avg_order_value',
        color_continuous_scale='RdYlGn',
        title="City Revenue Distribution (Treemap)"
    )
    st.plotly_chart(fig_cities, use_container_width=True)
    
    # Data table
    with st.expander("📊 View Detailed State Data"):
        st.dataframe(
            state_summary.style.format({
                'revenue': 'R$ {:,.2f}',
                'avg_order_value': 'R$ {:,.2f}',
                'orders': '{:,}',
                'customers': '{:,}'
            }),
            use_container_width=True
        )

# ===== PAGE 3: PRODUCT INSIGHTS =====
elif page == "📦 Product Insights":
    st.title("📦 Product Category Analysis")
    
    # Category performance
    category_data = run_query("""
        SELECT 
            t.product_category_name_english AS category,
            COUNT(DISTINCT oi.order_id) AS orders,
            SUM(oi.price) AS revenue,
            AVG(oi.price) AS avg_price,
            AVG(r.review_score) AS avg_review,
            COUNT(DISTINCT oi.product_id) AS unique_products
        FROM order_items_raw oi
        JOIN products_raw p ON oi.product_id = p.product_id
        LEFT JOIN product_category_name_translation_raw t 
            ON p.product_category_name = t.product_category_name
        LEFT JOIN order_reviews_raw r ON oi.order_id = r.order_id
        WHERE t.product_category_name_english IS NOT NULL
        GROUP BY category
        HAVING COUNT(DISTINCT oi.order_id) >= 50
        ORDER BY revenue DESC
    """)
    
    # Scatter plot: Price vs Review Score
    st.subheader("💰 Average Price vs Customer Satisfaction")
    fig_scatter = px.scatter(
        category_data,
        x='avg_price',
        y='avg_review',
        size='orders',
        color='revenue',
        hover_name='category',
        hover_data={'orders': True, 'revenue': ':,.2f'},
        color_continuous_scale='Plasma',
        labels={'avg_price': 'Average Price (R$)', 'avg_review': 'Avg Review Score'}
    )
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Top performers
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("⭐ Best Rated Categories")
        best_rated = category_data.nlargest(10, 'avg_review')[['category', 'avg_review', 'orders']]
        st.dataframe(
            best_rated.style.format({'avg_review': '{:.2f}', 'orders': '{:,}'}),
            use_container_width=True
        )
    
    with col2:
        st.subheader("💎 Most Expensive Categories")
        most_expensive = category_data.nlargest(10, 'avg_price')[['category', 'avg_price', 'orders']]
        st.dataframe(
            most_expensive.style.format({'avg_price': 'R$ {:,.2f}', 'orders': '{:,}'}),
            use_container_width=True
        )
    
    # Payment methods
    st.subheader("💳 Payment Method Distribution")
    payment_data = run_query("""
        SELECT 
            payment_type,
            COUNT(*) AS transactions,
            SUM(payment_value) AS total_value,
            AVG(payment_value) AS avg_value
        FROM order_payments_raw
        GROUP BY payment_type
        ORDER BY transactions DESC
    """)
    
    fig_payment = px.pie(
        payment_data,
        values='transactions',
        names='payment_type',
        title="Payment Methods by Transaction Count",
        hole=0.4
    )
    st.plotly_chart(fig_payment, use_container_width=True)

# ===== PAGE 4: DELIVERY PERFORMANCE =====
elif page == "🚚 Delivery Performance":
    st.title("🚚 Delivery Performance Analysis")
    
    # Delivery metrics by state
    delivery_data = run_query("""
        SELECT 
            c.customer_state AS state,
            COUNT(o.order_id) AS orders,
            AVG(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400) AS avg_delivery_days,
            AVG(r.review_score) AS avg_review
        FROM orders_raw o
        JOIN customers_raw c ON o.customer_id = c.customer_id
        LEFT JOIN order_reviews_raw r ON o.order_id = r.order_id
        WHERE o.order_delivered_customer_date IS NOT NULL
          AND o.order_status = 'delivered'
        GROUP BY state
        HAVING COUNT(o.order_id) >= 100
        ORDER BY avg_delivery_days
    """)
    
    # Delivery time distribution
    st.subheader("⏱️ Average Delivery Time by State")
    fig_delivery = px.bar(
        delivery_data.nsmallest(15, 'avg_delivery_days'),
        x='state',
        y='avg_delivery_days',
        color='avg_review',
        color_continuous_scale='RdYlGn',
        labels={'avg_delivery_days': 'Avg Delivery Days', 'avg_review': 'Avg Review'}
    )
    fig_delivery.update_layout(height=400)
    st.plotly_chart(fig_delivery, use_container_width=True)
    
    # Late delivery impact
    st.subheader("📉 Late Delivery Impact on Reviews")
    late_delivery = run_query("""
        SELECT 
            CASE 
                WHEN o.order_delivered_customer_date <= o.order_estimated_delivery_date THEN 'On Time'
                WHEN o.order_delivered_customer_date > o.order_estimated_delivery_date THEN 'Late'
            END AS delivery_status,
            COUNT(o.order_id) AS orders,
            AVG(r.review_score) AS avg_review,
            STDDEV(r.review_score) AS review_stddev
        FROM orders_raw o
        LEFT JOIN order_reviews_raw r ON o.order_id = r.order_id
        WHERE o.order_delivered_customer_date IS NOT NULL
          AND o.order_estimated_delivery_date IS NOT NULL
          AND r.review_score IS NOT NULL
        GROUP BY delivery_status
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig_late = px.bar(
            late_delivery,
            x='delivery_status',
            y='avg_review',
            color='delivery_status',
            title="Review Score: On Time vs Late",
            color_discrete_map={'On Time': 'green', 'Late': 'red'}
        )
        st.plotly_chart(fig_late, use_container_width=True)
    
    with col2:
        fig_count = px.pie(
            late_delivery,
            values='orders',
            names='delivery_status',
            title="Delivery Status Distribution",
            color='delivery_status',
            color_discrete_map={'On Time': 'green', 'Late': 'red'}
        )
        st.plotly_chart(fig_count, use_container_width=True)

# ===== PAGE 5: STATISTICAL ANALYSIS =====
elif page == "📊 Statistical Analysis":
    st.title("📊 Statistical Analysis & Regression")
    
    st.markdown("""
    ### Linear Regression: Delivery Time Impact on Reviews
    **Research Question**: Does delivery time affect customer satisfaction?
    """)
    
    # Get regression data
    regression_data = run_query("""
        SELECT 
            EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400 AS delivery_days,
            r.review_score
        FROM orders_raw o
        JOIN order_reviews_raw r ON o.order_id = r.order_id
        WHERE o.order_delivered_customer_date IS NOT NULL
          AND o.order_purchase_timestamp IS NOT NULL
          AND r.review_score IS NOT NULL
          AND EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400 > 0
          AND EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_purchase_timestamp))/86400 < 100
    """)
    
    # Perform regression
    X = regression_data['delivery_days'].values
    y = regression_data['review_score'].values
    
    slope, intercept, r_value, p_value, std_err = stats.linregress(X, y)
    
    # Display results
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("R² Score", f"{r_value**2:.4f}")
    col2.metric("Slope (β₁)", f"{slope:.4f}")
    col3.metric("Intercept (β₀)", f"{intercept:.4f}")
    col4.metric("P-value", f"{p_value:.2e}")
    
    # Interpretation
    if p_value < 0.05:
        st.success(f"✅ **Statistically Significant** (p < 0.05): Delivery time significantly impacts review scores!")
    else:
        st.warning(f"⚠️ Not statistically significant (p >= 0.05)")
    
    st.info(f"""
    **Model**: `review_score = {intercept:.4f} + ({slope:.4f}) × delivery_days`
    
    **Interpretation**: 
    - For each additional day of delivery, the review score changes by **{slope:.4f} points**
    - **{abs(r_value**2)*100:.2f}%** of review score variation is explained by delivery time
    - Correlation coefficient: **{r_value:.4f}**
    """)
    
    # Scatter plot with regression line
    fig_reg = go.Figure()
    
    # Sample for visualization (too many points)
    sample = regression_data.sample(min(5000, len(regression_data)))
    
    fig_reg.add_trace(go.Scatter(
        x=sample['delivery_days'],
        y=sample['review_score'],
        mode='markers',
        name='Actual Data',
        marker=dict(size=3, color='lightblue', opacity=0.5)
    ))
    
    # Regression line
    x_line = np.linspace(X.min(), X.max(), 100)
    y_line = intercept + slope * x_line
    
    fig_reg.add_trace(go.Scatter(
        x=x_line,
        y=y_line,
        mode='lines',
        name=f'Regression Line (R²={r_value**2:.4f})',
        line=dict(color='red', width=3)
    ))
    
    fig_reg.update_layout(
        title="Review Score vs Delivery Time",
        xaxis_title="Delivery Time (days)",
        yaxis_title="Review Score (1-5)",
        height=500
    )
    st.plotly_chart(fig_reg, use_container_width=True)
    
    # Distribution
    st.subheader("📈 Delivery Time Distribution")
    fig_hist = px.histogram(
        regression_data,
        x='delivery_days',
        nbins=50,
        title="Distribution of Delivery Times",
        labels={'delivery_days': 'Delivery Time (days)'}
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ===== PAGE 6: DATA QUALITY =====
elif page == "✅ Data Quality":
    st.title("✅ Data Quality Metrics")
    
    # Table row counts
    st.subheader("📊 Table Statistics")
    
    tables = [
        'customers_raw', 'sellers_raw', 'products_raw',
        'orders_raw', 'order_items_raw', 'order_payments_raw',
        'order_reviews_raw', 'geolocation_raw',
        'product_category_name_translation_raw'
    ]
    
    table_stats = []
    for table in tables:
        count = run_query(f"SELECT COUNT(*) as count FROM {table}")
        table_stats.append({'Table': table, 'Row Count': count.iloc[0, 0]})
    
    df_stats = pd.DataFrame(table_stats)
    df_stats['Row Count'] = df_stats['Row Count'].apply(lambda x: f"{x:,}")
    
    st.dataframe(df_stats, use_container_width=True)
    
    # Data quality checks
    st.subheader("🔍 Data Quality Checks")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # NULL checks
        st.markdown("**NULL Value Checks**")
        null_checks = run_query("""
            SELECT 
                'customers.customer_id' as column_name,
                COUNT(*) - COUNT(customer_id) as null_count
            FROM customers_raw
            UNION ALL
            SELECT 
                'orders.order_id',
                COUNT(*) - COUNT(order_id)
            FROM orders_raw
            UNION ALL
            SELECT 
                'orders.customer_id',
                COUNT(*) - COUNT(customer_id)
            FROM orders_raw
        """)
        
        for _, row in null_checks.iterrows():
            if row['null_count'] == 0:
                st.success(f"✓ {row['column_name']}: No NULLs")
            else:
                st.error(f"✗ {row['column_name']}: {row['null_count']} NULLs")
    
    with col2:
        # Range checks
        st.markdown("**Data Range Checks**")
        
        # Review scores
        invalid_reviews = run_query("""
            SELECT COUNT(*) as count
            FROM order_reviews_raw
            WHERE review_score NOT BETWEEN 1 AND 5
        """)
        
        if invalid_reviews.iloc[0, 0] == 0:
            st.success("✓ Review scores: All in range [1-5]")
        else:
            st.error(f"✗ Review scores: {invalid_reviews.iloc[0, 0]} out of range")
        
        # Positive prices
        invalid_prices = run_query("""
            SELECT COUNT(*) as count
            FROM order_items_raw
            WHERE price < 0
        """)
        
        if invalid_prices.iloc[0, 0] == 0:
            st.success("✓ Prices: All positive")
        else:
            st.error(f"✗ Prices: {invalid_prices.iloc[0, 0]} negative")
    
    # Recent update info
    st.markdown("---")
    st.info(f"""
    **Last Dashboard Update**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
    **Data Freshness**: Real-time (queries run on-demand)  
    **Cache TTL**: 10 minutes
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center'>
    <p><strong>Olist E-Commerce Analytics Dashboard</strong></p>
    <p>Duke IDS 706 - Data Engineering Final Project</p>
    <p>Team: Pinaki Ghosh, Austin Zhang, Diwas Puri, Michael Badu</p>
</div>
""", unsafe_allow_html=True)
