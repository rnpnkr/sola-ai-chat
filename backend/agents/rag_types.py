from typing import List, Dict
from typing_extensions import TypedDict
from pydantic import BaseModel

class Document(BaseModel):
    """Lightweight representation of a retrieved knowledge chunk."""

    id: str | None = None
    content: str
    title: str | None = None
    source_url: str | None = None
    category: str | None = None
    techniques: Dict | None = None
    relevance_score: float = 0.0

class RAGState(TypedDict, total=False):
    """TypedDict flow state for the Self-RAG LangGraph workflow."""

    # Core inputs
    user_message: str
    conversation_context: str
    user_id: str

    # Retrieval & doc grading
    should_retrieve: bool
    search_query: str
    documents: List[Document]
    graded_documents: List[Document]

    # Generation / output
    final_response: str
    citations: List[str]
    generation_attempts: int

    # Quality metrics
    answer_quality_score: float 