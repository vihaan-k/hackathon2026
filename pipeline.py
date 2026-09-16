import os
import json
from openai import OpenAI
from supabase import create_client
from schema import FullOfficerResponse
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()
# Initialize SDKs
openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
supabase = create_client(
    os.environ.get("SUPABASE_URL"), 
    os.environ.get("SUPABASE_API_KEY")
)

def extract_municipality(question: str) -> str:    
    class EntityExtraction(BaseModel):
        municipality: str

    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system", 
                "content": "Extract the Belgian municipality or city mentioned in the prompt. If no municipality is explicitly mentioned, return the default."
            },
            {"role": "user", "content": f"Default: Antwerpen\nQuestion: {question}"}
        ],
        response_format=EntityExtraction
    )
    
    parsed = completion.choices[0].message.parsed
    return parsed.municipality if parsed else "Antwerpen"

def generate_officer_payload(question: str, municipality: str) -> dict:
    # 1. Embed Question
    res = openai_client.embeddings.create(
        input=f"{municipality}: {question}",
        model="text-embedding-3-small"
    )
    q_vector = res.data[0].embedding

    # 2. Vector Search (Supabase RPC)
    matches = supabase.rpc(
        "match_documents",
        {"query_embedding": q_vector, "match_threshold": 0.3, "match_count": 3}
    ).execute().data

    if not matches:
        raise ValueError("No matching regulatory context found.")

    # Select top context chunk
    top_chunk = matches[0]
    meta = top_chunk["metadata"]
    content = top_chunk["content"]

    # 3. Formulate Prompt
    system_prompt = (
        '''You are an expert AI assistant specializing in Belgian municipal and regional administrative procedures, funding frameworks, and regulatory compliance. Your role is to provide accurate, step-by-step guidance to local economy officers, business owners, and regional operators in Flanders and Belgium.

Your knowledge base includes:
1. Provincial Funding & Subsidies: Provisions, eligibility, eligible expenses, and application workflows for regional innovation funds (e.g., Innovatiefonds Provincie Antwerpen).
2. Food Safety & Regulatory Compliance: FAVV (Federal Agency for the Safety of the Food Chain) requirements, including activity registrations, annual levies, auto-control system (ACS) reductions, e-invoicing mandates, and sectoral classifications (Horeca, Retail, Agriculture, Transport).
3. Administrative Portals & Operations: Navigation and procedures for official platforms such as "Mijn FAVV", KBO/CBE registrations, and CSAM access management.

Guidelines for responses:
- Maintain a professional, clear, and practical tone tailored to Belgian administrative contexts.
- Provide direct, structured answers with relevant references to legal limits, criteria, and official procedures where applicable.'''
    )

    user_prompt = f"""MUNICIPALITY: {municipality}
OFFICER QUESTION: {question}

TOP RETRIEVED SOURCE:
Document: {meta.get('source_file')}
Authority: {meta.get('authority', municipality)}
Page: {meta.get('page')}

TEXT CONTENT:
{content}
"""

    # 4. Generate Structured Output in One Shot
    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=FullOfficerResponse
    )

    # Convert Pydantic object directly to Python dictionary
    message = completion.choices[0].message
    if message.refusal:
        raise ValueError(f"Model refused the request: {message.refusal}")

    if not message.parsed:
        raise ValueError("Failed to parse structured output from model response.")

    payload = message.parsed.model_dump()
    
    # Optionally override exact passage to ensure 100% verbatim grounding
    if "evidence" not in payload or payload["evidence"] is None:
        payload["evidence"] = {}

    payload["evidence"]["exact_passage"] = content.strip()

    return payload

if __name__ == "__main__":
    # Local Test Run
    q = "Hoe vraag ik een vaste standplaats aan op de markt in Schoten?"
    m = extract_municipality(q)
    
    output = generate_officer_payload(q, m)
    print(json.dumps(output, indent=2, ensure_ascii=False))