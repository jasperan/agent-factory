#!/usr/bin/env python3
"""
Export Golden Test Cases from Neon PostgreSQL

Transforms your knowledge atoms into Phoenix eval-ready format.
Run this to create the golden dataset for LLM-as-judge evals.

Usage:
    # Export first 50 cases (for testing)
    python export_golden_dataset.py --limit 50
    
    # Export all relevant cases
    python export_golden_dataset.py
    
    # Custom output path
    python export_golden_dataset.py --output datasets/golden_v2.jsonl
"""

import os
import re
import json
import argparse
from datetime import datetime
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()


def get_db_connection():
    """Get Supabase client (REST API - avoids PostgreSQL IPv6 issues)."""
    from supabase import create_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env"
        )

    return create_client(url, key)


def extract_fault_code(content: str) -> str:
    """
    Extract fault code from content text using common patterns.
    
    Patterns detected:
    - Siemens: F47, F001, A001
    - Rockwell: E001, E123
    - Generic: ALM-123, FAULT-01, ERR-42
    """
    patterns = [
        r'\b[FEA]\d{2,4}\b',           # F47, E001, A123
        r'\bF\d+\b',                    # F1, F123
        r'\bALM[-_]?\d+\b',             # ALM-123, ALM_456
        r'\bFAULT[-_]?\d+\b',           # FAULT-01
        r'\bERR[-_]?\d+\b',             # ERR-42
        r'\bALARM[-_]?\d+\b',           # ALARM-01
        r'\b\d{4}\b',                   # 4-digit codes like 0047
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group().upper()
    
    return "UNKNOWN"


def extract_manufacturer(content: str, metadata: dict) -> str:
    """Extract equipment manufacturer from content or metadata."""
    # Check metadata first
    if metadata.get("manufacturer"):
        return metadata["manufacturer"]
    
    # Pattern matching in content
    manufacturers = {
        "siemens": ["siemens", "s7-1200", "s7-1500", "g120", "sinamics"],
        "rockwell": ["rockwell", "allen-bradley", "compactlogix", "controllogix", "powerflex"],
        "abb": ["abb", "acs580", "acs880"],
        "schneider": ["schneider", "altivar", "modicon"],
        "mitsubishi": ["mitsubishi", "melsec"],
        "fanuc": ["fanuc"],
    }
    
    content_lower = content.lower()
    for mfr, keywords in manufacturers.items():
        if any(kw in content_lower for kw in keywords):
            return mfr.title()
    
    return "Unknown"


def extract_equipment_model(content: str, metadata: dict) -> str:
    """Extract equipment model from content or metadata."""
    if metadata.get("model") or metadata.get("equipment_model"):
        return metadata.get("model") or metadata.get("equipment_model")
    
    # Common model patterns
    patterns = [
        r'\bS7-\d{4}\b',                # S7-1200, S7-1500
        r'\bCompactLogix\s*\d*\b',      # CompactLogix 5380
        r'\bG120[CD]?\b',               # G120, G120C, G120D
        r'\bPowerFlex\s*\d+\b',         # PowerFlex 525
        r'\bACS\d{3}\b',                # ACS580, ACS880
        r'\bAltivar\s*\d+\b',           # Altivar 320
    ]
    
    for pattern in patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group()
    
    return "Unknown"


def extract_root_cause(content: str, metadata: dict) -> str:
    """Extract root cause from content or metadata."""
    if metadata.get("root_cause"):
        return metadata["root_cause"]
    
    # Look for trigger phrases
    triggers = [
        "caused by", "root cause", "due to", "because of",
        "results from", "indicates", "means", "occurs when"
    ]
    
    content_lower = content.lower()
    for trigger in triggers:
        idx = content_lower.find(trigger)
        if idx != -1:
            # Extract surrounding context
            start = max(0, idx)
            end = min(len(content), idx + 300)
            # Find sentence end
            excerpt = content[start:end]
            # Cut at period if found
            period_idx = excerpt.find(". ", 50)
            if period_idx > 50:
                excerpt = excerpt[:period_idx + 1]
            return excerpt.strip()
    
    # Fallback: first 200 chars
    return content[:200].strip()


def extract_safety_warnings(content: str, metadata: dict) -> list:
    """Extract safety warnings from content."""
    if metadata.get("safety_warnings"):
        return metadata["safety_warnings"]
    
    warnings = []
    
    # Keywords that indicate safety concerns
    safety_triggers = [
        "lockout", "tagout", "loto", "de-energize",
        "verify voltage", "ppe", "arc flash", "high voltage",
        "rotating", "pinch point", "burn", "shock",
        "before inspection", "before work", "hazard"
    ]
    
    content_lower = content.lower()
    for trigger in safety_triggers:
        if trigger in content_lower:
            # Find the sentence containing this trigger
            idx = content_lower.find(trigger)
            # Find sentence boundaries
            start = content.rfind(".", 0, idx)
            end = content.find(".", idx)
            if start == -1:
                start = 0
            if end == -1:
                end = len(content)
            sentence = content[start+1:end].strip()
            if sentence and len(sentence) > 10:
                warnings.append(sentence)
    
    # Deduplicate and limit
    seen = set()
    unique_warnings = []
    for w in warnings:
        w_lower = w.lower()[:50]
        if w_lower not in seen:
            seen.add(w_lower)
            unique_warnings.append(w)
    
    return unique_warnings[:5]  # Max 5 warnings


def export_golden_cases(
    output_path: str,
    limit: Optional[int] = None,
    table_name: str = "knowledge_atoms"
) -> list:
    """
    Export fault-related knowledge atoms as golden test cases.
    
    Args:
        output_path: Path for output JSONL file
        limit: Max cases to export (None for all)
        table_name: Name of knowledge atoms table
    
    Returns:
        List of exported cases
    """
    client = get_db_connection()

    # Query for atoms with fault-related content using Supabase API
    logger.info(f"Querying {table_name} via Supabase REST API...")

    query = client.table(table_name).select("id,title,summary,content,created_at")

    # Apply fault-related filters (OR conditions)
    # Note: Supabase doesn't support multi-column OR in simple query, so we fetch and filter
    if limit:
        query = query.limit(min(limit * 5, 500))  # Fetch extra to account for filtering
    else:
        query = query.limit(500)  # Reasonable default limit

    result = query.execute()

    # Client-side filtering for fault-related content
    rows = []
    for atom in result.data:
        content = (atom.get('content') or '').lower()
        title = (atom.get('title') or '').lower()
        summary = (atom.get('summary') or '').lower()

        if any(keyword in content or keyword in title or keyword in summary
               for keyword in ['fault', 'error', 'alarm', 'troubleshoot', 'diagnosis', 'repair']):
            rows.append(atom)
            if limit and len(rows) >= limit:
                break

    logger.info(f"Found {len(rows)} fault-related atoms (filtered from {len(result.data)} total)")
    
    # Transform to golden dataset format
    cases = []
    for atom in rows:
        atom_id = atom.get('id')
        title = atom.get('title', '')
        summary = atom.get('summary', '')
        content = atom.get('content', '')
        created_at = atom.get('created_at')

        # Metadata not typically stored separately in knowledge_atoms, extract from content
        metadata = {}
        
        # Extract fields
        fault_code = extract_fault_code(content)
        manufacturer = extract_manufacturer(content, metadata)
        model = extract_equipment_model(content, metadata)
        root_cause = extract_root_cause(content, metadata)
        safety_warnings = extract_safety_warnings(content, metadata)
        
        case = {
            "test_case_id": f"atom_{atom_id}",
            "source": "supabase_knowledge_atoms",
            "equipment": {
                "manufacturer": manufacturer,
                "model": model,
                "subsystem": metadata.get("subsystem", "General")
            },
            "input": {
                "fault_code": fault_code,
                "fault_description": summary or title or content[:200],
                "sensor_data": metadata.get("sensor_data", {}),
                "context": content[:1000]
            },
            "expected_output": {
                "root_cause": root_cause,
                "safety_critical_warnings": safety_warnings,
                "repair_steps": metadata.get("repair_steps", []),
                "manual_citations": metadata.get("citations", []),
                "business_impact": {
                    "safety_critical": bool(safety_warnings) or metadata.get("safety_critical", False)
                }
            },
            "metadata": {
                "atom_id": atom_id,
                "exported_at": datetime.utcnow().isoformat(),
                "needs_review": True,  # Flag for manual verification
                "content_length": len(content)
            }
        }
        cases.append(case)
    
    # Write JSONL
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    
    logger.info(f"✅ Exported {len(cases)} cases to {output_path}")
    
    # Print summary stats
    manufacturers = {}
    fault_codes = {}
    for case in cases:
        mfr = case["equipment"]["manufacturer"]
        fc = case["input"]["fault_code"]
        manufacturers[mfr] = manufacturers.get(mfr, 0) + 1
        fault_codes[fc] = fault_codes.get(fc, 0) + 1
    
    logger.info("\nExport Summary:")
    logger.info(f"  Total cases: {len(cases)}")
    logger.info(f"  By manufacturer: {dict(sorted(manufacturers.items(), key=lambda x: -x[1])[:5])}")
    logger.info(f"  Unique fault codes: {len(fault_codes)}")
    logger.info(f"  Top fault codes: {dict(sorted(fault_codes.items(), key=lambda x: -x[1])[:5])}")

    # No need to close Supabase client
    return cases


def validate_golden_dataset(path: str) -> dict:
    """Validate a golden dataset file."""
    issues = {
        "missing_fault_code": [],
        "missing_root_cause": [],
        "no_safety_warnings": [],
        "short_content": [],
    }
    
    with open(path) as f:
        for i, line in enumerate(f, 1):
            case = json.loads(line)
            case_id = case.get("test_case_id", f"line_{i}")
            
            if case["input"]["fault_code"] == "UNKNOWN":
                issues["missing_fault_code"].append(case_id)
            
            if len(case["expected_output"]["root_cause"]) < 20:
                issues["missing_root_cause"].append(case_id)
            
            if not case["expected_output"]["safety_critical_warnings"]:
                issues["no_safety_warnings"].append(case_id)
            
            if case["metadata"]["content_length"] < 100:
                issues["short_content"].append(case_id)
    
    return issues


def main():
    parser = argparse.ArgumentParser(
        description="Export golden test cases from Neon knowledge atoms"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="datasets/golden_from_neon.jsonl",
        help="Output JSONL file path"
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=None,
        help="Limit number of cases to export"
    )
    parser.add_argument(
        "--table",
        type=str,
        default="knowledge_atoms",
        help="Table name to query"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate existing dataset instead of exporting"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GOLDEN DATASET EXPORT")
    print("=" * 60)
    
    if args.validate:
        print(f"Validating: {args.output}")
        issues = validate_golden_dataset(args.output)
        
        print("\n📋 Validation Results:")
        for issue_type, cases in issues.items():
            if cases:
                print(f"  ⚠️  {issue_type}: {len(cases)} cases")
                if len(cases) <= 5:
                    print(f"      {cases}")
            else:
                print(f"  ✅ {issue_type}: None")
        
        total_issues = sum(len(v) for v in issues.values())
        if total_issues == 0:
            print("\n🎉 Dataset looks good!")
        else:
            print(f"\n⚠️  Found {total_issues} potential issues to review")
    else:
        print(f"Output: {args.output}")
        print(f"Limit: {args.limit or 'None (all)'}")
        print(f"Table: {args.table}")
        print("=" * 60 + "\n")
        
        export_golden_cases(args.output, args.limit, args.table)
        
        print("\n" + "=" * 60)
        print("Next steps:")
        print("1. Review exported cases: head -n 5 " + args.output)
        print("2. Validate: python export_golden_dataset.py --validate")
        print("3. Run evals: python evals/run_eval.py --dataset " + args.output)
        print("=" * 60)


if __name__ == "__main__":
    main()
