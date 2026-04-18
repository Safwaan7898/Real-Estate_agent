"""RAG retriever for property documents using FAISS + SentenceTransformers."""
import os
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).parent.parent / "data" / "property_docs"

_index = None
_chunks: List[str] = []
_model = None


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_pdfs() -> List[str]:
    """Extract text chunks from all PDFs in the docs directory."""
    chunks = []
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.warning("pypdf not installed; skipping PDF loading.")
        return chunks

    for pdf_path in DOCS_DIR.glob("*.pdf"):
        try:
            reader = PdfReader(str(pdf_path))
            for page in reader.pages:
                text = page.extract_text() or ""
                # Split into ~500-char chunks with overlap
                for i in range(0, len(text), 400):
                    chunk = text[i:i + 500].strip()
                    if len(chunk) > 50:
                        chunks.append(chunk)
        except Exception as e:
            logger.error(f"Error reading {pdf_path}: {e}")
    return chunks


def build_index() -> bool:
    """Build FAISS index from property documents. Returns True if successful."""
    global _index, _chunks
    try:
        import faiss
        import numpy as np

        _chunks = _load_pdfs()
        if not _chunks:
            logger.info("No PDF chunks found; RAG index not built.")
            return False

        model = _get_model()
        embeddings = model.encode(_chunks, show_progress_bar=False)
        embeddings = np.array(embeddings, dtype="float32")
        faiss.normalize_L2(embeddings)

        dim = embeddings.shape[1]
        _index = faiss.IndexFlatIP(dim)
        _index.add(embeddings)
        logger.info(f"RAG index built with {len(_chunks)} chunks.")
        return True
    except Exception as e:
        logger.error(f"Failed to build RAG index: {e}")
        return False


def retrieve(query: str, top_k: int = 3) -> str:
    """Retrieve top-k relevant chunks for a query."""
    global _index, _chunks
    if _index is None:
        build_index()
    if _index is None or not _chunks:
        return "No property documents available for retrieval."

    try:
        import faiss
        import numpy as np

        model = _get_model()
        q_emb = model.encode([query], show_progress_bar=False)
        q_emb = np.array(q_emb, dtype="float32")
        faiss.normalize_L2(q_emb)

        scores, indices = _index.search(q_emb, min(top_k, len(_chunks)))
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and score > 0.3:
                results.append(f"[Score: {score:.2f}] {_chunks[idx]}")
        return "\n\n".join(results) if results else "No relevant documents found."
    except Exception as e:
        logger.error(f"Retrieval error: {e}")
        return "Retrieval failed."
