"""RAG (Retrieval-Augmented Generation) layer for RIVET Pro.

Provides semantic search over knowledge base with vendor/equipment filtering
and KB coverage estimation for routing decisions.
"""

# Lazy imports to avoid loading database dependencies unless needed
def __getattr__(name):
    if name == "search_docs":
        from agent_factory.rivet_pro.rag.retriever import search_docs
        return search_docs
    elif name == "estimate_coverage":
        from agent_factory.rivet_pro.rag.retriever import estimate_coverage
        return estimate_coverage
    elif name == "RetrievedDoc":
        from agent_factory.rivet_pro.rag.retriever import RetrievedDoc
        return RetrievedDoc
    elif name == "RAGConfig":
        from agent_factory.rivet_pro.rag.config import RAGConfig
        return RAGConfig
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "search_docs",
    "estimate_coverage",
    "RetrievedDoc",
    "RAGConfig",
]
