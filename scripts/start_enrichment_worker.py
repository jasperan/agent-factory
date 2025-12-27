"""Start the KB enrichment worker."""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.workers.enrichment_worker import run_enrichment_worker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enrichment_worker.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    print("Starting KB Enrichment Worker...")
    print("Press Ctrl+C to stop")

    try:
        asyncio.run(run_enrichment_worker())
    except KeyboardInterrupt:
        print("\nWorker stopped by user")
    except Exception as e:
        print(f"Worker crashed: {e}")
        sys.exit(1)
