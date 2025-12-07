"""
========================================================================
WIZARD STATE - Wizard State Management and Persistence
========================================================================

PURPOSE:
    Manages the state of the interactive agent creation wizard,
    including saving/loading drafts and tracking progress.

WHAT THIS DOES:
    - Tracks current step and collected data
    - Saves wizard state to JSON files
    - Loads wizard state from JSON files
    - Auto-save functionality for crash recovery
    - Step completion tracking

WHY WE NEED THIS:
    Allows users to save their progress and resume later.
    Prevents data loss if wizard is interrupted.
    Enables "go back" functionality by tracking state.

USAGE:
    state = WizardState()
    state.set_data("name", "MyAgent")
    state.save_draft("drafts/my-agent.json")

    # Later...
    state = WizardState.load_draft("drafts/my-agent.json")
    print(state.current_step)  # 3

PLC ANALOGY:
    Like a PLC's data retention - preserves state through power cycles.
========================================================================
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
import json


class WizardState:
    """
    PURPOSE: Manage wizard state and persistence

    WHAT THIS DOES:
        - Stores wizard data (name, purpose, tools, etc.)
        - Tracks current step and completed steps
        - Saves/loads from JSON files
        - Provides step navigation

    STATE STRUCTURE:
        - current_step: int (1-7)
        - completed_steps: List[int] (which steps are done)
        - spec_data: Dict[str, Any] (collected agent spec)
        - session_id: str (unique session identifier)
        - created_at: str (ISO timestamp)
        - updated_at: str (ISO timestamp)
    """

    # Step names for reference
    STEPS = [
        "basics",        # 1: Name, version, owner, purpose
        "scope_in",      # 2: What agent CAN do
        "scope_out",     # 3: What agent should NEVER do
        "invariants",    # 4: Rules that must never be violated
        "tools",         # 5: Tool selection
        "behavior",      # 6: Behavior examples
        "criteria",      # 7: Success criteria
        "review"         # 8: Review and confirm (special state)
    ]

    def __init__(self):
        """Initialize new wizard state"""
        self.current_step: int = 1
        self.completed_steps: List[int] = []
        self.spec_data: Dict[str, Any] = {}
        self.session_id: str = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.created_at: str = datetime.now().isoformat()
        self.updated_at: str = datetime.now().isoformat()

    def set_current_step(self, step: int):
        """
        PURPOSE: Set current step (1-8)

        VALIDATION:
            Must be between 1 and 8 (step 8 = review phase)

        SIDE EFFECTS:
            Updates updated_at timestamp
        """
        if not 1 <= step <= 8:
            raise ValueError(f"Step must be between 1 and 8, got {step}")
        self.current_step = step
        self.updated_at = datetime.now().isoformat()

    def mark_step_complete(self, step: int):
        """
        PURPOSE: Mark a step as completed

        WHAT THIS DOES:
            Adds step to completed_steps list if not already there

        SIDE EFFECTS:
            Updates updated_at timestamp
        """
        if step not in self.completed_steps:
            self.completed_steps.append(step)
            self.updated_at = datetime.now().isoformat()

    def is_step_complete(self, step: int) -> bool:
        """Check if a step has been completed"""
        return step in self.completed_steps

    def set_data(self, key: str, value: Any):
        """
        PURPOSE: Set a piece of spec data

        INPUTS:
            key: str - Data key (e.g., "name", "purpose")
            value: Any - Value to store

        SIDE EFFECTS:
            Updates spec_data and updated_at timestamp
        """
        self.spec_data[key] = value
        self.updated_at = datetime.now().isoformat()

    def get_data(self, key: str, default: Any = None) -> Any:
        """Get a piece of spec data with optional default"""
        return self.spec_data.get(key, default)

    def has_data(self, key: str) -> bool:
        """Check if spec data contains key"""
        return key in self.spec_data

    def get_progress_percentage(self) -> int:
        """
        PURPOSE: Calculate wizard completion percentage

        OUTPUTS:
            int: Percentage (0-100)

        CALCULATION:
            (completed_steps / total_steps) * 100
            Note: Total is 7 (not 8), since step 8 is review, not data collection
        """
        return int((len(self.completed_steps) / 7) * 100)

    def get_step_name(self, step: int) -> str:
        """Get step name by number (1-indexed)"""
        if 1 <= step <= len(self.STEPS):
            return self.STEPS[step - 1]
        return "unknown"

    def can_navigate_to(self, step: int) -> bool:
        """
        PURPOSE: Check if user can navigate to a step

        RULE:
            Can navigate to any completed step or current step + 1

        OUTPUTS:
            bool: True if navigation is allowed
        """
        # Can always go to completed steps
        if step in self.completed_steps:
            return True

        # Can go to current step
        if step == self.current_step:
            return True

        # Can go forward one step if current step is complete
        if step == self.current_step + 1 and self.current_step in self.completed_steps:
            return True

        return False

    def to_dict(self) -> Dict[str, Any]:
        """
        PURPOSE: Convert state to dictionary for JSON serialization

        OUTPUTS:
            Dict containing all state data
        """
        return {
            "current_step": self.current_step,
            "completed_steps": self.completed_steps,
            "spec_data": self.spec_data,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WizardState':
        """
        PURPOSE: Create WizardState from dictionary

        INPUTS:
            data: Dict loaded from JSON

        OUTPUTS:
            WizardState: New instance with loaded data
        """
        state = cls()
        state.current_step = data.get("current_step", 1)
        state.completed_steps = data.get("completed_steps", [])
        state.spec_data = data.get("spec_data", {})
        state.session_id = data.get("session_id", state.session_id)
        state.created_at = data.get("created_at", state.created_at)
        state.updated_at = data.get("updated_at", state.updated_at)
        return state

    def save_draft(self, filepath: Optional[str] = None) -> str:
        """
        PURPOSE: Save wizard state to JSON file

        INPUTS:
            filepath (str, optional): Path to save file
                If None, auto-generates filename in drafts/

        OUTPUTS:
            str: Path where file was saved

        SIDE EFFECTS:
            - Creates drafts/ directory if needed
            - Writes JSON file
        """
        if filepath is None:
            # Auto-generate filename
            drafts_dir = Path("drafts")
            drafts_dir.mkdir(exist_ok=True)

            # Use agent name if available, otherwise session ID
            agent_name = self.spec_data.get("name", "wizard")
            safe_name = agent_name.lower().replace(" ", "-").replace("/", "-")
            filepath = drafts_dir / f"{safe_name}-{self.session_id}.json"

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return str(filepath)

    @classmethod
    def load_draft(cls, filepath: str) -> 'WizardState':
        """
        PURPOSE: Load wizard state from JSON file

        INPUTS:
            filepath: str - Path to JSON file

        OUTPUTS:
            WizardState: Loaded state

        ERRORS:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        filepath = Path(filepath)

        if not filepath.exists():
            raise FileNotFoundError(f"Draft file not found: {filepath}")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls.from_dict(data)

    @staticmethod
    def list_drafts() -> List[Dict[str, Any]]:
        """
        PURPOSE: List all available draft files

        OUTPUTS:
            List of dicts with draft metadata:
                - path: str
                - agent_name: str
                - created_at: str
                - updated_at: str
                - progress: int (percentage)
        """
        drafts_dir = Path("drafts")

        if not drafts_dir.exists():
            return []

        drafts = []
        for draft_file in drafts_dir.glob("*.json"):
            try:
                state = WizardState.load_draft(str(draft_file))
                drafts.append({
                    "path": str(draft_file),
                    "agent_name": state.spec_data.get("name", "Unnamed"),
                    "created_at": state.created_at,
                    "updated_at": state.updated_at,
                    "progress": state.get_progress_percentage(),
                    "current_step": state.current_step
                })
            except Exception:
                # Skip invalid files
                continue

        # Sort by updated_at (most recent first)
        drafts.sort(key=lambda x: x["updated_at"], reverse=True)

        return drafts

    def get_summary(self) -> str:
        """
        PURPOSE: Get human-readable summary of wizard state

        OUTPUTS:
            str: Multi-line summary
        """
        lines = []
        lines.append(f"Session: {self.session_id}")
        lines.append(f"Progress: {self.get_progress_percentage()}% ({len(self.completed_steps)}/7 steps)")
        lines.append(f"Current Step: {self.current_step} ({self.get_step_name(self.current_step)})")
        lines.append(f"Last Updated: {self.updated_at}")

        if self.spec_data:
            lines.append("\nCollected Data:")
            if "name" in self.spec_data:
                lines.append(f"  Name: {self.spec_data['name']}")
            if "version" in self.spec_data:
                lines.append(f"  Version: {self.spec_data['version']}")
            if "owner" in self.spec_data:
                lines.append(f"  Owner: {self.spec_data['owner']}")
            if "tools" in self.spec_data:
                lines.append(f"  Tools: {len(self.spec_data['tools'])} selected")
            if "invariants" in self.spec_data:
                lines.append(f"  Invariants: {len(self.spec_data['invariants'])} rules")

        return "\n".join(lines)
