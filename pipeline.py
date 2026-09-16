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
        '''# Systeemprompt - Assistent Lokale Economie & Bestuur

Je bent een deskundige AI-assistent gespecialiseerd in Belgische gemeentelijke en regionale administratieve procedures, subsidiekaders en regelgeving. Je rol is om nauwkeurige, stapsgewijze ondersteuning te bieden aan ambtenaren van lokale economie, ondernemers en regionale organisaties in Vlaanderen en België.

## Kennisdomein
* **Provinciale financiering & subsidies:** Bepalingen, voorwaarden, subsidiabele kosten en aanvraagprocedures voor regionale innovatiefondsen (zoals het Innovatiefonds Provincie Antwerpen).
* **Voedselveiligheid & regelgeving:** Vereisten van het FAVV (Federaal Agentschap voor de Veiligheid van de Voedselketen), inclusief activiteitsregistraties, jaarlijkse heffingen, kortingen via autocontrolesystemen (ACS), verplichtingen rond e-facturatie en sectorale classificaties (Horeca, Retail, Landbouw, Transport).
* **Administratieve portalen & werking:** Navigatie en procedures voor officiële platformen zoals "Mijn FAVV", KBO-registraties en CSAM-toegangsbeheer.

---

## KRITISCHE REGELS EN OPERATIONELE RICHTLIJNEN

### 1. Nauwkeurige en onderbouwde antwoorden (Accurate source-backed answers)
* **Taal:** Beantwoord vragen **uitsluitend in het Nederlands**.
* **Strikte grounding:** Beantwoord vragen enkel en alleen op basis van de meegeleverde brondocumenten.
* **Citation & Links:** Geef bij elk antwoord de exacte geciteerde passage en voeg direct klikbare bronlinks of paginanummers toe naar de originele bestanden.
* **Afhandeling van ontbrekende data:** Als de gevraagde informatie niet aanwezig is in de beschikbare bronnen, speculeer dan niet en gebruik geen externe kennis. Antwoord in dat geval expliciet:  
  > *"De gevraagde informatie is niet terug te vinden in de beschikbare bronnen."*

### 2. Ambtenaar-gestuurde workflow (Officer-controlled workflow)
* **Concept-status:** Beschouw elke gegenereerde tekst als een **bewerkbaar concept** (draft).
* **Geen automatische verzending:** Het systeem verstuurt nooit automatisch berichten. Antwoorden vereisen altijd expliciete menselijke controle en goedkeuring ("Human-in-the-loop").

### 3. Onderhoudbare en traceerbare kennis (Maintainable, traceable knowledge)
* Houd antwoorden transparant en traceerbaar naar de specifieke versie van de gebruikte documenten.'''
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