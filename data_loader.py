import pandas as pd
from sentence_transformers import SentenceTransformer
import chromadb
from typing import Optional
import utils

def load_products_from_csv(filepath: str) -> pd.DataFrame:
    """
    Load product data from a CSV file
    
    Args:
        filepath (str): Path to the CSV file
        
    Returns:
        pd.DataFrame: DataFrame containing product data
        
    Raises:
        FileNotFoundError: If the CSV file is not found
    """
    try:
        df = pd.read_csv(filepath)
        print(f"Successfully loaded {len(df)} products from {filepath}")
        return df
    except FileNotFoundError:
        print(f"Error: File {filepath} not found")
        raise

def create_or_get_chroma_collection(persist_directory: str, collection_name: str) -> chromadb.Collection:
    """
    Initialize ChromaDB client and get or create a collection
    
    Args:
        persist_directory (str): Directory to persist ChromaDB data
        collection_name (str): Name of the collection
        
    Returns:
        chromadb.Collection: ChromaDB collection object
    """
    client = chromadb.PersistentClient(path=persist_directory)
    collection = client.get_or_create_collection(name=collection_name)
    return collection

def load_and_vectorize_data(csv_filepath: str, persist_directory: str, collection_name: str) -> None:
    """
    Load product data from CSV, generate embeddings, and store in ChromaDB
    
    Args:
        csv_filepath (str): Path to the CSV file
        persist_directory (str): Directory to persist ChromaDB data
        collection_name (str): Name of the collection
    """
    # Load products from CSV
    df = load_products_from_csv(csv_filepath)
    
    # Initialize the sentence transformer model
    print("Initializing Sentence Transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Get or create ChromaDB collection
    print(f"Creating or getting ChromaDB collection '{collection_name}'...")
    collection = create_or_get_chroma_collection(persist_directory, collection_name)
    
    # Prepare data for ChromaDB
    ids = []
    embeddings = []
    metadatas = []
    documents = []
    
    # Required columns for processing
    required_columns = ['product_id', 'name', 'description', 'price']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f"Warning: Missing required columns: {missing_columns}")
        print("Continuing with available columns...")
    
    # Process each product
    print(f"Processing {len(df)} products...")
    for _, row in df.iterrows():
        # Handle potential missing data
        product_id = str(row.get('product_id', ''))
        name = str(row.get('name', ''))
        description = str(row.get('description', ''))
        price = float(row.get('price', 0.0))
        
        # Skip rows with missing critical information
        if not product_id or not name:
            print(f"Skipping row with insufficient data: {row.to_dict()}")
            continue
        
        # Construct text for embedding
        text_for_embedding = f"Name: {name} Description: {description} Price: ${price}"
        
        # Add other specifications if available
        for col in row.index:
            if col not in ['product_id', 'name', 'description', 'price'] and not pd.isna(row[col]):
                text_for_embedding += f" {col}: {row[col]}"
        
        # Generate embedding
        embedding = model.encode(text_for_embedding)
        
        # Prepare metadata (convert row to dict, ensuring appropriate types)
        metadata = row.to_dict()
        # Ensure price is float
        if 'price' in metadata:
            metadata['price'] = float(metadata['price'])
        
        # Add to lists
        ids.append(product_id)
        embeddings.append(embedding.tolist())
        metadatas.append(metadata)
        documents.append(text_for_embedding)
    
    # Add data to ChromaDB collection (upsert for idempotency)
    if ids:
        print(f"Adding {len(ids)} products to ChromaDB collection...")
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
        )
        print("Successfully added products to ChromaDB collection")
    else:
        print("No valid products found to add to ChromaDB")

if __name__ == "__main__":
    # Use constants from utils
    print("Starting data loading and vectorization process...")
    load_and_vectorize_data(
        csv_filepath=utils.CSV_FILEPATH,
        persist_directory=utils.PERSIST_DIRECTORY,
        collection_name=utils.CHROMA_COLLECTION_NAME
    )
    print("Data loading and vectorization process completed") 