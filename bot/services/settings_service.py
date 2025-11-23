"""
Settings service for reading configuration from Google Docs
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Dict, Optional
import config
import logging

logger = logging.getLogger(__name__)


class SettingsService:
    """Service for reading settings from Google Docs"""

    SCOPES = [
        'https://www.googleapis.com/auth/documents.readonly',
        'https://www.googleapis.com/auth/drive.readonly'
    ]

    def __init__(self):
        self.credentials = service_account.Credentials.from_service_account_file(
            config.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=self.SCOPES
        )
        self.docs_service = build('docs', 'v1', credentials=self.credentials)
        self._cache = {}
        self._cache_enabled = True

    def read_settings_document(self, document_id: str) -> str:
        """
        Read settings document from Google Docs

        Args:
            document_id: Google Docs document ID

        Returns:
            Full text content of the document
        """
        try:
            # Check cache
            if self._cache_enabled and document_id in self._cache:
                logger.info(f"Using cached settings for document {document_id}")
                return self._cache[document_id]

            # Fetch document
            document = self.docs_service.documents().get(documentId=document_id).execute()

            # Extract text content
            content = []
            for element in document.get('body', {}).get('content', []):
                if 'paragraph' in element:
                    for text_run in element['paragraph'].get('elements', []):
                        if 'textRun' in text_run:
                            content.append(text_run['textRun']['content'])

            full_text = ''.join(content)

            # Cache the result
            if self._cache_enabled:
                self._cache[document_id] = full_text

            logger.info(f"Successfully read settings document {document_id}")
            return full_text

        except Exception as e:
            logger.error(f"Error reading settings document {document_id}: {e}")
            # Return cached value if available
            if document_id in self._cache:
                logger.warning(f"Returning cached settings due to error")
                return self._cache[document_id]
            raise

    def parse_ai_settings(self, document_id: str) -> Dict[str, str]:
        """
        Parse AI settings from Google Docs document

        Expected format:
        0.0.1
        ---
        RELEVANCE_MODEL: gemini-2.5-flash
        ANALYSIS_MODEL: gemini-2.5-pro
        ---
        RELEVANCE_PROMPT:
        [prompt text here]
        ---
        ANALYSIS_PROMPT:
        [prompt text here]
        ---

        Args:
            document_id: Google Docs document ID

        Returns:
            Dict with keys: prompt_version, relevance_model, analysis_model, relevance_prompt, analysis_prompt
        """
        try:
            content = self.read_settings_document(document_id)

            settings = {
                'prompt_version': 'unknown',  # default
                'relevance_model': config.GEMINI_FAST_MODEL,
                'analysis_model': config.GEMINI_ANALYSIS_MODEL,
                'relevance_prompt': None,
                'analysis_prompt': None
            }

            # Extract version from first line (before first ---)
            if '---' in content:
                version_section, rest = content.split('---', 1)
                version_line = version_section.strip()
                if version_line:
                    # First non-empty line is the version
                    settings['prompt_version'] = version_line.split('\n')[0].strip()
                content = rest  # Use rest for parsing sections

            # Parse sections
            sections = content.split('---')

            for section in sections:
                section = section.strip()
                if not section:
                    continue

                # Parse model settings
                if 'RELEVANCE_MODEL:' in section:
                    for line in section.split('\n'):
                        if line.strip().startswith('RELEVANCE_MODEL:'):
                            settings['relevance_model'] = line.split(':', 1)[1].strip()
                        elif line.strip().startswith('ANALYSIS_MODEL:'):
                            settings['analysis_model'] = line.split(':', 1)[1].strip()

                # Parse prompts
                elif section.startswith('RELEVANCE_PROMPT:'):
                    prompt_text = section.replace('RELEVANCE_PROMPT:', '', 1).strip()
                    if prompt_text:
                        settings['relevance_prompt'] = prompt_text

                elif section.startswith('ANALYSIS_PROMPT:'):
                    prompt_text = section.replace('ANALYSIS_PROMPT:', '', 1).strip()
                    if prompt_text:
                        settings['analysis_prompt'] = prompt_text

            logger.info(f"Parsed AI settings: version={settings['prompt_version']}, models={settings['relevance_model']}, {settings['analysis_model']}")
            return settings

        except Exception as e:
            logger.error(f"Error parsing AI settings: {e}")
            # Return defaults
            return {
                'prompt_version': 'unknown',
                'relevance_model': config.GEMINI_FAST_MODEL,
                'analysis_model': config.GEMINI_ANALYSIS_MODEL,
                'relevance_prompt': None,
                'analysis_prompt': None
            }

    def clear_cache(self):
        """Clear the settings cache"""
        self._cache.clear()
        logger.info("Settings cache cleared")

    def disable_cache(self):
        """Disable caching (read from Google Docs every time)"""
        self._cache_enabled = False
        logger.info("Settings cache disabled")

    def enable_cache(self):
        """Enable caching"""
        self._cache_enabled = True
        logger.info("Settings cache enabled")


# Global settings service instance
settings_service = SettingsService()
