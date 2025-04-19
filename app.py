import streamlit as st
import tempfile
from pathlib import Path
import os
import google.generativeai as genai
from langchain_core.messages import HumanMessage, AIMessage
import base64
import requests
import pandas as pd
import random
import json
from datetime import datetime

import agent_core
import utils

# Set Streamlit page configuration with theme
st.set_page_config(
    page_title="ShopSight AI Assistant",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium styling
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2196F3;
        --secondary-color: #4CAF50;
        --accent-color: #FFC107;
        --background-color: #f8f9fa;
        --card-color: #ffffff;
        --text-color: #212121;
        --text-light: #757575;
        --border-radius: 10px;
        --box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    /* Global styles */
    .main {
        background-color: var(--background-color);
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1.5rem;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        display: flex;
        box-shadow: var(--box-shadow);
    }
    .chat-message.user {
        background-color: #e6f3ff;
        border-left: 5px solid var(--primary-color);
    }
    .chat-message.assistant {
        background-color: #f0f7f0;
        border-left: 5px solid var(--secondary-color);
    }
    .chat-avatar {
        width: 60px;
    }
    .chat-content {
        flex-grow: 1;
        padding-left: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: var(--primary-color);
        color: white;
        border-radius: 20px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Headings */
    h1, h2, h3 {
        color: #1E3A8A;
    }
    h1 {
        font-size: 2.2rem;
        margin-bottom: 1rem;
    }
    h2 {
        font-size: 1.8rem;
        margin-bottom: 0.8rem;
    }
    h3 {
        font-size: 1.5rem;
        margin-bottom: 0.6rem;
    }
    
    /* Footer */
    .footer {
        margin-top: 3rem;
        text-align: center;
        color: var(--text-light);
        padding: 1rem;
        border-top: 1px solid #eee;
    }
    
    /* Category cards */
    .category-card {
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        padding: 20px;
        box-shadow: var(--box-shadow);
        transition: transform 0.3s ease-in-out, box-shadow 0.3s ease-in-out;
        text-align: center;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        min-height: 150px;
    }
    div[data-testid="stVerticalBlock"] > div[style*="flex-direction: column;"] > div[data-testid="stVerticalBlockBorderWrapper"]:has(.category-card) {
        margin-bottom: 10px;
    }
    .category-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    .category-icon {
        font-size: 2.5rem;
        margin-bottom: 15px;
        color: var(--primary-color);
    }
    
    /* Filter section */
    .filter-section {
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        padding: 20px;
        box-shadow: var(--box-shadow);
        margin-bottom: 20px;
    }
    
    /* Product cards */
    .product-card-container {
        padding: 15px;
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        height: 100%;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        border: 1px solid #eee;
        transition: box-shadow 0.3s ease;
    }
    .product-card-container:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    .product-card-container img {
        border-radius: calc(var(--border-radius) - 8px);
        margin-bottom: 15px;
        max-height: 180px;
        object-fit: contain;
    }
    .product-info-section {
        flex-grow: 1;
        margin-bottom: 15px;
    }
    .product-info-section h4 {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 5px;
        color: var(--text-color);
    }
    .product-info-section .caption {
        font-size: 0.85rem;
        color: var(--text-light);
        margin-bottom: 10px;
        display: block;
    }
    .product-info-section .price {
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--primary-color);
        margin-bottom: 10px;
        display: block;
    }
    .product-info-section .rating {
        font-size: 0.9rem;
        color: var(--text-light);
        margin-bottom: 10px;
    }
    .product-info-section .rating .stars {
        color: var(--accent-color);
        margin-right: 5px;
        font-size: 1rem;
    }
    .product-action-section {
        padding-top: 10px;
        border-top: 1px solid #eee;
    }
    
    /* Product cards */
    .product-card {
        background-color: var(--card-color);
        border-radius: var(--border-radius);
        overflow: hidden;
        box-shadow: var(--box-shadow);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
        display: flex;
        flex-direction: column;
    }
    .product-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .product-img {
        height: 200px;
        background-color: #f5f5f5;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .product-img img {
        width: 100%;
        height: 100%;
        object-fit: contain;
    }
    .product-info {
        padding: 15px;
        flex-grow: 1;
        display: flex;
        flex-direction: column;
    }
    .product-title {
        font-weight: 600;
        margin-bottom: 10px;
        color: var(--text-color);
        font-size: 1.1rem;
    }
    .product-category {
        font-size: 0.9rem;
        color: var(--text-light);
        margin-bottom: 10px;
    }
    .product-price {
        font-weight: 700;
        color: var(--primary-color);
        font-size: 1.2rem;
        margin-bottom: 15px;
    }
    .product-rating {
        display: flex;
        align-items: center;
        margin-bottom: 15px;
    }
    .product-rating .stars {
        color: var(--accent-color);
        margin-right: 5px;
    }
    .product-actions {
        margin-top: auto;
        display: flex;
        gap: 10px;
    }
    .product-btn {
        flex: 1;
        background-color: var(--primary-color);
        color: white;
        border: none;
        padding: 8px 0;
        border-radius: 5px;
        cursor: pointer;
        font-weight: 500;
        transition: background-color 0.3s ease;
    }
    .product-btn.secondary {
        background-color: #f5f5f5;
        color: var(--text-color);
    }
    .product-btn:hover {
        opacity: 0.9;
    }
    
    /* Badge styles */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 5px;
        margin-bottom: 5px;
    }
    .badge.new {
        background-color: var(--primary-color);
        color: white;
    }
    .badge.sale {
        background-color: #F44336;
        color: white;
    }
    .badge.popular {
        background-color: var(--accent-color);
        color: black;
    }
    
    /* Advanced filtering */
    .filter-chip {
        display: inline-block;
        background-color: #e0e0e0;
        color: var(--text-color);
        padding: 5px 10px;
        border-radius: 20px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.9rem;
    }
    .filter-chip.active {
        background-color: var(--primary-color);
        color: white;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 4px 4px 0 0;
        gap: 1rem;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: var(--primary-color);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f0f2f5;
        border-right: 1px solid #eaeaea;
    }
    [data-testid="stSidebar"] [data-testid="stImage"] {
        text-align: center;
        display: block;
        margin: 0 auto;
    }
    [data-testid="stExpander"] {
        background-color: white;
        border-radius: var(--border-radius);
        margin-bottom: 1rem;
        box-shadow: var(--box-shadow);
    }
    
    /* Ensure cards in columns have consistent height */
    .stVerticalBlock > [data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"] {
        height: 100%;
    }
    .product-card-container {
        height: 100%;
        display: flex;
    }
