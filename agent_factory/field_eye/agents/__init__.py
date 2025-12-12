"""
Field Eye Agents

Agent 1: DataIngestAgent - Video → frames → database
Agent 2: DefectDetectorAgent - AI vision model runner
Agent 3: ModelTrainerAgent - AutoML training orchestrator
Agent 4: KitFulfillmentAgent - Product order management (future)
"""

# Active agents
from .data_ingest_agent import DataIngestAgent, create_data_ingest_agent

# Future agents (will be uncommented as created)
# from .defect_detector_agent import DefectDetectorAgent
# from .model_trainer_agent import ModelTrainerAgent
# from .kit_fulfillment_agent import KitFulfillmentAgent

__all__ = [
    'DataIngestAgent',
    'create_data_ingest_agent',
]
