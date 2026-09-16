import os
from openai import OpenAI
from pipeline import extract_municipality, generate_officer_payload, openai_client

def generate_email_from_draft(approved_text: str, municipality: str) -> str:
    """Generates a formal professional email based on the approved answer."""
    prompt = f"""Schrijf op basis van onderstaande goedgekeurde ambtelijke inhoud een professionele, vriendelijke e-mail naar een ondernemer/burger in de gemeente {municipality}. 
    De toon moet behulpzaam, formeel en helder zijn.
    
    GOEDGEKEURDE INHOUD:
    {approved_text}
    """
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def run_interactive_workflow():
    print("==================================================")
    print("  Lokale Economie & Bestuur Assistant (Clean View)")
    print("==================================================")
    print("Typ 'exit' of 'quit' om te sluiten.\n")
    
    while True:
        try:
            # 1. Input question
            question = input("\n[Vraag aan de assistent] > ").strip()
            if question.lower() in ["exit", "quit"]:
                print("\nTot ziens!")
                break
            if not question:
                continue
                
            print("\n⏳ Gemeente detecteren & documenten doorzoeken...")
            municipality = extract_municipality(question)
            output = generate_officer_payload(question, municipality)
            
            # Extract fields cleanly from the response payload dictionary
            # Adjust keys to match your FullOfficerResponse schema fields (e.g., 'response' or 'answer')
            answer_text = output.get("answer", output.get("response", "Geen antwoord gegenereerd."))
            evidence = output.get("evidence", {})
            exact_passage = evidence.get("exact_passage", "Geen passage beschikbaar")
            
            # 2. Display Clean AI Paragraph, Proof, and Metadata (No JSON)
            print("\n" + "═" * 50)
            print(" 📄 AI CONCEPT ANTWOORD")
            print("═" * 50)
            print(f"{answer_text}\n")
            
            print("─" * 50)
            print(" 🔍 BRON & BEWIJS")
            print("─" * 50)
            print(f"• **Bronbestand:** {evidence.get('source_file', 'Onbekend')}")
            print(f"• **Pagina:** {evidence.get('page', 'Onbekend')}")
            print(f"• **Exacte passage:**\n  > \"{exact_passage}\"")
            
            print("─" * 50)
            print(" 📊 METADATA")
            print("─" * 50)
            print(f"• **Gemeente:** {municipality}")
            print(f"• **Model:** gpt-4o")
            print("═" * 50 + "\n")
            
            # 3. Prompt user for choices
            while True:
                choice = input("Kies een optie -> [1] goedkeuren / [2] corrigeren / [3] annuleren: ").strip().lower()
                
                if choice in ["1", "goedkeuren"]:
                    print("\n✉️ E-mail genereren op basis van dit concept...")
                    email_draft = generate_email_from_draft(answer_text, municipality)
                    print("\n" + "─" * 20 + " GEGENEREERDE E-MAIL " + "─" * 20)
                    print(email_draft)
                    print("─" * 61)
                    print("✅ Workflow voltooid. Je kunt een nieuwe vraag stellen.\n")
                    break
                    
                elif choice in ["2", "corrigeren"]:
                    correction = input("\n✍️ Voer je correctie of gewijzigde instructie in: ").strip()
                    print("🔄 Antwoord aanpassen met je feedback...")
                    refined_prompt = f"{question}\n\nFeedback van ambtenaar voor correctie: {correction}"
                    output = generate_officer_payload(refined_prompt, municipality)
                    answer_text = output.get("answer", output.get("response", ""))
                    print("\n✨ **Bijgewerkt concept:**")
                    print(answer_text)
                    continue
                    
                elif choice in ["3", "annuleren"]:
                    print("\n❌ Actie geannuleerd. Stel gerust een nieuwe vraag.\n")
                    break
                else:
                    print("⚠️ Ongeldige keuze. Typ 'goedkeuren', 'corrigeren' of 'annuleren'.")
                    
        except Exception as e:
            print(f"\n❌ [Fout]: {str(e)}\n")

if __name__ == "__main__":
    run_interactive_workflow()