</style>
""", unsafe_allow_html=True)

# Load product data for category display
@st.cache_data
def load_product_categories():
    try:
        # Use the centralized loading function
        df = utils.load_products_data()
        if df.empty:
            st.warning("Product data is currently empty or could not be loaded.")
            return [], {}
            
        categories = df['category'].unique().tolist()
        category_counts = df['category'].value_counts().to_dict()
        return categories, category_counts
    except Exception as e:
        st.error(f"Error processing product categories: {str(e)}")
        return [], {}

@st.cache_data
def load_product_price_range():
    try:
        # Use the centralized loading function
        df = utils.load_products_data()
        if df.empty or 'price' not in df.columns or df['price'].isnull().all():
             st.warning("Product price data is currently empty or could not be loaded.")
             return 0, 1000 # Return default range
             
        # Calculate min/max after ensuring data is present and numeric
        min_price = float(df['price'].min())
        max_price = float(df['price'].max())
        return min_price, max_price
    except Exception as e:
        st.error(f"Error processing product price range: {str(e)}")
        return 0, 1000

@st.cache_data
def load_product_brands():
    try:
        # Use the centralized loading function
        df = utils.load_products_data()
        if df.empty or 'brand' not in df.columns:
             st.warning("Product brand data is currently empty or could not be loaded.")
             return []
             
        brands = df['brand'].dropna().unique().tolist()
        return brands
    except Exception as e:
        st.error(f"Error processing product brands: {str(e)}")
        return []

# Get warm greeting messages
def get_random_greeting():
    greetings = [
        "Hello! I'm ShopSight, your friendly AI shopping assistant. How can I help you discover the perfect products today?",
        "Welcome to ShopSight! I'm here to make your shopping experience delightful. What can I help you find today?",
        "Hi there! I'm your personal ShopSight assistant, ready to help with all your shopping needs. What are you looking for today?",
        "Greetings! I'm ShopSight, your AI shopping companion. I'd be happy to help you find exactly what you need today!",
        "Welcome! I'm ShopSight, and I'm excited to help you discover amazing products. How can I assist you today?"
    ]
    return random.choice(greetings)

# Get random featured products
@st.cache_data
def get_featured_products(n=8):
    try:
        # Use the centralized loading function to ensure consistency
        df = utils.load_products_data()
        if df.empty or len(df) <= n:
            return df
        return df.sample(n=n)
    except Exception as e:
        st.error(f"Error loading featured products: {str(e)}")
        return pd.DataFrame()

# Category icons mapping
category_icons = {
    'Electronics': '🖥️',
    'Kitchen': '🍳',
    'Footwear': '👟',
    'Furniture': '🪑',
    'Home Appliances': '🧹',
    'Outdoor': '⛺',
    'Fitness': '🏋️',
    'Home': '🏠',
    'Home Office': '💼',
    'Home Security': '🔒',
    'Sports': '🚲',
    'Nutrition': '🥗',
    'Clothing': '👕',
    'Accessories': '👓',
    'Tools': '🔧',
    'Personal Care': '🪥',
    'Food & Beverage': '☕'
}

# Default icon for categories not in the mapping
default_icon = '��'

# Load API keys
try:
    api_keys = utils.load_api_keys()
    
    # Set Google API key for Gemini
    genai.configure(api_key=api_keys["GOOGLE_API_KEY"])
    
except Exception as e:
    st.error(f"Error loading API keys: {str(e)}")
    st.stop()

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(content=get_random_greeting())
    ]

if "processing" not in st.session_state:
    st.session_state.processing = False

if "tools_enabled" not in st.session_state:
    st.session_state.tools_enabled = {
        "search_products": True,
        "get_product_details": True,
        "check_stock": True,
        "list_product_categories": True,
        "get_category_products": True,
        "recommend_products": True
    }

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "filter_params" not in st.session_state:
    st.session_state.filter_params = {
        "price_min": None,
        "price_max": None,
        "category": None,
        "brand": None,
        "rating_min": 1.0,
        "search_query": "",
        "in_stock_only": True,
        "sort_by": "rating"
    }

if "view_mode" not in st.session_state:
    st.session_state.view_mode = "grid"

# --- Agent Interaction Function ---
def run_agent_query(query: str):
    """Adds user query to chat, runs agent, adds response, reruns."""
    st.session_state.chat_history.append(HumanMessage(content=query))
    with st.spinner("Thinking..."):
        try:
            active_tools = [k for k, v in st.session_state.tools_enabled.items() if v]
            agent_response_text = agent_core.run_agent_interaction(
                query, st.session_state.chat_history, active_tools
            )
        except Exception as e:
            agent_response_text = f"I encountered an error: {str(e)}. Please try again."
        st.session_state.chat_history.append(AIMessage(content=agent_response_text))
    # Use st.experimental_rerun() if st.rerun() causes issues, otherwise keep st.rerun()
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# --- UI Rendering & Callback Functions ---

# Function to handle details button click (Defined BEFORE render_product_card)
def handle_details_click(product_id):
    query = f"Show details for product ID {product_id}"
    run_agent_query(query)

# Refactored Function to render product card with improved aesthetics (Moved Definition Earlier)
def render_product_card(product, key_prefix):
    product_id = product.get('id', f"unknown_{key_prefix}_{random.randint(1000,9999)}")
    product_name = product.get('name', 'Unknown Product')
    product_price = float(product.get('price', 0.0))
    product_rating = float(product.get('rating', 0.0))
    product_category = product.get('category', 'N/A')
    product_brand = product.get('brand', 'N/A')
    
    placeholder_url = f"https://placehold.co/600x400/e0e0e0/757575?text={product_name.split()[0]}"
    
    try: is_new = int(product_id) > 1030 
    except: is_new = False
    is_popular = product_rating >= 4.7
    
    with st.container():
        st.markdown('<div class="product-card-container">', unsafe_allow_html=True)
        st.image(placeholder_url, use_column_width='auto')
        
        # --- Info Section ---
        badge_md = ""
        if is_new: badge_md += "<span class='badge new'>NEW</span> "
        if is_popular: badge_md += "<span class='badge popular'>POPULAR</span>"
        if badge_md: st.markdown(badge_md, unsafe_allow_html=True)

        st.markdown(f"<h4>{product_name}</h4>", unsafe_allow_html=True)
        st.markdown(f"<span class='caption'>{product_category} | {product_brand}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class='price'>${product_price:.2f}</span>", unsafe_allow_html=True)

        stars_html = f"<span class='stars'>{'★' * int(product_rating)}{'☆' * (5 - int(product_rating))}</span>"
        st.markdown(f"<div class='rating'>{stars_html} ({product_rating:.1f})</div>", unsafe_allow_html=True)
        # --- End Info Section ---

        # --- Action Section (Only Details button) ---
        st.markdown('<div class="product-action-section">', unsafe_allow_html=True)
        st.button("Details", 
                  key=f"details_{key_prefix}_{product_id}",
                  on_click=handle_details_click,
                  args=(product_id,),
                  use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# --- Category Click Handlers ---
def handle_category_click(category_name):
     query = f"Show me products in the {category_name} category"
     run_agent_query(query)

def handle_quick_category_click(category_name):
    query = f"Show me products in the {category_name} category"
    run_agent_query(query)

# --- User Input Form Callback ---
def handle_chat_input():
    if st.session_state.user_input:
        run_agent_query(st.session_state.user_input)

# --- Constants & Initializations ---
# ... [category_icons, default_icon] ...

# --- API Key Loading ---
# ... [try/except for API keys] ...

# --- Session State Initialization ---
# ... [st.session_state initializations] ...

# --- Sidebar ---
with st.sidebar:
    # ... [Sidebar content] ...

# --- Main Content Area ---
st.header("🛍️ ShopSight AI Shopping Assistant")

# Initial View (Welcome, Featured Products, Categories)
if len(st.session_state.chat_history) <= 1:
    # Hero banner
    st.markdown("""
    <div style="background-color: #e0f2f1; padding: 20px; border-radius: 10px; margin-bottom: 20px; text-align: center;">
        <h1 style="color: #004d40;">Welcome to ShopSight!</h1>
        <p style="font-size: 1.2rem; color: #00695c;">Your AI-powered shopping assistant. Find the perfect products with intelligent search and filtering.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Active filters display
    active_filters = []
    if st.session_state.filter_params["category"]:
        active_filters.append(f"Category: {st.session_state.filter_params['category']}")
    if st.session_state.filter_params["price_min"] or st.session_state.filter_params["price_max"]:
        active_filters.append(f"Price: ${st.session_state.filter_params['price_min']} - ${st.session_state.filter_params['price_max']}")
    if st.session_state.filter_params["brand"]:
        active_filters.append(f"Brand: {st.session_state.filter_params['brand']}")
    if st.session_state.filter_params["search_query"]:
        active_filters.append(f"Search: {st.session_state.filter_params['search_query']}")
    
    if active_filters:
        st.markdown("### Active Filters")
        filters_html = "".join([f"<span class='filter-chip active'>{f}</span>" for f in active_filters])
        st.markdown(f"<div>{filters_html}</div>", unsafe_allow_html=True)
        st.markdown("---")
    
    # Show featured products if no filters applied
    if not active_filters:
        st.markdown("### 🌟 Featured Products")
        featured_products_df = get_featured_products(n=8)
        
        if not featured_products_df.empty:
            cols = st.columns(4)
            for i, (_, product_row) in enumerate(featured_products_df.iterrows()):
                with cols[i % 4]:
                    # Pass a unique key prefix for featured items
                    render_product_card(product_row, f"feat_{i}")
        
        st.markdown("---")
    
    # Filter tips
    with st.container():
        st.markdown("### 🔍 Find Exactly What You Need")
        st.markdown("Use the filters in the sidebar to narrow down products by category, price range, brand, and more!")
    
    st.markdown("---")

