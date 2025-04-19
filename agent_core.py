import os
import json
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain.agents import create_openai_tools_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict, Any, Optional
import pandas as pd # Import pandas

import utils

# Configure Google Genai API with API key
try:
    api_keys = utils.load_api_keys()
    genai.configure(api_key=api_keys["GOOGLE_API_KEY"])
except Exception as e:
    print(f"Error configuring Google API: {str(e)}")
    raise e

# Load products data (just to get categories initially, real loading happens in utils)
try:
    products_df = utils.load_products_data()
except Exception as e:
    print(f"Initial product load failed: {e}")
    products_df = pd.DataFrame() # Create empty df if load fails

# Define tools for the agent to use
@tool
def search_products(
    query: Optional[str] = "", # Make query optional with default empty string
    min_price: Optional[float] = None, 
    max_price: Optional[float] = None, 
    category: Optional[str] = None, 
    brand: Optional[str] = None, 
    rating_min: Optional[float] = None, 
    in_stock_only: bool = True,
    sort_by: str = "price_low" # Add sort_by with default
) -> str:
    """
    Search for products based on a query string, price range, category, brand, rating, stock status, and sort order.
    If query is empty, searches based only on the other filters.
    
    Args:
        query: The search query to match against product names and descriptions (Optional)
        min_price: Minimum price filter (optional)
        max_price: Maximum price filter (optional)
        category: Category to filter by (optional)
        brand: Brand to filter by (optional)
        rating_min: Minimum rating filter (optional, 1.0-5.0)
        in_stock_only: Whether to show only in-stock items (default: True)
        sort_by: Sort order (options: "price_low", "price_high", "rating", "newest"; default: "price_low")
    
    Returns:
        String containing search results formatted for display
    """
    try:
        # Filter products using the updated utils function
        filtered_products = utils.search_products(
            query if query else "", # Pass empty string if query is None or empty
            min_price, 
            max_price, 
            category,
            brand,
            rating_min,
            in_stock_only,
            sort_by
        )
        
        if filtered_products.empty:
            return "No products found matching your criteria."
        
        # Format results
        results = []
        for _, product in filtered_products.iterrows():
            # Construct product info string
            product_info = f"ID: {product['id']}, Name: {product['name']}, Price: ${product['price']:.2f}, Category: {product['category']}"
            if 'brand' in product and pd.notna(product['brand']):
                product_info += f", Brand: {product['brand']}"
            if 'rating' in product and pd.notna(product['rating']):
                product_info += f", Rating: {product['rating']:.1f}/5"
            if 'in_stock' in product and pd.notna(product['in_stock']):
                 stock_status = "In Stock" if product['in_stock'] == True or str(product['in_stock']).lower() == 'true' else "Out of Stock"
                 product_info += f", Status: {stock_status}"
            results.append(product_info)
        
        result_text = "\n".join(results)
        
        # Add summary of results
        summary = f"Found {len(results)} products"
        if category:
            summary += f" in the {category} category"
        if brand:
             summary += f" from the {brand} brand"
        if min_price is not None and max_price is not None:
            summary += f" priced between ${min_price:.2f} and ${max_price:.2f}"
        elif min_price is not None:
            summary += f" priced above ${min_price:.2f}"
        elif max_price is not None:
            summary += f" priced below ${max_price:.2f}"
        if rating_min is not None:
            summary += f" with minimum rating {rating_min:.1f}"
        if in_stock_only:
            summary += " (in stock)"
            
        sort_descriptions = {
            "price_low": "sorted by price: low to high",
            "price_high": "sorted by price: high to low",
            "rating": "sorted by rating",
            "newest": "sorted by newest"
        }
        summary += f", {sort_descriptions.get(sort_by, '')}"
            
        return f"{summary}:\n\n{result_text}"
    
    except Exception as e:
        return f"Error searching products: {str(e)}"

