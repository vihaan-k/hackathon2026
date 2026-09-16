import os
import sys
import logging
from pathlib import Path
from pypdf import PdfReader

logging.getLogger("pypdf").setLevel(logging.ERROR)

def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    """Splits text into overlapping character windows."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def load_and_chunk_pdfs(pdf_dir="documents"):
    all_chunks = []
    pdf_folder = Path(pdf_dir)

    for pdf_path in pdf_folder.glob("*.pdf"):
        # Extract metadata directly from filename conventions
        is_historical = pdf_path.name.startswith("HISTORICAL-")
        status = "HISTORICAL" if is_historical else "CURRENT"

        with open(os.devnull, "w") as fnull:
            old_stdout = sys.stdout
            sys.stdout = fnull
            try:
                reader = PdfReader(pdf_path, strict=False)
                pages = list(reader.pages)
            finally:
                sys.stdout = old_stdout

        for page_num, page in enumerate(pages, start=1):
            text = page.extract_text()
            if not text or not text.strip():
                continue

            # Standardize whitespace across extracted lines
            clean_text = " ".join(text.split())
            page_chunks = chunk_text(clean_text, chunk_size=800, overlap=150)

            fname = pdf_path.name.lower()
            if "schoten" in fname:
                authority = "Gemeente Schoten"
            elif "antwerpen" in fname:
                authority = "Provincie Antwerpen"
            elif "vlaio" in fname or "favv" in fname or "omgevingsloket" in fname:
                authority = "Vlaams / Federaal"
            else:
                authority = "Overig"

            for chunk_idx, chunk_str in enumerate(page_chunks):
                all_chunks.append(
                    {
                        "id": f"{pdf_path.stem}_p{page_num}_c{chunk_idx}",
                        "text": chunk_str,
                        "metadata": {
                            "source_file": pdf_path.name,
                            "page": page_num,
                            "status": status,
                            "authority": authority
                        },
                    }
                )

    return all_chunks

if __name__ == "__main__":
    chunks = load_and_chunk_pdfs()
    print(f"Total Chunks Processed: {len(chunks)}")
    
    if chunks:
        lengths = [len(c["text"]) for c in chunks]
        print(f"Shortest: {min(lengths)} | Longest: {max(lengths)} | Avg: {sum(lengths)/len(lengths):.1f}")
        
        print("\n--- SAMPLE CHUNK FOR FRONTEND/EMBEDDINGS ---")
        print(f"ID: {chunks[0]['id']}")
        print(f"Metadata: {chunks[0]['metadata']}")
        print(f"Text Preview:\n{chunks[0]['text']}")