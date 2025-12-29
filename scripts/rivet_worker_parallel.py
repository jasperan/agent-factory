#!/usr/bin/env python3
"""
24/7 Background Worker - KB Ingestion Pipeline (PARALLEL VERSION)

Polls Redis queue 'kb_ingest_jobs' and processes URLs in parallel using ThreadPoolExecutor.
Configurable concurrency via WORKER_CONCURRENCY environment variable (default: 3).

Benefits over single-threaded worker:
- 3x faster throughput (3 URLs processed simultaneously)
- Better resource utilization (CPU + network I/O parallelized)
- Resilient to slow URLs (one slow URL doesn't block others)

Usage:
    poetry run python scripts/rivet_worker_parallel.py

Systemd service: deploy/vps/rivet-worker-parallel.service
"""

import os
import sys
import time
import signal
import logging
import redis
from pathlib import Path
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
import queue
import threading

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.workflows.ingestion_chain import ingest_source
from agent_factory.observability.ingestion_monitor import IngestionMonitor
from agent_factory.observability.telegram_notifier import TelegramNotifier
from agent_factory.core.database_manager import DatabaseManager

# Logging setup
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "rivet_worker_parallel.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Global state
shutdown_requested = False
processed_count = 0
count_lock = Lock()


def signal_handler(signum, frame):
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    shutdown_requested = True


# Register signal handlers
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)


def process_url(url: str, worker_id: int) -> dict:
    """
    Process a single URL through the ingestion pipeline.

    Args:
        url: Source URL to ingest
        worker_id: Worker thread ID (for logging)

    Returns:
        Result dictionary with success status and metadata
    """
    global processed_count

    with count_lock:
        processed_count += 1
        current_count = processed_count

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"[Worker {worker_id}] [{current_count}] Processing: {url}")
    logger.info("=" * 80)

    start_time = time.time()

    try:
        ingest_result = ingest_source(url)
        duration = time.time() - start_time

        if ingest_result.get("success"):
            atoms_created = ingest_result.get('atoms_created', 0)
            logger.info(
                f"[Worker {worker_id}] [SUCCESS] {url}\n"
                f"  Atoms created: {atoms_created}\n"
                f"  Duration: {duration:.1f}s"
            )
            return {
                "success": True,
                "url": url,
                "atoms_created": atoms_created,
                "duration": duration
            }
        else:
            errors = ingest_result.get('errors', [])
            logger.error(
                f"[Worker {worker_id}] [FAILED] {url}\n"
                f"  Errors: {errors}\n"
                f"  Duration: {duration:.1f}s"
            )
            return {
                "success": False,
                "url": url,
                "errors": errors,
                "duration": duration
            }

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"[Worker {worker_id}] [EXCEPTION] Ingestion failed: {e}",
            exc_info=True
        )
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "duration": duration
        }


def redis_fetcher_thread(redis_client, work_queue, concurrency):
    """
    Background thread that fetches URLs from Redis and adds to work queue.

    Args:
        redis_client: Redis connection
        work_queue: Thread-safe queue to add URLs to
        concurrency: Max queue size (limits memory usage)
    """
    logger.info("[Fetcher] Starting Redis fetcher thread")
    idle_count = 0
    poll_interval = 5  # seconds

    while not shutdown_requested:
        try:
            # Don't fetch if queue is full (backpressure)
            if work_queue.qsize() >= concurrency * 2:
                time.sleep(1)
                continue

            # Pop URL from Redis queue (blocking pop with timeout)
            result = redis_client.blpop("kb_ingest_jobs", timeout=poll_interval)

            if result:
                queue_name, url = result
                idle_count = 0

                # Add to work queue (blocks if queue full)
                work_queue.put(url, timeout=10)
                logger.debug(f"[Fetcher] Added URL to work queue: {url}")

            else:
                # Queue empty
                idle_count += 1
                if idle_count % 20 == 0:  # Log every ~100 seconds when idle
                    logger.info(
                        f"[Fetcher] Redis queue empty (checked {idle_count} times, "
                        f"{work_queue.qsize()} URLs in work queue)"
                    )

        except redis.ConnectionError as e:
            logger.error(f"[Fetcher] Redis connection error: {e}")
            logger.info("[Fetcher] Waiting 60s before retry...")
            time.sleep(60)

        except queue.Full:
            logger.warning("[Fetcher] Work queue full, waiting...")
            time.sleep(5)

        except Exception as e:
            logger.error(f"[Fetcher] Error: {e}", exc_info=True)
            time.sleep(10)

    logger.info("[Fetcher] Fetcher thread shutting down")