@tool
def get_product_details(product_id: int) -> str:
    """
    Get detailed information about a specific product by its ID.
    
    Args:
        product_id: The ID of the product to look up
    
    Returns:
        String containing detailed product information
    """
    try:
        # Look up product by ID
        product = utils.get_product_by_id(product_id)
        
        if product is None:
            return f"No product found with ID {product_id}."
        
        # Format all product details nicely
        details = []
        for column, value in product.items():
            if pd.notna(value):  # Only include non-NaN values
                # Format price specifically
                if column == 'price':
                    details.append(f"{column.title()}: ${value:.2f}")
                elif column == 'rating':
                    details.append(f"{column.title()}: {value:.1f}/5")
                elif column == 'in_stock':
                     stock_status = "Yes" if value == True or str(value).lower() == 'true' else "No"
                     details.append(f"In Stock: {stock_status}")
                elif column != 'id': # Don't repeat ID
                    details.append(f"{column.title()}: {value}")
        
        return "\n".join(details)
    
    except Exception as e:
        return f"Error retrieving product details: {str(e)}"

@tool
def check_stock(product_id: int) -> str:
    """
    Check if a product is in stock.
    
    Args:
        product_id: The ID of the product to check stock for
    
    Returns:
        String indicating whether the product is in stock
    """
    try:
        # Look up product by ID
        product = utils.get_product_by_id(product_id)
        
        if product is None:
            return f"No product found with ID {product_id}."
        
        # Check stock status
        if 'in_stock' not in product or pd.isna(product['in_stock']):
            return f"Stock information not available for product {product_id} ({product['name']})."
        
        is_in_stock = product['in_stock'] == True or str(product['in_stock']).lower() == 'true'
        
        if is_in_stock:
            return f"Product {product_id} ({product['name']}) is in stock. 👍"
        else:
            return f"Product {product_id} ({product['name']}) is currently out of stock. 😞"
    
    except Exception as e:
        return f"Error checking stock: {str(e)}"

@tool
def list_product_categories() -> str:
    """
    Get a list of all product categories available in the store.
    
    Returns:
        String containing a list of all product categories with counts
    """
    try:
        if products_df.empty:
            return "Product data not loaded yet. Please try again shortly."
        
        categories = products_df['category'].value_counts().to_dict()
        
        if not categories:
            return "No product categories found."
        
        # Format results
        result_lines = [f"We have {len(categories)} product categories:"]
        for category, count in sorted(categories.items()):
            result_lines.append(f"- {category}: {count} products")
        
        return "\n".join(result_lines)
    
    except Exception as e:
        return f"Error listing categories: {str(e)}"

@tool
def get_category_products(category: str) -> str:
    """
    Get all products in a specific category.
    
    Args:
        category: The category to get products for
    
    Returns:
        String containing a list of products in the category
    """
    try:
        if products_df.empty:
            return "Product data not loaded yet. Please try again shortly."
            
        # Use the search_products function for consistency
        category_products = utils.search_products(query="", category=category, in_stock_only=False)
        
        if category_products.empty:
             return f"No products found in the '{category}' category. Perhaps try searching all categories or use the filters?"
        else:
            result = f"Products in the '{category}' category:\n\n"
        
        # Format results
        product_list = []
        for _, product in category_products.iterrows():
            product_info = f"ID: {product['id']}, Name: {product['name']}, Price: ${product['price']:.2f}"
            if 'rating' in product and pd.notna(product['rating']):
                 product_info += f", Rating: {product['rating']:.1f}/5"
            product_list.append(product_info)
        
        return result + "\n".join(product_list[:20]) + ("\n... (showing top 20 results)" if len(product_list) > 20 else "")
    
    except Exception as e:
        return f"Error getting category products: {str(e)}"

@tool
def recommend_products(query: str, budget: Optional[float] = None) -> str:
    """
    Recommend products based on user preferences or needs.
    
    Args:
        query: Description of what the user is looking for
        budget: Optional maximum budget
    
    Returns:
        String containing recommended products
    """
    try:
        # Search for products based on the query, prioritizing highly rated ones
        filtered_products = utils.search_products(query, max_price=budget, sort_by="rating")
        
        if filtered_products.empty:
            return "I couldn't find specific recommendations based on that. Maybe try broadening your search?"
        
        # Take top 5 recommendations
        top_recommendations = filtered_products.head(5)
        
        # Format results
        results = []
        for _, product in top_recommendations.iterrows():
            product_info = f"ID: {product['id']}, Name: {product['name']}, Price: ${product['price']:.2f}, Category: {product['category']}"
            
            # Add rating if available
            if 'rating' in product and pd.notna(product['rating']):
                product_info += f", Rating: {product['rating']:.1f}/5"
            
            results.append(product_info)
        
        result_text = "\n".join(results)
        
        budget_text = f" within your ${budget:.2f} budget" if budget is not None else ""
        return f"Here are my top recommendations{budget_text} based on '{query}':\n\n{result_text}"
    
    except Exception as e:
        return f"Error recommending products: {str(e)}"

