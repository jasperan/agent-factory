"""
Performance benchmarks for OCR Pipeline and KB Search

Measures:
- OCR latency (GPT-4o vs Gemini)
- KB search precision with/without model filtering
- End-to-end photo processing time
"""

import asyncio
import time
import os
from pathlib import Path
from typing import List, Dict, Any

from agent_factory.integrations.telegram.ocr import OCRPipeline, OCRResult
from agent_factory.rivet_pro.rag.retriever import search_docs
from agent_factory.rivet_pro.models import RivetIntent, VendorType, EquipmentType, KBCoverage as RivetKBCoverage


class PerformanceBenchmark:
    """OCR and KB search performance benchmarking"""

    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    async def benchmark_ocr_latency(self, pipeline: OCRPipeline, image_bytes: bytes, iterations: int = 3):
        """Benchmark OCR latency over multiple iterations"""
        print(f"\n=== Benchmarking OCR Latency ({iterations} iterations) ===")

        latencies = []

        for i in range(iterations):
            print(f"\nIteration {i+1}/{iterations}...")

            start = time.time()
            result = await pipeline.analyze_photo(image_bytes, user_id="benchmark")
            latency = (time.time() - start) * 1000  # Convert to ms

            latencies.append(latency)

            print(f"  Provider: {result.provider}")
            print(f"  Confidence: {result.confidence:.2%}")
            print(f"  Latency: {latency:.0f}ms")

        # Calculate stats
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"\nOCR Latency Stats:")
        print(f"  Average: {avg_latency:.0f}ms")
        print(f"  Min: {min_latency:.0f}ms")
        print(f"  Max: {max_latency:.0f}ms")

        self.results.append({
            "test": "ocr_latency",
            "avg_ms": avg_latency,
            "min_ms": min_latency,
            "max_ms": max_latency,
        })

        return avg_latency

    def benchmark_kb_search_precision(self, manufacturer: str, model_number: str):
        """Benchmark KB search precision with/without model filtering"""
        print(f"\n=== Benchmarking KB Search Precision ===")

        # Map manufacturer to VendorType
        vendor_map = {
            "siemens": VendorType.SIEMENS,
            "allen_bradley": VendorType.ALLEN_BRADLEY,
            "rockwell": VendorType.ALLEN_BRADLEY,
            "schneider": VendorType.SCHNEIDER_ELECTRIC,
            "mitsubishi": VendorType.MITSUBISHI,
        }

        manufacturer_lower = manufacturer.lower().replace(" ", "_")
        vendor = vendor_map.get(manufacturer_lower, VendorType.SIEMENS)

        # Create intent
        intent = RivetIntent(
            vendor=vendor,
            equipment_type=EquipmentType.VFD,
            symptom=f"{model_number} troubleshooting",
            raw_summary=f"{manufacturer} {model_number} troubleshooting",
            context_source="text_only",
            confidence=0.9,
            kb_coverage=RivetKBCoverage.NONE
        )

        # Search without model filter
        print(f"\n1. Searching without model filter...")
        start = time.time()
        docs_without = search_docs(intent)
        latency_without = (time.time() - start) * 1000

        print(f"   Results: {len(docs_without)} documents")
        print(f"   Latency: {latency_without:.0f}ms")

        if docs_without:
            avg_sim_without = sum(d.similarity for d in docs_without) / len(docs_without)
            print(f"   Avg Similarity: {avg_sim_without:.3f}")
        else:
            avg_sim_without = 0.0

        # Search with model filter
        print(f"\n2. Searching with model filter ({model_number})...")
        start = time.time()
        docs_with = search_docs(intent, model_number=model_number)
        latency_with = (time.time() - start) * 1000

        print(f"   Results: {len(docs_with)} documents")
        print(f"   Latency: {latency_with:.0f}ms")

        if docs_with:
            avg_sim_with = sum(d.similarity for d in docs_with) / len(docs_with)
            print(f"   Avg Similarity: {avg_sim_with:.3f}")

            # Show top result
            print(f"\n   Top Result:")
            print(f"     Title: {docs_with[0].title}")
            print(f"     Similarity: {docs_with[0].similarity:.3f}")
        else:
            avg_sim_with = 0.0

        # Calculate precision improvement
        if avg_sim_without > 0:
            precision_improvement = ((avg_sim_with - avg_sim_without) / avg_sim_without) * 100
        else:
            precision_improvement = 0.0

        print(f"\nPrecision Analysis:")
        print(f"  Results reduction: {len(docs_without)} → {len(docs_with)} ({len(docs_with)/max(len(docs_without), 1)*100:.0f}%)")
        print(f"  Similarity improvement: {precision_improvement:+.1f}%")

        self.results.append({
            "test": "kb_search_precision",
            "results_without_filter": len(docs_without),
            "results_with_filter": len(docs_with),
            "avg_similarity_without": avg_sim_without,
            "avg_similarity_with": avg_sim_with,
            "precision_improvement_pct": precision_improvement,
            "latency_without_ms": latency_without,
            "latency_with_ms": latency_with,
        })

        return precision_improvement

    async def benchmark_e2e_flow(self, pipeline: OCRPipeline, image_bytes: bytes):
        """Benchmark end-to-end photo → OCR → KB search flow"""
        print(f"\n=== Benchmarking E2E Flow (Photo → OCR → KB) ===")

        start_total = time.time()

        # Step 1: OCR
        print("\n1. OCR extraction...")
        start_ocr = time.time()
        ocr_result = await pipeline.analyze_photo(image_bytes, user_id="benchmark")
        ocr_time = (time.time() - start_ocr) * 1000

        print(f"   Provider: {ocr_result.provider}")
        print(f"   Confidence: {ocr_result.confidence:.2%}")
        print(f"   Time: {ocr_time:.0f}ms")

        # Step 2: KB search (if manufacturer detected)
        kb_time = 0
        kb_results = 0

        if ocr_result.manufacturer:
            print(f"\n2. KB search...")

            vendor_map = {
                "siemens": VendorType.SIEMENS,
                "allen_bradley": VendorType.ALLEN_BRADLEY,
                "rockwell": VendorType.ALLEN_BRADLEY,
                "schneider": VendorType.SCHNEIDER_ELECTRIC,
                "mitsubishi": VendorType.MITSUBISHI,
            }

            manufacturer_lower = ocr_result.manufacturer.lower().replace(" ", "_")
            vendor = vendor_map.get(manufacturer_lower, VendorType.SIEMENS)

            intent = RivetIntent(
                vendor=vendor,
                equipment_type=EquipmentType.VFD,
                symptom=f"{ocr_result.model_number or 'VFD'} troubleshooting",
                raw_summary=f"{ocr_result.manufacturer} {ocr_result.model_number or 'VFD'} troubleshooting",
                context_source="text_only",
                confidence=0.9,
                kb_coverage=RivetKBCoverage.NONE
            )

            start_kb = time.time()
            docs = search_docs(intent, model_number=ocr_result.model_number)
            kb_time = (time.time() - start_kb) * 1000
            kb_results = len(docs)

            print(f"   Results: {kb_results} documents")
            print(f"   Time: {kb_time:.0f}ms")
        else:
            print(f"\n2. KB search skipped (no manufacturer detected)")

        # Total time
        total_time = (time.time() - start_total) * 1000

        print(f"\nE2E Timing Breakdown:")
        print(f"  OCR: {ocr_time:.0f}ms ({ocr_time/total_time*100:.0f}%)")
        print(f"  KB Search: {kb_time:.0f}ms ({kb_time/total_time*100:.0f}%)")
        print(f"  Total: {total_time:.0f}ms")

        self.results.append({
            "test": "e2e_flow",
            "ocr_ms": ocr_time,
            "kb_search_ms": kb_time,
            "total_ms": total_time,
            "kb_results": kb_results,
        })

        return total_time

    def print_summary(self):
        """Print benchmark summary"""
        print("\n" + "=" * 60)
        print("PERFORMANCE BENCHMARK SUMMARY")
        print("=" * 60)

        for result in self.results:
            print(f"\n{result['test'].upper()}:")
            for key, value in result.items():
                if key != "test":
                    if isinstance(value, float):
                        print(f"  {key}: {value:.2f}")
                    else:
                        print(f"  {key}: {value}")


