#!/usr/bin/env python3
"""
KB Seed URLs - Curated list of industrial PLC/automation PDF manuals

These URLs are pushed to the VPS KB Factory Redis queue for ingestion.
Target: 100+ knowledge atoms from high-quality sources.
"""

# =============================================================================
# ALLEN-BRADLEY / ROCKWELL AUTOMATION
# =============================================================================
ALLEN_BRADLEY_URLS = [
    # ControlLogix
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um001_-en-p.pdf",  # ControlLogix System User Manual
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/pm/1756-pm001_-en-p.pdf",  # Logix5000 Controllers General Instructions
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/rm/1756-rm003_-en-p.pdf",  # Logix5000 Controllers Motion Instructions

    # CompactLogix
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1769-um021_-en-p.pdf",  # CompactLogix 5380 Controllers User Manual

    # Studio 5000
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um022_-en-p.pdf",  # Studio 5000 Logix Designer User Manual

    # PowerFlex Drives
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/750-um001_-en-p.pdf",   # PowerFlex 750-Series User Manual
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/520-um001_-en-p.pdf",   # PowerFlex 520-Series User Manual

    # PanelView HMI
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/2711p-um001_-en-p.pdf", # PanelView Plus 7 User Manual

    # Safety
    "https://literature.rockwellautomation.com/idc/groups/literature/documents/um/1756-um020_-en-p.pdf",  # GuardLogix Safety Controllers
]

# =============================================================================
# SIEMENS
# =============================================================================
SIEMENS_URLS = [
    # S7-1200
    "https://support.industry.siemens.com/cs/attachments/109814829/s71200_system_manual_en-US_en-US.pdf",

    # S7-1500
    "https://support.industry.siemens.com/cs/attachments/109747136/s71500_system_manual_en-US_en-US.pdf",

    # TIA Portal (if accessible)
    # Note: Siemens often requires login for full manuals
]

# =============================================================================
# MITSUBISHI
# =============================================================================
MITSUBISHI_URLS = [
    # MELSEC iQ-R Series
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh080483eng/sh080483engap.pdf",  # iQ-R CPU User Manual

    # GX Works3
    "https://dl.mitsubishielectric.com/dl/fa/document/manual/plc/sh081215eng/sh081215engae.pdf",  # GX Works3 Operating Manual
]

# =============================================================================
# OMRON
# =============================================================================
OMRON_URLS = [
    # NX/NJ Series
    "https://assets.omron.eu/downloads/manual/en/w501_nx-series_cpu_unit_users_manual_en.pdf",

    # Sysmac Studio
    "https://assets.omron.eu/downloads/manual/en/w504_sysmac_studio_operation_manual_en.pdf",
]

# =============================================================================
# SCHNEIDER ELECTRIC / MODICON
# =============================================================================
SCHNEIDER_URLS = [
    # Modicon M340
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000001578&p_enDocType=User%20guide&p_File_Name=EIO0000001578.00.pdf",

    # Unity Pro
    "https://download.schneider-electric.com/files?p_Doc_Ref=EIO0000000071&p_enDocType=User%20guide&p_File_Name=EIO0000000071.03.pdf",
]

# =============================================================================
# ABB
# =============================================================================
ABB_URLS = [
    # AC500 PLC
    # Note: ABB requires account for most manuals - add accessible ones here
]

# =============================================================================
# FUJI ELECTRIC
# =============================================================================
FUJI_ELECTRIC_URLS = [
    # FRENIC-Mini Series (Variable Frequency Drives)
    "https://www.fujielectric.com/products/manuals/doc/INV/ND286131E.pdf",  # FRENIC-Mini User Manual
    "https://www.fujielectric.com/products/manuals/doc/INV/ND286131E_10.pdf",  # FRENIC-Mini Ver 10

    # FRENIC-Mega Series
    "https://www.fujielectric.com/products/manuals/doc/INV/ND286141E.pdf",  # FRENIC-Mega User Manual

    # FRENIC-HVAC Series
    "https://www.fujielectric.com/products/manuals/doc/INV/ND286151E.pdf",  # FRENIC-HVAC User Manual

    # FRENIC-Ace Series
    "https://www.fujielectric.com/products/manuals/doc/INV/ND286161E.pdf",  # FRENIC-Ace User Manual
]

