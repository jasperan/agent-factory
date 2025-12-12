"""
Pause Detector for Field Eye

Analyzes motion patterns in inspection videos to detect when
a technician pauses the camera - a strong signal for defects.

The Core Insight:
    When you find something wrong, you naturally pause.
    This creates a labeled dataset automatically.

Usage:
    detector = PauseDetector(motion_threshold=5000)
    pauses = detector.analyze_video("inspection.mp4")
    defect_candidates = detector.get_defect_candidates(pauses)
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class PauseEvent:
    """A detected pause event in video"""
    frame_start: int
    frame_end: int
    timestamp_start: float
    timestamp_end: float
    duration_sec: float
    avg_motion_score: float
    min_motion_score: float
    confidence: float  # How confident we are this is a real pause (0-1)
    is_defect_candidate: bool  # True if pause characteristics match defect inspection


class PauseDetector:
    """
    Detect pauses in inspection videos.

    Technicians naturally pause when they find defects.
    This detector identifies those pauses for automated labeling.

    Algorithm:
        1. Compute frame-to-frame motion scores
        2. Smooth scores with rolling average
        3. Detect sequences below threshold
        4. Filter by minimum duration
        5. Score confidence based on pause characteristics

    Example:
        >>> detector = PauseDetector(motion_threshold=5000)
        >>> pauses = detector.analyze_video("inspection.mp4")
        >>> print(f"Found {len(pauses)} pauses")
        >>> defects = [p for p in pauses if p.is_defect_candidate]
        >>> print(f"{len(defects)} are likely defects")
    """

    def __init__(
        self,
        motion_threshold: float = 5000.0,
        min_pause_duration_sec: float = 1.0,
        max_pause_duration_sec: float = 30.0,
        smoothing_window: int = 3
    ):
        """
        Initialize pause detector.

        Args:
            motion_threshold: Motion score below which frame is paused
            min_pause_duration_sec: Minimum pause duration to consider
            max_pause_duration_sec: Maximum pause duration (filter out long stops)
            smoothing_window: Number of frames to average for noise reduction
        """
        self.motion_threshold = motion_threshold
        self.min_pause_duration_sec = min_pause_duration_sec
        self.max_pause_duration_sec = max_pause_duration_sec
        self.smoothing_window = smoothing_window

    def analyze_video(
        self,
        video_path: str,
        start_sec: float = 0.0,
        end_sec: Optional[float] = None
    ) -> List[PauseEvent]:
        """
        Analyze video for pause events.

        Args:
            video_path: Path to video file
            start_sec: Start time (default: 0)
            end_sec: End time (default: end of video)

        Returns:
            List of detected pause events

        Example:
            >>> pauses = detector.analyze_video("inspection.mp4")
            >>> print(f"Found {len(pauses)} pauses")
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        if end_sec is None:
            end_sec = total_frames / fps

        # Start from beginning
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(start_sec * fps))

        # Compute motion scores
        motion_scores = []
        prev_frame = None
        frame_count = int(start_sec * fps)

        while frame_count / fps <= end_sec:
            ret, frame = cap.read()
            if not ret:
                break

            if prev_frame is not None:
                motion_score = self._compute_motion_score(prev_frame, frame)
                motion_scores.append(motion_score)

            prev_frame = frame.copy()
            frame_count += 1

        cap.release()

        # Smooth motion scores
        smoothed_scores = self._smooth_scores(motion_scores)

        # Detect pauses
        pauses = self._detect_pauses(smoothed_scores, fps, start_sec)

        return pauses

    def _compute_motion_score(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray
    ) -> float:
        """
        Compute motion score between two frames.

        Method: Absolute difference between grayscale frames.
        """
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)

        diff = cv2.absdiff(gray1, gray2)
        motion_score = float(diff.sum())

        return motion_score

    def _smooth_scores(self, scores: List[float]) -> List[float]:
        """
        Smooth motion scores with rolling average.

        Reduces noise from small camera movements.
        """
        if len(scores) < self.smoothing_window:
            return scores

        smoothed = []
        for i in range(len(scores)):
            start_idx = max(0, i - self.smoothing_window // 2)
            end_idx = min(len(scores), i + self.smoothing_window // 2 + 1)
            window = scores[start_idx:end_idx]
            smoothed.append(np.mean(window))

        return smoothed

    def _detect_pauses(
        self,
        motion_scores: List[float],
        fps: float,
        offset_sec: float = 0.0
    ) -> List[PauseEvent]:
        """
        Detect pause sequences in motion scores.

        Args:
            motion_scores: List of motion scores
            fps: Video frame rate
            offset_sec: Time offset (if analyzing subset of video)

        Returns:
            List of detected pause events
        """
        pauses = []
        pause_start = None
        pause_scores = []

        for i, score in enumerate(motion_scores):
            if score < self.motion_threshold:
                # Currently paused
                if pause_start is None:
                    pause_start = i
                pause_scores.append(score)
            else:
                # End of pause
                if pause_start is not None:
                    pause = self._create_pause_event(
                        pause_start,
                        i,
                        pause_scores,
                        fps,
                        offset_sec
                    )

                    # Filter by duration
                    if (pause.duration_sec >= self.min_pause_duration_sec and
                        pause.duration_sec <= self.max_pause_duration_sec):
                        pauses.append(pause)

                pause_start = None
                pause_scores = []

        # Handle pause at end of video
        if pause_start is not None:
            pause = self._create_pause_event(
                pause_start,
                len(motion_scores),
                pause_scores,
                fps,
                offset_sec
            )

            if (pause.duration_sec >= self.min_pause_duration_sec and
                pause.duration_sec <= self.max_pause_duration_sec):
                pauses.append(pause)

        return pauses

    def _create_pause_event(
        self,
        start_frame: int,
        end_frame: int,
        scores: List[float],
        fps: float,
        offset_sec: float
    ) -> PauseEvent:
        """Create PauseEvent from detected pause sequence"""
        duration_frames = end_frame - start_frame
        duration_sec = duration_frames / fps

        avg_motion = np.mean(scores) if scores else 0.0
        min_motion = np.min(scores) if scores else 0.0

        # Calculate confidence (how sure we are this is a real pause)
        confidence = self._calculate_confidence(
            duration_sec,
            avg_motion,
            min_motion
        )

        # Check if likely defect (based on duration and motion characteristics)
        is_defect_candidate = self._is_defect_candidate(
            duration_sec,
            avg_motion,
            confidence
        )

        return PauseEvent(
            frame_start=start_frame,
            frame_end=end_frame,
            timestamp_start=offset_sec + start_frame / fps,
            timestamp_end=offset_sec + end_frame / fps,
            duration_sec=duration_sec,
            avg_motion_score=avg_motion,
            min_motion_score=min_motion,
            confidence=confidence,
            is_defect_candidate=is_defect_candidate
        )

    def _calculate_confidence(
        self,
        duration_sec: float,
        avg_motion: float,
        min_motion: float
    ) -> float:
        """
        Calculate confidence score for pause (0-1).

        High confidence when:
        - Duration is 1-10 seconds (typical defect inspection)
        - Motion is very low (camera is steady)
        - Min motion is close to zero (no movement at all)
        """
        confidence = 0.0

        # Duration scoring (optimal: 2-5 seconds)
        if 1.0 <= duration_sec <= 2.0:
            confidence += 0.3
        elif 2.0 < duration_sec <= 5.0:
            confidence += 0.4  # Best range
        elif 5.0 < duration_sec <= 10.0:
            confidence += 0.3
        else:
            confidence += 0.1

        # Motion scoring (lower is better)
        motion_ratio = avg_motion / self.motion_threshold
        if motion_ratio < 0.2:
            confidence += 0.4  # Very low motion
        elif motion_ratio < 0.5:
            confidence += 0.3
        elif motion_ratio < 0.8:
            confidence += 0.2
        else:
            confidence += 0.1

        # Steadiness scoring (min motion close to zero)
        steadiness_ratio = min_motion / avg_motion if avg_motion > 0 else 0
        if steadiness_ratio < 0.3:
            confidence += 0.2  # Very steady

        return min(confidence, 1.0)

    def _is_defect_candidate(
        self,
        duration_sec: float,
        avg_motion: float,
        confidence: float
    ) -> bool:
        """
        Determine if pause is likely a defect inspection.

        Heuristics:
        - Duration: 1-10 seconds (too short = accidental, too long = break)
        - Motion: Very low (camera is steady on defect)
        - Confidence: >0.5
        """
        if confidence < 0.5:
            return False

        if not (1.0 <= duration_sec <= 10.0):
            return False

        if avg_motion > self.motion_threshold * 0.7:
            return False

        return True

    def get_defect_candidates(
        self,
        pauses: List[PauseEvent],
        min_confidence: float = 0.5
    ) -> List[PauseEvent]:
        """
        Filter pauses to likely defect candidates.

        Args:
            pauses: List of detected pauses
            min_confidence: Minimum confidence threshold

        Returns:
            List of high-confidence defect candidate pauses

        Example:
            >>> pauses = detector.analyze_video("inspection.mp4")
            >>> defects = detector.get_defect_candidates(pauses)
            >>> print(f"{len(defects)} defect candidates")
        """
        candidates = [
            p for p in pauses
            if p.is_defect_candidate and p.confidence >= min_confidence
        ]

        # Sort by confidence (highest first)
        candidates.sort(key=lambda p: p.confidence, reverse=True)

        return candidates

    def export_to_json(
        self,
        pauses: List[PauseEvent],
        output_path: str
    ) -> None:
        """
        Export pause events to JSON file.

        Args:
            pauses: List of pause events
            output_path: Output JSON file path
        """
        data = []
        for pause in pauses:
            data.append({
                'frame_start': pause.frame_start,
                'frame_end': pause.frame_end,
                'timestamp_start': pause.timestamp_start,
                'timestamp_end': pause.timestamp_end,
                'duration_sec': pause.duration_sec,
                'avg_motion_score': pause.avg_motion_score,
                'min_motion_score': pause.min_motion_score,
                'confidence': pause.confidence,
                'is_defect_candidate': pause.is_defect_candidate
            })

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

    def generate_report(self, pauses: List[PauseEvent]) -> str:
        """
        Generate human-readable pause analysis report.

        Args:
            pauses: List of detected pauses

        Returns:
            Formatted report string
        """
        if not pauses:
            return "No pauses detected."

        defect_candidates = [p for p in pauses if p.is_defect_candidate]

        report = []
        report.append("=" * 60)
        report.append("Pause Analysis Report")
        report.append("=" * 60)
        report.append(f"Total pauses: {len(pauses)}")
        report.append(f"Defect candidates: {len(defect_candidates)}")
        report.append(f"Average duration: {np.mean([p.duration_sec for p in pauses]):.2f}s")
        report.append("")

        report.append("Top Defect Candidates:")
        report.append("-" * 60)

        for i, pause in enumerate(sorted(defect_candidates, key=lambda p: p.confidence, reverse=True)[:10]):
            report.append(f"{i+1}. Time: {pause.timestamp_start:.1f}s, "
                         f"Duration: {pause.duration_sec:.1f}s, "
                         f"Confidence: {pause.confidence:.2f}")

        return "\n".join(report)


# ============================================================================
# CLI Interface
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pause_detector.py <video_path>")
        print("Example: python pause_detector.py inspection_001.mp4")
        sys.exit(1)

    video_path = sys.argv[1]

    print("=" * 60)
    print("Field Eye Pause Detector")
    print("=" * 60)

    detector = PauseDetector(
        motion_threshold=5000.0,
        min_pause_duration_sec=1.0,
        max_pause_duration_sec=30.0
    )

    print(f"\nAnalyzing: {video_path}")
    print("Detecting pauses...")

    pauses = detector.analyze_video(video_path)

    print(detector.generate_report(pauses))

    # Export to JSON
    output_path = Path(video_path).stem + "_pauses.json"
    detector.export_to_json(pauses, output_path)
    print(f"\nExported pause data to: {output_path}")
