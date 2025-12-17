"""Vendor detection for RIVET Pro queries.

Detects PLC vendor from query text using keyword matching and confidence scoring.
"""

from typing import Dict, List
from agent_factory.schemas.routing import VendorType, VendorDetection, CoverageThresholds


class VendorDetector:
    """Detects PLC vendor from query text."""

    # Vendor-specific keywords (lowercase for case-insensitive matching)
    VENDOR_KEYWORDS: Dict[VendorType, List[str]] = {
        VendorType.SIEMENS: [
            "siemens",
            "sinamics",
            "micromaster",
            "tia portal",
            "tia",
            "s7-1200",
            "s7-1500",
            "s7-300",
            "s7-400",
            "step 7",
            "step7",
            "simatic",
            "profinet",
            "profibus",
        ],
        VendorType.ROCKWELL: [
            "rockwell",
            "allen-bradley",
            "allen bradley",
            "ab plc",
            "controllogix",
            "compactlogix",
            "micrologix",
            "studio 5000",
            "rslogix",
            "rs logix",
            "factorytalk",
            "factory talk",
            "kinetix",
            "powerflex",
        ],
        VendorType.SAFETY: [
            "safety",
            "sil",
            "sil1",
            "sil2",
            "sil3",
            "iec 61508",
            "iec 61511",
            "safety relay",
            "emergency stop",
            "e-stop",
            "safety plc",
            "failsafe",
            "fail-safe",
        ],
    }

    def detect(self, query: str) -> VendorDetection:
        """Detect vendor from query text.

        Args:
            query: User query text

        Returns:
            VendorDetection with vendor, confidence, and matched keywords
        """
        query_lower = query.lower()

        # Score each vendor
        vendor_scores: Dict[VendorType, tuple[float, List[str]]] = {}

        for vendor_type, keywords in self.VENDOR_KEYWORDS.items():
            matched_keywords = [kw for kw in keywords if kw in query_lower]
            score = len(matched_keywords) / len(keywords) if keywords else 0.0
            vendor_scores[vendor_type] = (score, matched_keywords)

        # Find best match
        if not vendor_scores or all(score == 0.0 for score, _ in vendor_scores.values()):
            # No vendor keywords found → Generic PLC
            return VendorDetection(
                vendor=VendorType.GENERIC,
                confidence=1.0,  # High confidence in fallback
                keywords_matched=[]
            )

        best_vendor = max(vendor_scores.keys(), key=lambda v: vendor_scores[v][0])
        best_score, matched_kws = vendor_scores[best_vendor]

        # Convert score to confidence (0-1 scale)
        # More keywords matched = higher confidence
        confidence = min(best_score * 2.0, 1.0)  # Scale up, cap at 1.0

        return VendorDetection(
            vendor=best_vendor,
            confidence=confidence,
            keywords_matched=matched_kws
        )

    def get_confidence(self, query: str, vendor: VendorType) -> float:
        """Get confidence score for specific vendor.

        Args:
            query: User query text
            vendor: Vendor to check

        Returns:
            Confidence score 0-1
        """
        detection = self.detect(query)
        if detection.vendor == vendor:
            return detection.confidence
        return 0.0

    def is_high_confidence(self, detection: VendorDetection) -> bool:
        """Check if vendor detection confidence is above threshold.

        Args:
            detection: VendorDetection result

        Returns:
            True if confidence >= MIN_VENDOR_CONFIDENCE threshold
        """
        return detection.confidence >= CoverageThresholds.MIN_VENDOR_CONFIDENCE

    def detect_with_fallback(self, query: str) -> VendorDetection:
        """Detect vendor with automatic fallback to Generic if low confidence.

        Args:
            query: User query text

        Returns:
            VendorDetection, forced to GENERIC if confidence too low
        """
        detection = self.detect(query)

        if not self.is_high_confidence(detection) and detection.vendor != VendorType.GENERIC:
            # Low confidence non-generic → fallback to generic
            return VendorDetection(
                vendor=VendorType.GENERIC,
                confidence=0.9,  # High confidence in fallback decision
                keywords_matched=[]
            )

        return detection


# Example usage (for testing)
if __name__ == "__main__":
    detector = VendorDetector()

    test_queries = [
        "How do I configure SINAMICS G120 drive parameters?",
        "ControlLogix fault code 0x1234 troubleshooting",
        "What is ladder logic and how does it work?",
        "Safety relay configuration for SIL2 application",
    ]

    for query in test_queries:
        result = detector.detect(query)
        print(f"Query: {query}")
        print(f"  Vendor: {result.vendor}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Matched: {result.keywords_matched}")
        print()
