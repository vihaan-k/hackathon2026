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

# Defined test cases covering key hackathon scenarios
TEST_CASES = [
    {
        "id": "TC1_MARKET_FEES",
        "description": "Specific pricing/fee lookup for Schoten market stalls",
        "question": "Hoeveel kost een standplaats voor een marktkraam in Schoten per jaar of per meter?",
        "expected_keywords": ["15", "meter", "jaar", "retributie", "2026"],
        "expected_doc": "Schoten-markt-en-kermisretributies-2026-2031.pdf"
    },
    {
        "id": "TC2_TERRACE_RULES",
        "description": "Rules and conditions for open-air terraces in Schoten",
        "question": "Aan welke regels moet een terras in Schoten voldoen?",
        "expected_keywords": ["terras", "vergunning", "doorgang", "voetgangers"],
        "expected_doc": "Schoten-terrasreglement.pdf"
    },
    {
        "id": "TC3_STARTUP_GUIDANCE",
        "description": "General business startup assistance from regional guidance",
        "question": "Waar moet een startende ondernemer in Vlaanderen op letten bij het starten van een zaak?",
        "expected_keywords": ["KBO", "ondernemingsnummer", "VLAIO", "starten"],
        "expected_doc": "VLAIO-Handleiding-starten-van-een-zaak-2026-01.pdf"
    },
    {
        "id": "TC4_HISTORICAL_FILTER",
        "description": "Verify metadata tagging catches older/historical background material",
        "question": "Wat waren de regels voor de omgevingsvergunning voor kleinhandel in 2019?",
        "expected_keywords": ["omgevingsloket", "kleinhandel", "vergunning"],
        "expected_doc": "HISTORICAL-omgevingsloket-handleiding-kleinhandel-2019.pdf"
    }
]

def run_rag_tests():
    print("==================================================")
    print("       RUNNING BACKEND RAG SUITE VERIFICATION      ")
    print("==================================================\n")

    passed_tests = 0

    for test in TEST_CASES:
        print(f"Executing: [{test['id']}] - {test['description']}")
        print(f"Query: \"{test['question']}\"")

        # 1. Generate Query Vector
        res = openai_client.embeddings.create(
            input=test["question"],
            model="text-embedding-3-small"
        )
        q_vector = res.data[0].embedding

        # 2. Search Database
        matches = supabase.rpc(
            "match_documents",
            {"query_embedding": q_vector, "match_threshold": 0.3, "match_count": 3}
        ).execute().data

        if not matches:
            print("  ❌ FAIL: No relevant chunks retrieved above threshold (0.3)\n")
            continue

        top_match = matches[0]
        retrieved_doc = top_match["metadata"]["source_file"]
        retrieved_text = top_match["content"].lower()

        # 3. Evaluate Match Quality
        doc_matched = test["expected_doc"].lower() in retrieved_doc.lower()
        keyword_hits = [kw for kw in test["expected_keywords"] if kw.lower() in retrieved_text]
        score = top_match["similarity"]

        print(f"  -> Top Source: {retrieved_doc} (Page {top_match['metadata']['page']})")
        print(f"  -> Similarity: {score:.2f}")
        print(f"  -> Keyword Matches: {len(keyword_hits)}/{len(test['expected_keywords'])} {keyword_hits}")

        # Test criteria: similarity > 0.50 and expected doc matches
        if doc_matched and score >= 0.50:
            print("  STATUS: ✅ PASS\n")
            passed_tests += 1
        else:
            print(f"  STATUS: ⚠️ WARNING (Expected doc: {test['expected_doc']})\n")

    print("==================================================")
    print(f"RESULTS SUMMARY: {passed_tests}/{len(TEST_CASES)} Test Cases Passed Cleanly")
    print("==================================================")

if __name__ == "__main__":
    run_rag_tests()