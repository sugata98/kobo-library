"""
Kobo AI Companion Service

Integrates Telegram bot with Google Gemini AI for reading companion functionality.
Uses webhooks for deployment on platforms like Render.
"""

import logging
from typing import Optional
from telegram import Update, Bot
from telegram.ext import Application, ContextTypes, MessageHandler, filters
import google.generativeai as genai
from app.core.config import settings

logger = logging.getLogger(__name__)


class KoboAICompanion:
    """
    Kobo AI Companion service.
    
    Handles:
    1. Sending Kobo highlights to Telegram with AI analysis
    2. Listening for user replies and providing follow-up insights
    """
    
    def __init__(
        self,
        telegram_token: str,
        gemini_api_key: str,
        chat_id: str,
        gemini_model: str = "gemini-3-flash-preview"
    ):
        """
        Initialize the Kobo AI Companion service.
        
        Args:
            telegram_token: Telegram bot API token from @BotFather
            gemini_api_key: Google AI Studio API key
            chat_id: Telegram chat/group ID where highlights are sent
            gemini_model: Gemini model to use (default: gemini-3-flash-preview)
        """
        self.telegram_token = telegram_token
        self.chat_id = chat_id
        self.gemini_model = gemini_model
        
        # Configure Gemini
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel(gemini_model)
        
        # Create bot instance
        self.bot = Bot(token=telegram_token)
        
        logger.info(f"KoboAICompanion initialized with model: {gemini_model}, chat_id: {chat_id}")
    
    async def send_highlight_with_analysis(
        self,
        text: str,
        book: str,
        author: str,
        chapter: Optional[str] = None
    ) -> Optional[int]:
        """
        Send a Kobo highlight to Telegram and reply with AI analysis.
        
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
            
            # Generate AI analysis
            logger.info(f"Generating AI analysis for '{book}'")
            ai_response = await self._generate_analysis(text, book, author, chapter)
            
            # Send AI analysis as a reply (creates thread)
            logger.info(f"Sending AI analysis as reply")
            analysis_msg = await self.bot.send_message(
                chat_id=self.chat_id,
                text=f"🤖 *AI Analysis:*\n\n{ai_response}",
                parse_mode="Markdown",
                reply_to_message_id=highlight_msg.message_id
            )
            
            logger.info(f"Successfully sent highlight and analysis for '{book}'")
            return analysis_msg.message_id
            
        except Exception as e:
            logger.error(f"Error sending highlight with analysis: {e}", exc_info=True)
            return None
    
    async def _generate_analysis(
        self,
        text: str,
        book: str,
        author: str,
        chapter: Optional[str] = None
    ) -> str:
        """
        Generate AI analysis for a highlighted passage.
        
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

            # Generate response using Gemini
            response = self.model.generate_content(system_prompt)
            
            if not response or not response.text:
                logger.warning("Empty response from Gemini")
                return "I apologize, but I couldn't generate an analysis at this time. Please try again later."
            
            return response.text.strip()
            
        except Exception as e:
            logger.error(f"Error generating AI analysis: {e}", exc_info=True)
            return f"I encountered an error while analyzing this passage. Please try again later."
    
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
        if update.message.reply_to_message.from_user.id != self.bot.id:
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

            response = self.model.generate_content(prompt)
            
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
        return KoboAICompanion(
            telegram_token=settings.TELEGRAM_BOT_TOKEN.get_secret_value(),
            gemini_api_key=settings.GEMINI_API_KEY.get_secret_value(),
            chat_id=settings.TELEGRAM_CHAT_ID,
            gemini_model=settings.GEMINI_MODEL
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

