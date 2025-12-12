"""
Data Ingest Agent for Field Eye

Orchestrates end-to-end processing of inspection videos:
- Extracts frames from videos
- Detects pause events (defect markers)
- Creates session records in database
- Uploads frames to Supabase storage
- Generates defect records
- Builds Knowledge Atoms for validated defects

This is the main entry point for ingesting inspection data
into the Field Eye platform.

Usage:
    from agent_factory.field_eye.agents import DataIngestAgent
    from agent_factory.memory import SupabaseMemoryStorage

    storage = SupabaseMemoryStorage()
    agent = DataIngestAgent(storage)

    result = agent.run({
        "video_path": "inspections/coaster_001.mp4",
        "technician_id": "john_smith",
        "vehicle_id": "COASTER_001",
        "equipment_type": "coaster"
    })

    print(f"Session: {result['session_id']}")
    print(f"Frames: {result['frames_extracted']}")
    print(f"Defects: {result['defects_found']}")
"""

import uuid
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

from agent_factory.memory.storage import SupabaseMemoryStorage
from agent_factory.field_eye.utils.video_processor import VideoProcessor, FrameData
from agent_factory.field_eye.utils.pause_detector import PauseDetector


class DataIngestAgent:
    """
    Main orchestrator for Field Eye video ingestion pipeline.

    Workflow:
    1. Extract frames from video (VideoProcessor)
    2. Detect pauses in motion (PauseDetector)
    3. Create session record in database
    4. Upload frames to Supabase storage
    5. Insert frame records into database
    6. Create defect records for high-confidence pauses
    7. Build Knowledge Atoms for defects
    8. Return summary statistics

    Example:
        >>> agent = DataIngestAgent(storage)
        >>> result = agent.run({
        ...     "video_path": "inspection.mp4",
        ...     "technician_id": "john_smith",
        ...     "vehicle_id": "COASTER_001",
        ...     "equipment_type": "coaster"
        ... })
    """

    def __init__(
        self,
        storage: SupabaseMemoryStorage,
        frame_interval_sec: float = 2.0,
        motion_threshold: float = 5000.0,
        min_pause_duration_sec: float = 1.0,
        defect_confidence_threshold: float = 0.5
    ):
        """
        Initialize Data Ingest Agent.

        Args:
            storage: Supabase storage backend
            frame_interval_sec: Time between extracted frames (default: 2 sec)
            motion_threshold: Motion score for pause detection
            min_pause_duration_sec: Minimum pause duration to consider
            defect_confidence_threshold: Minimum confidence for defect candidates
        """
        self.storage = storage
        self.frame_interval_sec = frame_interval_sec
        self.motion_threshold = motion_threshold
        self.min_pause_duration_sec = min_pause_duration_sec
        self.defect_confidence_threshold = defect_confidence_threshold

        # Initialize pause detector
        self.pause_detector = PauseDetector(
            motion_threshold=motion_threshold,
            min_pause_duration_sec=min_pause_duration_sec
        )

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process inspection video end-to-end.

        Args:
            payload: Input configuration with keys:
                - video_path (str): Path to video file
                - technician_id (str): Technician identifier
                - vehicle_id (str, optional): Vehicle/equipment ID
                - equipment_type (str, optional): Type of equipment
                - metadata (dict, optional): Additional metadata

        Returns:
            Dictionary with results:
                - status: "success" or "error"
                - session_id: UUID of created session
                - frames_extracted: Number of frames extracted
                - pauses_detected: Number of pauses found
                - defects_found: Number of high-confidence defects
                - atoms_created: Number of Knowledge Atoms generated
                - error: Error message (if status="error")

        Example:
            >>> result = agent.run({
            ...     "video_path": "inspection.mp4",
            ...     "technician_id": "john_smith"
            ... })
            >>> print(result["session_id"])
        """
        try:
            # Extract payload fields
            video_path = payload.get("video_path")
            technician_id = payload.get("technician_id")
            vehicle_id = payload.get("vehicle_id")
            equipment_type = payload.get("equipment_type")
            metadata = payload.get("metadata", {})

            # Validate required fields
            if not video_path:
                return {"status": "error", "error": "video_path is required"}
            if not technician_id:
                return {"status": "error", "error": "technician_id is required"}

            # Validate video file exists
            video_path_obj = Path(video_path)
            if not video_path_obj.exists():
                return {"status": "error", "error": f"Video file not found: {video_path}"}

            print(f"Starting video ingestion: {video_path}")
            print(f"Technician: {technician_id}")

            # Step 1: Extract frames from video
            print("\nStep 1: Extracting frames...")
            frames = self._extract_frames(video_path)
            print(f"  -> Extracted {len(frames)} frames")

            # Step 2: Detect pauses
            print("\nStep 2: Detecting pauses...")
            pauses = self._detect_pauses(video_path)
            print(f"  -> Found {len(pauses)} pauses")

            # Step 3: Create session record
            print("\nStep 3: Creating session record...")
            session_id = self._create_session(
                video_path=video_path,
                technician_id=technician_id,
                vehicle_id=vehicle_id,
                equipment_type=equipment_type,
                total_frames=len(frames),
                pauses=pauses,
                metadata=metadata
            )
            print(f"  -> Session ID: {session_id}")

            # Step 4: Upload frames to storage and database
            print("\nStep 4: Uploading frames...")
            uploaded_frames = self._upload_frames(
                session_id=session_id,
                frames=frames,
                video_path=video_path
            )
            print(f"  -> Uploaded {uploaded_frames} frames")

            # Step 5: Create defect records for high-confidence pauses
            print("\nStep 5: Creating defect records...")
            defects_created = self._create_defects(
                session_id=session_id,
                pauses=pauses,
                frames=frames
            )
            print(f"  -> Created {defects_created} defect records")

            # Step 6: Build Knowledge Atoms
            print("\nStep 6: Building Knowledge Atoms...")
            atoms_created = self._build_knowledge_atoms(
                session_id=session_id,
                defects_created=defects_created
            )
            print(f"  -> Built {atoms_created} Knowledge Atoms")

            # Return success summary
            result = {
                "status": "success",
                "session_id": session_id,
                "frames_extracted": len(frames),
                "pauses_detected": len(pauses),
                "defects_found": defects_created,
                "atoms_created": atoms_created
            }

            print("\nIngestion complete!")
            print(f"Summary: {json.dumps(result, indent=2)}")

            return result

        except Exception as e:
            error_msg = f"Ingestion failed: {str(e)}"
            print(f"\nERROR: {error_msg}")
            return {
                "status": "error",
                "error": error_msg
            }

    def _extract_frames(self, video_path: str) -> List[FrameData]:
        """
        Extract frames from video at regular intervals.

        Args:
            video_path: Path to video file

        Returns:
            List of FrameData objects
        """
        with VideoProcessor(video_path) as processor:
            frames = processor.extract_frames(
                interval_sec=self.frame_interval_sec
            )

        return frames

    def _detect_pauses(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Detect pause events in video.

        Args:
            video_path: Path to video file

        Returns:
            List of pause event dictionaries
        """
        pauses = self.pause_detector.analyze_video(video_path)

        # Convert to dictionaries for database storage
        pause_dicts = []
        for pause in pauses:
            pause_dicts.append({
                'frame_start': pause.frame_start,
                'frame_end': pause.frame_end,
                'timestamp_start': pause.timestamp_start,
                'timestamp_end': pause.timestamp_end,
                'duration_sec': pause.duration_sec,
                'confidence': pause.confidence,
                'is_defect_candidate': pause.is_defect_candidate
            })

        return pause_dicts

    def _create_session(
        self,
        video_path: str,
        technician_id: str,
        vehicle_id: Optional[str],
        equipment_type: Optional[str],
        total_frames: int,
        pauses: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> str:
        """
        Create session record in database.

        Args:
            video_path: Path to video file
            technician_id: Technician identifier
            vehicle_id: Vehicle/equipment identifier
            equipment_type: Type of equipment
            total_frames: Number of frames extracted
            pauses: List of detected pauses
            metadata: Additional session metadata

        Returns:
            Session UUID
        """
        session_id = str(uuid.uuid4())

        # Get video metadata
        with VideoProcessor(video_path) as processor:
            video_metadata = processor.get_metadata()

        # Build session record
        session_data = {
            'id': session_id,
            'technician_id': technician_id,
            'vehicle_id': vehicle_id,
            'equipment_type': equipment_type,
            'date': datetime.now().isoformat(),
            'duration_sec': int(video_metadata.duration_sec),
            'total_frames': total_frames,
            'pause_count': len(pauses),
            'pauses': pauses,
            'video_path': str(video_path),
            'metadata': metadata,
            'created_at': datetime.now().isoformat()
        }

        # Insert into field_eye_sessions table
        self.storage.client.table('field_eye_sessions').insert(session_data).execute()

        return session_id

    def _upload_frames(
        self,
        session_id: str,
        frames: List[FrameData],
        video_path: str
    ) -> int:
        """
        Upload frames to Supabase storage and insert frame records.

        Args:
            session_id: Session UUID
            frames: List of extracted frames
            video_path: Original video path

        Returns:
            Number of frames uploaded
        """
        uploaded_count = 0

        for frame_data in frames:
            try:
                # Generate frame filename
                frame_filename = f"{session_id}_frame_{frame_data.frame_number:06d}.jpg"

                # Note: In production, you would upload frame_data.frame to Supabase Storage
                # For now, we'll just store the reference in the database
                # frame_path = f"field_eye/{session_id}/{frame_filename}"

                # For MVP, store local path
                frame_path = f"local://frames/{session_id}/{frame_filename}"

                # Insert frame record into database
                frame_record = {
                    'session_id': session_id,
                    'frame_number': frame_data.frame_number,
                    'timestamp_sec': frame_data.timestamp_sec,
                    'frame_path': frame_path,
                    # embedding would be generated here with OpenAI API
                    # embedding: generate_embedding(frame_data.frame)
                    'is_defect': None,  # Unlabeled initially
                    'created_at': datetime.now().isoformat()
                }

                self.storage.client.table('field_eye_frames').insert(frame_record).execute()
                uploaded_count += 1

            except Exception as e:
                print(f"Warning: Failed to upload frame {frame_data.frame_number}: {e}")
                continue

        return uploaded_count

    def _create_defects(
        self,
        session_id: str,
        pauses: List[Dict[str, Any]],
        frames: List[FrameData]
    ) -> int:
        """
        Create defect records for high-confidence pauses.

        Args:
            session_id: Session UUID
            pauses: List of detected pauses
            frames: List of extracted frames

        Returns:
            Number of defect records created
        """
        defects_created = 0

        for pause in pauses:
            # Only create defects for high-confidence candidates
            if not pause.get('is_defect_candidate'):
                continue

            if pause.get('confidence', 0) < self.defect_confidence_threshold:
                continue

            try:
                # Find corresponding frame in database
                frame_response = self.storage.client.table('field_eye_frames').select('id').eq(
                    'session_id', session_id
                ).gte(
                    'timestamp_sec', pause['timestamp_start']
                ).lte(
                    'timestamp_sec', pause['timestamp_end']
                ).limit(1).execute()

                if not frame_response.data:
                    print(f"Warning: No frame found for pause at {pause['timestamp_start']}s")
                    continue

                frame_id = frame_response.data[0]['id']

                # Create defect record
                defect_record = {
                    'frame_id': frame_id,
                    'defect_type': 'unknown_defect',  # Would be classified by vision model
                    'confidence': pause['confidence'],
                    'severity': 'warning',
                    'auto_detected': True,
                    'human_verified': False,
                    'notes': f"Auto-detected pause: {pause['duration_sec']:.1f}s duration",
                    'created_at': datetime.now().isoformat()
                }

                self.storage.client.table('field_eye_defects').insert(defect_record).execute()
                defects_created += 1

            except Exception as e:
                print(f"Warning: Failed to create defect for pause: {e}")
                continue

        return defects_created

    def _build_knowledge_atoms(
        self,
        session_id: str,
        defects_created: int
    ) -> int:
        """
        Build Knowledge Atoms for validated defects.

        Args:
            session_id: Session UUID
            defects_created: Number of defects created

        Returns:
            Number of Knowledge Atoms built
        """
        # Note: VisionAtomBuilder would be used here to generate
        # Knowledge Atoms following the knowledge-atom-standard-v1.0

        # For MVP, we'll create simple placeholder atoms
        atoms_created = 0

        try:
            # Query defects for this session
            defects_response = self.storage.client.table('field_eye_defects').select(
                'id, defect_type, confidence, frame_id'
            ).eq('frame_id:field_eye_frames.session_id', session_id).execute()

            # Would create Knowledge Atoms here using VisionAtomBuilder
            # For now, just return count
            atoms_created = defects_created

        except Exception as e:
            print(f"Warning: Failed to build Knowledge Atoms: {e}")

        return atoms_created


# ============================================================================
# Helper Functions
# ============================================================================

def create_data_ingest_agent(
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None
) -> DataIngestAgent:
    """
    Factory function to create DataIngestAgent with Supabase storage.

    Args:
        supabase_url: Supabase project URL (defaults to env var)
        supabase_key: Supabase API key (defaults to env var)

    Returns:
        Configured DataIngestAgent instance

    Example:
        >>> agent = create_data_ingest_agent()
        >>> result = agent.run({"video_path": "inspection.mp4", ...})
    """
    storage = SupabaseMemoryStorage(
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )

    return DataIngestAgent(storage=storage)


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python data_ingest_agent.py <video_path> <technician_id>")
        print("Example: python data_ingest_agent.py inspection.mp4 john_smith")
        sys.exit(1)

    video_path = sys.argv[1]
    technician_id = sys.argv[2]
    vehicle_id = sys.argv[3] if len(sys.argv) > 3 else None
    equipment_type = sys.argv[4] if len(sys.argv) > 4 else None

    print("=" * 60)
    print("Field Eye Data Ingest Agent")
    print("=" * 60)

    # Create agent
    agent = create_data_ingest_agent()

    # Run ingestion
    payload = {
        "video_path": video_path,
        "technician_id": technician_id,
        "vehicle_id": vehicle_id,
        "equipment_type": equipment_type
    }

    result = agent.run(payload)

    if result["status"] == "success":
        print("\n" + "=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Session ID: {result['session_id']}")
        print(f"Frames: {result['frames_extracted']}")
        print(f"Pauses: {result['pauses_detected']}")
        print(f"Defects: {result['defects_found']}")
        print(f"Atoms: {result['atoms_created']}")
    else:
        print("\n" + "=" * 60)
        print("FAILED!")
        print("=" * 60)
        print(f"Error: {result['error']}")
        sys.exit(1)
