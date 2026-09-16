# schema.py
from typing import List, Optional
from pydantic import BaseModel, Field

class AiAnswerBlock(BaseModel):
    source_count: int = Field(description="Number of unique sources consulted, e.g. 1")
    proof_status: str = Field(description="Status label, e.g. 'Onderbouwd'")
    summary: str = Field(description="Opening sentence summarizing the answer")
    requirements: List[str] = Field(description="Numbered/bulleted requirements extracted from the text")
    disclaimer: str = Field(description="Closing contextual notice regarding municipal approval")
    live_verification_note: str = Field(description="Warning regarding potential fee or policy updates")

class EmailDraftBlock(BaseModel):
    subject: str = Field(description="Formal email subject line in Dutch")
    body_paragraphs: List[str] = Field(description="List of text paragraphs forming the body of the email")
    sources_footer: List[str] = Field(description="Formatted list of citations to display at the bottom of the email")

class EvidenceBlock(BaseModel):
    kb_type: str = "PDF-kennisbank"
    primary_source: str = Field(description="Full name of the document, e.g. 'Marktreglement Gemeente Schoten'")
    authority: str = Field(description="Issuing authority, e.g. 'Gemeente Schoten'")
    source_type: str = Field(description="Legal type, e.g. 'Gemeentelijk reglement'")
    status: str = Field(description="Current status, e.g. 'Toepasbaarheid te controleren'")
    date: str = Field(description="Date of adoption/publication, e.g. '28 maart 2024'")
    article: str = Field(description="Relevant article number, e.g. 'Artikel 13 §3'")
    pages: str = Field(description="Page numbers, e.g. '5–6'")
    exact_passage: str = Field(description="Verbatim exact quote copied from the retrieved chunk text")
    pdf_url: Optional[str] = Field(default="", description="URL or anchor link to open the PDF page")

class FullOfficerResponse(BaseModel):
    question: str
    municipality: str
    ai_answer: AiAnswerBlock
    email_draft: EmailDraftBlock
    evidence: EvidenceBlock