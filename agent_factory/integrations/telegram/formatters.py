"""
Response formatting utilities for Telegram.

Handles:
- Markdown V2 formatting
- Message chunking (4096 char limit)
- Error message formatting
- Special character escaping
"""

import re
from typing import List


class ResponseFormatter:
    """
    Format agent responses for Telegram.

    Telegram limits:
    - Max 4096 characters per message
    - Markdown V2 requires escaping special chars

    Example:
        >>> formatter = ResponseFormatter()
        >>> chunks = formatter.chunk_message(long_text, max_length=4096)
        >>> safe_text = formatter.escape_markdown("Hello *world*")
    """

    # Telegram Markdown V2 special characters
    MARKDOWN_SPECIAL_CHARS = r'_*[]()~`>#+-=|{}.!'

    @staticmethod
    def escape_markdown(text: str) -> str:
        """
        Escape special Markdown V2 characters.

        Telegram requires escaping these chars: _ * [ ] ( ) ~ ` > # + - = | { } . !

        Args:
            text: Raw text

        Returns:
            Escaped text safe for Markdown V2

        Example:
            >>> ResponseFormatter.escape_markdown("Price: $100!")
            'Price: \\$100\\!'
        """
        # Escape each special character with backslash
        for char in ResponseFormatter.MARKDOWN_SPECIAL_CHARS:
            text = text.replace(char, f'\\{char}')
        return text

    @staticmethod
    def chunk_message(
        text: str,
        max_length: int = 4096,
        max_chunks: int = 5
    ) -> List[str]:
        """
        Split long messages into chunks.

        Respects Telegram's 4096 character limit.
        Tries to split on sentence boundaries when possible.

        Args:
            text: Message text
            max_length: Max chars per chunk (default 4096)
            max_chunks: Max number of chunks (prevent spam)

        Returns:
            List of message chunks

        Example:
            >>> chunks = ResponseFormatter.chunk_message(very_long_text)
            >>> len(chunks)
            3
        """
        if len(text) <= max_length:
            return [text]

        chunks = []
        remaining = text

        while remaining and len(chunks) < max_chunks:
            if len(remaining) <= max_length:
                chunks.append(remaining)
                break

            # Find best split point (prefer sentence boundaries)
            chunk = remaining[:max_length]

            # Try to split on sentence boundary
            split_point = max(
                chunk.rfind('. '),
                chunk.rfind('! '),
                chunk.rfind('? '),
                chunk.rfind('\n\n')
            )

            if split_point > max_length * 0.5:  # At least 50% of chunk
                split_point += 1  # Include the punctuation
            else:
                # Fall back to word boundary
                split_point = chunk.rfind(' ')
                if split_point == -1:  # No spaces, force split
                    split_point = max_length

            chunks.append(remaining[:split_point].strip())
            remaining = remaining[split_point:].strip()

        # If still text remaining, add truncation notice
        if remaining and len(chunks) >= max_chunks:
            chunks[-1] += f"\n\n[Message truncated - {len(remaining)} chars omitted]"

        return chunks

    @staticmethod
    def format_error(error: Exception, include_type: bool = False) -> str:
        """
        Format error for user-friendly display.

        Hides technical details, shows actionable message.

        Args:
            error: Exception instance
            include_type: Include exception type name

        Returns:
            User-friendly error message

        Example:
            >>> ResponseFormatter.format_error(ValueError("Invalid input"))
            'Error: Invalid input'
        """
        error_msg = str(error)

        # Remove technical stack traces
        if '\n' in error_msg:
            error_msg = error_msg.split('\n')[0]

        # Shorten overly long messages
        if len(error_msg) > 200:
            error_msg = error_msg[:197] + "..."

        if include_type:
            return f"Error ({type(error).__name__}): {error_msg}"
        return f"Error: {error_msg}"

    @staticmethod
    def format_code_block(code: str, language: str = "") -> str:
        """
        Format code block for Telegram.

        Args:
            code: Code content
            language: Programming language (for syntax highlighting)

        Returns:
            Formatted code block

        Example:
            >>> ResponseFormatter.format_code_block("print('hello')", "python")
            '```python\\nprint(\\'hello\\')\\n```'
        """
        # Escape backticks in code
        code = code.replace('```', '\\`\\`\\`')
        return f"```{language}\n{code}\n```"

    @staticmethod
    def format_agent_info(agent_type: str, session_active: bool = True) -> str:
        """
        Format agent status message.

        Args:
            agent_type: Agent type (research, coding, bob)
            session_active: Whether session is active

        Returns:
            Formatted status message

        Example:
            >>> ResponseFormatter.format_agent_info("bob", True)
            '[Agent: Bob (Market Research) - Session Active]'
        """
        agent_names = {
            "research": "Research Assistant",
            "coding": "Coding Assistant",
            "bob": "Bob (Market Research)"
        }

        name = agent_names.get(agent_type, agent_type.title())
        status = "Session Active" if session_active else "New Session"

        return f"[Agent: {name} - {status}]"

    @staticmethod
    def format_approval_request(action: str, details: dict) -> str:
        """
        Format approval request message.

        Args:
            action: Action requiring approval
            details: Action details

        Returns:
            Formatted approval request

        Example:
            >>> ResponseFormatter.format_approval_request(
            ...     "delete_files",
            ...     {"count": 23, "pattern": "test_*.py"}
            ... )
            'Approval Required: delete_files\\n\\nDetails:\\n- count: 23\\n- pattern: test_*.py'
        """
        lines = [f"*Approval Required:* {action}", ""]

        if details:
            lines.append("*Details:*")
            for key, value in details.items():
                lines.append(f"- {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def strip_markdown(text: str) -> str:
        """
        Remove Markdown formatting from text.

        Useful for logging or plaintext contexts.

        Args:
            text: Text with Markdown

        Returns:
            Plain text

        Example:
            >>> ResponseFormatter.strip_markdown("**bold** and *italic*")
            'bold and italic'
        """
        # Remove bold
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        # Remove italic
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        # Remove code blocks
        text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`(.+?)`', r'\1', text)
        # Remove links
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)

        return text.strip()

    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
        """
        Truncate text to max length.

        Args:
            text: Text to truncate
            max_length: Max length including suffix
            suffix: Truncation suffix

        Returns:
            Truncated text

        Example:
            >>> ResponseFormatter.truncate("Very long text here", 10)
            'Very lo...'
        """
        if len(text) <= max_length:
            return text

        truncate_at = max_length - len(suffix)
        return text[:truncate_at] + suffix