def main():
    """Main worker loop with parallel processing."""
    logger.info("=" * 80)
    logger.info("RIVET WORKER (PARALLEL) - 24/7 KB INGESTION DAEMON")
    logger.info("=" * 80)

    # Load environment
    load_dotenv()

    # Get concurrency setting
    concurrency = int(os.getenv("WORKER_CONCURRENCY", "3"))
    logger.info(f"Worker concurrency: {concurrency} threads")

    # Connect to Redis
    redis_host = os.getenv("VPS_KB_HOST", "localhost")
    redis_port = int(os.getenv("VPS_KB_PORT", "6379"))

    logger.info(f"Connecting to Redis: {redis_host}:{redis_port}")

    try:
        redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=60
        )
        redis_client.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return 1

    # Initialize observability
    try:
        db = DatabaseManager()

        notification_mode = os.getenv("KB_NOTIFICATION_MODE", "VERBOSE")

        notifier = TelegramNotifier(
            bot_token=os.getenv("ORCHESTRATOR_BOT_TOKEN"),
            chat_id=int(os.getenv("TELEGRAM_ADMIN_CHAT_ID", "8445149012")),
            mode=notification_mode,
            quiet_hours_start=int(os.getenv("NOTIFICATION_QUIET_START", "23")),
            quiet_hours_end=int(os.getenv("NOTIFICATION_QUIET_END", "7")),
            db_manager=db
        )

        monitor = IngestionMonitor(db, telegram_notifier=notifier)

        logger.info(f"Observability initialized (mode={notification_mode})")
    except Exception as e:
        logger.error(f"Observability initialization failed: {e}")
        logger.warning("Continuing without monitoring...")
        monitor = None

    # Create work queue for URLs
    work_queue = queue.Queue(maxsize=concurrency * 2)

    # Start Redis fetcher thread
    fetcher = threading.Thread(
        target=redis_fetcher_thread,
        args=(redis_client, work_queue, concurrency),
        name="RedisFetcher",
        daemon=True
    )
    fetcher.start()

    # Create thread pool for parallel processing
    logger.info(f"Starting {concurrency} worker threads")
    executor = ThreadPoolExecutor(
        max_workers=concurrency,
        thread_name_prefix="Worker"
    )

    # Submit initial batch of URLs
    futures = {}
    worker_id_counter = 0

    try:
        while not shutdown_requested:
            # Maintain concurrency by submitting new work as threads complete
            while len(futures) < concurrency and not work_queue.empty():
                try:
                    url = work_queue.get(timeout=1)
                    worker_id_counter += 1
                    future = executor.submit(process_url, url, worker_id_counter)
                    futures[future] = url
                except queue.Empty:
                    break

            # Check for completed futures
            if futures:
                done, pending = {}, set(futures.keys())

                # Use as_completed with timeout to check periodically
                try:
                    for future in as_completed(futures.keys(), timeout=1):
                        result = future.result()
                        url = futures.pop(future)
                        # Result already logged in process_url
                except TimeoutError:
                    # No futures completed in 1 second, continue loop
                    pass

            # If no work, sleep briefly
            if not futures and work_queue.empty():
                time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received KeyboardInterrupt, shutting down...")
        shutdown_requested = True

    # Graceful shutdown
    logger.info("")
    logger.info("=" * 80)
    logger.info("SHUTTING DOWN PARALLEL WORKER")
    logger.info("=" * 80)

    # Wait for in-flight work to complete (with timeout)
    logger.info(f"Waiting for {len(futures)} in-flight jobs to complete...")
    executor.shutdown(wait=True, cancel_futures=False)

    # Wait for fetcher thread
    logger.info("Waiting for Redis fetcher thread to stop...")
    fetcher.join(timeout=10)

    logger.info("")
    logger.info("=" * 80)
    logger.info("WORKER SHUTDOWN COMPLETE")
    logger.info(f"Total URLs processed: {processed_count}")
    logger.info("=" * 80)

    # Shutdown monitor
    if monitor:
        import asyncio
        try:
            asyncio.run(monitor.shutdown())
        except Exception as e:
            logger.error(f"Monitor shutdown failed: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
