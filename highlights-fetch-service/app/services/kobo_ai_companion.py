"""
Kobo AI Companion Service

Integrates Telegram bot with Google Gemini AI for reading companion functionality.
Uses webhooks for deployment on platforms like Render.
Supports automatic diagram generation using gemini-2.5-flash-image.
"""

import asyncio
import io
import logging
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class KoboAICompanion:
    """
    Kobo AI Companion service.
    
    Handles:
    1. Sending Kobo highlights to Telegram with AI analysis (text)
    2. Optionally generating diagrams for technical concepts (images)
    3. Listening for user replies and providing follow-up insights
    
    Uses hybrid model approach:
    - gemini-3-flash-preview for fast, powerful text analysis
    - gemini-2.5-flash-image for optional diagram generation
    """
    
    def __init__(
        self,
        telegram_token: str,
        gemini_api_key: str,
        chat_id: str,
        text_model: str = "gemini-3-flash-preview",
        image_model: Optional[str] = None
    ):
        """
        Initialize the Kobo AI Companion service.
        
        Args:
            telegram_token: Telegram bot API token from @BotFather
            gemini_api_key: Google AI Studio API key
            chat_id: Telegram chat/group ID where highlights are sent
            text_model: Gemini model for text analysis (default: gemini-3-flash-preview)
            image_model: Gemini model for image generation (default: None/disabled)
        """
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.text_model = text_model
        self.image_model = image_model if image_model else None
        
        # Configure Gemini with Cloud SDK
        self.client = genai.Client(api_key=gemini_api_key)
        
        # Create bot instance
        self.bot = Bot(token=telegram_token)
        
        logger.info(f"KoboAICompanion initialized:")
        logger.info(f"  - Text model: {text_model}")
        if self.image_model:
            logger.info(f"  ✅ Image generation enabled: {self.image_model}")
        else:
            logger.info(f"  ⚪ Image generation disabled")
        logger.info(f"  - Chat ID: {chat_id}")
    
    async def send_highlight_with_analysis(
        self,
        text: str,
        book: str,
        author: str,
        chapter: Optional[str] = None
    ) -> Optional[int]:
        """
        Send a Kobo highlight to Telegram with AI analysis.
        Optionally generates and sends a diagram if helpful.
        
        Args:
            text: The highlighted text
            book: Book title
            author: Author name
            chapter: Chapter name (optional)
            
        Returns:
            Message ID of the AI analysis message (for threading), or None if failed
        """
        try:
            # Format the highlight message
            chapter_text = f" ({chapter})" if chapter else ""
            highlight_message = (
                f"📖 *{book}*{chapter_text}\n"
                f"✍️ _by {author}_\n\n"
                f"💡 Highlighted:\n"
                f"> {text}"
            )
            
            # Send highlight to Telegram
            logger.info(f"Sending highlight from '{book}' to Telegram")
            highlight_msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=highlight_message,
                parse_mode="Markdown"
            )
            
            # Generate AI text analysis
            logger.info(f"Generating text analysis for '{book}'")
            ai_response = await self._generate_analysis(text, book, author, chapter)
            
            # Send AI analysis as a reply (creates thread)
            logger.info(f"Sending AI analysis as reply")
            analysis_msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"🤖 *AI Analysis:*\n\n{ai_response}",
                parse_mode="Markdown",
                reply_to_message_id=highlight_msg.message_id
            )
            
            # Try to generate and send a diagram (if image generation is enabled)
            if self.image_model:
                logger.info(f"Attempting to generate diagram for '{book}'")
                image_bytes = await self._try_generate_image(text, book, author, ai_response)
                
                if image_bytes:
                    try:
                        # Send image as a reply to the analysis (in the same thread)
                        await self.bot.send_photo(
                            chat_id=self.chat_id,
                            photo=io.BytesIO(image_bytes),
                            caption="🎨 Visual explanation",
                            reply_to_message_id=analysis_msg.message_id
                        )
                        logger.info(f"✅ Sent diagram for '{book}'")
                    except Exception as e:
                        logger.error(f"Failed to send image to Telegram: {e}", exc_info=True)
            
            logger.info(f"Successfully sent highlight and analysis for '{book}'")
            return analysis_msg.message_id
            
        except Exception as e:
            logger.error(f"Error sending highlight with analysis: {e}", exc_info=True)
            return None
    
    async def generate_short_summary(
        self,
        text: str,
        book: str,
        author: str,
        chapter: Optional[str] = None
    ) -> str:
        """
        Generate a SHORT 1-2 sentence summary for Kobo device display.
        
        This is optimized for Kobo's qndb toast notifications which have ~200 char limit.
        Public API for external modules.
        
        Args:
            text: The highlighted text to analyze
            book: The book title
            author: The author name
            chapter: Optional chapter name
            
        Returns:
            A short summary (1-2 sentences, max 200 chars)
        """
        try:
            chapter_context = f" (from {chapter})" if chapter else ""
            
            # Prompt for very short summary
            prompt = f"""You are a concise reading companion. 

Book: "{book}" by {author}{chapter_context}

Highlighted Text:
"{text}"

Provide a ONE SENTENCE summary (max 150 characters) explaining the KEY concept or main idea. Be concise and clear."""

            # Generate response
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,
                contents=prompt
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for short summary")
                return "Sent detailed analysis to Telegram!"
            
            summary = response.text.strip()
            
            # Ensure it's actually short (qndb limit)
            if len(summary) > 200:
                summary = summary[:197] + "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating short summary: {e}", exc_info=True)
            return "Sent analysis to Telegram!"
    
    async def _generate_analysis(
        self,
        text: str,
        book: str,
        author: str,
        chapter: Optional[str] = None
    ) -> str:
        """
        Generate AI text analysis for a highlighted passage.
        Uses the text model (gemini-3-flash-preview) for fast, high-quality analysis.
        
        Args:
            text: The highlighted text
            book: Book title
            author: Author name
            chapter: Chapter name (optional)
            
        Returns:
            AI-generated analysis text
        """
        try:
            # Build context-aware system prompt
            chapter_context = f" from chapter '{chapter}'" if chapter else ""
            
            system_prompt = f"""You are an expert reading companion specializing in technical, engineering, and scientific literature (but also knowledgeable about general topics).

The user is currently reading "{book}" by {author}{chapter_context}.

They've highlighted the following passage:

"{text}"

Provide insightful analysis that:
1. **Explains key concepts clearly** - Break down technical terms, principles, or ideas
2. **Provides practical context** - How does this apply in real-world scenarios?
3. **Connects to broader themes** - How does this relate to the book's main topics or the field in general?
4. **Offers actionable insights** - What should the reader take away or explore further?

Keep your response:
- Concise (2-3 paragraphs max)
- Technically accurate when dealing with engineering/scientific content
- Conversational and genuinely helpful
- Focused on practical understanding

If this is a technical/engineering book, focus on concepts, applications, and principles.
If it's fiction or non-technical, provide literary or thematic analysis instead."""

            # Generate response using Gemini text model (run in thread pool to avoid blocking event loop)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,
                contents=system_prompt
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for text analysis")
                return "I apologize, but I couldn't generate an analysis at this time. Please try again later."
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}", exc_info=True)
            return f"I encountered an error while analyzing this passage. Please try again later."
    
    async def _try_generate_image(
        self,
        text: str,
        book: str,
        author: str,
        analysis: str
    ) -> Optional[bytes]:
        """
        Attempt to generate a helpful diagram for the highlighted text.
        
        Strategy depends on the model:
        - If using gemini-2.5-flash-image: Direct image generation (photorealistic/artistic)
        - Otherwise: Generate Mermaid code → Convert to PNG (technical diagrams)
        
        Args:
            text: The highlighted text
            book: Book title
            author: Author name
            analysis: The text analysis already generated
            
        Returns:
            Image bytes (PNG) if generated, None otherwise
        """
        if not self.image_model:
            logger.info("Image generation disabled (GEMINI_IMAGE_MODEL not set)")
            return None
        
        logger.info(f"🎨 Image generation enabled. Model: {self.image_model}")
        
        # Determine approach based on model
        if "2.5-flash-image" in self.image_model.lower() or "imagen" in self.image_model.lower():
            logger.info("Using direct image generation approach (Gemini 2.5 Flash Image)")
            return await self._generate_direct_image(text, book, author, analysis)
        else:
            logger.info("Using Mermaid diagram approach (text model → mermaid.ink)")
            return await self._generate_mermaid_diagram(text, book, author, analysis)
    
    async def _generate_direct_image(
        self,
        text: str,
        book: str,
        author: str,
        analysis: str
    ) -> Optional[bytes]:
        """
        Generate image directly using Gemini 2.5 Flash Image or Imagen.
        Best for photorealistic/artistic images.
        """
        try:
            # Prompt for technical diagram generation
            image_prompt = f"""Based on this highlighted text from "{book}" by {author}:

"{text}"

Analysis: {analysis[:300]}...

Create a clean, professional technical diagram that illustrates this concept. The diagram should:
- Be simple and clear
- Use a whiteboard or technical drawing style
- Include labeled components
- Be easy to understand at a glance
- Focus on the core concept

Only generate an image if this concept would genuinely benefit from visualization (system architectures, data flows, algorithms, etc.).

If a diagram wouldn't add value, respond with text "SKIP" instead."""

            # Generate image using Gemini 2.5 Flash Image
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.image_model,
                contents=image_prompt
            )
            
            if not response or not response.parts:
                logger.info("No response from Gemini image generation")
                return None
            
            # Check if response contains an image
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    logger.info(f"✅ Image generated successfully by {self.image_model}")
                    return part.inline_data.data
            
            # Check if Gemini decided to skip
            if response.text and "SKIP" in response.text.upper():
                logger.info("Gemini decided this concept doesn't need a visual")
                return None
            
            logger.info(f"No image in response from {self.image_model}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating direct image: {e}", exc_info=True)
            return None
    
    async def _generate_mermaid_diagram(
        self,
        text: str,
        book: str,
        author: str,
        analysis: str
    ) -> Optional[bytes]:
        """
        Generate Mermaid diagram code and convert to PNG.
        Best for technical diagrams, flowcharts, system architectures.
        """
        
        try:
            import urllib.parse
            import base64
            import aiohttp
            
            # Ask Gemini to generate Mermaid diagram code
            mermaid_prompt = f"""Based on this highlighted text from "{book}" by {author}:

"{text}"

Analysis: {analysis[:300]}...

**Task**: Determine if this concept would benefit from a visual diagram. If YES, generate valid Mermaid diagram code.

Generate Mermaid code ONLY if it would genuinely help understanding:
- System architectures
- Data structures
- Algorithms / Flowcharts
- Workflows / Processes
- Comparisons / Relationships
- Database schemas

If a diagram would help, respond with ONLY the Mermaid code (starting with ```mermaid).
If visualization wouldn't add value, respond with exactly: "SKIP"

Keep the diagram simple, clear, and focused on the core concept."""

            # Generate Mermaid code using text model
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.image_model,  # Using image_model setting but it's still a text model
                contents=mermaid_prompt
            )
            
            if not response or not response.text:
                logger.info("No response from Gemini for diagram generation")
                return None
            
            response_text = response.text.strip()
            
            # Check if Gemini decided to skip
            if response_text.upper() == "SKIP" or "SKIP" in response_text.upper()[:20]:
                logger.info("Gemini decided this concept doesn't need a diagram")
                return None
            
            # Extract Mermaid code from response (handle multiple formats)
            mermaid_code = None
            
            # Try extracting from markdown code block
            if "```mermaid" in response_text:
                start = response_text.find("```mermaid") + 10
                end = response_text.find("```", start)
                if end > start:
                    mermaid_code = response_text[start:end].strip()
                    logger.info("Extracted Mermaid code from markdown block")
            
            # Try extracting from plain ``` block
            elif "```" in response_text and not mermaid_code:
                start = response_text.find("```") + 3
                # Skip language identifier if present
                newline_pos = response_text.find("\n", start)
                if newline_pos > start:
                    start = newline_pos + 1
                end = response_text.find("```", start)
                if end > start:
                    potential_code = response_text[start:end].strip()
                    # Verify it looks like Mermaid
                    if any(keyword in potential_code for keyword in ["graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram"]):
                        mermaid_code = potential_code
                        logger.info("Extracted Mermaid code from plain code block")
            
            # Try raw Mermaid code without markdown
            if not mermaid_code and any(response_text.startswith(keyword) for keyword in ["graph", "flowchart", "sequenceDiagram", "classDiagram", "stateDiagram", "erDiagram"]):
                mermaid_code = response_text
                logger.info("Using raw Mermaid code (no markdown wrapper)")
            
            if not mermaid_code:
                logger.warning(f"No valid Mermaid code found in response. Full response: {response_text[:500]}")
                return None
            
            logger.info(f"✅ Generated Mermaid code ({len(mermaid_code)} chars):")
            logger.info(f"Mermaid code preview: {mermaid_code[:200]}...")
            
            # Convert Mermaid code to image using mermaid.ink
            # This is a free public service that renders Mermaid diagrams
            try:
                # Use URL-safe base64 encoding (replace + with - and / with _)
                encoded_mermaid = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
                # Remove padding (= characters) as mermaid.ink doesn't expect them
                encoded_mermaid = encoded_mermaid.rstrip('=')
                mermaid_url = f"https://mermaid.ink/img/{encoded_mermaid}"
                
                logger.info(f"Requesting image from mermaid.ink: {mermaid_url[:100]}...")
                
                # Download the rendered image
                async with aiohttp.ClientSession() as session:
                    async with session.get(mermaid_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                        if resp.status == 200:
                            image_bytes = await resp.read()
                            logger.info(f"✅ Successfully rendered Mermaid diagram to PNG ({len(image_bytes)} bytes)")
                            return image_bytes
                        else:
                            error_text = await resp.text()
                            logger.warning(f"Failed to render Mermaid diagram: HTTP {resp.status}")
                            logger.warning(f"Response body: {error_text[:200]}")
                            return None
            except aiohttp.ClientError as e:
                logger.error(f"Network error fetching Mermaid image: {e}", exc_info=True)
                return None
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}", exc_info=True)
            return None
    
    async def handle_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle conversational replies in Telegram.
        
        This handles when the user replies to the bot's AI analysis with follow-up questions.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        if not update.message or not update.message.text:
            return
        
        # Ignore messages not in the configured chat
        if str(update.effective_chat.id) != self.chat_id:
            logger.debug(f"Ignoring message from chat {update.effective_chat.id}")
            return
        
        # Ignore the bot's own messages
        if update.message.from_user.is_bot:
            logger.debug("Ignoring bot's own message")
            return
        
        # Only respond to replies to the bot's messages
        if not update.message.reply_to_message:
            logger.debug("Message is not a reply, ignoring")
            return
        
        # Check if the reply is to the bot's message
        if update.message.reply_to_message.from_user.id != context.bot.id:
            logger.debug("Reply is not to bot's message, ignoring")
            return
        
        user_question = update.message.text
        previous_context = update.message.reply_to_message.text
        
        logger.info(f"Received follow-up question from user {update.effective_user.id}")
        
        # Send typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Generate follow-up response
        follow_up_response = await self._generate_follow_up(user_question, previous_context)
        
        # Reply to the user's question
        await update.message.reply_text(
            follow_up_response,
            parse_mode="Markdown"
        )
        
        logger.info(f"Successfully replied to follow-up question")
    
    async def _generate_follow_up(self, question: str, previous_context: str) -> str:
        """
        Generate a follow-up response based on user's question and previous context.
        Uses the text model for fast, high-quality responses.
        
        Args:
            question: User's follow-up question
            previous_context: The previous message being replied to
            
        Returns:
            AI-generated follow-up response
        """
        try:
            prompt = f"""You are an expert reading companion specializing in technical, engineering, and scientific literature (but also knowledgeable about general topics).

You're in a conversation with a reader about their book.

Previous context:
{previous_context}

The reader's follow-up question:
{question}

Provide a thoughtful response that:
1. **Directly answers their question** with technical accuracy
2. **Builds on the previous context** - Reference what was already discussed
3. **Offers deeper insights** - Go beyond the surface when appropriate
4. **Suggests connections** - Link to related concepts, chapters, or real-world applications
5. Is concise (2-3 paragraphs) but comprehensive

If discussing technical/engineering topics:
- Use precise terminology but explain it clearly
- Provide practical examples or applications
- Suggest related concepts to explore

Be warm, knowledgeable, and genuinely helpful."""

            # Generate response using Gemini text model (run in thread pool to avoid blocking event loop)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,
                contents=prompt
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for follow-up")
                return "I apologize, but I couldn't generate a response. Could you rephrase your question?"
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating follow-up response: {e}", exc_info=True)
            return "I encountered an error. Please try asking again."


