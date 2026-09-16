import os
from openai import OpenAI
from supabase import create_client, Client
from rag_pipeline import load_and_chunk_pdfs
from dotenv import load_dotenv

load_dotenv()
# Initialize Clients
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_API_KEY")
)

def embed_and_store():
    chunks = load_and_chunk_pdfs()
    print(f"Embedding {len(chunks)} chunks...")

    # Process in batches of 100 for speed
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        texts = [c["text"] for c in batch]

        # 1. Generate Embeddings
        response = openai_client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        embeddings = [data.embedding for data in response.data]

        # 2. Prepare Records for Supabase
        records = []
        for chunk, embedding in zip(batch, embeddings):
            records.append({
                "id": chunk["id"],
                "content": chunk["text"],
                "metadata": chunk["metadata"],
                "embedding": embedding
            })

        # 3. Upsert to Supabase vector table
        supabase.table("documents").upsert(records).execute()
        print(f"Stored chunks {i} to {i + len(batch)}")

if __name__ == "__main__":
    embed_and_store()