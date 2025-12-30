"""
Supabase Filter Builder for RIVET Pro RAG

Constructs Supabase query filters from RivetIntent metadata.

Phase 2/8 of RIVET Pro Multi-Agent Backend.
"""

from typing import Dict, List, Optional, Any
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType

def build_metadata_filter(intent: RivetIntent) -> Dict[str, Any]:
    """
    Build Supabase metadata filter from RivetIntent.

    Args:
        intent: Classified user intent with vendor, equipment, etc.

    Returns:
        Dictionary of Supabase query filters
    """
    filters = {}

    # Vendor filter
    if intent.vendor and intent.vendor != VendorType.UNKNOWN:
        vendor_str = intent.vendor if isinstance(intent.vendor, str) else intent.vendor.value
        filters["vendor"] = {
            "$eq": vendor_str
        }

    # Equipment type filter
    if intent.equipment_type and intent.equipment_type != EquipmentType.UNKNOWN:
        equip_str = intent.equipment_type if isinstance(intent.equipment_type, str) else intent.equipment_type.value
        filters["equipment_type"] = {
            "$eq": equip_str
        }

    # Fault code filter (if detected)
    if intent.detected_fault_codes:
        filters["fault_codes"] = {
            "$contains": intent.detected_fault_codes
        }

    # Equipment model filter (if detected)
    if intent.detected_model:
        filters["models"] = {
            "$contains": [intent.detected_model]
        }

    return filters


def build_atom_type_filter(atom_types: Optional[List[str]] = None) -> Optional[Dict[str, Any]]:
    """
    Build filter for atom types (fault, procedure, concept, etc.).

    Args:
        atom_types: List of atom types to include. If None, no filter.

    Returns:
        Supabase filter or None
    """
    if not atom_types:
        return None

    return {
        "atom_type": {
            "$in": atom_types
        }
    }


def build_safety_filter(min_safety_level: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Build filter for safety level (info, caution, warning, danger).

    Args:
        min_safety_level: Minimum safety level to include

    Returns:
        Supabase filter or None
    """
    if not min_safety_level:
        return None

    # Safety levels in order of severity
    safety_order = ["info", "caution", "warning", "danger"]

    if min_safety_level not in safety_order:
        return None

    # Include all levels >= min_safety_level
    min_index = safety_order.index(min_safety_level)
    included_levels = safety_order[min_index:]

    return {
        "safety_level": {
            "$in": included_levels
        }
    }


def combine_filters(*filter_dicts: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Combine multiple filter dictionaries using AND logic.

    Args:
        *filter_dicts: Variable number of filter dictionaries

    Returns:
        Combined filter dictionary
    """
    combined = {}

    for filter_dict in filter_dicts:
        if filter_dict:
            combined.update(filter_dict)

    return combined if combined else {}


# ============================================================================
# Keyword Extraction for Hybrid Search
# ============================================================================

def extract_search_keywords(intent: RivetIntent) -> List[str]:
    """
    Extract searchable keywords from RivetIntent.

    Used for keyword search component of hybrid search.

    Args:
        intent: Classified user intent

    Returns:
        List of keywords to search
    """
    keywords = []

    # Add vendor name
    if intent.vendor and intent.vendor != VendorType.UNKNOWN:
        vendor_str = intent.vendor if isinstance(intent.vendor, str) else intent.vendor.value
        keywords.append(vendor_str)

    # Add equipment type
    if intent.equipment_type and intent.equipment_type != EquipmentType.UNKNOWN:
        equip_str = intent.equipment_type if isinstance(intent.equipment_type, str) else intent.equipment_type.value
        keywords.append(equip_str)

    # Add fault codes
    if intent.detected_fault_codes:
        keywords.extend(intent.detected_fault_codes)

    # Add equipment model
    if intent.detected_model:
        keywords.append(intent.detected_model)

    # Add application context
    if intent.application:
        app_str = intent.application if isinstance(intent.application, str) else intent.application.value
        keywords.append(app_str)

    # Add symptom keywords (extract nouns from raw_summary)
    if intent.raw_summary:
        # Simple noun extraction: words longer than 4 chars, not common stopwords
        stopwords = {"this", "that", "with", "from", "what", "when", "where", "have", "been"}
        words = intent.raw_summary.lower().split()
        keywords.extend([
            word.strip(".,!?;:")
            for word in words
            if len(word) > 4 and word.lower() not in stopwords
        ])

    # Deduplicate and filter
    return list(set(k.lower() for k in keywords if k))