def create_kobo_ai_companion() -> Optional[KoboAICompanion]:
    """
    Factory function to create KoboAICompanion from settings.
    
    Returns:
        KoboAICompanion instance if configured, None otherwise
    """
    if not settings.TELEGRAM_ENABLED:
        logger.info("Kobo AI Companion is disabled (TELEGRAM_ENABLED=False)")
        return None
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is required when TELEGRAM_ENABLED=True")
        return None
    
    if not settings.TELEGRAM_CHAT_ID:
        logger.error("TELEGRAM_CHAT_ID is required when TELEGRAM_ENABLED=True")
        return None
    
    if not settings.GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is required when TELEGRAM_ENABLED=True")
        return None
    
    try:
        # Normalize empty string to None for image model
        image_model = settings.GEMINI_IMAGE_MODEL
        if image_model == "":
            image_model = None
        
        return KoboAICompanion(
            telegram_token=settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
            gemini_api_key=settings.GEMINI_API_KEY.get_secret_value(),
            chat_id=settings.TELEGRAM_CHAT_ID,
            text_model=settings.GEMINI_MODEL,
            image_model=image_model
        )
    except Exception as e:
        logger.error(f"Failed to create KoboAICompanion: {e}", exc_info=True)
        return None


async def create_telegram_application() -> Optional[Application]:
    """
    Create and configure Telegram Application for webhook mode.
    
    Returns:
        Configured Application instance, or None if disabled/misconfigured
    """
    if not settings.TELEGRAM_ENABLED:
        return None
    
    if not settings.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is required")
        return None
    
    try:
        # Create application for webhook mode
        application = (
            Application.builder()
            .token(settings.TELEGRAM_BOT_TOKEN.get_secret_value())
            .build()
        )
        
        # Create companion service
        companion = create_kobo_ai_companion()
        if not companion:
            logger.error("Failed to create KoboAICompanion")
            return None
        
        # Add conversation handler
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.REPLY,
                companion.handle_conversation
            )
        )
        
        logger.info("Telegram application created successfully for webhook mode")
        return application
        
    except Exception as e:
        logger.error(f"Failed to create Telegram application: {e}", exc_info=True)
        return None
