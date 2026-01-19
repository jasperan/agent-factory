"""Test importing ContextExtractor"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Step 1: Importing ContextExtractor...")
sys.stdout.flush()

from agent_factory.rivet_pro.context_extractor import ContextExtractor

print("Step 2: ContextExtractor imported successfully!")
sys.stdout.flush()
