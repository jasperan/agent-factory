"""
Field Eye: Industrial Vision & Robotics Training Platform

Agent Factory's 3rd vertical - creates proprietary datasets from real-world
industrial inspections that trains robots and generates licensing revenue.

Components:
- agents/: Data ingest, defect detection, model training
- utils/: Video processing, pause detection, atom building
- config/: Database schemas, hardware specs
- models/: Trained vision models (ONNX)

Timeline:
- Month 1-2: Foundation (hardware + data pipeline)
- Month 3-6: AI training + product kits
- Month 7-12: Advanced sensors (thermal, vibration)
- Year 2+: Robot licensing ($1M+ potential)

Revenue Streams:
1. Product kits: $99-$149/kit (40-60% margin)
2. SaaS subscriptions: $20-$50/month
3. Robot licensing: $100K-$500K upfront + royalties
"""

__version__ = "0.1.0"
__author__ = "Agent Factory"

from . import agents
from . import utils
