"""Vector store wrapper for maintenance cases.

Reference: https://github.com/pixegami/rag-tutorial-v2/blob/main/populate_database.py
"""

import json
from pathlib import Path
from typing import List, Optional
from .schemas import MaintenanceCase

# TODO: Import your existing vector store client
# from your_existing_module import PineconeClient  # or SupabaseClient


class CaseStore:
    """
    Wrapper for storing and retrieving maintenance cases.

    Reuses existing RivetCEO vector store infrastructure.
    DO NOT create new infrastructure - use what exists.
    """

    def __init__(
        self,
        collection_name: str = "maintenance_cases",
        test_mode: bool = False
    ):
        self.collection_name = collection_name
        self.test_mode = test_mode
        self._cases: List[MaintenanceCase] = []  # In-memory for test mode

        if not test_mode:
            # TODO: Initialize your existing vector store client
            # self.client = PineconeClient() or SupabaseClient()
            raise NotImplementedError(
                "Production mode not implemented. "
                "Connect to existing Pinecone/Supabase vector store."
            )

    def add_case(self, case: MaintenanceCase) -> str:
        """Add a case to the store. Returns case_id."""
        if self.test_mode:
            self._cases.append(case)
            return case.case_id

        # TODO: Implement production storage
        # embedding = self.embedder.embed(case.to_embedding_text())
        # self.client.upsert(case.case_id, embedding, case.model_dump())
        raise NotImplementedError()

    def get_case(self, case_id: str) -> Optional[MaintenanceCase]:
        """Retrieve a case by ID."""
        if self.test_mode:
            for case in self._cases:
                if case.case_id == case_id:
                    return case
            return None

        # TODO: Implement production retrieval
        raise NotImplementedError()

    def list_cases(self) -> List[MaintenanceCase]:
        """List all cases."""
        if self.test_mode:
            return self._cases.copy()

        # TODO: Implement production listing
        raise NotImplementedError()

    def load_from_directory(self, cases_dir: str = "cases") -> int:
        """Load cases from JSON files in directory."""
        path = Path(cases_dir)
        if not path.exists():
            return 0

        loaded = 0
        for json_file in path.glob("*.json"):
            with open(json_file) as f:
                data = json.load(f)

                # Handle both single case and array of cases
                if isinstance(data, list):
                    for case_data in data:
                        case = MaintenanceCase(**case_data)
                        self.add_case(case)
                        loaded += 1
                else:
                    case = MaintenanceCase(**data)
                    self.add_case(case)
                    loaded += 1

        return loaded

    def count(self) -> int:
        """Return number of cases in store."""
        if self.test_mode:
            return len(self._cases)
        raise NotImplementedError()
