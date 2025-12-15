#!/usr/bin/env python3
"""
ThumbnailAgent - Generate eye-catching YouTube thumbnails that drive clicks

Responsibilities:
- Generate compelling thumbnail designs using AI (DALL-E 3 or Pillow templates)
- Apply ISH brand colors and styling (dark theme, industrial aesthetic)
- Add text overlays (video title snippet, key visual)
- Support A/B testing variants (generate 2-3 options per video)
- Optimize for YouTube specs (1280x720, <2MB, JPG/PNG)
- Track click-through rates (CTR) for iterative improvement

Design Principles:
- High contrast: Dark background, bright text
- Readable text: 60pt+ font, bold sans-serif
- Brand consistency: Industrial/technical aesthetic
- Emotion: Intrigue, curiosity, problem-solving
- A/B testing: Generate variants with different text/colors

Schedule: On-demand (triggered by orchestrator)
Dependencies: Supabase, PIL/Pillow, OpenAI (optional)
Output: Updates Supabase tables, saves thumbnails to data/thumbnails/

Based on: docs/AGENT_ORGANIZATION.md Section 5 (Media Team)
"""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent_factory.memory.storage import SupabaseMemoryStorage

logger = logging.getLogger(__name__)


# ============================================================================
# ISH Brand Colors (Industrial Aesthetic)
# ============================================================================
BRAND_COLORS = {
    "dark_bg": "#1a1a1a",           # Dark charcoal background
    "accent_orange": "#ff6b35",     # High-visibility orange
    "accent_blue": "#00b4d8",       # Industrial blue
    "accent_yellow": "#ffd700",     # Warning yellow
    "text_white": "#ffffff",        # Pure white text
    "text_gray": "#cccccc",         # Subtitle gray
    "danger_red": "#e63946",        # Alert/problem red
}


class ThumbnailVariant(Dict):
    """Pydantic-style dict for thumbnail variants"""
    def __init__(
        self,
        variant_id: int,
        file_path: str,
        text_overlay: str,
        color_scheme: str,
        file_size_bytes: int
    ):
        super().__init__(
            variant_id=variant_id,
            file_path=file_path,
            text_overlay=text_overlay,
            color_scheme=color_scheme,
            file_size_bytes=file_size_bytes,
            created_at=datetime.now().isoformat()
        )


