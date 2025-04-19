#!/usr/bin/env python3
"""
ShopSight AI - Launch script
------------------------------
This script launches the ShopSight AI shopping assistant application.
"""

import os
import subprocess
import sys

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import langchain
        import google.generativeai
        import sentence_transformers
        import chromadb
        return True
    except ImportError as e:
        print(f"Error: Missing dependency - {e}")
        print("Please install all required packages using: pip install -r requirements.txt")
        return False

def check_env():
    """Check if .env file exists with API key"""
    if not os.path.exists(".env"):
        print("Error: .env file not found")
        print("Please create a .env file with your GOOGLE_API_KEY")
        return False
    
    with open(".env", "r") as f:
        if "GOOGLE_API_KEY" not in f.read():
            print("Error: GOOGLE_API_KEY not found in .env file")
            print("Please add your Gemini API key to the .env file as GOOGLE_API_KEY=your_key_here")
            return False
    
    return True

def check_data():
    """Check if products.csv and chroma_db directory exist"""
    if not os.path.exists("products.csv"):
        print("Warning: products.csv not found")
        print("The application may not work correctly without product data.")
    
    if not os.path.exists("./chroma_db"):
        print("Warning: chroma_db directory not found")
        print("You may need to run data_loader.py first to create the vector database.")
    
    return True

def main():
    """Main function to launch the application"""
    print("🛍️ Starting ShopSight AI Application")
    
    # Check requirements
    print("\nChecking requirements...")
    if not check_requirements():
        return
    
    # Check environment
    print("\nChecking environment...")
    if not check_env():
        return
    
    # Check data
    print("\nChecking data...")
    check_data()
    
    # Launch application
    print("\n✅ All checks passed! Launching ShopSight AI Application...")
    print("Access the application at: http://localhost:8501")
    
    try:
        subprocess.run(["streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n🛑 ShopSight AI Application stopped")
    except Exception as e:
        print(f"\n❌ Error launching application: {e}")

if __name__ == "__main__":
    main() 