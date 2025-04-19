# ShopSight AI Shopping Assistant 🛍️

ShopSight is an interactive web application demonstrating an AI-powered shopping assistant. Built with Streamlit, Langchain, and Google's Gemini LLM, it allows users to find products, get details, and receive recommendations through a conversational chat interface and visual product browsing.

## Overview

The core of ShopSight is an AI agent designed to simulate a helpful e-commerce assistant. Users can:

*   **Chat Naturally:** Ask questions about products in plain English.
*   **Filter Precisely:** Use sidebar filters for category, price, brand, rating, and stock status.
*   **Browse Visually:** Explore featured products and categories on the initial screen.
*   **Get Information:** Request detailed specifications or stock availability for specific products.

## Features

*   **Conversational AI Agent:** Powered by Google Gemini (`gemini-1.5-pro-latest`) via Langchain.
*   **Multi-Turn Chat Interface:** Remembers conversation history for context.
*   **Product Discovery Tools:** The agent can utilize the following tools:
    *   `search_products`: Finds products based on keywords, category, price range, brand, minimum rating, stock status, and sorting preferences.
    *   `get_product_details`: Retrieves detailed information for a specific product ID.
    *   `check_stock`: Confirms if a product ID is currently in stock.
    *   `list_product_categories`: Lists all available product categories and their counts.
    *   `get_category_products`: Retrieves products within a specific category (primarily used by category buttons).
    *   `recommend_products`: Suggests products based on user queries, often prioritizing higher ratings or budget constraints.
*   **Interactive Streamlit UI:**
    *   Clean chat interface for user/assistant messages.
    *   Sidebar with multi-tab filtering options (Basic & Advanced).
    *   Dynamic loading of categories, price ranges, and brands for filters.
    *   Visual product card display (currently using placeholders for images).
    *   Featured products section on the home view.
    *   Category browsing cards.
    *   "New Conversation" and "Export Chat" options.
*   **Data Handling:** Uses Pandas to load and filter product data from a CSV file (`data/products.csv`).
*   **Configuration:** Loads API keys securely via a configuration file.

## Technology Stack

*   **Frontend:** Streamlit
*   **Backend / Language:** Python 3
*   **AI / LLM:** Google Gemini (via `google-generativeai`)
*   **Agent Framework:** Langchain (`langchain`, `langchain-google-genai`, `langchain-core`)
*   **Data Manipulation:** Pandas
*   **Configuration:** python-dotenv, JSON
*   **Dependencies:** See `requirements.txt` for all packages.

## Setup and Installation

1.  **Clone the Repository:**
    ```bash
    # Replace with your repository URL if applicable
    git clone https://your-repository-url/ShopSight.git
    cd ShopSight
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    # Create a virtual environment
    python -m venv .venv 
    
    # Activate it (Linux/macOS)
    source .venv/bin/activate
    
    # Activate it (Windows)
    # .\venv\Scripts\activate 
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Key:**
    *   Create a directory named `config` in the project root.
    *   Inside `config`, create a file named `api_keys.json`.
    *   Add your Google AI API key to this file in the following JSON format:
        ```json
        {
            "GOOGLE_API_KEY": "YOUR_GOOGLE_API_KEY_HERE"
        }
        ```
    *   *Alternatively, ensure your key is set as an environment variable `GOOGLE_API_KEY` if the code is modified to use `dotenv` directly (currently it primarily uses the JSON file via `utils.load_api_keys`).*

5.  **Ensure Product Data:**
    *   Make sure the `products.csv` file is located in a `data` directory within the project root (`data/products.csv`).
    *   The CSV should have columns like: `product_id`, `name`, `description`, `price`, `category`, `brand`, `color`, `size`, `material`, `weight`, `in_stock`, `rating`.

## Running the Application

Once the setup is complete, run the Streamlit application from the project's root directory:

```bash
streamlit run app.py
```

The application should open in your default web browser.

## Screenshots / Demo

*(Placeholder: Add screenshots here later. Consider creating an `/images` directory in the repository.)*

*   *Example: Screenshot of the main interface with featured products.* 
*   *Example: Screenshot showing filter options in the sidebar.*
*   *Example: Screenshot of a chat interaction with the AI assistant.*

## Future Improvements

*   Integrate ChromaDB (from `data_loader.py`) for semantic product search instead of relying solely on keyword matching.
*   Implement actual image loading for product cards.
*   Add user authentication.
*   Develop a full cart/checkout simulation.
*   More sophisticated recommendation engine. 