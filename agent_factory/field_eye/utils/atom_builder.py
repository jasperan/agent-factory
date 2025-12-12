"""
Vision Atom Builder for Field Eye.

Converts vision data (frames, defects, pauses) into Knowledge Atoms following
the Industrial Maintenance Knowledge Atom Standard v1.0.

Atoms are stored in Supabase with pgvector embeddings for semantic search.

Example Usage:
    >>> from agent_factory.field_eye.utils.atom_builder import VisionAtomBuilder
    >>>
    >>> builder = VisionAtomBuilder()
    >>>
    >>> # Build defect atom
    >>> frame_data = {"frame_number": 1234, "timestamp": "2025-12-11T17:30:00Z"}
    >>> defect_data = {
    ...     "defect_type": "missing_stripe",
    ...     "severity": "warning",
    ...     "bbox": {"x": 100, "y": 200, "width": 50, "height": 30},
    ...     "confidence": 0.92
    ... }
    >>> metadata = {"session_id": "abc123", "vehicle_id": "COASTER_001"}
    >>> atom = builder.build_defect_atom(frame_data, defect_data, metadata)
    >>>
    >>> # Upload to Supabase
    >>> atom_id = builder.upload_to_supabase(atom)
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class KnowledgeAtom:
    """
    Knowledge Atom data structure following Industrial Maintenance Standard v1.0.

    Simplified for Field Eye use case while remaining compatible with
    the full standard. Extended metadata stored in 'metadata' field.
    """
    atom_id: str
    type: str  # "fault", "observation", "measurement"
    manufacturer: str
    equipment_type: str
    title: str
    summary: str
    content: Dict[str, Any]
    embedding: Optional[List[float]] = None
    keywords: List[str] = field(default_factory=list)
    difficulty: str = "intermediate"
    source_document: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class VisionAtomBuilder:
    """
    Builds Knowledge Atoms from Field Eye vision data.

    Handles:
    - Defect detection atoms (missing torque stripes, wear, damage)
    - Observation atoms (general inspection notes)
    - Measurement atoms (sensor readings, dimensions)
    - Embedding generation via OpenAI
    - Upload to Supabase with pgvector storage
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        embedding_model: str = "text-embedding-3-small"
    ):
        """
        Initialize Vision Atom Builder.

        Args:
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            embedding_model: OpenAI embedding model (default: text-embedding-3-small)

        Raises:
            ValueError: If OpenAI API key not provided
            ImportError: If openai package not installed
        """
        # Initialize OpenAI client
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "OpenAI package required for embeddings. "
                "Install with: pip install openai"
            )

        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError(
                "OpenAI API key not found. "
                "Set OPENAI_API_KEY environment variable or pass to constructor."
            )

        self.openai_client = OpenAI(api_key=self.openai_api_key)
        self.embedding_model = embedding_model

        # Embedding dimensions by model
        self.embedding_dims = {
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
            "text-embedding-ada-002": 1536
        }

    def build_defect_atom(
        self,
        frame_data: Dict[str, Any],
        defect_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> KnowledgeAtom:
        """
        Build a defect Knowledge Atom from vision data.

        Args:
            frame_data: Frame information
                - frame_number: int
                - timestamp: str (ISO format)
                - image_path: Optional[str]
            defect_data: Defect detection results
                - defect_type: str (e.g., "missing_stripe", "wear", "damage")
                - severity: str ("critical", "warning", "info")
                - bbox: Dict (x, y, width, height)
                - confidence: float (0-1)
                - location: Optional[str] (human-readable location)
            metadata: Session/context metadata
                - session_id: str
                - vehicle_id: Optional[str]
                - equipment_type: Optional[str] (default: "torque_stripe")
                - manufacturer: Optional[str] (default: "unknown")

        Returns:
            KnowledgeAtom instance ready for upload

        Example:
            >>> frame_data = {
            ...     "frame_number": 1234,
            ...     "timestamp": "2025-12-11T17:30:00Z",
            ...     "image_path": "s3://field-eye/frames/session_abc/frame_1234.jpg"
            ... }
            >>> defect_data = {
            ...     "defect_type": "missing_stripe",
            ...     "severity": "warning",
            ...     "bbox": {"x": 100, "y": 200, "width": 50, "height": 30},
            ...     "confidence": 0.92,
            ...     "location": "wheel_assembly_bolt_3"
            ... }
            >>> metadata = {
            ...     "session_id": "abc123",
            ...     "vehicle_id": "COASTER_001",
            ...     "equipment_type": "torque_stripe"
            ... }
            >>> atom = builder.build_defect_atom(frame_data, defect_data, metadata)
        """
        # Extract data
        defect_type = defect_data["defect_type"]
        severity = defect_data.get("severity", "warning")
        confidence = defect_data.get("confidence", 0.0)
        location = defect_data.get("location", "unknown_location")
        bbox = defect_data.get("bbox", {})

        equipment_type = metadata.get("equipment_type", "torque_stripe")
        manufacturer = metadata.get("manufacturer", "unknown")
        vehicle_id = metadata.get("vehicle_id", "unknown_vehicle")
        session_id = metadata.get("session_id", "unknown_session")

        # Generate atom ID
        atom_uuid = str(uuid.uuid4())
        atom_id = f"field_eye:{equipment_type}:{defect_type}:{atom_uuid}"

        # Build title and summary
        title = f"{defect_type.replace('_', ' ').title()} Detected"
        summary = (
            f"{defect_type.replace('_', ' ').title()} on {location}, "
            f"{vehicle_id}, detected at {frame_data.get('timestamp', 'unknown time')}"
        )

        # Build content structure
        content = {
            "defect_type": defect_type,
            "severity": severity,
            "location": location,
            "image_path": frame_data.get("image_path", ""),
            "bounding_box": bbox,
            "confidence": confidence,
            "detected_by": "vision_analysis",
            "timestamp": frame_data.get("timestamp", datetime.now().isoformat()),
            "detection_details": {
                "frame_number": frame_data.get("frame_number", 0),
                "detection_method": defect_data.get("detection_method", "pause_analysis")
            }
        }

        # Extract keywords
        keywords = [
            equipment_type,
            defect_type,
            severity,
            location.split("_")[0] if "_" in location else location,
            manufacturer
        ]
        keywords = [k for k in keywords if k and k != "unknown"]

        # Build metadata
        atom_metadata = {
            "frame_number": frame_data.get("frame_number", 0),
            "session_id": session_id,
            "vehicle_id": vehicle_id,
            "detection_confidence": confidence,
            "source": "field_eye_vision"
        }

        # Create atom
        atom = KnowledgeAtom(
            atom_id=atom_id,
            type="fault",
            manufacturer=manufacturer,
            equipment_type=equipment_type,
            title=title,
            summary=summary,
            content=content,
            keywords=keywords,
            difficulty="intermediate",
            source_document=f"field_eye_session_{session_id}",
            metadata=atom_metadata
        )

        # Generate embedding
        atom.embedding = self._generate_embedding(atom)

        return atom

    def build_observation_atom(
        self,
        frame_data: Dict[str, Any],
        metadata: Dict[str, Any]
    ) -> KnowledgeAtom:
        """
        Build an observation Knowledge Atom from frame data.

        Used for general inspection notes without specific defects.

        Args:
            frame_data: Frame information
                - frame_number: int
                - timestamp: str (ISO format)
                - image_path: Optional[str]
                - observation: str (description)
            metadata: Session/context metadata
                - session_id: str
                - vehicle_id: Optional[str]
                - equipment_type: Optional[str]

        Returns:
            KnowledgeAtom instance ready for upload

        Example:
            >>> frame_data = {
            ...     "frame_number": 5678,
            ...     "timestamp": "2025-12-11T18:00:00Z",
            ...     "observation": "All torque stripes present and properly aligned"
            ... }
            >>> metadata = {"session_id": "abc123", "vehicle_id": "COASTER_001"}
            >>> atom = builder.build_observation_atom(frame_data, metadata)
        """
        equipment_type = metadata.get("equipment_type", "general")
        manufacturer = metadata.get("manufacturer", "unknown")
        vehicle_id = metadata.get("vehicle_id", "unknown_vehicle")
        session_id = metadata.get("session_id", "unknown_session")
        observation = frame_data.get("observation", "General inspection observation")

        # Generate atom ID
        atom_uuid = str(uuid.uuid4())
        atom_id = f"field_eye:{equipment_type}:observation:{atom_uuid}"

        # Build title and summary
        title = f"Inspection Observation - {vehicle_id}"
        summary = f"Observation from {vehicle_id} at {frame_data.get('timestamp', 'unknown time')}"

        # Build content
        content = {
            "observation_type": "inspection",
            "description": observation,
            "image_path": frame_data.get("image_path", ""),
            "timestamp": frame_data.get("timestamp", datetime.now().isoformat()),
            "frame_number": frame_data.get("frame_number", 0)
        }

        # Extract keywords
        keywords = [equipment_type, "inspection", "observation", vehicle_id]
        keywords = [k for k in keywords if k and k != "unknown"]

        # Build metadata
        atom_metadata = {
            "frame_number": frame_data.get("frame_number", 0),
            "session_id": session_id,
            "vehicle_id": vehicle_id,
            "source": "field_eye_vision"
        }

        # Create atom
        atom = KnowledgeAtom(
            atom_id=atom_id,
            type="observation",
            manufacturer=manufacturer,
            equipment_type=equipment_type,
            title=title,
            summary=summary,
            content=content,
            keywords=keywords,
            difficulty="beginner",
            source_document=f"field_eye_session_{session_id}",
            metadata=atom_metadata
        )

        # Generate embedding
        atom.embedding = self._generate_embedding(atom)

        return atom

    def _generate_embedding(self, atom: KnowledgeAtom) -> List[float]:
        """
        Generate OpenAI embedding for Knowledge Atom.

        Combines title, summary, and key content fields into single text
        for embedding generation.

        Args:
            atom: KnowledgeAtom instance

        Returns:
            List of floats (embedding vector)

        Raises:
            Exception: If embedding generation fails
        """
        # Build text for embedding
        text_parts = [
            atom.title,
            atom.summary,
            f"Equipment: {atom.equipment_type}",
            f"Manufacturer: {atom.manufacturer}",
            f"Type: {atom.type}"
        ]

        # Add content details
        if "defect_type" in atom.content:
            text_parts.append(f"Defect: {atom.content['defect_type']}")
        if "location" in atom.content:
            text_parts.append(f"Location: {atom.content['location']}")
        if "severity" in atom.content:
            text_parts.append(f"Severity: {atom.content['severity']}")

        # Add keywords
        text_parts.append(f"Keywords: {', '.join(atom.keywords)}")

        # Combine
        embedding_text = "\n".join(text_parts)

        try:
            response = self.openai_client.embeddings.create(
                input=embedding_text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")

    def upload_to_supabase(self, atom: KnowledgeAtom) -> str:
        """
        Upload Knowledge Atom to Supabase.

        Stores in two tables:
        1. knowledge_atoms - Full atom with embedding
        2. field_eye_defects - Cross-reference for Field Eye specific data

        Args:
            atom: KnowledgeAtom instance to upload

        Returns:
            atom_id (str) - Unique identifier of uploaded atom

        Raises:
            ValueError: If Supabase credentials not configured
            Exception: If upload fails

        Example:
            >>> atom = builder.build_defect_atom(frame_data, defect_data, metadata)
            >>> atom_id = builder.upload_to_supabase(atom)
            >>> print(f"Uploaded atom: {atom_id}")
        """
        try:
            from agent_factory.memory.storage import SupabaseMemoryStorage
        except ImportError:
            raise ImportError(
                "SupabaseMemoryStorage required for upload. "
                "Ensure agent_factory.memory.storage is available."
            )

        # Initialize storage
        try:
            storage = SupabaseMemoryStorage()
        except Exception as e:
            raise ValueError(f"Failed to initialize Supabase storage: {str(e)}")

        # Prepare atom data for knowledge_atoms table
        atom_data = {
            "atom_id": atom.atom_id,
            "type": atom.type,
            "manufacturer": atom.manufacturer,
            "equipment_type": atom.equipment_type,
            "title": atom.title,
            "summary": atom.summary,
            "content": atom.content,
            "embedding": atom.embedding,
            "keywords": atom.keywords,
            "difficulty": atom.difficulty,
            "source_document": atom.source_document,
            "metadata": atom.metadata,
            "created_at": atom.created_at
        }

        try:
            # Insert into knowledge_atoms table
            response = storage.client.table("knowledge_atoms").insert(atom_data).execute()

            # Also insert into field_eye_defects if it's a fault
            if atom.type == "fault":
                defect_data = {
                    "atom_id": atom.atom_id,
                    "session_id": atom.metadata.get("session_id", "unknown"),
                    "defect_type": atom.content.get("defect_type", "unknown"),
                    "severity": atom.content.get("severity", "info"),
                    "confidence": atom.content.get("confidence", 0.0),
                    "frame_number": atom.metadata.get("frame_number", 0),
                    "vehicle_id": atom.metadata.get("vehicle_id", "unknown"),
                    "detected_at": atom.content.get("timestamp", atom.created_at)
                }

                storage.client.table("field_eye_defects").insert(defect_data).execute()

            return atom.atom_id

        except Exception as e:
            raise Exception(f"Failed to upload atom to Supabase: {str(e)}")

    def batch_upload(self, atoms: List[KnowledgeAtom]) -> List[str]:
        """
        Upload multiple Knowledge Atoms to Supabase.

        More efficient than individual uploads for large batches.

        Args:
            atoms: List of KnowledgeAtom instances

        Returns:
            List of atom_ids successfully uploaded

        Example:
            >>> atoms = [
            ...     builder.build_defect_atom(frame1, defect1, meta1),
            ...     builder.build_defect_atom(frame2, defect2, meta2)
            ... ]
            >>> uploaded_ids = builder.batch_upload(atoms)
            >>> print(f"Uploaded {len(uploaded_ids)} atoms")
        """
        uploaded_ids = []

        for atom in atoms:
            try:
                atom_id = self.upload_to_supabase(atom)
                uploaded_ids.append(atom_id)
            except Exception as e:
                print(f"Failed to upload atom {atom.atom_id}: {str(e)}")
                continue

        return uploaded_ids


# Simple test
if __name__ == "__main__":
    print("=" * 80)
    print("Vision Atom Builder - Test")
    print("=" * 80)

    # Initialize builder
    try:
        builder = VisionAtomBuilder()
        print("[OK] Builder initialized successfully")
    except Exception as e:
        print(f"[SKIP] Builder requires OPENAI_API_KEY: {e}")
        print("\nDemonstrating atom structure without embedding generation...")

        # Create builder mock for testing structure
        class MockBuilder:
            def build_defect_atom(self, frame_data, defect_data, metadata):
                equipment_type = metadata.get("equipment_type", "torque_stripe")
                manufacturer = metadata.get("manufacturer", "unknown")
                vehicle_id = metadata.get("vehicle_id", "unknown_vehicle")
                session_id = metadata.get("session_id", "unknown_session")
                defect_type = defect_data["defect_type"]
                severity = defect_data.get("severity", "warning")
                confidence = defect_data.get("confidence", 0.0)
                location = defect_data.get("location", "unknown_location")
                bbox = defect_data.get("bbox", {})

                atom_uuid = str(uuid.uuid4())
                atom_id = f"field_eye:{equipment_type}:{defect_type}:{atom_uuid}"
                title = f"{defect_type.replace('_', ' ').title()} Detected"
                summary = (
                    f"{defect_type.replace('_', ' ').title()} on {location}, "
                    f"{vehicle_id}, detected at {frame_data.get('timestamp', 'unknown time')}"
                )

                content = {
                    "defect_type": defect_type,
                    "severity": severity,
                    "location": location,
                    "image_path": frame_data.get("image_path", ""),
                    "bounding_box": bbox,
                    "confidence": confidence,
                    "detected_by": "vision_analysis",
                    "timestamp": frame_data.get("timestamp", datetime.now().isoformat()),
                    "detection_details": {
                        "frame_number": frame_data.get("frame_number", 0),
                        "detection_method": defect_data.get("detection_method", "pause_analysis")
                    }
                }

                keywords = [equipment_type, defect_type, severity, location.split("_")[0] if "_" in location else location, manufacturer]
                keywords = [k for k in keywords if k and k != "unknown"]

                atom_metadata = {
                    "frame_number": frame_data.get("frame_number", 0),
                    "session_id": session_id,
                    "vehicle_id": vehicle_id,
                    "detection_confidence": confidence,
                    "source": "field_eye_vision"
                }

                return KnowledgeAtom(
                    atom_id=atom_id,
                    type="fault",
                    manufacturer=manufacturer,
                    equipment_type=equipment_type,
                    title=title,
                    summary=summary,
                    content=content,
                    keywords=keywords,
                    difficulty="intermediate",
                    source_document=f"field_eye_session_{session_id}",
                    metadata=atom_metadata,
                    embedding=None  # No embedding without API key
                )

            def build_observation_atom(self, frame_data, metadata):
                equipment_type = metadata.get("equipment_type", "general")
                manufacturer = metadata.get("manufacturer", "unknown")
                vehicle_id = metadata.get("vehicle_id", "unknown_vehicle")
                session_id = metadata.get("session_id", "unknown_session")
                observation = frame_data.get("observation", "General inspection observation")

                atom_uuid = str(uuid.uuid4())
                atom_id = f"field_eye:{equipment_type}:observation:{atom_uuid}"
                title = f"Inspection Observation - {vehicle_id}"
                summary = f"Observation from {vehicle_id} at {frame_data.get('timestamp', 'unknown time')}"

                content = {
                    "observation_type": "inspection",
                    "description": observation,
                    "image_path": frame_data.get("image_path", ""),
                    "timestamp": frame_data.get("timestamp", datetime.now().isoformat()),
                    "frame_number": frame_data.get("frame_number", 0)
                }

                keywords = [equipment_type, "inspection", "observation", vehicle_id]
                keywords = [k for k in keywords if k and k != "unknown"]

                atom_metadata = {
                    "frame_number": frame_data.get("frame_number", 0),
                    "session_id": session_id,
                    "vehicle_id": vehicle_id,
                    "source": "field_eye_vision"
                }

                return KnowledgeAtom(
                    atom_id=atom_id,
                    type="observation",
                    manufacturer=manufacturer,
                    equipment_type=equipment_type,
                    title=title,
                    summary=summary,
                    content=content,
                    keywords=keywords,
                    difficulty="beginner",
                    source_document=f"field_eye_session_{session_id}",
                    metadata=atom_metadata,
                    embedding=None
                )

        builder = MockBuilder()
        print("[OK] Using mock builder (no embeddings)")

    # Sample data
    frame_data = {
        "frame_number": 1234,
        "timestamp": "2025-12-11T17:30:00Z",
        "image_path": "s3://field-eye/frames/session_test/frame_1234.jpg"
    }

    defect_data = {
        "defect_type": "missing_stripe",
        "severity": "warning",
        "bbox": {"x": 100, "y": 200, "width": 50, "height": 30},
        "confidence": 0.92,
        "location": "wheel_assembly_bolt_3"
    }

    metadata = {
        "session_id": "test_session_123",
        "vehicle_id": "COASTER_001",
        "equipment_type": "torque_stripe",
        "manufacturer": "unknown"
    }

    # Build defect atom
    print("\nBuilding defect atom...")
    defect_atom = builder.build_defect_atom(frame_data, defect_data, metadata)
    print(f"[OK] Created defect atom: {defect_atom.atom_id}")
    print(f"  Type: {defect_atom.type}")
    print(f"  Title: {defect_atom.title}")
    print(f"  Summary: {defect_atom.summary}")
    print(f"  Keywords: {', '.join(defect_atom.keywords)}")
    print(f"  Embedding dims: {len(defect_atom.embedding) if defect_atom.embedding else 0}")

    # Build observation atom
    print("\nBuilding observation atom...")
    observation_frame = {
        "frame_number": 5678,
        "timestamp": "2025-12-11T18:00:00Z",
        "observation": "All torque stripes present and properly aligned"
    }

    observation_atom = builder.build_observation_atom(observation_frame, metadata)
    print(f"[OK] Created observation atom: {observation_atom.atom_id}")
    print(f"  Type: {observation_atom.type}")
    print(f"  Title: {observation_atom.title}")

    # Print full atom as JSON
    print("\n" + "=" * 80)
    print("Sample Defect Atom (JSON):")
    print("=" * 80)
    print(defect_atom.to_json())

    print("\n" + "=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print("\nTo upload to Supabase:")
    print("  atom_id = builder.upload_to_supabase(defect_atom)")
    print("\nEnsure SUPABASE_URL and SUPABASE_KEY are set in .env")
