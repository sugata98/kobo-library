"""
Kobo AI Companion Service

Integrates Telegram bot with Google Gemini AI for reading companion functionality.
Uses webhooks for deployment on platforms like Render.
Supports automatic diagram generation using gemini-2.5-flash-image.
"""

import asyncio
import html
import io
import logging
from typing import Optional, Union, List
from telegram import Update, Bot, Message, PhotoSize
from telegram.ext import Application, ContextTypes, MessageHandler, filters
from telegram.error import BadRequest
from google import genai
from google.genai import types
from app.core.config import settings
import base64

logger = logging.getLogger(__name__)


class KoboAICompanion:
    """
    Kobo AI Companion service.
    
    Handles:
    1. Sending Kobo highlights to Telegram with AI analysis (text)
    2. Optionally generating diagrams for technical concepts (images)
    3. Listening for user replies and providing follow-up insights
    4. Understanding and analyzing images sent by users (vision/multimodal)
    
    Uses hybrid model approach:
    - gemini-3-flash-preview for fast, powerful text analysis and vision
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
    
    def _escape_html(self, text: str) -> str:
        """
        Escape HTML special characters for Telegram HTML parse mode.
        
        Uses Python's html.escape() to properly escape only &, <, > without
        double-escaping existing entities. As per Telegram documentation,
        these characters must be escaped:
        - & → &amp;
        - < → &lt;
        - > → &gt;
        
        Args:
            text: Text to escape
            
        Returns:
            HTML-escaped text
        """
        return html.escape(text, quote=False)
    
    async def _safe_send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        reply_to_message_id: Optional[int] = None,
        use_markdown: bool = True,
        **kwargs
    ) -> Optional[Message]:
        """
        Safely send a message with formatting, falling back gracefully on errors.
        
        Strategy:
        1. Try Markdown mode first (AI generates Markdown syntax like **bold**)
        2. Fall back to HTML if Markdown parsing fails
        3. Fall back to plain text if both fail
        
        Args:
            chat_id: Chat ID to send to (int or str)
            text: Message text
            reply_to_message_id: Optional message ID to reply to
            use_markdown: Whether to prefer Markdown mode (default: True)
            **kwargs: Additional arguments for send_message
            
        Returns:
            Sent message object or None if failed
        """
        # Try Markdown first (AI generates Markdown syntax like **bold**, *italic*, etc.)
        if use_markdown:
            try:
                return await self.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_to_message_id=reply_to_message_id,
                    **kwargs
                )
            except BadRequest as e:
                if "can't parse entities" in str(e).lower() or "can't find end" in str(e).lower():
                    logger.warning(f"Markdown parsing failed: {e}. Trying HTML.")
                else:
                    logger.error(f"Markdown BadRequest error: {e}", exc_info=True)
            except Exception as e:
                logger.warning(f"Markdown mode failed: {e}. Trying HTML.")
        
        # Fall back to HTML (escape special chars and send)
        try:
            # Escape HTML special characters but preserve the text structure
            escaped_text = self._escape_html(text)
            return await self.bot.send_message(
                chat_id=chat_id,
                text=escaped_text,
                parse_mode="HTML",
                reply_to_message_id=reply_to_message_id,
                **kwargs
            )
        except BadRequest as e:
            if "can't parse entities" in str(e).lower() or "can't find end" in str(e).lower():
                logger.warning(f"HTML parsing failed: {e}. Falling back to plain text.")
            else:
                logger.error(f"HTML BadRequest error: {e}", exc_info=True)
        except Exception as e:
            logger.warning(f"HTML mode failed: {e}. Falling back to plain text.")
        
        # Final fallback: plain text
        try:
            return await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                reply_to_message_id=reply_to_message_id,
                **kwargs
            )
        except Exception as fallback_error:
            logger.error(f"Failed to send message even as plain text: {fallback_error}", exc_info=True)
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
    
    def _extract_mermaid_code(self, response_text: str) -> Optional[str]:
        """
        Extract Mermaid diagram code from various response formats.
        
        Handles:
        - Markdown code blocks with ```mermaid
        - Plain ``` code blocks
        - Raw Mermaid code without markdown
        
        Args:
            response_text: AI response text that may contain Mermaid code
            
        Returns:
            Extracted Mermaid code or None if not found
        """
        mermaid_code = None
        
        # Try extracting from markdown code block (```mermaid)
        if "```mermaid" in response_text:
            start = response_text.find("```mermaid") + 10
            end = response_text.find("```", start)
            if end > start:
                mermaid_code = response_text[start:end].strip()
                logger.info("Extracted Mermaid code from markdown block")
        
        # Try extracting from plain ``` block
        elif "```" in response_text:
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
        
        return mermaid_code
    
    async def _render_mermaid_to_png(self, mermaid_code: str) -> Optional[bytes]:
        """
        Render Mermaid diagram code to PNG image using mermaid.ink service.
        
        Args:
            mermaid_code: Valid Mermaid diagram code
            
        Returns:
            PNG image bytes or None if rendering fails
        """
        try:
            import base64
            import aiohttp
            
            logger.info(f"Rendering Mermaid code ({len(mermaid_code)} chars)")
            logger.info(f"Mermaid code preview: {mermaid_code[:200]}...")
            
            # Convert Mermaid code to image using mermaid.ink
            # This is a free public service that renders Mermaid diagrams
            # Use URL-safe base64 encoding (replace + with - and / with _)
            encoded_mermaid = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('utf-8')
            # Remove padding (= characters) as mermaid.ink doesn't expect them
            encoded_mermaid = encoded_mermaid.rstrip('=')
            mermaid_url = "https://mermaid.ink/img/" + encoded_mermaid
            
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
        except Exception as e:
            logger.error(f"Error rendering Mermaid to PNG: {e}", exc_info=True)
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

            # Generate Mermaid code using text model (Mermaid is text-based diagram code)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,  # Use text_model for generating text-based diagram code
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
            
            # Extract Mermaid code using helper
            mermaid_code = self._extract_mermaid_code(response_text)
            
            if not mermaid_code:
                logger.warning(f"No valid Mermaid code found in response. Full response: {response_text[:500]}")
                return None
            
            logger.info(f"✅ Generated Mermaid code ({len(mermaid_code)} chars)")
            
            # Render Mermaid code to PNG using helper
            return await self._render_mermaid_to_png(mermaid_code)
            
        except Exception as e:
            logger.error(f"Error generating diagram: {e}", exc_info=True)
            return None
    
    async def handle_general_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle general questions directed to the bot via mentions/tags.
        
        This handles when the user tags/mentions the bot to ask a general question,
        without needing to reply to a specific message.
        
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
        
        # Check if the bot is mentioned/tagged in the message
        bot_username = context.bot.username
        message_text = update.message.text
        
        # Check for bot mention (either @username or entity mention)
        has_mention = False
        if update.message.entities:
            for entity in update.message.entities:
                if entity.type == "mention":
                    mention = message_text[entity.offset:entity.offset + entity.length]
                    if bot_username and mention == f"@{bot_username}":
                        has_mention = True
                        break
                elif entity.type == "text_mention" and entity.user.id == context.bot.id:
                    has_mention = True
                    break
        
        # Also check for plain text mention
        if bot_username and f"@{bot_username}" in message_text:
            has_mention = True
        
        if not has_mention:
            logger.debug("Bot not mentioned in message, ignoring")
            return
        
        # Extract the question (remove the bot mention)
        user_question = message_text
        if bot_username:
            user_question = user_question.replace(f"@{bot_username}", "").strip()
        
        if not user_question:
            logger.debug("Empty question after removing mention, ignoring")
            return
        
        logger.info(f"Received general question from user {update.effective_user.id}: {user_question[:50]}...")
        
        # Send typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Generate response to general question
        response = await self.generate_general_answer(user_question)
        
        # Reply to the user's message using safe send method
        reply_msg = await self._safe_send_message(
            chat_id=update.effective_chat.id,
            text=f"🤖 {response}",
            reply_to_message_id=update.message.message_id
        )
        
        if not reply_msg:
            logger.error("Failed to send response message")
            return
        
        # Check if user wants a visual/diagram
        if self._wants_visual_explanation(user_question):
            logger.info("User requested visual explanation, generating image...")
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="upload_photo"
            )
            
            # Generate image based on the question and answer
            image_bytes = await self._try_generate_image_from_text(
                question=user_question,
                answer=response
            )
            
            if image_bytes:
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=io.BytesIO(image_bytes),
                        caption="🎨 Visual explanation",
                        reply_to_message_id=reply_msg.message_id
                    )
                    logger.info("✅ Sent diagram for general question")
                except Exception as e:
                    logger.error(f"Failed to send image: {e}", exc_info=True)
        
        logger.info(f"Successfully replied to general question")
    
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
        
        # Reply to the user's question using safe send method
        reply_msg = await self._safe_send_message(
            chat_id=update.effective_chat.id,
            text=follow_up_response,
            reply_to_message_id=update.message.message_id
        )
        
        if not reply_msg:
            logger.error("Failed to send follow-up response message")
            return
        
        # Check if user wants a visual/diagram
        if self._wants_visual_explanation(user_question):
            logger.info("User requested visual explanation, generating image...")
            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id,
                action="upload_photo"
            )
            
            # Generate image based on the question and context
            image_bytes = await self._try_generate_image_from_text(
                question=user_question,
                answer=follow_up_response,
                context=previous_context
            )
            
            if image_bytes:
                try:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=io.BytesIO(image_bytes),
                        caption="🎨 Visual explanation",
                        reply_to_message_id=reply_msg.message_id
                    )
                    logger.info("✅ Sent diagram for follow-up question")
                except Exception as e:
                    logger.error(f"Failed to send image: {e}", exc_info=True)
        
        logger.info(f"Successfully replied to follow-up question")
    
    async def _download_photo(self, photo_sizes: List[PhotoSize]) -> Optional[bytes]:
        """
        Download a photo from Telegram.
        
        Args:
            photo_sizes: List of PhotoSize objects (different resolutions)
            
        Returns:
            Photo bytes or None if download fails
        """
        try:
            # Get the highest resolution photo (last in the list)
            largest_photo = photo_sizes[-1]
            logger.info(f"Downloading photo: {largest_photo.file_id} ({largest_photo.width}x{largest_photo.height})")
            
            # Download the file
            file = await self.bot.get_file(largest_photo.file_id)
            photo_bytes = await file.download_as_bytearray()
            
            logger.info(f"✅ Downloaded photo: {len(photo_bytes)} bytes")
            return bytes(photo_bytes)
            
        except Exception as e:
            logger.error(f"Error downloading photo: {e}", exc_info=True)
            return None
    
    async def handle_photo_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Handle questions about photos sent to the bot.
        
        This handles when the user:
        - Sends a photo with a caption mentioning the bot
        - Sends a photo and then mentions the bot in a reply
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        logger.info("📸 Photo message handler triggered")
        
        if not update.message:
            logger.debug("No message in update")
            return
        
        # Ignore messages not in the configured chat
        if str(update.effective_chat.id) != self.chat_id:
            logger.info(f"❌ Ignoring photo from wrong chat: {update.effective_chat.id} (expected: {self.chat_id})")
            return
        
        # Ignore the bot's own messages
        if update.message.from_user.is_bot:
            logger.debug("Ignoring bot's own message")
            return
        
        # Check if there's a photo
        if not update.message.photo:
            logger.debug("No photo in message, ignoring")
            return
        
        logger.info(f"✅ Photo message received from user {update.effective_user.id} in correct chat")
        
        # Check if the bot is mentioned in the caption
        bot_username = context.bot.username
        caption = update.message.caption or ""
        
        has_mention = False
        if update.message.caption_entities:
            for entity in update.message.caption_entities:
                if entity.type == "mention":
                    mention = caption[entity.offset:entity.offset + entity.length]
                    if bot_username and mention == f"@{bot_username}":
                        has_mention = True
                        break
                elif entity.type == "text_mention" and entity.user.id == context.bot.id:
                    has_mention = True
                    break
        
        # Also check for plain text mention
        if bot_username and f"@{bot_username}" in caption:
            has_mention = True
        
        if not has_mention:
            logger.debug("Bot not mentioned in photo caption, ignoring")
            return
        
        # Extract the question (remove the bot mention)
        user_question = caption
        if bot_username:
            user_question = user_question.replace(f"@{bot_username}", "").strip()
        
        # If no question text, use a default prompt
        if not user_question:
            user_question = "What can you tell me about this image?"
        
        logger.info(f"Received photo question from user {update.effective_user.id}: {user_question[:50]}...")
        
        # Send typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action="typing"
        )
        
        # Download the photo
        photo_bytes = await self._download_photo(update.message.photo)
        if not photo_bytes:
            await self._safe_send_message(
                chat_id=update.effective_chat.id,
                text="Sorry, I couldn't download the image. Please try again.",
                reply_to_message_id=update.message.message_id
            )
            return
        
        # Generate response using vision
        response = await self.generate_image_analysis(user_question, photo_bytes)
        
        # Reply to the user's message using safe send method
        reply_msg = await self._safe_send_message(
            chat_id=update.effective_chat.id,
            text=f"🤖 {response}",
            reply_to_message_id=update.message.message_id
        )
        
        if not reply_msg:
            logger.error("Failed to send response message")
            return
        
        logger.info(f"Successfully replied to photo question")
    
    async def generate_image_analysis(self, question: str, image_bytes: bytes) -> str:
        """
        Analyze an image and answer a question about it using Gemini's vision capabilities.
        
        Args:
            question: User's question about the image
            image_bytes: Raw image bytes
            
        Returns:
            AI-generated analysis/answer
        """
        try:
            # Convert image to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine image mime type (basic detection based on magic bytes)
            mime_type = "image/jpeg"  # default
            if image_bytes.startswith(b'\x89PNG'):
                mime_type = "image/png"
            elif image_bytes.startswith(b'GIF'):
                mime_type = "image/gif"
            elif image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
                mime_type = "image/webp"
            
            logger.info(f"Analyzing image ({mime_type}, {len(image_bytes)} bytes) with question: {question[:100]}...")
            
            # Build prompt for vision analysis
            prompt = f"""You are an expert assistant with vision capabilities, specializing in technical, engineering, and scientific content analysis.

