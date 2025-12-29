#!/usr/bin/env python3
"""
Proactive OEM Discovery Agent

Autonomously discovers new PDF manuals from manufacturer websites without
manual URL curation. Runs daily to expand the knowledge base proactively.

Discovery Strategies:
1. Sitemap Parsing: Extract PDF URLs from /sitemap.xml
2. HTML Link Extraction: CSS selectors per manufacturer
3. Pattern-Based Generation: Guess URLs from naming conventions

Target Manufacturers:
- Yaskawa, Danfoss, Lenze (already have seed URLs, discover MORE)
- SEW-Eurodrive, WEG, Eaton (new manufacturers)
- ABB, Schneider (expand beyond seed list)

Usage:
    poetry run python agents/research/proactive_oem_discovery_agent.py
"""

import os
import re
import logging
import hashlib
import requests
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


class ProactiveOEMDiscoveryAgent:
    """
    Discovers new PDF manuals from manufacturer websites autonomously.

    Deduplicates against source_fingerprints table to avoid re-ingesting.
    Queues new URLs to Redis for worker processing.
    """

    # Manufacturer-specific discovery configurations
    MANUFACTURERS = {
        "yaskawa": {
            "base_url": "https://www.yaskawa.com",
            "sitemap_url": "https://www.yaskawa.com/sitemap.xml",
            "download_patterns": [
                "/downloads/download/",
                "/documentation/"
            ],
            "product_families": ["A1000", "V1000", "GA700", "GP2000", "U1000"],
        },
        "danfoss": {
            "base_url": "https://assets.danfoss.com",
            "sitemap_url": None,  # No public sitemap
            "download_patterns": [
                "/documents/DOC",
                "/downloads/"
            ],
            "product_families": ["FC 300", "FC 302", "FC 360", "VLT"],
        },
        "lenze": {
            "base_url": "https://www.lenze.com",
            "sitemap_url": "https://www.lenze.com/sitemap.xml",
            "download_patterns": [
                "/fileadmin/DE/downloads/",
                "/en/downloads/"
            ],
            "product_families": ["8400", "i550", "9400", "m550"],
        },
        "sew_eurodrive": {
            "base_url": "https://www.sew-eurodrive.com",
            "sitemap_url": None,
            "download_patterns": [
                "/download/",
                "/fileadmin/"
            ],
            "product_families": ["MOVIAXIS", "MOVITRAC", "MOVIDRIVE"],
        },
        "weg": {
            "base_url": "https://www.weg.net",
            "sitemap_url": "https://www.weg.net/sitemap.xml",
            "download_patterns": [
                "/catalog/weg/",
                "/downloads/"
            ],
            "product_families": ["CFW", "MVW", "SSW"],
        },
        "eaton": {
            "base_url": "https://www.eaton.com",
            "sitemap_url": None,
            "download_patterns": [
                "/content/dam/eaton/",
                "/resources/"
            ],
            "product_families": ["PowerXL", "S811", "SVX"],
        },
    }

    def __init__(self, db_manager=None, redis_client=None):
        """
        Initialize proactive discovery agent.

        Args:
            db_manager: DatabaseManager instance (for fingerprint checks)
            redis_client: Redis client (for queueing discovered URLs)
        """
        self.db = db_manager
        self.redis = redis_client

        # User agent to avoid blocking
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; RIVETBot/1.0; +https://rivet.ai/bot)"
        }

        # Track discovered URLs
        self.discovered_urls: Set[str] = set()
        self.new_urls: List[str] = []
        self.duplicate_urls: List[str] = []

        # Stats
        self.stats = {
            "manufacturers_processed": 0,
            "sitemaps_parsed": 0,
            "pdfs_discovered": 0,
            "new_pdfs": 0,
            "duplicates": 0,
            "queued": 0,
        }

    def discover_all_manufacturers(self) -> Dict:
        """
        Run discovery across all configured manufacturers.

        Returns:
            Summary dictionary with stats
        """
        logger.info("=" * 70)
        logger.info("PROACTIVE OEM DISCOVERY - Starting")
        logger.info("=" * 70)

        for manufacturer, config in self.MANUFACTURERS.items():
            logger.info(f"\n[{manufacturer.upper()}] Starting discovery...")

            try:
                urls = self.discover_manufacturer(manufacturer, config)
                logger.info(
                    f"[{manufacturer.upper()}] Found {len(urls)} PDFs "
                    f"({len([u for u in urls if u not in self.duplicate_urls])} new)"
                )
                self.stats["manufacturers_processed"] += 1

            except Exception as e:
                logger.error(f"[{manufacturer.upper()}] Discovery failed: {e}")

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("DISCOVERY COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Manufacturers processed: {self.stats['manufacturers_processed']}")
        logger.info(f"PDFs discovered: {self.stats['pdfs_discovered']}")
        logger.info(f"New PDFs: {self.stats['new_pdfs']}")
        logger.info(f"Duplicates skipped: {self.stats['duplicates']}")
        logger.info(f"Queued for ingestion: {self.stats['queued']}")

        return {
            "discovered_urls": list(self.discovered_urls),
            "new_urls": self.new_urls,
            "stats": self.stats
        }

    def discover_manufacturer(self, manufacturer: str, config: Dict) -> List[str]:
        """
        Discover PDFs for a single manufacturer using all strategies.

        Args:
            manufacturer: Manufacturer name
            config: Manufacturer configuration

        Returns:
            List of discovered PDF URLs
        """
        urls = set()

        # Strategy 1: Sitemap parsing
        if config.get("sitemap_url"):
            sitemap_urls = self._discover_from_sitemap(
                config["sitemap_url"],
                config["download_patterns"]
            )
            urls.update(sitemap_urls)
            logger.info(f"  [Sitemap] Found {len(sitemap_urls)} PDFs")

        # Strategy 2: HTML link extraction (limited without full crawl)
        # Note: Requires more sophisticated crawling, deferred for now

        # Strategy 3: Pattern-based generation
        pattern_urls = self._generate_pattern_urls(
            manufacturer,
            config["base_url"],
            config["product_families"]
        )
        urls.update(pattern_urls)
        logger.info(f"  [Patterns] Generated {len(pattern_urls)} candidate URLs")

        # Validate URLs (check if they exist)
        validated_urls = self._validate_urls(list(urls))
        logger.info(f"  [Validation] {len(validated_urls)}/{len(urls)} URLs valid")

        # Check for duplicates
        new_urls = self._filter_duplicates(validated_urls)
        logger.info(f"  [Deduplication] {len(new_urls)} new URLs (not in DB)")

        # Queue new URLs
        if self.redis and new_urls:
            queued = self._queue_urls(new_urls)
            logger.info(f"  [Queue] {queued} URLs queued for ingestion")

        self.stats["pdfs_discovered"] += len(validated_urls)
        self.stats["new_pdfs"] += len(new_urls)
        self.stats["duplicates"] += len(validated_urls) - len(new_urls)

        return validated_urls

    def _discover_from_sitemap(
        self,
        sitemap_url: str,
        download_patterns: List[str]
    ) -> Set[str]:
        """
        Parse sitemap.xml and extract PDF URLs matching download patterns.

        Args:
            sitemap_url: URL to sitemap.xml
            download_patterns: URL patterns to match

        Returns:
            Set of PDF URLs found in sitemap
        """
        pdfs = set()

        try:
            response = requests.get(
                sitemap_url,
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            # Handle namespace
            ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Extract URLs
            for url_elem in root.findall('.//sm:url/sm:loc', ns):
                url = url_elem.text

                # Check if URL matches patterns and ends with .pdf
                if url and url.lower().endswith('.pdf'):
                    if any(pattern in url for pattern in download_patterns):
                        pdfs.add(url)

            self.stats["sitemaps_parsed"] += 1

        except Exception as e:
            logger.warning(f"Sitemap parsing failed for {sitemap_url}: {e}")

        return pdfs

    def _generate_pattern_urls(
        self,
        manufacturer: str,
        base_url: str,
        product_families: List[str]
    ) -> Set[str]:
        """
        Generate candidate URLs based on common naming patterns.

        Args:
            manufacturer: Manufacturer name
            base_url: Base URL
            product_families: List of product family names

        Returns:
            Set of candidate URLs to validate
        """
        candidates = set()

        # Common manual naming patterns
        doc_types = [
            "manual", "user_manual", "technical_manual",
            "operating_instructions", "programming_guide",
            "reference_guide", "quick_start", "installation"
        ]

        # Common file naming conventions
        for product in product_families:
            product_clean = product.replace(" ", "_").replace("-", "_")

            for doc_type in doc_types:
                # Pattern 1: /downloads/{product}_{doc_type}.pdf
                candidates.add(
                    f"{base_url}/downloads/{product_clean}_{doc_type}.pdf"
                )

                # Pattern 2: /documentation/{product}/{doc_type}.pdf
                candidates.add(
                    f"{base_url}/documentation/{product_clean}/{doc_type}.pdf"
                )

                # Pattern 3: /manuals/{product}-{doc_type}.pdf
                candidates.add(
                    f"{base_url}/manuals/{product.replace(' ', '-')}-{doc_type}.pdf"
                )

        return candidates

    def _validate_urls(self, urls: List[str]) -> List[str]:
        """
        Validate that URLs exist (HTTP HEAD request).

        Args:
            urls: List of candidate URLs

        Returns:
            List of valid URLs (200 OK)
        """
        valid = []

        for url in urls:
            try:
                response = requests.head(
                    url,
                    headers=self.headers,
                    timeout=10,
                    allow_redirects=True
                )

                # Check if PDF exists
                if response.status_code == 200:
                    content_type = response.headers.get('Content-Type', '')
                    if 'pdf' in content_type.lower() or url.lower().endswith('.pdf'):
                        valid.append(url)
                        self.discovered_urls.add(url)

            except Exception as e:
                logger.debug(f"URL validation failed for {url}: {e}")
                continue

        return valid

    def _filter_duplicates(self, urls: List[str]) -> List[str]:
        """
        Filter out URLs already in source_fingerprints table.

        Args:
            urls: List of discovered URLs

        Returns:
            List of new URLs (not in database)
        """
        if not self.db:
            # No database, assume all are new
            self.new_urls.extend(urls)
            return urls

        new = []

        for url in urls:
            fingerprint = self._compute_fingerprint(url)

            if not self._fingerprint_exists(fingerprint):
                new.append(url)
                self.new_urls.append(url)
            else:
                self.duplicate_urls.append(url)

        return new

    def _compute_fingerprint(self, url: str) -> str:
        """Compute SHA-256 fingerprint for URL."""
        return hashlib.sha256(url.encode('utf-8')).hexdigest()

    def _fingerprint_exists(self, fingerprint: str) -> bool:
        """
        Check if fingerprint exists in source_fingerprints table.

        Args:
            fingerprint: SHA-256 hash of URL

        Returns:
            True if exists, False otherwise
        """
        try:
            conn = self.db.get_connection("supabase")
            if not conn:
                return False

            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM source_fingerprints WHERE url_hash = %s",
                    (fingerprint,)
                )
                count = cursor.fetchone()[0]
                return count > 0

        except Exception as e:
            logger.error(f"Error checking fingerprint: {e}")
            return False

    def _queue_urls(self, urls: List[str]) -> int:
        """
        Queue URLs to Redis for worker processing.

        Args:
            urls: List of URLs to queue

        Returns:
            Number of URLs successfully queued
        """
        if not self.redis:
            logger.warning("No Redis client, skipping queue")
            return 0

        queued = 0

        for url in urls:
            try:
                self.redis.rpush("kb_ingest_jobs", url)
                queued += 1
            except Exception as e:
                logger.error(f"Failed to queue {url}: {e}")

        self.stats["queued"] = queued
        return queued


def main():
    """
    Demo: Run proactive discovery for all manufacturers.

    Usage:
        poetry run python agents/research/proactive_oem_discovery_agent.py
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )

    # Initialize agent (no DB/Redis for demo)
    agent = ProactiveOEMDiscoveryAgent()

    # Run discovery
    result = agent.discover_all_manufacturers()

    # Save results
    output_file = Path("data/discovered_urls.txt")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        f.write(f"# Proactive OEM Discovery Results\n")
        f.write(f"# Date: {datetime.utcnow().isoformat()}\n")
        f.write(f"# Total discovered: {len(result['discovered_urls'])}\n\n")

        for url in sorted(result['discovered_urls']):
            f.write(f"{url}\n")

    print(f"\nResults saved to: {output_file}")
    print(f"Total URLs discovered: {len(result['discovered_urls'])}")


if __name__ == "__main__":
    main()
