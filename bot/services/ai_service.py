"""
AI Service for analyzing construction photos using Google Gemini
"""
import json
import google.generativeai as genai
from typing import Dict, Any, Optional
from PIL import Image
import io
import logging
import config
from bot.services.settings_service import settings_service
from bot.utils.markdown_utils import escape_markdown

logger = logging.getLogger(__name__)


class AIService:
    """Service for analyzing construction defects using Google Gemini"""

    SYSTEM_PROMPT = """РОЛЬ:
Ты — строгий и опытный инженер строительного контроля (Технадзор) в РФ. Твоя цель — найти нарушения, оценить их критичность и сослаться на нормы.

ЗАДАЧА:
1. Проверь, является ли фото строительным. Если это кот, еда, селфи или явный мусор — верни "is_relevant": false и шутливый комментарий.
2. Если это стройка, используй предоставленный пользователем контекст (Объект/Место).
3. Найди дефекты. Для каждого дефекта определи:
   - Наименование.
   - Точное местонахождение на фото.
   - Критичность (Критический / Значительный / Малозначительный).
   - Вероятная причина.
   - Нарушенная норма РФ (СП, ГОСТ, СНиП, Приказ Минтруда). Обязательно укажи номер пункта.
   - Рекомендация по устранению (императив: "Сделать", "Устранить").
4. Сформируй краткое экспертное заключение по фото.

ФОРМАТ ОТВЕТА (JSON):
{
  "is_relevant": true,
  "joke": null,
  "items": [
    {
      "defect": "Название дефекта",
      "location": "Где именно на фото",
      "criticality": "Критический",
      "cause": "Причина",
      "norm": "СП 70.13330 п. 5.17.4",
      "recommendation": "Текст рекомендации"
    }
  ],
  "expert_summary": "Текст заключения (2-3 предложения)."
}

Если фото нерелевантно:
{
  "is_relevant": false,
  "joke": "Красивый кот, но это не стройплощадка! Присылай фото строительных работ.",
  "items": [],
  "expert_summary": null
}

ВАЖНО: Отвечай ТОЛЬКО валидным JSON. Никакого дополнительного текста."""

    def __init__(self):
        genai.configure(api_key=config.GOOGLE_API_KEY)

        # Быстрая модель для проверки релевантности
        self.fast_model = genai.GenerativeModel(
            config.GEMINI_FAST_MODEL,
            generation_config={
                "temperature": 0.4,
                "response_mime_type": "application/json"
            }
        )

        # Точная модель для детального анализа дефектов
        self.analysis_model = genai.GenerativeModel(
            config.GEMINI_ANALYSIS_MODEL,
            generation_config={
                "temperature": 0.4,
                "response_mime_type": "application/json"
            }
        )

        logger.info(f"AI Service initialized. Fast model: {config.GEMINI_FAST_MODEL}, Analysis model: {config.GEMINI_ANALYSIS_MODEL}")

    async def check_relevance(self, photo_bytes: bytes, context: str = None) -> Dict[str, Any]:
        """
        Quick relevance check using Flash model (1-2 seconds)

        Args:
            photo_bytes: Photo binary data
            context: User-provided context

        Returns:
            Dictionary with is_relevant and joke (if not relevant)
        """
        try:
            logger.info(f"Quick relevance check. Context: {context}, Photo size: {len(photo_bytes)} bytes")

            # Load image
            image = Image.open(io.BytesIO(photo_bytes))
            logger.info(f"Image loaded. Size: {image.size}, Format: {image.format}")

            # Read settings
            settings = None
            if config.GOOGLE_SETTINGS_DOC_ID:
                try:
                    settings = settings_service.parse_ai_settings(config.GOOGLE_SETTINGS_DOC_ID)
                except Exception as e:
                    logger.warning(f"Failed to read settings, using defaults: {e}")

            # Prepare model and prompt
            if settings:
                relevance_model_name = settings['relevance_model']
                relevance_model = genai.GenerativeModel(
                    relevance_model_name,
                    generation_config={"temperature": 0.4, "response_mime_type": "application/json"}
                )
                system_prompt = settings['relevance_prompt'] if settings['relevance_prompt'] else self.SYSTEM_PROMPT
            else:
                relevance_model = self.fast_model
                relevance_model_name = config.GEMINI_FAST_MODEL
                system_prompt = self.SYSTEM_PROMPT

            logger.info(f"Checking relevance with {relevance_model_name}...")
            relevance_prompt = f"Контекст: {context}\n\nПроверь, является ли это фото строительным объектом. Если это кот, еда, селфи или не стройка - верни is_relevant: false с шуткой. Если это стройка - верни is_relevant: true." if context else "Проверь, является ли это фото строительным объектом."

            response = relevance_model.generate_content(
                [system_prompt, relevance_prompt, image],
                request_options={"timeout": 120}
            )

            logger.info(f"Relevance check complete")
            result = json.loads(response.text)

            return result

        except Exception as e:
            logger.error(f"Relevance check error: {str(e)}", exc_info=True)
            return {
                "is_relevant": False,
                "joke": "⚠️ Не удалось проверить фото. Попробуй еще раз.",
                "error": str(e)
            }

    async def analyze_defects(self, photo_bytes: bytes, context: str = None) -> Dict[str, Any]:
        """
        Detailed defect analysis using Pro model (10-30 seconds)

        Args:
            photo_bytes: Photo binary data
            context: User-provided context

        Returns:
            Dictionary with detailed analysis results
        """
        try:
            logger.info(f"Detailed defect analysis. Context: {context}")

            # Load image
            image = Image.open(io.BytesIO(photo_bytes))

            # Read settings
            settings = None
            if config.GOOGLE_SETTINGS_DOC_ID:
                try:
                    settings = settings_service.parse_ai_settings(config.GOOGLE_SETTINGS_DOC_ID)
                except Exception as e:
                    logger.warning(f"Failed to read settings, using defaults: {e}")

            # Prepare model and prompt
            if settings:
                analysis_model_name = settings['analysis_model']
                analysis_model = genai.GenerativeModel(
                    analysis_model_name,
                    generation_config={"temperature": 0.4, "response_mime_type": "application/json"}
                )
                system_prompt = settings['analysis_prompt'] if settings['analysis_prompt'] else self.SYSTEM_PROMPT
            else:
                analysis_model = self.analysis_model
                analysis_model_name = config.GEMINI_ANALYSIS_MODEL
                system_prompt = self.SYSTEM_PROMPT

            logger.info(f"Analyzing defects with {analysis_model_name}...")
            analysis_prompt = f"Контекст: {context}\n\nПроанализируй это фото согласно инструкции. Найди все дефекты." if context else "Проанализируй это фото согласно инструкции."

            response = analysis_model.generate_content(
                [system_prompt, analysis_prompt, image],
                request_options={"timeout": 180}
            )

            logger.info(f"Defect analysis complete")
            result = json.loads(response.text)
            result['is_relevant'] = True  # Already checked by check_relevance

            logger.info(f"Analysis complete. Defects found: {len(result.get('items', []))}")

            return result

        except Exception as e:
            logger.error(f"Defect analysis error: {str(e)}", exc_info=True)
            return {
                "is_relevant": True,
                "items": [],
                "expert_summary": None,
                "error": str(e)
            }

    async def analyze_photo(self, photo_bytes: bytes, context: str = None) -> Dict[str, Any]:
        """
        Analyze construction photo for defects using two-stage approach:
        1. Fast model checks relevance
        2. Analysis model performs detailed defect analysis (if relevant)

        Args:
            photo_bytes: Photo binary data
            context: User-provided context (e.g., "ЖК Пионер, 5 этаж")

        Returns:
            Dictionary with analysis results
        """
        try:
            logger.info(f"Starting two-stage photo analysis. Context: {context}, Photo size: {len(photo_bytes)} bytes")

            # Load image
            image = Image.open(io.BytesIO(photo_bytes))
            logger.info(f"Image loaded successfully. Size: {image.size}, Format: {image.format}")

            # Read settings from Google Docs (if configured)
            settings = None
            if config.GOOGLE_SETTINGS_DOC_ID:
                try:
                    logger.info(f"Reading AI settings from Google Doc: {config.GOOGLE_SETTINGS_DOC_ID}")
                    settings = settings_service.parse_ai_settings(config.GOOGLE_SETTINGS_DOC_ID)
                    logger.info(f"Settings loaded: relevance_model={settings['relevance_model']}, analysis_model={settings['analysis_model']}")
                except Exception as e:
                    logger.warning(f"Failed to read settings from Google Docs, using defaults: {e}")

            # Prepare models and prompts
            if settings:
                # Create models with settings from Google Docs
                relevance_model_name = settings['relevance_model']
                analysis_model_name = settings['analysis_model']

                relevance_model = genai.GenerativeModel(
                    relevance_model_name,
                    generation_config={
                        "temperature": 0.4,
                        "response_mime_type": "application/json"
                    }
                )

                analysis_model = genai.GenerativeModel(
                    analysis_model_name,
                    generation_config={
                        "temperature": 0.4,
                        "response_mime_type": "application/json"
                    }
                )

                # Use prompts from settings or defaults
                system_prompt_relevance = settings['relevance_prompt'] if settings['relevance_prompt'] else self.SYSTEM_PROMPT
                system_prompt_analysis = settings['analysis_prompt'] if settings['analysis_prompt'] else self.SYSTEM_PROMPT

                logger.info(f"Using custom models from settings: {relevance_model_name}, {analysis_model_name}")
            else:
                # Use default models and prompts
                relevance_model = self.fast_model
                analysis_model = self.analysis_model
                system_prompt_relevance = self.SYSTEM_PROMPT
                system_prompt_analysis = self.SYSTEM_PROMPT
                relevance_model_name = config.GEMINI_FAST_MODEL
                analysis_model_name = config.GEMINI_ANALYSIS_MODEL
                logger.info(f"Using default models: {relevance_model_name}, {analysis_model_name}")

            # STAGE 1: Quick relevance check with fast model
            logger.info(f"STAGE 1: Checking relevance with {relevance_model_name}...")
            relevance_prompt = f"Контекст: {context}\n\nПроверь, является ли это фото строительным объектом. Если это кот, еда, селфи или не стройка - верни is_relevant: false с шуткой. Если это стройка - верни is_relevant: true." if context else "Проверь, является ли это фото строительным объектом."

            relevance_response = relevance_model.generate_content(
                [system_prompt_relevance, relevance_prompt, image],
                request_options={"timeout": 120}  # 2 minutes timeout
            )

            logger.info(f"Relevance check complete. Response length: {len(relevance_response.text)} chars")
            logger.debug(f"Fast model response: {relevance_response.text}")

            relevance_result = json.loads(relevance_response.text)

            # If not relevant, return immediately
            if not relevance_result.get('is_relevant'):
                logger.info(f"Photo is NOT relevant. Stopping analysis.")
                return relevance_result

            # STAGE 2: Detailed analysis with analysis model
            logger.info(f"STAGE 2: Photo is relevant. Starting detailed analysis with {analysis_model_name}...")
            analysis_prompt = f"Контекст: {context}\n\nПроанализируй это фото согласно инструкции. Найди все дефекты." if context else "Проанализируй это фото согласно инструкции."

            analysis_response = analysis_model.generate_content(
                [system_prompt_analysis, analysis_prompt, image],
                request_options={"timeout": 180}  # 3 minutes timeout for detailed analysis
            )

            logger.info(f"Detailed analysis complete. Response length: {len(analysis_response.text)} chars")
            logger.debug(f"Analysis model response: {analysis_response.text}")

            # Parse response
            result = json.loads(analysis_response.text)

            logger.info(f"Analysis complete. Defects found: {len(result.get('items', []))}")

            return result

        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error in AI response: {str(e)}")
            return {
                "is_relevant": False,
                "joke": "⚠️ AI вернул некорректный ответ. Попробуй другое фото или обратись к администратору.",
                "items": [],
                "expert_summary": None,
                "error": f"JSON parse error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"AI service error: {str(e)}", exc_info=True)
            return {
                "is_relevant": False,
                "joke": "⚠️ Не удалось связаться с AI-сервисом. Попробуй через минуту или обратись к администратору.",
                "items": [],
                "expert_summary": None,
                "error": str(e)
            }

    def format_telegram_message(self, analysis: Dict[str, Any], context: str = None) -> str:
        """
        Format analysis results for Telegram message

        Args:
            analysis: Analysis results from AI
            context: Object context

        Returns:
            Formatted message string
        """
        if not analysis.get("is_relevant"):
            # Escape joke text as it may contain special characters
            joke_text = escape_markdown(analysis.get('joke', 'Фото не относится к строительству.'))
            return f"😄 {joke_text}"

        items = analysis.get("items", [])
        summary = analysis.get("expert_summary", "")

        # Escape context for safe Markdown
        safe_context = escape_markdown(context) if context else 'Не указан'

        # Build message
        msg = f"🏗 **Объект:** {safe_context}\n\n"
        msg += f"🚨 **Выявлено дефектов: {len(items)}**\n\n"

        # Add each defect
        for idx, item in enumerate(items, 1):
            criticality_emoji = {
                "Критический": "🔥",
                "Значительный": "⚠️",
                "Малозначительный": "ℹ️"
            }.get(item.get("criticality", ""), "❓")

            # Escape all AI-generated text for safe Markdown
            defect_name = escape_markdown(item.get('defect', 'Неизвестный дефект'))
            location = escape_markdown(item.get('location', 'Не указано'))
            norm = escape_markdown(item.get('norm', 'Норма не указана'))
            recommendation = escape_markdown(item.get('recommendation', 'Рекомендация не указана'))
            criticality = escape_markdown(item.get('criticality', 'Неизвестно'))

            msg += f"{idx}️⃣ **{defect_name}** ({criticality_emoji} {criticality})\n"
            msg += f"📍 *{location}*\n"
            msg += f"📜 *{norm}*\n"
            msg += f"🛠 {recommendation}\n\n"

        # Add summary (escape it too)
        if summary:
            safe_summary = escape_markdown(summary)
            msg += f"📝 **Заключение:** {safe_summary}\n\n"

        msg += "✅ **Данные сохранены в таблицу!**"

        return msg


# Global AI service instance
ai_service = AIService()