class ThumbnailAgent:
    """
    Generate eye-catching YouTube thumbnails that drive clicks

    This agent is part of the Media Team (docs/AGENT_ORGANIZATION.md Section 5).
    """

    # YouTube thumbnail specs
    WIDTH = 1280
    HEIGHT = 720
    MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

    def __init__(self, use_dalle: bool = False, enable_supabase: bool = True):
        """
        Initialize agent with Supabase connection and design configuration

        Args:
            use_dalle: If True, use DALL-E 3 for image generation (requires OpenAI API key)
                      If False, use Pillow template-based design (FREE, faster)
            enable_supabase: If True, connect to Supabase (required for production)
                           If False, run in standalone mode (for testing/demos)
        """
        # Initialize Supabase (optional for standalone demos)
        self.storage = None
        if enable_supabase:
            try:
                self.storage = SupabaseMemoryStorage()
            except ValueError as e:
                logger.warning(f"Supabase not available: {e}. Running in standalone mode.")

        self.agent_name = "thumbnail_agent"
        self.use_dalle = use_dalle and os.getenv("OPENAI_API_KEY")

        # Output directory
        self.output_dir = Path(os.getenv("THUMBNAIL_DIR", "data/thumbnails"))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Font paths (fallback to system fonts)
        self.font_bold = self._get_font("arial.ttf", 72)
        self.font_subtitle = self._get_font("arial.ttf", 36)

        logger.info(f"ThumbnailAgent initialized (DALL-E: {self.use_dalle}, Supabase: {self.storage is not None})")
        if self.storage:
            self._register_status()

    def _get_font(self, font_name: str, size: int) -> ImageFont.FreeTypeFont:
        """
        Load font with fallback to default

        Args:
            font_name: Font filename (e.g., 'arial.ttf')
            size: Font size in points

        Returns:
            ImageFont.FreeTypeFont object
        """
        # Try common font paths
        font_paths = [
            f"C:\\Windows\\Fonts\\{font_name}",
            f"/usr/share/fonts/truetype/{font_name}",
            f"/System/Library/Fonts/{font_name}",
        ]

        for path in font_paths:
            try:
                return ImageFont.truetype(path, size)
            except (OSError, IOError):
                continue

        # Fallback to default font
        logger.warning(f"Font {font_name} not found, using default")
        return ImageFont.load_default()

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
        if not self.storage:
            return
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
                Expected keys:
                - video_id: str
                - title: str
                - script: str
                - key_visual: Optional[str] (path to screenshot)

        Returns:
            Dict with status, result (list of ThumbnailVariant), or error

        Example:
            >>> agent = ThumbnailAgent()
            >>> result = agent.run({
            ...     "video_id": "plc_001",
            ...     "title": "Master 3-Wire Motor Control",
            ...     "script": "Learn how to wire a start/stop circuit..."
            ... })
            >>> assert result["status"] == "success"
            >>> assert len(result["result"]) == 3  # 3 variants
        """
        try:
            self._send_heartbeat()
            self._update_status("running")

            # Extract payload
            video_id = payload.get("video_id")
            title = payload.get("title")
            script = payload.get("script", "")
            key_visual = payload.get("key_visual")

            if not video_id or not title:
                raise ValueError("video_id and title are required")

            # Generate thumbnails
            variants = self.generate_thumbnails(
                video_id=video_id,
                title=title,
                script=script,
                key_visual=key_visual
            )

            self._update_status("completed")
            return {"status": "success", "result": variants}

        except Exception as e:
            logger.error(f"{self.agent_name} failed: {e}")
            self._update_status("error", str(e))
            return {"status": "error", "error": str(e)}

    def generate_thumbnails(
        self,
        video_id: str,
        title: str,
        script: str,
        key_visual: Optional[str] = None
    ) -> List[ThumbnailVariant]:
        """
        Generate 2-3 thumbnail variants for A/B testing.

        Args:
            video_id: Unique video identifier
            title: Video title (for text overlay)
            script: Full script (to extract key concept)
            key_visual: Optional screenshot or visual cue path

        Returns:
            List of ThumbnailVariant dicts with file paths

        Example:
            >>> agent = ThumbnailAgent()
            >>> variants = agent.generate_thumbnails(
            ...     video_id="plc_001",
            ...     title="Master 3-Wire Motor Control",
            ...     script="Learn the basics of motor control circuits..."
            ... )
            >>> assert len(variants) == 3
            >>> assert all(Path(v["file_path"]).exists() for v in variants)
        """
        logger.info(f"Generating thumbnails for video: {video_id}")

        # Create video-specific directory
        video_dir = self.output_dir / video_id
        video_dir.mkdir(parents=True, exist_ok=True)

        # Generate 3 variants with different color schemes
        variants = []

        # Variant 1: Orange accent (default ISH brand)
        variants.append(self._generate_variant(
            video_id=video_id,
            variant_id=1,
            title=title,
            output_path=video_dir / "variant_1.jpg",
            color_scheme="orange",
            key_visual=key_visual
        ))

        # Variant 2: Blue accent (professional)
        variants.append(self._generate_variant(
            video_id=video_id,
            variant_id=2,
            title=title,
            output_path=video_dir / "variant_2.jpg",
            color_scheme="blue",
            key_visual=key_visual
        ))

        # Variant 3: Yellow accent (high visibility)
        variants.append(self._generate_variant(
            video_id=video_id,
            variant_id=3,
            title=title,
            output_path=video_dir / "variant_3.jpg",
            color_scheme="yellow",
            key_visual=key_visual
        ))

        logger.info(f"Generated {len(variants)} thumbnail variants")
        return variants

    def _generate_variant(
        self,
        video_id: str,
        variant_id: int,
        title: str,
        output_path: Path,
        color_scheme: str,
        key_visual: Optional[str] = None
    ) -> ThumbnailVariant:
        """
        Generate a single thumbnail variant

        Args:
            video_id: Video identifier
            variant_id: Variant number (1, 2, 3)
            title: Video title for text overlay
            output_path: Path to save the thumbnail
            color_scheme: Color scheme ("orange", "blue", "yellow")
            key_visual: Optional background image path

        Returns:
            ThumbnailVariant dict
        """
        # Create base image
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), BRAND_COLORS["dark_bg"])
        draw = ImageDraw.Draw(img)

        # Add background visual if provided
        if key_visual and Path(key_visual).exists():
            try:
                bg_img = Image.open(key_visual)
                bg_img = bg_img.resize((self.WIDTH, self.HEIGHT), Image.Resampling.LANCZOS)
                # Darken background image (40% opacity)
                enhancer = ImageEnhance.Brightness(bg_img)
                bg_img = enhancer.enhance(0.4)
                img.paste(bg_img, (0, 0))
            except Exception as e:
                logger.warning(f"Failed to load key visual: {e}")

        # Add gradient overlay for text readability
        self._add_gradient_overlay(img)

        # Select accent color
        accent_color = {
            "orange": BRAND_COLORS["accent_orange"],
            "blue": BRAND_COLORS["accent_blue"],
            "yellow": BRAND_COLORS["accent_yellow"]
        }.get(color_scheme, BRAND_COLORS["accent_orange"])

        # Add text overlay (title)
        # Break title into lines (max 35 chars per line for readability)
        lines = self._wrap_text(title, max_chars=35)

        # Calculate text position (centered vertically)
        line_height = 90
        total_height = len(lines) * line_height
        y_start = (self.HEIGHT - total_height) // 2

        # Draw each line with shadow for depth
        for i, line in enumerate(lines):
            y_pos = y_start + (i * line_height)

            # Text shadow (offset +4px)
            draw.text(
                (self.WIDTH // 2 + 4, y_pos + 4),
                line,
                font=self.font_bold,
                fill="#000000",
                anchor="mm"
            )

            # Main text
            draw.text(
                (self.WIDTH // 2, y_pos),
                line,
                font=self.font_bold,
                fill=BRAND_COLORS["text_white"],
                anchor="mm"
            )

        # Add accent bar at bottom
        bar_height = 8
        draw.rectangle(
            [(0, self.HEIGHT - bar_height), (self.WIDTH, self.HEIGHT)],
            fill=accent_color
        )

        # Add ISH branding (top-left corner)
        draw.text(
            (40, 40),
            "INDUSTRIAL SKILLS HUB",
            font=self.font_subtitle,
            fill=accent_color
        )

        # Save thumbnail with compression
        img.save(output_path, "JPEG", quality=85, optimize=True)

        # Verify file size
        file_size = output_path.stat().st_size
        if file_size > self.MAX_FILE_SIZE:
            # Re-save with lower quality
            logger.warning(f"Thumbnail too large ({file_size} bytes), reducing quality")
            img.save(output_path, "JPEG", quality=70, optimize=True)
            file_size = output_path.stat().st_size

        logger.info(f"Generated variant {variant_id}: {output_path} ({file_size} bytes)")

        return ThumbnailVariant(
            variant_id=variant_id,
            file_path=str(output_path.absolute()),
            text_overlay=title,
            color_scheme=color_scheme,
            file_size_bytes=file_size
        )

    def _add_gradient_overlay(self, img: Image.Image):
        """
        Add gradient overlay for text readability

        Args:
            img: PIL Image to modify in-place
        """
        # Create gradient mask (dark at center, transparent at edges)
        gradient = Image.new("RGBA", (self.WIDTH, self.HEIGHT), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # Draw ellipse gradient (center darkened)
        for i in range(10):
            opacity = int(255 * (10 - i) / 10 * 0.3)  # Max 30% opacity
            color = (0, 0, 0, opacity)
            offset = i * 40
            draw.ellipse(
                [(offset, offset), (self.WIDTH - offset, self.HEIGHT - offset)],
                fill=color
            )

        # Composite gradient onto image
        img.paste(gradient, (0, 0), gradient)

    def _wrap_text(self, text: str, max_chars: int = 35) -> List[str]:
        """
        Wrap text into multiple lines

        Args:
            text: Text to wrap
            max_chars: Maximum characters per line

        Returns:
            List of text lines
        """
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            if len(test_line) <= max_chars:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _update_status(self, status: str, error_message: Optional[str] = None):
        """Update agent status in database"""
        if not self.storage:
            return
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


# ============================================================================
# DALL-E 3 Integration (Optional, Paid)
# ============================================================================

def generate_dalle_thumbnail(
    video_id: str,
    title: str,
    script: str,
    output_path: Path
) -> str:
    """
    Generate thumbnail using DALL-E 3 (PAID, requires OpenAI API key)

    Args:
        video_id: Video identifier
        title: Video title
        script: Full script (for context)
        output_path: Path to save the generated image

    Returns:
        str: Path to generated thumbnail

    Raises:
        ImportError: If openai package not installed
        ValueError: If OPENAI_API_KEY not set

    Example:
        >>> path = generate_dalle_thumbnail(
        ...     video_id="plc_001",
        ...     title="Master 3-Wire Motor Control",
        ...     script="Learn motor control circuits...",
        ...     output_path=Path("data/thumbnails/plc_001/dalle.jpg")
        ... )
        >>> assert Path(path).exists()
    """
    try:
        from openai import OpenAI
        import requests
    except ImportError:
        raise ImportError("openai package not installed. Run: poetry add openai")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set in environment")

    # Extract key concept from script (first 200 chars)
    concept = script[:200] if script else title

    # Generate prompt for DALL-E
    prompt = f"""
    Create a YouTube thumbnail for a technical education video titled "{title}".

    Style: Dark industrial aesthetic, high contrast, bold text overlay.
    Visual: Industrial equipment, technical diagrams, or abstract tech imagery.
    Mood: Professional, educational, slightly dramatic.
    Text: Include "{title[:30]}..." in large, bold white text.

    Aspect ratio: 16:9 (YouTube thumbnail format)
    """

    logger.info(f"Generating DALL-E thumbnail for: {title}")

    # Call DALL-E 3 API
    client = OpenAI(api_key=api_key)
    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1792x1024",  # Closest to 1280x720 ratio
        quality="standard",  # or "hd" for higher quality ($0.08 vs $0.04)
        n=1
    )

    # Download image
    image_url = response.data[0].url
    img_response = requests.get(image_url)
    img_response.raise_for_status()

    # Resize to YouTube specs
    img = Image.open(BytesIO(img_response.content))
    img = img.resize((1280, 720), Image.Resampling.LANCZOS)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "JPEG", quality=85, optimize=True)

    logger.info(f"DALL-E thumbnail generated: {output_path}")
    return str(output_path.absolute())


if __name__ == "__main__":
    # Demo usage (standalone mode without Supabase)
    agent = ThumbnailAgent(use_dalle=False, enable_supabase=False)

    result = agent.run({
        "video_id": "plc_demo_001",
        "title": "Master 3-Wire Motor Control Circuits",
        "script": "Learn how to wire and troubleshoot industrial motor control circuits..."
    })

    print(f"Status: {result['status']}")
    if result['status'] == 'success':
        for variant in result['result']:
            print(f"  Variant {variant['variant_id']}: {variant['file_path']}")
