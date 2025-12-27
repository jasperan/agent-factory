"""
Equipment Taxonomy for Context Extraction
Phase 1: 50+ manufacturers, common component families
Phase 2 Prep: Extensible for user-defined equipment types
"""
import re
from typing import Dict, List, Optional, Tuple

# Component families dictionary - copied from spec
COMPONENT_FAMILIES = {
    "vfd": {
        "canonical": "Variable Frequency Drive",
        "aliases": ["VFD", "drive", "inverter", "AC drive", "variable speed drive", "frequency drive"],
        "category": "Motor Controls",
        "keywords": ["motor", "speed", "frequency", "hz"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["powerflex", "1336", "160", "22a", "22b", "22c", "22d", "22f"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["sinamics", "micromaster", "g120", "g110", "v20"],
                "brand": "Siemens"
            },
            "abb": {
                "patterns": ["acs", "ach", "acs880", "acs580", "acs355"],
                "brand": "ABB"
            },
            "yaskawa": {
                "patterns": ["v1000", "a1000", "j1000", "ga700", "ga500"],
                "brand": "Yaskawa"
            },
            "danfoss": {
                "patterns": ["vlt", "fc-", "fc102", "fc302"],
                "brand": "Danfoss"
            },
            "schneider": {
                "patterns": ["altivar", "atv", "atv320", "atv630"],
                "brand": "Schneider Electric"
            },
            "weg": {
                "patterns": ["cfw", "cfw11", "cfw500"],
                "brand": "WEG"
            }
        }
    }
}

# Issue type keywords
ISSUE_KEYWORDS = {
    "fault_code": ["fault", "error", "alarm", "code", "f0", "e0", "err", "failure"],
    "wont_start": ["won't start", "wont start", "no start", "doesn't start", "dead", "no power"],
    "intermittent": ["intermittent", "sometimes", "random", "sporadic", "comes and goes", "occasionally"],
    "noise_vibration": ["noise", "vibration", "grinding", "humming", "buzzing", "rattling", "squealing"],
    "overheating": ["hot", "overheating", "temperature", "thermal", "burning", "smoke"],
    "communication": ["communication", "network", "ethernet", "no connection", "offline", "lost comm", "timeout"],
    "calibration": ["calibration", "drift", "accuracy", "offset", "scaling", "out of range"],
    "physical_damage": ["broken", "cracked", "damaged", "burnt", "melted", "corroded"],
    "performance": ["slow", "weak", "reduced", "poor", "degraded", "sluggish"],
    "leak": ["leak", "leaking", "drip", "seep"]
}

# Urgency keywords
URGENCY_KEYWORDS = {
    "critical": ["down", "stopped", "urgent", "emergency", "production stopped", "critical", "safety"],
    "high": ["asap", "high priority", "soon", "important", "need now"],
    "low": ["when you can", "no rush", "minor", "cosmetic", "when possible"]
}

def identify_component(text: str) -> Dict:
    """Identify component family and manufacturer from text."""
    text_lower = text.lower()
    
    for family_key, family_data in COMPONENT_FAMILIES.items():
        for alias in family_data["aliases"]:
            if alias.lower() in text_lower:
                manufacturer = None
                
                for mfr_key, mfr_data in family_data.get("manufacturers", {}).items():
                    for pattern in mfr_data["patterns"]:
                        if pattern.lower() in text_lower:
                            manufacturer = mfr_data["brand"]
                            break
                    if manufacturer:
                        break
                
                return {
                    "family": family_data["canonical"],
                    "family_key": family_key,
                    "category": family_data["category"],
                    "manufacturer": manufacturer
                }
    
    return {"family": None, "family_key": None, "category": None, "manufacturer": None}

def identify_issue_type(text: str) -> str:
    """Identify the type of issue from text."""
    text_lower = text.lower()
    
    for issue_type, keywords in ISSUE_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return issue_type
    
    return "unknown"

def identify_urgency(text: str) -> str:
    """Identify urgency level from text."""
    text_lower = text.lower()
    
    for urgency, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return urgency
    
    return "medium"

def extract_fault_code(text: str) -> Optional[str]:
    """Extract fault code from text."""
    patterns = [
        r'\b[fF]\d{1,4}\b',
        r'\b[eE]rr?\d{1,4}\b',
        r'\b[aA]larm\s*\d{1,4}\b',
        r'\bfault\s*code\s*(\d+)\b',
        r'\bcode\s+([A-Za-z]?\d+)\b',
        r'\berror\s+([A-Za-z]?\d+)\b',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0).upper().replace(" ", "")
    
    return None
