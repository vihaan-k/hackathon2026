import os
from openai import OpenAI
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
supabase = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_API_KEY")
)

# Test query for Schoten market stall pricing
res = openai_client.embeddings.create(
    input="Wat zijn de tarieven en retributies voor een standplaats op de markt in Schoten?",
    model="text-embedding-3-small"
)
q_vector = res.data[0].embedding

matches = supabase.rpc(
    "match_documents",
    {"query_embedding": q_vector, "match_threshold": 0.3, "match_count": 3}
).execute()

for m in matches.data:
    print(f"[{m['metadata']['authority']}] {m['metadata']['source_file']} (Page {m['metadata']['page']})")
    print(f"Similarity: {m['similarity']:.2f}")
    print(f"Text: {m['content'][:150]}...\n")