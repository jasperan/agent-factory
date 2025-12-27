"""Test direct import of database module"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Step 1: Direct import of database module...")
sys.stdout.flush()

import agent_factory.rivet_pro.database as db_module

print("Step 2: Import successful!")
sys.stdout.flush()

print("Step 3: Creating RIVETProDatabase instance...")
sys.stdout.flush()

db = db_module.RIVETProDatabase()

print("Step 4: Instance created!")
sys.stdout.flush()

db.close()

print("Step 5: Test complete!")
