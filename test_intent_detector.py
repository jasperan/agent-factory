"""Test importing IntentDetector"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Step 1: Importing IntentDetector...")
sys.stdout.flush()

from agent_factory.rivet_pro.intent_detector import IntentDetector

print("Step 2: IntentDetector imported successfully!")
sys.stdout.flush()
