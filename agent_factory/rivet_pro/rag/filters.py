"""
Intent-to-Filter Mapping for RIVET Pro RAG

Converts RivetIntent objects into Supabase filter expressions for
knowledge_atoms table queries.

Author: Agent Factory
Created: 2025-12-17
Phase: 2/8 (RAG Layer)
"""

from typing import Dict, Any, List, Optional
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType


def build_filters(intent: RivetIntent) -> Dict[str, Any]:
    """
    Build Supabase filter dict from RivetIntent.

    Filters by vendor, equipment type, fault codes, and model numbers
    to retrieve relevant documentation.

    Args:
        intent: Parsed intent with vendor/equipment/fault info

    Returns:
        Dict suitable for Supabase .match() or .filter() operations

    Examples:
        >>> intent = RivetIntent(
        ...     vendor=VendorType.SIEMENS,
        ...     equipment_type=EquipmentType.VFD,
        ...     detected_model="G120C",
        ...     detected_fault_codes=["F3002"],
        ...     raw_summary="VFD fault troubleshooting",
        ...     context_source="text_only",
        ...     confidence=0.9,
        ...     kb_coverage="strong"
        ... )
        >>> filters = build_filters(intent)
        >>> filters
        {'vendor': 'Siemens', 'equipment_type': 'VFD'}
    """
    filters = {}

    # Always filter by vendor (unless unknown)
    if intent.vendor != VendorType.UNKNOWN:
        filters["vendor"] = intent.vendor.value

    # Always filter by equipment type (unless unknown)
    if intent.equipment_type != EquipmentType.UNKNOWN:
        filters["equipment_type"] = intent.equipment_type.value

    return filters


def build_keyword_filters(intent: RivetIntent) -> List[str]:
    """
    Extract keywords from intent for full-text search.

    Used in hybrid search mode to boost results containing specific
    model numbers, fault codes, or application keywords.

    Args:
        intent: Parsed intent

    Returns:
        List of keywords to search for

    Examples:
        >>> intent = RivetIntent(
        ...     vendor=VendorType.SIEMENS,
        ...     equipment_type=EquipmentType.VFD,
        ...     detected_model="G120C",
        ...     detected_fault_codes=["F3002"],
        ...     application="overhead_crane",
        ...     raw_summary="VFD fault troubleshooting",
        ...     context_source="text_only",
        ...     confidence=0.9,
        ...     kb_coverage="strong"
        ... )
        >>> build_keyword_filters(intent)
        ['G120C', 'F3002', 'overhead_crane', 'VFD', 'fault', 'troubleshooting']
    """
    keywords = []

    # Add detected model
    if intent.detected_model:
        keywords.append(intent.detected_model)

    # Add fault codes
    if intent.detected_fault_codes:
        keywords.extend(intent.detected_fault_codes)

    # Add application context
    if intent.application:
        keywords.append(intent.application)

    # Extract keywords from raw_summary (simple tokenization)
    if intent.raw_summary:
        # Split by spaces and filter out short words
        words = [
            word.strip().lower()
            for word in intent.raw_summary.split()
            if len(word.strip()) >= 3
        ]
        keywords.extend(words)

    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword.lower() not in seen:
            seen.add(keyword.lower())
            unique_keywords.append(keyword)

    return unique_keywords


def build_part_number_filter(part_number: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Build filter for exact part number match.

    When a part number is detected (e.g., from nameplate OCR),
    we want exact matches first before falling back to general docs.

    Args:
        part_number: Detected part number (e.g., "6SL3244-0BB13-1PA0")

    Returns:
        Filter dict or None if no part number

    Examples:
        >>> build_part_number_filter("6SL3244-0BB13-1PA0")
        {'part_number': '6SL3244-0BB13-1PA0'}
        >>> build_part_number_filter(None)
        None
    """
    if not part_number:
        return None

    return {"part_number": part_number}
