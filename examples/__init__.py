"""Few-shot RAG example system for RivetCEO Bot."""

from .schemas import MaintenanceCase, Equipment, CaseInput, Diagnosis, Resolution
from .store import CaseStore
from .embedder import CaseEmbedder
from .retriever import CaseRetriever, RetrievalResult
from .formatter import format_maintenance_examples, format_for_sme_prompt
from .integration import FewShotEnhancer, FewShotConfig

__all__ = [
    "MaintenanceCase",
    "Equipment",
    "CaseInput",
    "Diagnosis",
    "Resolution",
    "CaseStore",
    "CaseEmbedder",
    "CaseRetriever",
    "RetrievalResult",
    "format_maintenance_examples",
    "format_for_sme_prompt",
    "FewShotEnhancer",
    "FewShotConfig",
]