# =============================================================================
# YASKAWA
# =============================================================================
YASKAWA_URLS = [
    # A1000 Series Drives
    "https://www.yaskawa.com/downloads/download/7261/A1000_TechnicalManual.pdf",  # A1000 Technical Manual
    "https://www.yaskawa.com/downloads/download/7265/A1000_QuickStartGuide.pdf",  # A1000 Quick Start

    # V1000 Series Drives
    "https://www.yaskawa.com/downloads/download/7367/V1000_TechnicalManual.pdf",  # V1000 Technical Manual

    # GA700 Series Drives
    "https://www.yaskawa.com/downloads/download/8912/GA700_TechnicalManual.pdf",  # GA700 Technical Manual

    # MP3300iec Machine Controller
    "https://www.yaskawa.com/downloads/download/9245/MP3300iec_ProgrammingManual.pdf",  # MP3300iec Programming
]

# =============================================================================
# DANFOSS
# =============================================================================
DANFOSS_URLS = [
    # VLT FC 300 Series
    "https://assets.danfoss.com/documents/DOC353817433665/DOC353817433665.pdf",  # FC 300 Design Guide
    "https://assets.danfoss.com/documents/DOC116786436895/DOC116786436895.pdf",  # FC 300 Operating Instructions

    # VLT FC 302 Series
    "https://assets.danfoss.com/documents/DOC352889436638/DOC352889436638.pdf",  # FC 302 Programming Guide

    # VLT HVAC Drive
    "https://assets.danfoss.com/documents/DOC344618436596/DOC344618436596.pdf",  # VLT HVAC Drive Operating Instructions

    # VLT Automation Drive FC 360
    "https://assets.danfoss.com/documents/DOC375318437064/DOC375318437064.pdf",  # FC 360 Design Guide
]

# =============================================================================
# LENZE
# =============================================================================
LENZE_URLS = [
    # 8400 Inverter Drives
    "https://www.lenze.com/fileadmin/DE/downloads/Frequenzumrichter/8400/8400_EN_v6-2.pdf",  # 8400 Operating Instructions

    # i550 Servo Inverter
    "https://www.lenze.com/fileadmin/DE/downloads/Frequenzumrichter/i550/i550_EN_v4-0.pdf",  # i550 Technical Manual

    # 9400 Servo Drives
    "https://www.lenze.com/fileadmin/DE/downloads/Servoantriebe/9400/9400_EN_v3-1.pdf",  # 9400 Operating Manual

    # Smart Motor M550
    "https://www.lenze.com/fileadmin/DE/downloads/Smart_Motor/m550_EN_v2-0.pdf",  # m550 User Manual
]

# =============================================================================
# COMBINED LIST
# =============================================================================
SEED_URLS = (
    ALLEN_BRADLEY_URLS +
    SIEMENS_URLS +
    MITSUBISHI_URLS +
    OMRON_URLS +
    SCHNEIDER_URLS +
    ABB_URLS +
    FUJI_ELECTRIC_URLS +
    YASKAWA_URLS +
    DANFOSS_URLS +
    LENZE_URLS
)

# Metadata for tracking
URL_METADATA = {
    "allen_bradley": len(ALLEN_BRADLEY_URLS),
    "siemens": len(SIEMENS_URLS),
    "mitsubishi": len(MITSUBISHI_URLS),
    "omron": len(OMRON_URLS),
    "schneider": len(SCHNEIDER_URLS),
    "abb": len(ABB_URLS),
    "fuji_electric": len(FUJI_ELECTRIC_URLS),
    "yaskawa": len(YASKAWA_URLS),
    "danfoss": len(DANFOSS_URLS),
    "lenze": len(LENZE_URLS),
    "total": len(SEED_URLS),
}

if __name__ == "__main__":
    print("=" * 60)
    print("KB Seed URLs Summary")
    print("=" * 60)
    for manufacturer, count in URL_METADATA.items():
        if manufacturer != "total":
            print(f"  {manufacturer.replace('_', ' ').title()}: {count} PDFs")
    print("-" * 60)
    print(f"  TOTAL: {URL_METADATA['total']} PDFs")
    print("=" * 60)
    print("\nURLs to ingest:")
    for i, url in enumerate(SEED_URLS, 1):
        print(f"  {i}. {url[:80]}...")
