import os
import json
import pandas as pd
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import csv

# Constants for file paths and configurations
CSV_FILEPATH = "data/products.csv"
API_KEYS_FILE = "config/api_keys.json"
PERSIST_DIRECTORY = "data/chroma_db"
CHROMA_COLLECTION_NAME = "products"

def load_api_keys() -> Dict[str, str]:
    """
    Load API keys from the configuration file
    
    Returns:
        Dict[str, str]: Dictionary of API keys
    """
    try:
        with open(API_KEYS_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"API keys file not found at {API_KEYS_FILE}. Please create this file.")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in {API_KEYS_FILE}. Please check the file format.")

def load_products_data() -> pd.DataFrame:
    """
    Load product data from CSV file
    
    Returns:
        pd.DataFrame: DataFrame containing product data
    """
    try:
        # Check if CSV file exists
        if not os.path.exists(CSV_FILEPATH):
            raise FileNotFoundError(f"Products CSV file not found at {CSV_FILEPATH}")
        
        # Load the data with explicit quoting rules and python engine
        df = pd.read_csv(
            CSV_FILEPATH, 
            engine='python', # Use the python engine for more robust parsing
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL,
            on_bad_lines='warn' # Keep warning to see if lines are still skipped
        )
        
        # Ensure required columns exist (using the actual header names)
        required_columns = ['product_id', 'name', 'price', 'category'] 
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns in CSV: {', '.join(missing_columns)}")
        
        # Rename product_id to id for consistency if needed elsewhere
        if 'product_id' in df.columns:
            df.rename(columns={'product_id': 'id'}, inplace=True)
            
        # Attempt to convert types, handling potential errors
        if 'price' in df.columns:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        if 'rating' in df.columns:
            df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
        if 'in_stock' in df.columns:
             # Convert various string representations of boolean to actual boolean
            if pd.api.types.is_string_dtype(df['in_stock']):
                df['in_stock'] = df['in_stock'].str.lower().map({'true': True, 'yes': True}).fillna(False).astype(bool)
            else:
                df['in_stock'] = df['in_stock'].astype(bool)
        
        # Drop rows where essential numeric columns couldn't be parsed
        df.dropna(subset=['id', 'price'], inplace=True)
            
        return df
    
    except pd.errors.ParserError as pe:
        print(f"Pandas ParserError loading products data: {str(pe)}")
        # Attempt to read the specific line causing the error
        try:
            with open(CSV_FILEPATH, 'r') as f:
                lines = f.readlines()
                # Error messages often use 1-based indexing, adjust for 0-based list index
                error_line_num_str = str(pe).split('line ')[-1].split(',')[0]
                if error_line_num_str.isdigit():
                    error_line_num = int(error_line_num_str)
                    if 0 < error_line_num <= len(lines):
                        print(f"Problematic line ({error_line_num}): {lines[error_line_num - 1].strip()}")
                else:
                    print("Could not extract line number from parser error.")
        except Exception as read_err:
            print(f"Could not read problematic line: {read_err}")
        # Return empty DataFrame in case of parsing error to avoid crashing downstream
        return pd.DataFrame(columns=['id', 'name', 'price', 'category', 'description', 'brand', 'rating'])
        
    except Exception as e:
        print(f"General Error loading products data: {str(e)}")
        # Return empty DataFrame if there's any other error
        return pd.DataFrame(columns=['id', 'name', 'price', 'category', 'description', 'brand', 'rating'])

