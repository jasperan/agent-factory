"""Pydantic schemas for maintenance case validation."""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class Equipment(BaseModel):
    """Equipment information for a maintenance case."""
    type: str = Field(..., description="Equipment type: PLC, VFD, motor, sensor, etc.")
    manufacturer: str = Field(..., description="Equipment manufacturer")
    model: str = Field(..., description="Model number or name")
    location: Optional[str] = Field(None, description="Physical location")


class CaseInput(BaseModel):
    """Raw input from technician."""
    raw_text: str = Field(..., description="Original technician input (messy/shorthand OK)")
    photo_url: Optional[str] = Field(None, description="Telegram photo ID if provided")


class Diagnosis(BaseModel):
    """Diagnostic findings."""
    root_cause: str = Field(..., description="Root cause of the issue")
    fault_codes: List[str] = Field(default_factory=list, description="Error/fault codes")
    symptoms: List[str] = Field(default_factory=list, description="Observable symptoms")


class Resolution(BaseModel):
    """How the issue was resolved."""
    steps: List[str] = Field(..., description="Steps taken to resolve")
    parts_used: List[str] = Field(default_factory=list, description="Parts replaced/used")
    time_to_fix: str = Field(..., description="Time to resolve (e.g., '45 minutes')")


class MaintenanceCase(BaseModel):
    """Complete maintenance case for few-shot learning."""
    case_id: str = Field(..., description="Unique case identifier (e.g., RC-001)")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    equipment: Equipment
    input: CaseInput
    diagnosis: Diagnosis
    resolution: Resolution
    keywords: List[str] = Field(default_factory=list, description="Searchable keywords")
    category: str = Field(..., description="Category: electrical, mechanical, instrumentation, safety")

    def to_embedding_text(self) -> str:
        """Convert case to text suitable for embedding."""
        return f"""
Equipment: {self.equipment.type} - {self.equipment.manufacturer} {self.equipment.model}
Location: {self.equipment.location or 'Not specified'}
Problem: {self.input.raw_text}
Symptoms: {', '.join(self.diagnosis.symptoms)}
Fault Codes: {', '.join(self.diagnosis.fault_codes)}
Root Cause: {self.diagnosis.root_cause}
Keywords: {', '.join(self.keywords)}
Category: {self.category}
""".strip()

    def to_few_shot_example(self) -> str:
        """Format case as a few-shot example for prompt injection."""
        steps = '\n'.join(f"  {i+1}. {step}" for i, step in enumerate(self.resolution.steps))
        return f"""
---
SIMILAR CASE: {self.case_id}
Technician reported: "{self.input.raw_text}"
Equipment: {self.equipment.type} - {self.equipment.manufacturer} {self.equipment.model}
Root cause found: {self.diagnosis.root_cause}
Resolution steps:
{steps}
Time to fix: {self.resolution.time_to_fix}
---
""".strip()
