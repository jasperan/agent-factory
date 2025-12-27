"""
Equipment Taxonomy for Context Extraction
Phase 1: 50+ manufacturers, common component families
Phase 2 Prep: Extensible for user-defined equipment types
"""
import re
from typing import Dict, List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════
# COMPONENT FAMILIES (15 families, 50+ manufacturers)
# ═══════════════════════════════════════════════════════════════════════════

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
    },
    "plc": {
        "canonical": "Programmable Logic Controller",
        "aliases": ["PLC", "controller", "processor", "CPU", "logic controller"],
        "category": "PLCs & Controllers",
        "keywords": ["program", "logic", "io", "input", "output"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["controllogix", "compactlogix", "micrologix", "slc", "plc-5",
                            "1756", "1769", "1766", "1762", "1763", "5069"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["s7-1500", "s7-1200", "s7-300", "s7-400", "logo",
                            "1500", "1200", "et200"],
                "brand": "Siemens"
            },
            "mitsubishi": {
                "patterns": ["melsec", "fx", "q series", "iq-r", "iq-f", "fx5"],
                "brand": "Mitsubishi"
            },
            "omron": {
                "patterns": ["cj", "nj", "nx", "cp1", "cj2"],
                "brand": "Omron"
            },
            "beckhoff": {
                "patterns": ["cx", "twincat", "el"],
                "brand": "Beckhoff"
            }
        }
    },
    "hmi": {
        "canonical": "Human Machine Interface",
        "aliases": ["HMI", "touchscreen", "operator panel", "operator interface", "OIT", "display"],
        "category": "PLCs & Controllers",
        "keywords": ["screen", "display", "touch", "operator"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["panelview", "2711", "2711p", "2715"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["simatic", "comfort panel", "tp", "ktp", "mp"],
                "brand": "Siemens"
            },
            "proface": {
                "patterns": ["gp", "sp", "lt"],
                "brand": "Pro-face"
            }
        }
    },
    "motor": {
        "canonical": "Electric Motor",
        "aliases": ["motor", "induction motor", "AC motor", "DC motor"],
        "category": "Motors",
        "keywords": ["hp", "horsepower", "rpm", "torque"],
        "manufacturers": {}
    },
    "servo": {
        "canonical": "Servo Motor",
        "aliases": ["servo", "servo motor", "servo drive", "servo system"],
        "category": "Motion Control",
        "keywords": ["position", "encoder", "axis"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["kinetix", "mpl", "vpl", "2198"],
                "brand": "Allen-Bradley"
            },
            "siemens": {
                "patterns": ["simotics", "1fk", "1fl"],
                "brand": "Siemens"
            },
            "yaskawa": {
                "patterns": ["sigma", "sgd", "sgm"],
                "brand": "Yaskawa"
            }
        }
    },
    "sensor": {
        "canonical": "Sensor",
        "aliases": ["sensor", "proximity", "prox", "photoelectric", "photo eye", "limit switch"],
        "category": "Sensors & Instrumentation",
        "keywords": ["detect", "sense", "signal"],
        "manufacturers": {
            "banner": {
                "patterns": ["q", "qs", "world-beam", "s18", "m18"],
                "brand": "Banner Engineering"
            },
            "keyence": {
                "patterns": ["lr", "lv", "il", "pr", "pz"],
                "brand": "Keyence"
            },
            "ifm": {
                "patterns": ["efector", "o5", "ig", "ie"],
                "brand": "IFM"
            },
            "omron": {
                "patterns": ["e2e", "e3", "e2a"],
                "brand": "Omron"
            },
            "sick": {
                "patterns": ["w", "wl", "dt", "dx"],
                "brand": "SICK"
            },
            "turck": {
                "patterns": ["bi", "ni", "uprox"],
                "brand": "Turck"
            }
        }
    },
    "safety_relay": {
        "canonical": "Safety Relay",
        "aliases": ["safety relay", "guard relay", "e-stop relay", "safety controller"],
        "category": "Safety",
        "keywords": ["safety", "emergency", "stop", "guard"],
        "manufacturers": {
            "pilz": {
                "patterns": ["pnoz", "pss", "psen"],
                "brand": "Pilz"
            },
            "allen-bradley": {
                "patterns": ["guardmaster", "msr", "440r", "guardlogix"],
                "brand": "Allen-Bradley"
            },
            "banner": {
                "patterns": ["sc", "xsm"],
                "brand": "Banner"
            },
            "sick": {
                "patterns": ["flexi", "ue"],
                "brand": "SICK"
            }
        }
    },
    "contactor": {
        "canonical": "Motor Contactor",
        "aliases": ["contactor", "starter", "motor starter", "magnetic starter"],
        "category": "Motor Controls",
        "keywords": ["contact", "start", "coil"],
        "manufacturers": {}
    },
    "overload": {
        "canonical": "Overload Relay",
        "aliases": ["overload", "overload relay", "motor protector", "thermal overload"],
        "category": "Motor Controls",
        "keywords": ["overload", "thermal", "protection"],
        "manufacturers": {}
    },
    "valve": {
        "canonical": "Solenoid Valve",
        "aliases": ["valve", "solenoid", "solenoid valve", "directional valve", "pneumatic valve"],
        "category": "Pneumatics",
        "keywords": ["air", "pneumatic", "cylinder"],
        "manufacturers": {
            "festo": {
                "patterns": ["vuvs", "mfh", "jmfh", "cpv", "vtug"],
                "brand": "Festo"
            },
            "smc": {
                "patterns": ["sy", "vq", "vf", "sq"],
                "brand": "SMC"
            },
            "parker": {
                "patterns": ["viking", "gold ring"],
                "brand": "Parker"
            }
        }
    },
    "pressure_transmitter": {
        "canonical": "Pressure Transmitter",
        "aliases": ["pressure transmitter", "pressure sensor", "pressure transducer"],
        "category": "Sensors & Instrumentation",
        "keywords": ["pressure", "psi", "bar"],
        "manufacturers": {
            "endress": {
                "patterns": ["cerabar", "deltabar"],
                "brand": "Endress+Hauser"
            },
            "rosemount": {
                "patterns": ["3051", "2051", "2088"],
                "brand": "Rosemount"
            }
        }
    },
    "flow_meter": {
        "canonical": "Flow Meter",
        "aliases": ["flow meter", "flowmeter", "flow sensor", "flow transmitter"],
        "category": "Sensors & Instrumentation",
        "keywords": ["flow", "gpm", "rate"],
        "manufacturers": {}
    },
    "temperature": {
        "canonical": "Temperature Sensor",
        "aliases": ["temperature sensor", "thermocouple", "RTD", "temp sensor"],
        "category": "Sensors & Instrumentation",
        "keywords": ["temperature", "temp", "degrees", "thermal"],
        "manufacturers": {}
    },
    "power_supply": {
        "canonical": "Power Supply",
        "aliases": ["power supply", "PSU", "DC power"],
        "category": "Power Distribution",
        "keywords": ["24v", "voltage", "dc", "power"],
        "manufacturers": {
            "allen-bradley": {
                "patterns": ["1606", "bulletin 1606"],
                "brand": "Allen-Bradley"
            },
            "phoenix": {
                "patterns": ["quint", "trio", "step"],
                "brand": "Phoenix Contact"
            },
            "mean_well": {
                "patterns": ["dr-", "hdr-", "edr-"],
                "brand": "Mean Well"
            }
        }
    },
    "circuit_breaker": {
        "canonical": "Circuit Breaker",
        "aliases": ["breaker", "circuit breaker", "CB", "MCCB"],
        "category": "Power Distribution",
        "keywords": ["breaker", "amp", "trip"],
        "manufacturers": {}
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
    """
    Identify component family and manufacturer from text.

    Returns:
        {
            "family": "Variable Frequency Drive",
            "family_key": "vfd",
            "category": "Motor Controls",
            "manufacturer": "Allen-Bradley"
        }
    """
    text_lower = text.lower()

    for family_key, family_data in COMPONENT_FAMILIES.items():
        # Check aliases
        for alias in family_data["aliases"]:
            if alias.lower() in text_lower:
                # Found family, now check manufacturer
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

    # Check manufacturer patterns even without family match
    for family_key, family_data in COMPONENT_FAMILIES.items():
        for mfr_key, mfr_data in family_data.get("manufacturers", {}).items():
            for pattern in mfr_data["patterns"]:
                if pattern.lower() in text_lower:
                    return {
                        "family": family_data["canonical"],
                        "family_key": family_key,
                        "category": family_data["category"],
                        "manufacturer": mfr_data["brand"]
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