# Display categories only on the first page load or when no conversation has happened yet
if len(st.session_state.chat_history) <= 1:
    st.markdown("### Explore Our Product Categories")
    
    # Load categories data
    categories, category_counts = load_product_categories()
    
    # Define handler function *before* the loop where it's used
    def handle_category_click(category_name):
         query = f"Show me products in the {category_name} category"
         run_agent_query(query)
         
    if categories:
        cols = st.columns(4)
        for i, category in enumerate(sorted(categories)):
            col_idx = i % 4
            icon = category_icons.get(category, default_icon)
            count = category_counts.get(category, 0)
            
            # Use the column directly
            with cols[col_idx]:
                # Container for the visual card part
                with st.container(): 
                    st.markdown(f""" 
                    <div class="category-card"> 
                        <div class="category-icon">{icon}</div>
                        <h3>{category}</h3>
                        <p>{count} products</p>
                    </div>
                    """, unsafe_allow_html=True)
                # Place the button *directly within the column*, below the visual card container
                st.button(f"Browse {category}", 
                          key=f"cat_btn_{category}_{i}",
                          on_click=handle_category_click, 
                          args=(category,), 
                          use_container_width=True)
    else:
        st.info("No product categories found.")
        
    st.markdown("---")
    st.markdown("### Ask me anything about our products!")
    st.markdown("I can help you find products, compare options, check availability, and more.")