def search_products(query: str, min_price: Optional[float] = None, max_price: Optional[float] = None, category: Optional[str] = None, brand: Optional[str] = None, rating_min: Optional[float] = None, in_stock_only: bool = True, sort_by: str = "price_low") -> pd.DataFrame:
    """
    Search for products based on query, price range, category, brand, rating, stock, and sort order.
    
    Args:
        query: Search query string
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        category: Category filter (optional)
        brand: Brand filter (optional)
        rating_min: Minimum rating filter (optional)
        in_stock_only: If True, filter for in-stock items (default: True)
        sort_by: Sorting criteria ("price_low", "price_high", "rating", "newest")
    
    Returns:
        DataFrame containing matching products
    """
    try:
        # Load products data
        df = load_products_data()
        
        # Apply filters
        filtered_df = df.copy()
        
        # Apply category filter if provided
        if category is not None:
            filtered_df = filtered_df[filtered_df['category'].str.lower() == category.lower()]
            
        # Apply brand filter if provided
        if brand is not None and 'brand' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['brand'].str.lower() == brand.lower()]
        
        # Apply price range filters if provided
        if min_price is not None:
            filtered_df = filtered_df[filtered_df['price'] >= min_price]
        
        if max_price is not None:
            filtered_df = filtered_df[filtered_df['price'] <= max_price]
            
        # Apply minimum rating filter if provided
        if rating_min is not None and 'rating' in filtered_df.columns:
             # Ensure rating column is numeric, coerce errors to NaN
            filtered_df['rating'] = pd.to_numeric(filtered_df['rating'], errors='coerce')
            filtered_df = filtered_df[filtered_df['rating'] >= rating_min]
            
        # Apply in-stock filter if requested
        if in_stock_only and 'in_stock' in filtered_df.columns:
            # Handle boolean or string representations of stock status
            if pd.api.types.is_string_dtype(filtered_df['in_stock']):
                filtered_df = filtered_df[filtered_df['in_stock'].str.lower() == 'true']
            else:
                 # Assume boolean if not string
                filtered_df = filtered_df[filtered_df['in_stock'] == True]
        
        # If query is provided, filter based on query matching name or description
        if query and not query.isspace():
            # Convert query to lowercase for case-insensitive matching
            query_lower = query.lower()
            
            # Create mask for products where name or description contains the query
            name_mask = filtered_df['name'].str.lower().str.contains(query_lower, na=False)
            
            # Check if description column exists before filtering on it
            desc_mask = pd.Series([False] * len(filtered_df))
            if 'description' in filtered_df.columns:
                desc_mask = filtered_df['description'].str.lower().str.contains(query_lower, na=False)
                
            mask = name_mask | desc_mask
            filtered_df = filtered_df[mask]
            
        # Apply sorting
        if not filtered_df.empty:
            if sort_by == "price_low":
                filtered_df = filtered_df.sort_values(by='price', ascending=True)
            elif sort_by == "price_high":
                filtered_df = filtered_df.sort_values(by='price', ascending=False)
            elif sort_by == "rating" and 'rating' in filtered_df.columns:
                filtered_df = filtered_df.sort_values(by='rating', ascending=False, na_position='last')
            elif sort_by == "newest":
                # Assuming 'id' represents creation order (higher id = newer)
                filtered_df = filtered_df.sort_values(by='id', ascending=False)
        
        return filtered_df
    
    except Exception as e:
        print(f"Error searching products: {str(e)}")
        return pd.DataFrame(columns=['id', 'name', 'price', 'category', 'description', 'brand', 'rating'])

def get_product_by_id(product_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a product by its ID
    
    Args:
        product_id: ID of the product to retrieve
    
    Returns:
        Dictionary containing product data, or None if not found
    """
    try:
        # Load products data
        df = load_products_data()
        
        # Find product with matching ID
        product = df[df['id'] == product_id]
        
        if product.empty:
            return None
        
        # Convert product to dictionary
        product_dict = product.iloc[0].to_dict()
        
        return product_dict
    
    except Exception as e:
        print(f"Error retrieving product: {str(e)}")
        return None

def get_product_categories() -> List[str]:
    """
    Get a list of all unique product categories
    
    Returns:
        List of category names
    """
    try:
        # Load products data
        df = load_products_data()
        
        # Get unique categories
        categories = df['category'].unique().tolist()
        
        return categories
    
    except Exception as e:
        print(f"Error retrieving categories: {str(e)}")
        return []

def get_category_count() -> Dict[str, int]:
    """
    Get a count of products in each category
    
    Returns:
        Dictionary mapping category names to product counts
    """
    try:
        # Load products data
        df = load_products_data()
        
        # Count products in each category
        category_counts = df['category'].value_counts().to_dict()
        
        return category_counts
    
    except Exception as e:
        print(f"Error counting categories: {str(e)}")
        return {}

# STT/TTS Helper Functions (Placeholders)

def transcribe_audio(audio_data: bytes) -> str:
    """
    Transcribe audio data to text using Google Speech-to-Text API.
    
    Args:
        audio_data (bytes): The audio data to transcribe
        
    Returns:
        str: The transcribed text
    """
    # Placeholder for implementation
    # This would use Google's Speech-to-Text API
    pass

def synthesize_speech(text: str) -> bytes:
    """
    Synthesize speech from text using Google Text-to-Speech API.
    
    Args:
        text (str): The text to convert to speech
        
    Returns:
        bytes: The synthesized audio data
    """
    # Placeholder for implementation
    # This would use Google's Text-to-Speech API
    pass 