async def run_benchmarks():
    """Run all performance benchmarks"""
    print("=" * 60)
    print("OCR PERFORMANCE BENCHMARKS")
    print("=" * 60)

    benchmark = PerformanceBenchmark()

    # Initialize pipeline
    pipeline = OCRPipeline()

    # Check for test image
    test_image_path = Path("tests/fixtures/sample_nameplate.jpg")

    if not test_image_path.exists():
        print(f"\nERROR: Test image not found at {test_image_path}")
        print("To run benchmarks, add a sample industrial nameplate image")
        print("Expected location: tests/fixtures/sample_nameplate.jpg")
        return

    # Read image
    with open(test_image_path, "rb") as f:
        image_bytes = f.read()

    # Run benchmarks
    await benchmark.benchmark_ocr_latency(pipeline, image_bytes, iterations=3)

    # Get OCR result for subsequent tests
    ocr_result = await pipeline.analyze_photo(image_bytes, user_id="benchmark")

    if ocr_result.manufacturer and ocr_result.model_number:
        benchmark.benchmark_kb_search_precision(
            ocr_result.manufacturer,
            ocr_result.model_number
        )

    await benchmark.benchmark_e2e_flow(pipeline, image_bytes)

    # Print summary
    benchmark.print_summary()

    print("\n" + "=" * 60)
    print("Benchmarks completed!")
    print("=" * 60)


if __name__ == "__main__":
    # Check prerequisites
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY not set in environment")
        print("Run: export OPENAI_API_KEY=your_key")
        exit(1)

    # Run benchmarks
    asyncio.run(run_benchmarks())