# Display shopping assistant header
if len(st.session_state.chat_history) > 1:
    st.markdown("""
    <div style="background-color: #e3f2fd; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h2 style="color: #1565c0; margin-bottom: 5px;">Your Shopping Assistant</h2>
        <p>Ask me anything about products, or use the filters to browse the catalog</p>
    </div>
    """, unsafe_allow_html=True)

# Custom chat display
chat_container = st.container()
with chat_container:
    for i, message in enumerate(st.session_state.chat_history):
        if message.type == "human":
            with st.container():
                st.markdown(f"""
                <div class="chat-message user">
                    <div class="chat-avatar">👤</div>
                    <div class="chat-content">{message.content}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            with st.container():
                st.markdown(f"""
                <div class="chat-message assistant">
                    <div class="chat-avatar">🤖</div>
                    <div class="chat-content">{message.content}</div>
                </div>
                """, unsafe_allow_html=True)

# Text input using a form with premium styling
with st.form(key="input_form", clear_on_submit=True):
    st.text_input(
        "Type your question about products here:",
        key="user_input",
        placeholder="e.g., 'Find me running shoes under $150' or 'What kitchen products do you have?'"
    )
    
    col1, col2 = st.columns([4, 1])
    with col2:
        submit_button = st.form_submit_button("Send 📤", on_click=handle_chat_input)

# Action buttons
action_col1, action_col2 = st.columns(2)
with action_col1:
    if st.button("📋 New Conversation", use_container_width=True):
        st.session_state.chat_history = [
            AIMessage(content=get_random_greeting())
        ]
        st.session_state.selected_category = None
        st.session_state.filter_params = {
            "price_min": None,
            "price_max": None,
            "category": None,
            "brand": None,
            "rating_min": None,
            "search_query": "",
            "in_stock_only": True,
            "sort_by": "price_low"
        }
        st.rerun()

with action_col2:
    if st.button("💾 Export Chat", use_container_width=True):
        chat_text = "\n\n".join([f"{'User' if msg.type == 'human' else 'ShopSight'}: {msg.content}" for msg in st.session_state.chat_history])
        st.download_button(
            label="Download Chat",
            data=chat_text,
            file_name="shopsight_conversation.txt",
            mime="text/plain"
        )

# Quick category buttons
if len(st.session_state.chat_history) > 1:  # Only show after conversation has started
    st.markdown("---")
    st.markdown("### Popular Categories")
    categories, _ = load_product_categories()
    
    # Define handler function *before* the loop
    def handle_quick_category_click(category_name):
        query = f"Show me products in the {category_name} category"
        run_agent_query(query)
        
    if categories:
        top_categories = sorted(categories)[:8] if len(categories) > 8 else sorted(categories)
        button_cols = st.columns(4)
        for i, category in enumerate(top_categories):
            col_idx = i % 4
            icon = category_icons.get(category, default_icon)
            # Use the column directly for the button
            with button_cols[col_idx]:
                 st.button(f"{icon} {category}", 
                           key=f"quick_btn_{category}_{i}", 
                           on_click=handle_quick_category_click, 
                           args=(category,), 
                           use_container_width=True)

# Footer
st.markdown("""
<div class="footer">
    <p>ShopSight AI Assistant • Powered by LangChain and Gemini</p>
    <p style="font-size: 0.8rem; margin-top: 5px;">© 2024 ShopSight. All rights reserved.</p>
</div>
""", unsafe_allow_html=True) 