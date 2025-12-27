"""
Response Synthesizer - Enhance SME responses with citations, safety warnings, and formatting.

This module standardizes response formatting across all routes with:
- Inline citations [1], [2] with footer
- Safety warnings (LOTO, arc flash, voltage)
- Formatted troubleshooting steps
- Confidence indicators (High, Limited, Low)
"""

import re
import os
from typing import List, Dict, Optional
from dataclasses import dataclass

from agent_factory.rivet_pro.models import RivetResponse, RivetRequest, KBCoverage, VendorType


@dataclass
class SafetyWarning:
    """Safety warning with severity level."""
    level: str  # "danger", "warning", "caution", "info"
    message: str
    icon: str  # "🔴", "🟠", "⚠️", "ℹ️"


class ResponseSynthesizer:
    """
    Enhance SME responses with citations, safety warnings, steps, and confidence.

    Usage:
        synthesizer = ResponseSynthesizer()
        enhanced = synthesizer.synthesize(
            response=rivet_response,
            kb_coverage=KBCoverage.STRONG,
            vendor=VendorType.SIEMENS,
            request=rivet_request
        )
    """

    # Safety keywords by severity
    DANGER_KEYWORDS = [
        "480v", "high voltage", "arc flash", "live electrical", "energized",
        "electrocution", "shock hazard", "de-energize"
    ]

    WARNING_KEYWORDS = [
        "vfd", "drive", "dc bus", "capacitor", "residual voltage",
        "stored energy", "wait 5 minutes", "lockout", "tagout", "loto"
    ]

    CAUTION_KEYWORDS = [
        "moving parts", "pinch point", "hot surface", "sharp edge",
        "overhead hazard", "confined space", "wear ppe", "safety glasses"
    ]

    # VFD-specific safety (vendor-aware)
    VFD_SAFETY_WARNINGS = {
        VendorType.SIEMENS: "⚠️ **VFD Safety:** Siemens drives retain DC bus voltage for 5+ minutes after shutdown. Verify zero voltage with multimeter before servicing.",
        VendorType.ROCKWELL: "⚠️ **VFD Safety:** PowerFlex drives retain DC bus voltage for 5+ minutes after shutdown. Verify zero voltage with multimeter before servicing.",
        VendorType.ABB: "⚠️ **VFD Safety:** ABB drives retain DC bus voltage for 5+ minutes after shutdown. Verify zero voltage with multimeter before servicing.",
        VendorType.SCHNEIDER: "⚠️ **VFD Safety:** Schneider drives retain DC bus voltage for 5+ minutes after shutdown. Verify zero voltage with multimeter before servicing.",
        VendorType.GENERIC: "⚠️ **VFD Safety:** VFDs retain DC bus voltage after shutdown. Wait manufacturer-specified time and verify zero voltage before servicing."
    }

    def __init__(self, enable_citations: bool = True, enable_safety: bool = True):
        """
        Initialize Response Synthesizer.

        Args:
            enable_citations: Add inline citations and footer (default: True)
            enable_safety: Inject safety warnings (default: True)
        """
        # Feature flags (can be disabled via environment)
        self.enable_citations = enable_citations and os.getenv("ENABLE_RESPONSE_CITATIONS", "true").lower() == "true"
        self.enable_safety = enable_safety and os.getenv("ENABLE_RESPONSE_SAFETY", "true").lower() == "true"
        self.enable_step_formatting = os.getenv("ENABLE_RESPONSE_STEPS", "true").lower() == "true"
        self.enable_confidence_badge = os.getenv("ENABLE_RESPONSE_CONFIDENCE", "true").lower() == "true"

    def synthesize(
        self,
        response: RivetResponse,
        kb_coverage: KBCoverage,
        vendor: VendorType,
        request: RivetRequest
    ) -> RivetResponse:
        """
        Apply all enhancements to response.

        Args:
            response: Raw response from SME agent
            kb_coverage: Knowledge base coverage level
            vendor: Detected vendor
            request: Original user request

        Returns:
            Enhanced RivetResponse with all formatting applied
        """
        # Work on a copy
        enhanced_text = response.answer_text

        # 1. Format citations (if sources exist)
        if self.enable_citations and response.sources:
            enhanced_text = self._add_inline_citations(enhanced_text, response.sources)
            citation_footer = self._format_citation_footer(response.sources)
            enhanced_text += f"\n\n{citation_footer}"

        # 2. Inject safety warnings
        if self.enable_safety:
            safety_warnings = self._generate_safety_warnings(vendor, request, response)
            if safety_warnings:
                safety_section = self._format_safety_section(safety_warnings)
                enhanced_text = f"{safety_section}\n\n{enhanced_text}"

        # 3. Format troubleshooting steps
        if self.enable_step_formatting and self._has_steps(enhanced_text):
            enhanced_text = self._format_steps(enhanced_text)

        # 4. Add confidence indicator
        if self.enable_confidence_badge:
            confidence_badge = self._get_confidence_badge(kb_coverage)
            enhanced_text = f"{confidence_badge}\n\n{enhanced_text}"

        # Return new response with enhanced text
        return RivetResponse(
            answer_text=enhanced_text,
            sources=response.sources,
            confidence=response.confidence,
            route_decision=response.route_decision,
            links=response.links
        )

    def _add_inline_citations(self, text: str, sources: List[Dict]) -> str:
        """
        Add [1], [2] inline where sources are mentioned.

        Args:
            text: Original response text
            sources: List of source dictionaries

        Returns:
            Text with inline citations added
        """
        # Sort sources by length (longest first to avoid partial matches)
        sorted_sources = sorted(sources, key=lambda s: len(s.get("title", "")), reverse=True)

        for i, source in enumerate(sorted_sources, 1):
            title = source.get("title", "")
            if not title:
                continue

            # Find mentions of source title in text
            # Only replace first occurrence to avoid over-citing
            if title.lower() in text.lower():
                # Find position (case-insensitive)
                pattern = re.compile(re.escape(title), re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    # Replace with cited version
                    text = text[:match.end()] + f" [{i}]" + text[match.end():]

        return text

    def _format_citation_footer(self, sources: List[Dict]) -> str:
        """
        Format citation footer: [1] Source Title, Page 45 (URL)

        Args:
            sources: List of source dictionaries

        Returns:
            Formatted footer string
        """
        footer = "📚 **Sources:**"

        # Limit to top 5 sources
        for i, source in enumerate(sources[:5], 1):
            title = source.get("title", "Unknown")
            page = source.get("page_num") or source.get("page")
            url = source.get("url", "")

            citation = f"\n[{i}] {title}"

            if page:
                citation += f", Page {page}"

            if url and url != "":
                citation += f" ({url})"

            footer += citation

        if len(sources) > 5:
            footer += f"\n_(+{len(sources) - 5} more sources)_"

        return footer

    def _generate_safety_warnings(
        self,
        vendor: VendorType,
        request: RivetRequest,
        response: RivetResponse
    ) -> List[SafetyWarning]:
        """
        Auto-detect safety hazards and generate warnings.

        Args:
            vendor: Detected vendor
            request: Original request
            response: Response text

        Returns:
            List of SafetyWarning objects
        """
        warnings = []

        # Combine request + response text for analysis
        text_combined = f"{request.text} {response.answer_text}".lower()

        # Check for DANGER keywords (high voltage, arc flash)
        if any(kw in text_combined for kw in self.DANGER_KEYWORDS):
            warnings.append(SafetyWarning(
                level="danger",
                icon="🔴",
                message="**DANGER:** De-energize equipment and verify zero voltage before servicing. Follow NFPA 70E arc flash requirements and facility lockout/tagout procedures."
            ))

        # Check for WARNING keywords (VFD, capacitors)
        elif any(kw in text_combined for kw in self.WARNING_KEYWORDS):
            # VFD-specific warning
            if "vfd" in text_combined or "drive" in text_combined:
                vfd_warning = self.VFD_SAFETY_WARNINGS.get(vendor, self.VFD_SAFETY_WARNINGS[VendorType.GENERIC])
                warnings.append(SafetyWarning(
                    level="warning",
                    icon="⚠️",
                    message=vfd_warning
                ))
            else:
                warnings.append(SafetyWarning(
                    level="warning",
                    icon="⚠️",
                    message="**WARNING:** Follow facility lockout/tagout (LOTO) procedures before servicing equipment. Verify all energy sources are isolated."
                ))

        # Check for CAUTION keywords
        elif any(kw in text_combined for kw in self.CAUTION_KEYWORDS):
            warnings.append(SafetyWarning(
                level="caution",
                icon="⚠️",
                message="**CAUTION:** Wear appropriate PPE. Be aware of pinch points, hot surfaces, and moving parts."
            ))

        # Default LOTO reminder (if no specific hazard detected)
        if not warnings:
            warnings.append(SafetyWarning(
                level="info",
                icon="ℹ️",
                message="Follow facility lockout/tagout procedures before servicing equipment."
            ))

        return warnings

    def _format_safety_section(self, warnings: List[SafetyWarning]) -> str:
        """
        Format safety warnings into section.

        Args:
            warnings: List of SafetyWarning objects

        Returns:
            Formatted safety section string
        """
        if not warnings:
            return ""

        # Sort by severity (danger → warning → caution → info)
        severity_order = {"danger": 0, "warning": 1, "caution": 2, "info": 3}
        sorted_warnings = sorted(warnings, key=lambda w: severity_order.get(w.level, 99))

        # Format section
        section = "🛡️ **SAFETY FIRST**\n"
        for warning in sorted_warnings:
            section += f"{warning.icon} {warning.message}\n"

        return section.strip()

    def _has_steps(self, text: str) -> bool:
        """Check if text contains troubleshooting steps."""
        step_indicators = [
            r'step \d+',
            r'\d+\.\s',  # Numbered list
            r'first,.*second,.*third',
            r'procedure:',
            r'follow these steps'
        ]

        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in step_indicators)

    def _format_steps(self, text: str) -> str:
        """
        Convert narrative to numbered steps with checkboxes.

        Args:
            text: Text potentially containing steps

        Returns:
            Text with formatted steps
        """
        lines = text.split("\n")
        formatted_lines = []

        for line in lines:
            stripped = line.strip()

            # Already numbered (1. or Step 1:)
            if re.match(r'^(\d+\.|\d+\))\s', stripped):
                # Add checkbox
                formatted_lines.append(f"☐ {stripped}")

            # "Step X:" format
            elif re.match(r'^step\s+\d+:', stripped, re.IGNORECASE):
                formatted_lines.append(f"☐ {stripped}")

            else:
                # Keep as-is
                formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _get_confidence_badge(self, kb_coverage: KBCoverage) -> str:
        """
        Return confidence indicator based on KB coverage.

        Args:
            kb_coverage: Knowledge base coverage level

        Returns:
            Formatted confidence badge
        """
        if kb_coverage == KBCoverage.STRONG:
            return "✅ **High Confidence** - Strong knowledge base coverage"
        elif kb_coverage == KBCoverage.THIN:
            return "⚠️ **Limited Coverage** - Answer based on available documentation"
        elif kb_coverage == KBCoverage.NONE:
            return "❓ **Low Confidence** - Consider booking expert call for verification"
        else:
            return "ℹ️ **Informational** - General guidance provided"
