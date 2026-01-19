"""Minimal database test to identify hang point"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Step 1: Starting test...")
sys.stdout.flush()

print("Step 2: Importing RIVETProDatabase...")
sys.stdout.flush()

from agent_factory.rivet_pro.database import RIVETProDatabase

print("Step 3: Import successful, creating instance...")
sys.stdout.flush()

db = RIVETProDatabase()

print("Step 4: Instance created successfully!")
sys.stdout.flush()

print("Step 5: Testing create_machine...")
sys.stdout.flush()

machine = db.create_machine(
    "test-user-id",
    "Test Lathe",
    "Test machine for backend validation"
)

print(f"Step 6: Machine created: {machine}")
sys.stdout.flush()

db.close()

print("Step 7: Test complete!")
