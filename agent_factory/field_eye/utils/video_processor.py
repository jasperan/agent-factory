"""
Video Processor for Field Eye

Extracts frames from inspection videos, analyzes motion,
and prepares data for AI training.

Usage:
    processor = VideoProcessor(video_path)
    frames = processor.extract_frames(interval_sec=2.0)
    metadata = processor.get_metadata()
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class FrameData:
    """Extracted frame with metadata"""
    frame_number: int
    timestamp_sec: float
    frame: np.ndarray  # RGB image
    motion_score: float  # Motion delta from previous frame
    is_pause: bool  # True if motion score < threshold


@dataclass
class VideoMetadata:
    """Video file metadata"""
    path: str
    duration_sec: float
    total_frames: int
    fps: float
    width: int
    height: int
    codec: str
    file_size_mb: float
    checksum: str  # SHA256 hash for integrity


class VideoProcessor:
    """
    Process inspection videos for Field Eye platform.

    Features:
    - Extract frames at regular intervals
    - Compute motion scores for pause detection
    - Generate video metadata
    - Validate video integrity

    Example:
        >>> processor = VideoProcessor("inspection_001.mp4")
        >>> frames = processor.extract_frames(interval_sec=2.0)
        >>> print(f"Extracted {len(frames)} frames")
        >>> processor.release()
    """

    def __init__(
        self,
        video_path: str,
        motion_threshold: float = 5000.0,
        resize_width: Optional[int] = None
    ):
        """
        Initialize video processor.

        Args:
            video_path: Path to video file
            motion_threshold: Motion score below which frame is considered "paused"
            resize_width: Optional width to resize frames (maintains aspect ratio)
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        self.motion_threshold = motion_threshold
        self.resize_width = resize_width

        # Open video
        self.cap = cv2.VideoCapture(str(self.video_path))
        if not self.cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        # Cache metadata
        self._metadata = None

    def get_metadata(self) -> VideoMetadata:
        """
        Extract video metadata.

        Returns:
            VideoMetadata with video properties
        """
        if self._metadata is not None:
            return self._metadata

        # Get video properties
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        codec_int = int(self.cap.get(cv2.CAP_PROP_FOURCC))

        # Decode codec
        codec = "".join([chr((codec_int >> 8 * i) & 0xFF) for i in range(4)])

        # Calculate duration
        duration_sec = total_frames / fps if fps > 0 else 0.0

        # File size
        file_size_mb = self.video_path.stat().st_size / (1024 * 1024)

        # Compute checksum (for integrity verification)
        checksum = self._compute_checksum()

        self._metadata = VideoMetadata(
            path=str(self.video_path),
            duration_sec=duration_sec,
            total_frames=total_frames,
            fps=fps,
            width=width,
            height=height,
            codec=codec,
            file_size_mb=file_size_mb,
            checksum=checksum
        )

        return self._metadata

    def _compute_checksum(self) -> str:
        """Compute SHA256 checksum of video file"""
        sha256 = hashlib.sha256()
        with open(self.video_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()[:16]  # First 16 chars

    def extract_frames(
        self,
        interval_sec: float = 2.0,
        max_frames: Optional[int] = None,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None
    ) -> List[FrameData]:
        """
        Extract frames from video at regular intervals.

        Args:
            interval_sec: Time interval between frames (default: 2 seconds)
            max_frames: Maximum number of frames to extract (optional)
            start_sec: Start time in seconds (default: 0)
            end_sec: End time in seconds (optional, default: end of video)

        Returns:
            List of FrameData objects

        Example:
            >>> frames = processor.extract_frames(interval_sec=1.0, max_frames=100)
            >>> print(f"Extracted {len(frames)} frames")
        """
        metadata = self.get_metadata()
        fps = metadata.fps

        if end_sec is None:
            end_sec = metadata.duration_sec

        # Calculate frame interval
        frame_interval = int(interval_sec * fps)

        # Start from beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_sec * fps))

        frames = []
        prev_frame = None
        frame_count = int(start_sec * fps)

        while True:
            # Stop conditions
            if max_frames and len(frames) >= max_frames:
                break

            if frame_count / fps > end_sec:
                break

            ret, frame = self.cap.read()
            if not ret:
                break

            # Extract at intervals
            if frame_count % frame_interval == 0:
                # Compute motion score
                motion_score = 0.0
                is_pause = False

                if prev_frame is not None:
                    motion_score = self._compute_motion_score(prev_frame, frame)
                    is_pause = motion_score < self.motion_threshold

                # Resize if requested
                if self.resize_width:
                    frame = self._resize_frame(frame, self.resize_width)

                # Store frame data
                frame_data = FrameData(
                    frame_number=frame_count,
                    timestamp_sec=frame_count / fps,
                    frame=frame.copy(),
                    motion_score=motion_score,
                    is_pause=is_pause
                )

                frames.append(frame_data)
                prev_frame = frame.copy()

            frame_count += 1

        return frames

    def _compute_motion_score(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> float:
        """
        Compute motion score between two frames.

        Method: Absolute difference between frames, summed.
        Low score = little motion (paused).
        High score = lots of motion (moving camera).

        Args:
            frame1: First frame (RGB)
            frame2: Second frame (RGB)

        Returns:
            Motion score (higher = more motion)
        """
        # Convert to grayscale for faster computation
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        # Compute absolute difference
        diff = cv2.absdiff(gray1, gray2)

        # Sum all pixel differences
        motion_score = float(diff.sum())

        return motion_score

    def _resize_frame(self, frame: np.ndarray, width: int) -> np.ndarray:
        """Resize frame maintaining aspect ratio"""
        height = frame.shape[0]
        original_width = frame.shape[1]
        aspect_ratio = height / original_width
        new_height = int(width * aspect_ratio)

        resized = cv2.resize(frame, (width, new_height), interpolation=cv2.INTER_AREA)
        return resized

    def extract_pauses(
        self,
        min_pause_duration_sec: float = 1.0,
        motion_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        Extract pause events (likely defect highlights).

        When a technician finds a defect, they naturally pause the camera.
        This detects those pauses for automated defect labeling.

        Args:
            min_pause_duration_sec: Minimum pause duration to consider
            motion_threshold: Override default motion threshold

        Returns:
            List of pause events: [{frame: 123, timestamp: 45.2, duration: 2.1}, ...]
        """
        if motion_threshold is None:
            motion_threshold = self.motion_threshold

        metadata = self.get_metadata()
        fps = metadata.fps
        min_pause_frames = int(min_pause_duration_sec * fps)

        # Reset to beginning
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        pauses = []
        prev_frame = None
        frame_count = 0
        pause_start = None
        pause_frames = 0

        while True:
            ret, frame = self.cap.read()
            if not ret:
                break

            if prev_frame is not None:
                motion_score = self._compute_motion_score(prev_frame, frame)

                # Check if paused
                if motion_score < motion_threshold:
                    if pause_start is None:
                        pause_start = frame_count
                    pause_frames += 1
                else:
                    # End of pause
                    if pause_start is not None and pause_frames >= min_pause_frames:
                        pause_duration = pause_frames / fps
                        pauses.append({
                            'frame': pause_start,
                            'timestamp': pause_start / fps,
                            'duration': pause_duration,
                            'frame_count': pause_frames
                        })

                    pause_start = None
                    pause_frames = 0

            prev_frame = frame.copy()
            frame_count += 1

        # Handle pause at end of video
        if pause_start is not None and pause_frames >= min_pause_frames:
            pause_duration = pause_frames / fps
            pauses.append({
                'frame': pause_start,
                'timestamp': pause_start / fps,
                'duration': pause_duration,
                'frame_count': pause_frames
            })

        return pauses

    def save_frame(
        self,
        frame: np.ndarray,
        output_path: str,
        quality: int = 95
    ) -> None:
        """
        Save frame to disk.

        Args:
            frame: Frame to save (RGB numpy array)
            output_path: Output file path (e.g., 'frame_001.jpg')
            quality: JPEG quality (0-100, default: 95)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        cv2.imwrite(
            str(output_path),
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, quality]
        )

    def release(self) -> None:
        """Release video capture resources"""
        if self.cap is not None:
            self.cap.release()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - release resources"""
        self.release()


# ============================================================================
# Helper Functions
# ============================================================================

def batch_process_videos(
    video_paths: List[str],
    output_dir: str,
    interval_sec: float = 2.0
) -> Dict[str, List[FrameData]]:
    """
    Process multiple videos in batch.

    Args:
        video_paths: List of video file paths
        output_dir: Directory to save extracted frames
        interval_sec: Frame extraction interval

    Returns:
        Dictionary mapping video path to extracted frames

    Example:
        >>> results = batch_process_videos(
        ...     ["video1.mp4", "video2.mp4"],
        ...     output_dir="data/frames"
        ... )
        >>> print(f"Processed {len(results)} videos")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = {}

    for video_path in video_paths:
        print(f"Processing: {video_path}")

        with VideoProcessor(video_path) as processor:
            frames = processor.extract_frames(interval_sec=interval_sec)
            results[video_path] = frames

            # Save frames
            video_name = Path(video_path).stem
            for i, frame_data in enumerate(frames):
                output_path = output_dir / f"{video_name}_frame_{i:06d}.jpg"
                processor.save_frame(frame_data.frame, str(output_path))

        print(f"  -> Extracted {len(frames)} frames")

    return results


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_processor.py <video_path>")
        print("Example: python video_processor.py inspection_001.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    print("=" * 60)
    print("Field Eye Video Processor")
    print("=" * 60)

    with VideoProcessor(video_path) as processor:
        # Get metadata
        metadata = processor.get_metadata()
        print(f"\nVideo: {metadata.path}")
        print(f"Duration: {metadata.duration_sec:.1f}s")
        print(f"Frames: {metadata.total_frames} @ {metadata.fps:.1f}fps")
        print(f"Resolution: {metadata.width}x{metadata.height}")
        print(f"Codec: {metadata.codec}")
        print(f"Size: {metadata.file_size_mb:.1f}MB")
        print(f"Checksum: {metadata.checksum}")

        # Extract frames
        print(f"\nExtracting frames (every 2 seconds)...")
        frames = processor.extract_frames(interval_sec=2.0)
        print(f"Extracted {len(frames)} frames")

        # Detect pauses
        print(f"\nDetecting pauses...")
        pauses = processor.extract_pauses(min_pause_duration_sec=1.0)
        print(f"Found {len(pauses)} pauses")

        for i, pause in enumerate(pauses[:5]):  # Show first 5
            print(f"  Pause {i+1}: frame {pause['frame']}, "
                  f"time {pause['timestamp']:.1f}s, "
                  f"duration {pause['duration']:.1f}s")

    print("\nDone!")