A user has shared an image and asked:
"{question}"

Analyze the image carefully and provide a thoughtful, detailed response that:
1. **Describes what you see** - Key elements, structure, content
2. **Answers their specific question** - Address exactly what they asked
3. **Provides context and insights** - Explain technical concepts, patterns, or relationships you observe
4. **Offers additional observations** - Share relevant details they might find interesting

If the image contains:
- Technical diagrams: Explain the architecture, flow, or components
- Code/text: Analyze and explain the content
- Charts/graphs: Interpret the data and trends
- Documents: Summarize and explain key points
- General photos: Describe and contextualize what's shown

Be detailed, accurate, and genuinely helpful."""

            # Create multimodal content with image
            # Using the correct API: Part class methods should be called with keyword arguments
            contents = [
                types.Part(text=prompt),
                types.Part(
                    inline_data=types.Blob(
                        data=image_bytes,
                        mime_type=mime_type
                    )
                )
            ]
            
            # Generate response using Gemini with vision
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,  # gemini-3-flash-preview supports vision
                contents=contents
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for image analysis")
                return "I apologize, but I couldn't analyze the image. Could you try asking in a different way?"
            
            logger.info(f"✅ Generated image analysis ({len(response.text)} chars)")
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error analyzing image: {e}", exc_info=True)
            return "I encountered an error while analyzing the image. Please try again."
    
    def _wants_visual_explanation(self, text: str) -> bool:
        """
        Check if the user is asking for a visual/diagram explanation.
        
        Args:
            text: The user's message text
            
        Returns:
            True if user wants a visual explanation
        """
        visual_keywords = [
            "diagram", "diagrammatically", "diagrammatic",
            "visualize", "visualise", "visual", "visually",
            "draw", "drawing", "sketch",
            "show", "illustrate", "illustration",
            "chart", "graph", "flowchart",
            "picture", "image",
            "explain with", "show me"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in visual_keywords)
    
    async def _try_generate_image_from_text(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate a visual diagram for a general question or follow-up.
        
        Args:
            question: The user's question
            answer: The text answer already generated
            context: Optional previous context (for follow-ups)
            
        Returns:
            Image bytes (PNG) if generated, None otherwise
        """
        if not self.image_model:
            logger.info("Image generation disabled (GEMINI_IMAGE_MODEL not set)")
            return None
        
        logger.info(f"🎨 Generating visual for: {question[:100]}...")
        
        # Determine approach based on model
        if "2.5-flash-image" in self.image_model.lower() or "imagen" in self.image_model.lower():
            return await self._generate_direct_image_from_text(question, answer, context)
        else:
            return await self._generate_mermaid_from_text(question, answer, context)
    
    async def _generate_direct_image_from_text(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate image directly using Gemini 2.5 Flash Image for general questions.
        """
        try:
            context_text = f"\n\nPrevious context:\n{context[:300]}..." if context else ""
            
            # Prompt for visual diagram generation
            image_prompt = f"""User's question: "{question}"

Text explanation provided:
{answer[:500]}...{context_text}

Create a clean, professional technical diagram or visual that illustrates this concept. The diagram should:
- Be simple, clear, and easy to understand
- Use a whiteboard or technical drawing style
- Include labeled components and relationships
- Focus on the core concept being explained
- Use appropriate diagram type (flowchart, architecture, comparison, etc.)

Make it visually informative and complement the text explanation."""

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
            
            logger.info(f"No image in response from {self.image_model}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating direct image: {e}", exc_info=True)
            return None
    
    async def _generate_mermaid_from_text(
        self,
        question: str,
        answer: str,
        context: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate Mermaid diagram code from text and convert to PNG.
        
        Note: Unlike _generate_mermaid_diagram, this method does NOT support SKIP responses
        because it's called when the user explicitly requests a visual (e.g., "show me a diagram").
        We always attempt to generate a diagram when this method is invoked.
        """
        try:
            context_text = f"\n\nPrevious context:\n{context[:300]}..." if context else ""
            
            # Ask Gemini to generate Mermaid diagram code
            mermaid_prompt = f"""User's question: "{question}"

Text explanation:
{answer[:500]}...{context_text}

**Task**: Generate a Mermaid diagram that visually explains this concept.

Create valid Mermaid code that:
- Uses the appropriate diagram type (flowchart, sequenceDiagram, classDiagram, graph, etc.)
- Is simple and focused on the core concept
- Includes clear labels and relationships
- Is technically accurate

Respond with ONLY the Mermaid code (starting with the diagram type like "flowchart TD" or "graph LR").
Do NOT include markdown code fences or explanations."""

            # Generate Mermaid code using text model (Mermaid is text-based diagram code)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,  # Use text_model for generating text-based diagram code
                contents=mermaid_prompt
            )
            
            if not response or not response.text:
                logger.info("No response from Gemini for diagram generation")
                return None
            
            response_text = response.text.strip()
            
            # Extract Mermaid code using helper
            mermaid_code = self._extract_mermaid_code(response_text)
            
            if not mermaid_code:
                logger.warning(f"No valid Mermaid code found in response")
                return None
            
            logger.info(f"✅ Generated Mermaid code ({len(mermaid_code)} chars)")
            
            # Render Mermaid code to PNG using helper
            return await self._render_mermaid_to_png(mermaid_code)
            
        except Exception as e:
            logger.error(f"Error generating Mermaid diagram: {e}", exc_info=True)
            return None
    
    async def generate_general_answer(self, question: str) -> str:
        """
        Generate a response to a general question (not tied to a specific highlight).
        Uses the text model for fast, high-quality responses.
        
        This is a public API method that can be called from API endpoints or handlers.
        
        Args:
            question: User's general question
            
        Returns:
            AI-generated answer
        """
        try:
            # Check if user wants a visual - adjust prompt accordingly
            wants_visual = self._wants_visual_explanation(question)
            visual_instruction = ""
            if wants_visual:
                visual_instruction = "\n\n**IMPORTANT**: The user has requested a visual/diagram explanation. DO NOT create ASCII art or text-based diagrams in your response. Instead, describe the concept clearly in text - a proper visual diagram will be generated separately and sent after this message."
            
            prompt = f"""You are an expert assistant specializing in technical, engineering, and scientific topics, but also knowledgeable about general subjects.

A user has asked you a question:
{question}

Provide a thoughtful, accurate response that:
1. **Directly answers their question** with precision and clarity
2. **Explains complex concepts simply** - Break down technical terms when needed
3. **Provides practical context** - Include real-world examples or applications
4. **Offers additional insights** - Share related information that might be helpful
5. Is concise (2-3 paragraphs) but comprehensive

If the question is about technical/engineering topics:
- Use precise terminology but explain it clearly
- Provide concrete examples or use cases
- Suggest related concepts to explore

If the question is about general topics:
- Be informative and engaging
- Provide relevant context and background
- Share interesting connections or perspectives

Be warm, knowledgeable, and genuinely helpful.{visual_instruction}"""

            # Generate response using Gemini text model (run in thread pool to avoid blocking event loop)
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.text_model,
                contents=prompt
            )
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini for general question")
                return "I apologize, but I couldn't generate a response. Could you rephrase your question?"
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating general answer: {e}", exc_info=True)
            return "I encountered an error. Please try asking again."
    
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
            # Check if user wants a visual - adjust prompt accordingly
            wants_visual = self._wants_visual_explanation(question)
            visual_instruction = ""
            if wants_visual:
                visual_instruction = "\n\n**IMPORTANT**: The user has requested a visual/diagram explanation. DO NOT create ASCII art or text-based diagrams in your response. Instead, describe the concept clearly in text - a proper visual diagram will be generated separately and sent after this message."
            
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

