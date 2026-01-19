"""Test just the database operations"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing database...")
from agent_factory.rivet_pro.database import RIVETProDatabase

db = RIVETProDatabase()

# Test machine creation
import uuid
test_user_id = str(uuid.uuid4())
machine = db.create_machine(
    test_user_id,
    "Test Lathe",
    "Test machine for backend validation"
)
print(f"  [OK] Created machine: {machine['name']}")
assert machine['name'] == "Test Lathe"

# Test manual gap logging
gap = db.log_manual_gap("Allen-Bradley", "VFD", "PowerFlex 525")
print(f"  [OK] Logged gap: {gap['manufacturer']} {gap['component_family']}")
assert gap['manufacturer'] == "Allen-Bradley"

# Test top gaps retrieval
gaps = db.get_top_manual_gaps()
print(f"  [OK] Top gaps: {len(gaps)} found")
assert isinstance(gaps, list)

db.close()
print("Database tests passed!")
