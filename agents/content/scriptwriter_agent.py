#!/usr/bin/env python3
"""
ScriptwriterAgent - Write video scripts from knowledge atoms

Responsibilities:
- Transform atom content into narration\n- Add personality markers ([enthusiastic], [cautionary])\n- Include visual cues (show diagram, highlight code)\n- Cite atom sources in script\n- Generate recap quiz question

Schedule: On-demand (triggered by orchestrator)
Dependencies: Supabase, agent_factory.memory
Output: Updates Supabase tables, logs to agent_status

Based on: docs/AGENT_ORGANIZATION.md Section 4
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


class ScriptwriterAgent:
    """
    Write video scripts from knowledge atoms

    Write video scripts from knowledge atoms\n\nThis agent is part of the Content Team.
    """

    def __init__(self):
        """Initialize agent with Supabase connection"""
        self.storage = SupabaseMemoryStorage()
        self.agent_name = "scriptwriter_agent"
        self._register_status()

    def _register_status(self):
        """Register agent in agent_status table"""
        try:
            self.storage.client.table("agent_status").upsert({
                "agent_name": self.agent_name,
                "status": "idle",
                "last_heartbeat": datetime.now().isoformat(),
                "tasks_completed_today": 0,
                "tasks_failed_today": 0
            }).execute()
            logger.info(f"{self.agent_name} registered")
        except Exception as e:
            logger.error(f"Failed to register {self.agent_name}: {e}")

    def _send_heartbeat(self):
        """Update heartbeat in agent_status table"""
        try:
            self.storage.client.table("agent_status") \
                .update({"last_heartbeat": datetime.now().isoformat()}) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")

    def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method called by orchestrator.

        Args:
            payload: Job payload from agent_jobs table

        Returns:
            Dict with status, result/error

        Example:
            >>> agent = ScriptwriterAgent()
            >>> result = agent.run({"task": "process"})
            >>> assert result["status"] == "success"
        """
        try:
            self._send_heartbeat()
            self._update_status("running")

            # TODO: Implement agent logic
            result = self._process(payload)

            self._update_status("completed")
            return {"status": "success", "result": result}

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def _process(self, payload: Dict[str, Any]) -> Any:
        """Agent-specific processing logic"""
        # TODO: Implement in subclass or concrete agent
        raise NotImplementedError("Agent must implement _process()")

    def _update_status(self, status: str, error_message: Optional[str] = None):
        """Update agent status in database"""
        try:
            update_data = {"status": status}
            if error_message:
                update_data["error_message"] = error_message

            self.storage.client.table("agent_status") \
                .update(update_data) \
                .eq("agent_name", self.agent_name) \
                .execute()
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    def query_atoms(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Query Supabase for relevant atoms by topic using keyword search.

        Args:
            topic: Topic keyword to search for in atom titles/content
            limit: Maximum number of atoms to return (default: 5)

        Returns:
            List of atom dictionaries from Supabase

        Example:
            >>> agent = ScriptwriterAgent()
            >>> atoms = agent.query_atoms("motor control", limit=3)
            >>> print(len(atoms))
            3
        """
        try:
            # Simple keyword search (no vector search needed for MVP)
            # Search in title, summary, content, and keywords fields
            result = self.storage.client.table('knowledge_atoms') \
                .select('*') \
                .or_(f'title.ilike.%{topic}%,summary.ilike.%{topic}%,content.ilike.%{topic}%') \
                .limit(limit) \
                .execute()

            logger.info(f"Query '{topic}' returned {len(result.data)} atoms")
            return result.data

        except Exception as e:
            logger.error(f"Failed to query atoms for topic '{topic}': {e}")
            return []

    def generate_script(self, topic: str, atoms: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate video script from knowledge atoms using templates.

        Args:
            topic: Video topic/title
            atoms: List of atoms retrieved from query_atoms()

        Returns:
            Dictionary with script structure:
            {
                'title': str,
                'hook': str,
                'intro': str,
                'sections': List[Dict],
                'summary': str,
                'cta': str,
                'citations': List[str],
                'word_count': int
            }

        Example:
            >>> atoms = agent.query_atoms("PLC basics")
            >>> script = agent.generate_script("Introduction to PLCs", atoms)
            >>> print(script['word_count'])
            450
        """
        if not atoms:
            raise ValueError("No atoms provided for script generation")

        # Extract key information from atoms
        primary_atom = atoms[0]
        supporting_atoms = atoms[1:] if len(atoms) > 1 else []

        # Generate hook (first 10 seconds - grab attention)
        hook = self._generate_hook(topic, primary_atom)

        # Generate intro (establish credibility)
        intro = self._generate_intro(topic, primary_atom)

        # Generate main content sections
        sections = self._generate_sections(primary_atom, supporting_atoms)

        # Generate summary/recap
        summary = self._generate_summary(topic, primary_atom)

        # Generate call-to-action
        cta = self._generate_cta()

        # Collect citations
        citations = self._extract_citations(atoms)

        # Combine all parts
        full_script = f"{hook}\n\n{intro}\n\n"
        for section in sections:
            full_script += f"{section['content']}\n\n"
        full_script += f"{summary}\n\n{cta}"

        # Calculate word count
        word_count = len(full_script.split())

        return {
            'title': topic,
            'hook': hook,
            'intro': intro,
            'sections': sections,
            'summary': summary,
            'cta': cta,
            'citations': citations,
            'full_script': full_script,
            'word_count': word_count,
            'estimated_duration_seconds': word_count // 2.5  # ~150 words/minute
        }

    def _generate_hook(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate attention-grabbing hook (first 10 seconds)"""
        difficulty = atom.get('difficulty', 'beginner')

        if difficulty == 'beginner':
            return f"Ever wondered how {topic.lower()} works? Let me break it down in simple terms."
        elif difficulty == 'intermediate':
            return f"Ready to level up your {topic.lower()} skills? Here's what you need to know."
        else:
            return f"Let's dive deep into {topic.lower()}. This is advanced stuff, so pay attention."

    def _generate_intro(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate intro with credibility and context"""
        manufacturer = atom.get('manufacturer', '').replace('_', ' ').title()
        atom_type = atom.get('atom_type', 'concept')

        intro = f"Today we're covering {topic}. "

        if manufacturer:
            intro += f"This is based on official {manufacturer} documentation, "
        else:
            intro += f"This is based on industry-standard documentation, "

        intro += f"so you're getting accurate, reliable information. "

        if atom_type == 'procedure':
            intro += "I'll walk you through the exact steps you need to follow."
        elif atom_type == 'concept':
            intro += "I'll explain the core concepts and how they work."
        elif atom_type == 'pattern':
            intro += "I'll show you the pattern and when to use it."
        else:
            intro += "Let's get started."

        return intro

    def _generate_sections(self, primary_atom: Dict[str, Any], supporting_atoms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate main content sections from atoms"""
        sections = []

        # Primary section from main atom
        primary_section = {
            'title': primary_atom.get('title', 'Main Content'),
            'content': self._format_atom_content(primary_atom),
            'source': primary_atom.get('source_document', 'Official documentation')
        }
        sections.append(primary_section)

        # Supporting sections
        for atom in supporting_atoms[:2]:  # Max 2 supporting atoms to keep video concise
            section = {
                'title': atom.get('title', 'Additional Information'),
                'content': self._format_atom_content(atom),
                'source': atom.get('source_document', 'Official documentation')
            }
            sections.append(section)

        return sections

    def _format_atom_content(self, atom: Dict[str, Any]) -> str:
        """
        Format atom content for TEACHING narration (not data dumps).

        Handles different atom types intelligently:
        - concept: Explain the idea in plain language
        - procedure: Walk through steps conversationally
        - specification: Explain what the specs mean, not raw tables
        - pattern: Show when/why to use it
        - fault: Explain symptoms and fixes
        """
        atom_type = atom.get('atom_type', 'concept')
        title = atom.get('title', '')
        summary = atom.get('summary', '')
        content = atom.get('content', '')

        # STRATEGY: Use summary as teaching content, NOT raw content
        # Raw content often has tables/specs that don't narrate well

        if atom_type == 'concept':
            # Explain the concept clearly
            narration = summary if summary else content

        elif atom_type == 'procedure':
            # Extract steps and make them conversational
            if 'step' in content.lower():
                # Parse step-by-step format
                lines = content.split('\n')
                steps = [l.strip() for l in lines if l.strip() and ('step' in l.lower() or l[0].isdigit())]
                if steps:
                    narration = "Here's how to do it. "
                    for i, step in enumerate(steps[:6], 1):  # Max 6 steps for video
                        # Clean step text (remove "Step 1:", just keep action)
                        step_text = step.split(':', 1)[-1].strip() if ':' in step else step
                        narration += f"Step {i}: {step_text}. [pause] "
                else:
                    narration = summary if summary else content
            else:
                narration = summary if summary else content

        elif atom_type == 'specification':
            # CRITICAL: Don't read raw tables! Explain what they mean
            if summary:
                narration = f"{summary} Check the documentation for full specifications."
            else:
                # If no summary, create a generic explanation
                narration = f"This covers the specifications for {title}. The documentation includes detailed tables with all the technical parameters you'll need."

        elif atom_type == 'pattern':
            # Explain the pattern and when to use it
            narration = summary if summary else content
            if 'when' not in narration.lower() and 'use' not in narration.lower():
                narration += " Use this pattern when you need to implement similar functionality in your projects."

        elif atom_type == 'fault':
            # Explain problem and solution
            narration = summary if summary else content

        else:
            # Default: Use summary if available, otherwise clean content
            narration = summary if summary else content

        # Clean up for narration
        narration = ' '.join(narration.split())  # Remove excess whitespace

        # Remove markdown tables (they don't narrate well)
        if '|' in narration and '---' in narration:
            # This is a markdown table, skip it
            narration = f"{title}. See the documentation for the full reference table."

        # Limit length (max 150 words per section for pacing)
        words = narration.split()
        if len(words) > 150:
            narration = ' '.join(words[:150])
            # Add natural ending
            if not narration.endswith('.'):
                narration = narration.rsplit('.', 1)[0] + '.'

        return narration

    def _generate_summary(self, topic: str, atom: Dict[str, Any]) -> str:
        """Generate recap/summary"""
        summary = f"So to recap: {topic} is "

        # Use atom summary as base
        atom_summary = atom.get('summary', '')
        if atom_summary:
            # Take first sentence
            first_sentence = atom_summary.split('.')[0] + '.'
            summary += first_sentence.lower()

        summary += " Remember, this information comes from official documentation, "
        summary += "so you can trust it's accurate and up-to-date."

        return summary

    def _generate_cta(self) -> str:
        """Generate call-to-action"""
        return ("If you found this helpful, hit that like button and subscribe for more PLC tutorials. "
                "Drop a comment if you have questions - I read every single one. "
                "See you in the next video!")

    def _extract_citations(self, atoms: List[Dict[str, Any]]) -> List[str]:
        """Extract source citations from atoms"""
        citations = []
        for atom in atoms:
            source_doc = atom.get('source_document', '')
            source_pages = atom.get('source_pages', [])

            if source_doc:
                citation = source_doc
                if source_pages:
                    citation += f" (pages {', '.join(map(str, source_pages))})"
                citations.append(citation)

        return list(set(citations))  # Remove duplicates

    def transform_atom_to_script(self, *args, **kwargs):
        """
        [DEPRECATED] Use generate_script() instead.

        This method is kept for backwards compatibility.
        """
        raise NotImplementedError("Use generate_script() instead of transform_atom_to_script")

    def add_personality_markers(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add personality markers for voice production guidance.

        Markers guide voice tone/emotion:
        - [enthusiastic] - excited, energetic delivery
        - [cautionary] - careful, warning tone
        - [explanatory] - clear, teaching tone
        - [emphasize] - stress this point
        - [pause] - brief pause for effect

        Args:
            script: Script dictionary from generate_script()

        Returns:
            Updated script with personality markers added to text

        Example:
            >>> script = agent.generate_script("PLC Basics", atoms)
            >>> marked_script = agent.add_personality_markers(script)
            >>> print(marked_script['hook'])
            '[enthusiastic] Ever wondered how plcs work? [pause] Let me break it down!'
        """
        # Add markers to hook (always enthusiastic)
        script['hook'] = f"[enthusiastic] {script['hook']}"

        # Add markers to intro (explanatory tone)
        script['intro'] = f"[explanatory] {script['intro']}"

        # Add markers to sections based on content
        for section in script['sections']:
            content = section['content']

            # Add cautionary markers for warning/error content
            if any(word in content.lower() for word in ['warning', 'error', 'fault', 'danger', 'caution']):
                content = f"[cautionary] {content}"

            # Add emphasize markers for important points
            if any(word in content.lower() for word in ['important', 'critical', 'must', 'required']):
                content = content.replace('important', '[emphasize] important')
                content = content.replace('Important', '[emphasize] Important')
                content = content.replace('critical', '[emphasize] critical')
                content = content.replace('Critical', '[emphasize] Critical')

            # Add pause after key phrases
            content = content.replace('. ', '. [pause] ')

            section['content'] = content

        # Add markers to summary (reflective, calm)
        script['summary'] = f"[explanatory] {script['summary']}"

        # Add markers to CTA (enthusiastic, encouraging)
        script['cta'] = f"[enthusiastic] {script['cta']}"

        # Rebuild full_script with markers
        full_script = f"{script['hook']}\n\n{script['intro']}\n\n"
        for section in script['sections']:
            full_script += f"{section['content']}\n\n"
        full_script += f"{script['summary']}\n\n{script['cta']}"

        script['full_script'] = full_script

        return script

    def add_visual_cues(self, script: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add visual cues for video production guidance.

        Cues guide visual elements:
        - [show title: TEXT] - Display title card
        - [show diagram: DESC] - Display diagram/image
        - [highlight: TEXT] - Highlight specific text
        - [show code: LANG] - Display code snippet
        - [show table] - Display table/data

        Args:
            script: Script dictionary from generate_script()

        Returns:
            Updated script with visual cues added

        Example:
            >>> script = agent.generate_script("PLC Basics", atoms)
            >>> visual_script = agent.add_visual_cues(script)
        """
        # Add title card cue at beginning
        script['hook'] = f"[show title: {script['title']}] {script['hook']}"

        # Add visual cues based on content type
        for section in script['sections']:
            content = section['content']
            atom_type = section.get('type', '')

            # Add diagram cue for concepts
            if 'diagram' in content.lower() or 'figure' in content.lower():
                content = f"[show diagram: {section['title']}] {content}"

            # Add code cue for programming content
            if any(word in content.lower() for word in ['code', 'programming', 'ladder', 'function']):
                content = f"[show code: ladder_logic] {content}"

            # Add table cue for specifications
            if 'table' in content.lower() or atom_type == 'specification':
                content = f"[show table] {content}"

            # Add citation visual at end of section
            source = section.get('source', '')
            if source:
                content += f" [show citation: {source}]"

            section['content'] = content

        # Rebuild full_script with visual cues
        full_script = f"{script['hook']}\n\n{script['intro']}\n\n"
        for section in script['sections']:
            full_script += f"{section['content']}\n\n"
        full_script += f"{script['summary']}\n\n{script['cta']}"

        script['full_script'] = full_script

        return script

    def include_visual_cues(self, *args, **kwargs):
        """
        [DEPRECATED] Use add_visual_cues() instead.

        This method is kept for backwards compatibility.
        """
        raise NotImplementedError("Use add_visual_cues() instead of include_visual_cues")

    def cite_sources(self, *args, **kwargs):
        """
        Cite atom sources in script

        TODO: Implement cite_sources logic

        Args:
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            TODO: Define return type

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Implement cite_sources
        raise NotImplementedError("cite_sources not yet implemented")

    def generate_quiz_question(self, *args, **kwargs):
        """
        Generate recap quiz question

        TODO: Implement generate_quiz_question logic

        Args:
            *args: Method arguments
            **kwargs: Method keyword arguments

        Returns:
            TODO: Define return type

        Raises:
            NotImplementedError: Not yet implemented
        """
        # TODO: Implement generate_quiz_question
        raise NotImplementedError("generate_quiz_question not yet implemented")

