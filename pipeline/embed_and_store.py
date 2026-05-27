import os
os.environ['HF_HOME'] = os.getenv(
    'HF_CACHE_DIR', 
    'D:\\omproject\\hf_cache'
)
os.environ['TRANSFORMERS_CACHE'] = os.getenv(
    'TRANSFORMERS_CACHE',
    'D:\\omproject\\hf_cache'
)
os.makedirs('D:\\omproject\\hf_cache', exist_ok=True)
import json
import time
from datetime import datetime
import chromadb
from sentence_transformers import SentenceTransformer

def main():
    # 1. Load schemes_raw.json
    current_dir = os.path.dirname(__file__)
    json_path = os.path.join(current_dir, "schemes_raw.json")
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found. Please run scrape_schemes.py first.")
        return

    print(f"Loading schemes from {json_path}...")
    with open(json_path, "r", encoding="utf-8") as f:
        schemes = json.load(f)

    # 2. Load the model
    print("\nDownloading paraphrase-multilingual-MiniLM-L12-v2 model...")
    print("This is a one-time download (~120MB)")
    print("Please wait...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("Model loaded successfully!")

    # 3. Setup ChromaDB persistent storage
    chroma_path = os.path.abspath(os.path.join(current_dir, "..", "chroma_db"))
    print(f"\nConnecting to ChromaDB at {chroma_path}...")
    client = chromadb.PersistentClient(path=chroma_path)
    
    # Handle "collection already exists"
    collection_name = "govt_schemes"
    try:
        # Try to create it
        collection = client.create_collection(name=collection_name)
        print("Created new collection.")
    except Exception:
        # If it exists, clear and recreate
        print("Collection already exists. Clearing old data...")
        client.delete_collection(name=collection_name)
        collection = client.create_collection(name=collection_name)
        print("Recreated collection for fresh data.")

    # 4. Prepare data for embedding
    documents = []
    metadatas = []
    ids = []

    print(f"\nPreparing {len(schemes)} schemes for embedding...")
    for i, scheme in enumerate(schemes):
        name = scheme.get("name", "Unknown Scheme")
        benefit = scheme.get("benefit", "")
        eligibility = scheme.get("eligibility", "")
        ministry = scheme.get("ministry", "Unknown Ministry")
        apply_link = scheme.get("apply_link", "")
        
        tags = scheme.get("tags", [])
        tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)
            
        code = scheme.get("id")
        if not code:
            code = f"SCHEME_{i}"

        # MiniLM works without prefixes
        doc_text = f"scheme: {name} benefit: {benefit} eligibility: {eligibility} ministry: {ministry} tags: {tags_str}"
        documents.append(doc_text)
        
        # Save exact metadata format
        metadata = {
            "scheme_code": code,
            "name": name,
            "beneficiary_types": tags_str,
            "ministry": ministry,
            "apply_link": apply_link,
            "benefit_amount": benefit[:100]  # Chroma metadata is best kept short
        }
        metadatas.append(metadata)
        ids.append(code)

    # 5. Batching and Embedding (Memory Issue Fix)
    BATCH_SIZE = 32
    total = len(documents)
    
    print(f"\nStarting embedding process (Batch Size: {BATCH_SIZE})...")
    for i in range(0, total, BATCH_SIZE):
        batch_docs = documents[i:i+BATCH_SIZE]
        batch_ids = ids[i:i+BATCH_SIZE]
        batch_metadatas = metadatas[i:i+BATCH_SIZE]
        
        print(f"  -> Encoding batch {min(i+BATCH_SIZE, total)}/{total}...")
        
        # We normalize embeddings for e5 (it improves cosine similarity)
        batch_embeddings = model.encode(batch_docs, normalize_embeddings=True).tolist()
        
        # Store in ChromaDB
        collection.add(
            documents=batch_docs,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas,
            ids=batch_ids
        )
        
    # 6. Verification
    print("\n--- VERIFICATION ---")
    count = collection.count()
    print(f"Successfully stored {count} schemes")
    
    # Test query (without prefix for MiniLM)
    test_q = "farmer income support"
    print(f"\nRunning test query: '{test_q}'")
    query_emb = model.encode([test_q], normalize_embeddings=True).tolist()
    
    test_results = collection.query(
        query_embeddings=query_emb,
        n_results=3
    )
    
    print("Test query results:")
    if test_results['documents'] and len(test_results['documents']) > 0:
        for r in test_results['documents'][0]:
            print(f"  - {r[:100]}...")
    else:
        print("  - No results found!")

    # 7. Save metadata file
    info_path = os.path.join(current_dir, "chroma_info.json")
    info_data = {
        "total_schemes": count,
        "model_used": "paraphrase-multilingual-MiniLM-L12-v2",
        "created_at": datetime.now().isoformat(),
        "chroma_path": chroma_path
    }
    
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(info_data, f, indent=2)
        
    print(f"\nMetadata saved to {info_path}")

if __name__ == "__main__":
    main()