# Dict of all tools
all_tools = {
    "search_products": search_products,
    "get_product_details": get_product_details,
    "check_stock": check_stock,
    "list_product_categories": list_product_categories,
    "get_category_products": get_category_products,
    "recommend_products": recommend_products
}

# Define custom prompt for the agent
custom_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are ShopSight, a friendly AI shopping assistant for an e-commerce store.

Your goal is to help customers find products, learn about product details, check availability, and get recommendations.

Be polite, helpful, and concise in your responses. Focus on answering the customer's questions to the best of your ability using the available tools.

When searching for products, clearly state the criteria used based on the user's request and the filter parameters provided.

If a customer asks about a product or category you don't have information about, apologize and suggest alternatives.

Always sound friendly and enthusiastic. Use emojis occasionally to appear more engaging. 😊

When a customer asks about products in a category, offer to show more details about specific products.

When recommending products, consider factors like budget, features, and ratings.

Available tools:
- search_products: Search for products based on query, price range, category, brand, rating, stock status, and sort order. Use this for nearly all product finding requests.
- get_product_details: Get detailed information about a specific product by ID. Use this when a user asks for details about a specific product ID.
- check_stock: Check if a product is in stock by ID. Use this only when explicitly asked about stock for a specific ID.
- list_product_categories: Get a list of all product categories. Use this when asked for available categories.
- get_category_products: Get all products in a specific category. Prefer search_products if other filters are involved.
- recommend_products: Recommend products based on user needs or preferences. Uses the search tool internally but formats as recommendations.

Use these tools effectively to provide the best shopping experience."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

def run_agent_interaction(query: str, chat_history: List, active_tools: List[str]) -> str:
    """
    Run the agent with the given query, chat history, and active tools.
    
    Args:
        query: The user's query
        chat_history: The chat history as a list of messages
        active_tools: List of tool names that are currently enabled
    
    Returns:
        The agent's response as a string
    """
    try:
        # Create LLM - Use a current and valid model name
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3)
        
        # Filter tools based on active tools
        filtered_tools = [all_tools[tool_name] for tool_name in active_tools if tool_name in all_tools]
        
        # Ensure essential tools are always available if they exist in all_tools
        required_tool_names = ["search_products", "get_product_details", "list_product_categories"]
        for req_tool in required_tool_names:
            if req_tool in all_tools and req_tool not in active_tools:
                filtered_tools.append(all_tools[req_tool])
        
        # Create agent with the filtered tools
        agent = create_openai_tools_agent(llm, filtered_tools, custom_prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=filtered_tools,
            verbose=False,
            handle_parsing_errors=True,
            max_iterations=5 # Add max iterations to prevent long loops
        )
        
        # Run the agent
        result = agent_executor.invoke({
            "input": query,
            "chat_history": chat_history
        })
        
        return result["output"]
    
    except Exception as e:
        error_message = f"I encountered an error while processing your request: {str(e)}"
        print(f"Agent error: {str(e)}")
        # Provide more specific feedback for common errors if possible
        if "quota" in str(e).lower():
            error_message = "Apologies, I seem to be quite popular right now and reached my processing limit. Please try again in a moment. ⏳"
        return error_message

if __name__ == "__main__":
    # Simple command-line test
    print("ShopSight Agent Test (Press Ctrl+C to exit)")
    print("-------------------------------------------")
    
    # Initialize chat history
    chat_history = []
    
    try:
        while True:
            # Get user input
            user_input = input("\nYou: ")
            
            # Add to chat history
            chat_history.append(HumanMessage(content=user_input))
            
            # Run agent interaction with all tools enabled for testing
            response = run_agent_interaction(user_input, chat_history, list(all_tools.keys()))
            
            # Add agent response to chat history
            chat_history.append(AIMessage(content=response))
            
            # Print agent response
            print(f"\nShopSight: {response}")
    except KeyboardInterrupt:
        print("\nExiting ShopSight Agent Test...")
    except Exception as e:
        print(f"\nAn error occurred: {str(e)}") 