Be warm, knowledgeable, and genuinely helpful.{visual_instruction}"""

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


class BotMentionFilter(filters.MessageFilter):
    """
    Custom filter that only matches messages where this specific bot is mentioned.
    
    Checks for:
    - @bot_username mentions in entities
    - text_mention entities referring to this bot (validated by bot ID)
    """
    
    def __init__(self, bot_username: str, bot_id: int):
        """
        Initialize the filter with the bot's username and ID.
        
        Args:
            bot_username: The bot's username (without @)
            bot_id: The bot's numeric Telegram ID
        """
        self.bot_username = bot_username
        self.bot_id = bot_id
        super().__init__()
    
    def filter(self, message):
        """
        Check if the message mentions this specific bot.
        
        Args:
            message: The Telegram message to check
            
        Returns:
            True if this bot is mentioned, False otherwise
        """
        # Check both text entities (for regular messages) and caption entities (for photos/media)
        entities_to_check = []
        text_to_check = ""
        
        if message.entities:
            entities_to_check = message.entities
            text_to_check = message.text or ""
        elif message.caption_entities:
            entities_to_check = message.caption_entities
            text_to_check = message.caption or ""
        else:
            return False
        
        for entity in entities_to_check:
            # Check for @username mention
            if entity.type == "mention":
                mention_text = text_to_check[entity.offset:entity.offset + entity.length]
                if mention_text == f"@{self.bot_username}":
                    return True
            # Check for text_mention (when user doesn't have a public username)
            elif entity.type == "text_mention":
                # Validate that the mention refers to this specific bot by ID
                if entity.user and entity.user.id == self.bot_id:
                    return True
        
        return False


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
        
        # Get bot username and ID for the mention filter
        bot = application.bot
        bot_info = await bot.get_me()
        bot_username = bot_info.username
        bot_id = bot_info.id
        
        # Add handler for photo questions (photos with captions mentioning the bot)
        # This should be checked first, as it's more specific
        application.add_handler(
            MessageHandler(
                filters.PHOTO & BotMentionFilter(bot_username, bot_id),
                companion.handle_photo_question
            )
        )
        
        # Add handler for general questions (bot mentions/tags)
        # Use custom filter to only trigger when THIS bot is mentioned
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & BotMentionFilter(bot_username, bot_id),
                companion.handle_general_question
            )
        )
        
        # Add conversation handler for replies to bot messages
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.REPLY,
                companion.handle_conversation
            )
        )
        
        logger.info("Telegram application created successfully for webhook mode")
        logger.info("  - Photo questions: Send photo with caption tagging @botname")
        logger.info("  - General questions: Tag bot with @botname")
        logger.info("  - Follow-up questions: Reply to bot messages")
        return application
        
    except Exception as e:
        logger.error(f"Failed to create Telegram application: {e}", exc_info=True)
        return None
