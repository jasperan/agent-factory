"""
Natural Language Intent Detector for Telegram Bot

Parses user messages to detect intent and extract parameters:
- KB search queries
- Script generation requests
- GitHub issue solving
- General chat (fallback)

Examples:
    "Tell me about motor control" → KB search for "motor control"
    "Generate a script about PLCs" → Script generation for "PLCs"
    "Solve issue 52" → GitHub solve issue #52
    "What's the weather?" → General chat (research agent)
"""

import re
from typing import Optional, Tuple


class IntentDetector:
    """
    Detects user intent from natural language messages.

    Uses regex patterns and keyword matching to understand what the user wants.
    """

    # KB Search patterns
    KB_SEARCH_PATTERNS = [
        r"(?:search|find|lookup|look up)\s+(?:for\s+)?(.+)",
        r"tell me about (.+)",
        r"what (?:do you know|can you tell me) about (.+)",
        r"info(?:rmation)? (?:on|about) (.+)",
        r"explain (.+)",
        r"what is (.+)",
        r"what are (.+)",
        r"show me (.+)",
    ]

    # Script generation patterns
    SCRIPT_GEN_PATTERNS = [
        r"generate (?:a\s+)?script (?:about|on|for) (.+)",
        r"create (?:a\s+)?(?:video|script) (?:about|on|for) (.+)",
        r"write (?:a\s+)?script (?:about|on|for) (.+)",
        r"make (?:a\s+)?(?:video|script) (?:about|on|for) (.+)",
        r"(?:can you )?(?:create|generate|write) (?:me )?(?:a )?script (.+)",
    ]

    # GitHub issue patterns
    GITHUB_ISSUE_PATTERNS = [
        r"solve issue\s+#?(\d+)",
        r"work on issue\s+#?(\d+)",
        r"fix (?:bug|issue)\s+#?(\d+)",
        r"tackle issue\s+#?(\d+)",
        r"handle issue\s+#?(\d+)",
    ]

    @staticmethod
    def detect_kb_search(message: str) -> Optional[str]:
        """
        Detect if message is a KB search query and extract topic.

        Args:
            message: User's message

        Returns:
            Topic string if KB search detected, None otherwise

        Examples:
            "Tell me about motor control" → "motor control"
            "Search for PLC basics" → "PLC basics"
            "What do you know about Allen-Bradley?" → "Allen-Bradley?"
            "Find info on ladder logic" → "ladder logic"
        """
        message_lower = message.lower().strip()

        # Try each pattern
        for pattern in IntentDetector.KB_SEARCH_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                # Remove trailing question marks/punctuation
                topic = re.sub(r'[?!.]+$', '', topic).strip()
                return topic if topic else None

        # Check for direct topic mentions (common KB topics)
        kb_keywords = [
            'plc', 'motor', 'ladder', 'siemens', 'allen', 'bradley',
            'timer', 'counter', 'troubleshoot', 'control', 'program',
            'fault', 'error', 'manual', 'diagram'
        ]

        # If message contains KB keywords and is a question, treat as search
        if any(keyword in message_lower for keyword in kb_keywords):
            if message_lower.endswith('?') or message_lower.startswith(('what', 'how', 'why', 'when')):
                # Extract everything after the question word
                for q_word in ['what is', 'what are', 'how do', 'why', 'when']:
                    if message_lower.startswith(q_word):
                        topic = message.split(q_word, 1)[1].strip()
                        topic = re.sub(r'[?!.]+$', '', topic).strip()
                        return topic if topic else None

        return None

    @staticmethod
    def detect_script_generation(message: str) -> Optional[str]:
        """
        Detect if message is a script generation request and extract topic.

        Args:
            message: User's message

        Returns:
            Topic string if script generation detected, None otherwise

        Examples:
            "Generate a script about PLC basics" → "PLC basics"
            "Create video on troubleshooting" → "troubleshooting"
            "Write a script for motor control" → "motor control"
        """
        message_lower = message.lower().strip()

        # Try each pattern
        for pattern in IntentDetector.SCRIPT_GEN_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                topic = match.group(1).strip()
                # Remove "about", "on", "for" prefixes if captured
                topic = re.sub(r'^(about|on|for)\s+', '', topic, flags=re.IGNORECASE).strip()
                topic = re.sub(r'[?!.]+$', '', topic).strip()
                return topic if topic else None

        return None

    @staticmethod
    def detect_github_issue(message: str) -> Optional[int]:
        """
        Detect if message is a GitHub issue solving request and extract issue number.

        Args:
            message: User's message

        Returns:
            Issue number if GitHub intent detected, None otherwise

        Examples:
            "Solve issue 52" → 52
            "Work on issue #47" → 47
            "Fix bug 32" → 32
        """
        message_lower = message.lower().strip()

        # Try each pattern
        for pattern in IntentDetector.GITHUB_ISSUE_PATTERNS:
            match = re.search(pattern, message_lower, re.IGNORECASE)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue

        return None

    @staticmethod
    def classify(message: str) -> Tuple[str, Optional[str]]:
        """
        Classify message intent and extract parameters.

        Args:
            message: User's message

        Returns:
            Tuple of (intent_type, parameter)
            - intent_type: "kb_search", "script_gen", "github_issue", "general_chat"
            - parameter: Extracted topic/issue_number as string, or None

        Examples:
            "Tell me about PLCs" → ("kb_search", "PLCs")
            "Generate script for ladder logic" → ("script_gen", "ladder logic")
            "Solve issue 52" → ("github_issue", "52")
            "What's the weather?" → ("general_chat", None)
        """
        # Check GitHub issue first (most specific)
        issue_num = IntentDetector.detect_github_issue(message)
        if issue_num is not None:
            return ("github_issue", str(issue_num))

        # Check script generation (more specific than KB search)
        script_topic = IntentDetector.detect_script_generation(message)
        if script_topic:
            return ("script_gen", script_topic)

        # Check KB search
        kb_topic = IntentDetector.detect_kb_search(message)
        if kb_topic:
            return ("kb_search", kb_topic)

        # Default to general chat
        return ("general_chat", None)
