import logging
import unicodedata
from typing import Dict, Optional, Tuple

from app.core.config import settings
from app.schemas.voice import (
    REAL_TRANSLATION_DISCLAIMER,
    SUPPORTED_LANGUAGE_CODES,
)
from app.services.voice.adapters.base import BaseTranslationAdapter, TranslationResult

logger = logging.getLogger("pulseguardian.voice.translation")

# Mapping from ISO-639-1 code to IndicTrans2 language-script identifier
INDICTRANS2_LANG_MAP: Dict[str, str] = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "kn": "kan_Knda",
    "ml": "mal_Mlym",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "ur": "urd_Arab",
}

# IndicTrans2 checkpoint directional models
INDICTRANS2_CHECKPOINTS = {
    "indic-en": {
        "model_id": "ai4bharat/indictrans2-indic-en-1B",
        "distilled_id": "ai4bharat/indictrans2-indic-en-dist-200M",
        "supported_sources": ["hi", "kn", "ml", "ta", "te", "ur"],
        "supported_targets": ["en"],
        "description": "Translates from 22 Indic languages to English only.",
    },
    "en-indic": {
        "model_id": "ai4bharat/indictrans2-en-indic-1B",
        "distilled_id": "ai4bharat/indictrans2-en-indic-dist-200M",
        "supported_sources": ["en"],
        "supported_targets": ["hi", "kn", "ml", "ta", "te", "ur"],
        "description": "Translates from English to 22 Indic languages only.",
    },
    "indic-indic": {
        "model_id": "ai4bharat/indictrans2-indic-indic-1B",
        "distilled_id": "ai4bharat/indictrans2-indic-indic-dist-320M",
        "supported_sources": ["hi", "kn", "ml", "ta", "te", "ur"],
        "supported_targets": ["hi", "kn", "ml", "ta", "te", "ur"],
        "description": "Translates between Indic languages. Does not support English as source or target.",
    },
}


def detect_script_language(text: str) -> Tuple[Optional[str], bool]:
    """
    Best-effort Unicode script detection for candidate text.
    In accordance with safety requirements:
    - Latin script is NOT automatically confirmed as English (could be Spanish, French, or transliterated Hinglish/Tanglish).
    - Devanagari script is NOT automatically confirmed as Hindi (could be Marathi, Sanskrit, Nepali).
    - Perso-Arabic script is NOT automatically confirmed as Urdu (could be Arabic, Persian, Kashmiri, Sindhi).
    Returns (tentative_language_code, is_uncertain: bool).
    If language is ambiguous or unresolvable, returns ("uncertain", True).
    """
    if not text or not text.strip():
        return None, True

    counts = {
        "kn": 0,  # Kannada
        "hi": 0,  # Devanagari
        "ml": 0,  # Malayalam
        "ta": 0,  # Tamil
        "te": 0,  # Telugu
        "ur": 0,  # Arabic / Perso-Arabic
        "en": 0,  # Latin
        "other": 0,
    }

    for char in text:
        cp = ord(char)
        if 0x0C80 <= cp <= 0x0CFF:
            counts["kn"] += 1
        elif 0x0900 <= cp <= 0x097F:
            counts["hi"] += 1
        elif 0x0D00 <= cp <= 0x0D7F:
            counts["ml"] += 1
        elif 0x0B80 <= cp <= 0x0BFF:
            counts["ta"] += 1
        elif 0x0C00 <= cp <= 0x0C7F:
            counts["te"] += 1
        elif 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F or 0xFB50 <= cp <= 0xFDFF:
            counts["ur"] += 1
        elif (0x0041 <= cp <= 0x005A) or (0x0061 <= cp <= 0x007A):
            counts["en"] += 1
        elif unicodedata.category(char).startswith("L"):
            counts["other"] += 1

    total_letters = sum(counts.values())
    if total_letters == 0:
        return None, True

    # Check for dominant script (> 40% of alphabetical characters)
    for lang, cnt in counts.items():
        if cnt / total_letters >= 0.40:
            if lang in ("kn", "ml", "ta", "te"):
                # Regional Dravidian scripts have strong 1:1 script-to-language association in this context
                return lang, False
            elif lang in ("hi", "ur", "en"):
                # Multi-language scripts (Devanagari, Perso-Arabic, Latin) are best-effort and flagged as uncertain
                return lang, True
            elif lang == "other":
                return "uncertain", True

    return "uncertain", True


class HostedTranslationAdapter(BaseTranslationAdapter):
    """
    Hosted Neural Text Translation Adapter.
    Translates between the 7 supported languages (kn, en, hi, ml, ta, te, ur) over TLS
    using a hosted LLM / NMT API (e.g. OpenAI GPT-4o-mini or a hosted IndicTrans2 endpoint).
    Masks API keys and never logs sensitive personal health text.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ):
        self.api_key = api_key if api_key is not None else (settings.TRANSLATION_API_KEY or settings.OPENAI_API_KEY)
        self.api_base = api_base or settings.TRANSLATION_API_BASE
        self.model_name = model_name or settings.TRANSLATION_MODEL_NAME
        self.timeout_seconds = timeout_seconds

    def translate(
        self,
        text: str,
        source_language: Optional[str],
        target_language: str,
    ) -> TranslationResult:
        if not text or not text.strip():
            raise ValueError("Translation source text cannot be empty.")

        if len(text) > settings.VOICE_MAX_TRANSLATION_CHARS:
            raise ValueError(
                f"Translation text length ({len(text)} chars) exceeds maximum limit of "
                f"{settings.VOICE_MAX_TRANSLATION_CHARS} characters."
            )

        if not self.api_key or not self.api_key.strip():
            raise RuntimeError(
                "TRANSLATION_API_KEY (or OPENAI_API_KEY) is not configured for hosted translation."
            )

        tgt = target_language.lower().strip()
        if tgt not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(f"Unsupported target language '{target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}")

        # Source language handling & best-effort script detection
        uncertain_translation = False
        if source_language:
            src = source_language.lower().strip()
            if src not in SUPPORTED_LANGUAGE_CODES:
                raise ValueError(f"Unsupported source language '{source_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}")
        else:
            detected_src, is_uncertain = detect_script_language(text)
            if detected_src == "uncertain" or not detected_src:
                src = "uncertain"
                uncertain_translation = True
            else:
                src = detected_src
                if is_uncertain:
                    uncertain_translation = True

        # If source equals target and not uncertain, return directly
        if src == tgt and not uncertain_translation:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=src,
                target_language=tgt,
                confidence=None,
                provider="hosted_translation",
                is_mock=False,
                disclaimer=REAL_TRANSLATION_DISCLAIMER,
                uncertain_translation=False,
            )

        # Language display names for translation prompt
        lang_names = {
            "kn": "Kannada",
            "en": "English",
            "hi": "Hindi",
            "ml": "Malayalam",
            "ta": "Tamil",
            "te": "Telugu",
            "ur": "Urdu",
            "uncertain": "the detected source language",
        }
        target_name = lang_names.get(tgt, tgt)
        source_name = lang_names.get(src, src)

        system_prompt = (
            f"You are a professional medical assistant translator. "
            f"Translate the following text accurately from {source_name} to {target_name}. "
            f"Maintain clinical clarity, polite patient tone, and preserve medical numbers/vitals exactly. "
            f"Output ONLY the translated text without commentary, explanation, quotation marks, or notes."
        )

        import httpx

        url = f"{self.api_base.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        data = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        }

        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=data)
        except httpx.TimeoutException:
            logger.error("Hosted translation request timed out.")
            raise TimeoutError("Hosted translation service timed out.")
        except httpx.RequestError as exc:
            logger.error(f"Hosted translation network error: {exc.__class__.__name__}")
            raise ConnectionError(f"Network error communicating with translation provider: {exc.__class__.__name__}")

        if response.status_code == 401:
            raise RuntimeError("Hosted translation authentication failed: Invalid API credentials.")
        elif response.status_code == 429:
            raise RuntimeError("Hosted translation rate limit or quota exceeded.")
        elif response.status_code >= 400:
            raise ConnectionError(f"Hosted translation provider error with status {response.status_code}")

        try:
            res_json = response.json()
            translated = res_json["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            raise ConnectionError(f"Invalid JSON response from hosted translation provider: {exc}")

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=src,
            target_language=tgt,
            confidence=None,  # Neural translation does not provide calibrated sentence confidence
            provider="hosted_translation",
            is_mock=False,
            disclaimer=REAL_TRANSLATION_DISCLAIMER,
            uncertain_translation=uncertain_translation,
        )


class IndicTrans2TranslationAdapter(BaseTranslationAdapter):
    """
    Local AI4Bharat IndicTrans2 Neural Machine Translation Adapter.
    Uses partitioned checkpoints based on translation direction:
    - indic-en (Indic to English)
    - en-indic (English to Indic)
    - indic-indic (Indic to Indic)
    Loads models lazily. If PyTorch or transformers are missing, raises RuntimeError.
    """

    def __init__(self, model_dir: Optional[str] = None):
        self.model_dir = model_dir or settings.INDICTRANS_MODEL_DIR
        self._models = {}
        self._tokenizers = {}

    def _get_direction(self, src: str, tgt: str) -> str:
        """Determines required IndicTrans2 directional checkpoint."""
        if src in ("hi", "kn", "ml", "ta", "te", "ur") and tgt == "en":
            return "indic-en"
        elif src == "en" and tgt in ("hi", "kn", "ml", "ta", "te", "ur"):
            return "en-indic"
        elif src in ("hi", "kn", "ml", "ta", "te", "ur") and tgt in ("hi", "kn", "ml", "ta", "te", "ur"):
            return "indic-indic"
        else:
            raise ValueError(f"Language pair {src} -> {tgt} is not supported by IndicTrans2 directional models.")

    def _load_model(self, direction: str):
        """Lazily imports transformers/torch and loads directional model weights."""
        if direction not in self._models:
            try:
                import torch
                from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
            except ImportError as err:
                raise RuntimeError(
                    "IndicTrans2 dependencies (torch, transformers) are not installed. "
                    "Install PyTorch and Transformers or configure VOICE_TRANSLATION_PROVIDER=mock_development."
                ) from err

            checkpoint_info = INDICTRANS2_CHECKPOINTS[direction]
            model_id = checkpoint_info["model_id"]
            logger.info(f"Loading IndicTrans2 direction='{direction}' model='{model_id}'")

            try:
                tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_id, trust_remote_code=True)
                self._tokenizers[direction] = tokenizer
                self._models[direction] = model
            except Exception as exc:
                raise RuntimeError(f"Failed to load IndicTrans2 model '{model_id}': {exc}") from exc

        return self._models[direction], self._tokenizers[direction]

    def translate(
        self,
        text: str,
        source_language: Optional[str],
        target_language: str,
    ) -> TranslationResult:
        if not text or not text.strip():
            raise ValueError("Translation source text cannot be empty.")

        if len(text) > settings.VOICE_MAX_TRANSLATION_CHARS:
            raise ValueError(
                f"Translation text length ({len(text)} chars) exceeds maximum limit of "
                f"{settings.VOICE_MAX_TRANSLATION_CHARS} characters."
            )

        tgt = target_language.lower().strip()
        if tgt not in SUPPORTED_LANGUAGE_CODES:
            raise ValueError(f"Unsupported target language '{target_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}")

        uncertain_translation = False
        if source_language:
            src = source_language.lower().strip()
            if src not in SUPPORTED_LANGUAGE_CODES:
                raise ValueError(f"Unsupported source language '{source_language}'. Supported: {', '.join(SUPPORTED_LANGUAGE_CODES)}")
        else:
            detected_src, is_uncertain = detect_script_language(text)
            if detected_src == "uncertain" or not detected_src:
                src = "uncertain"
                uncertain_translation = True
            else:
                src = detected_src
                if is_uncertain:
                    uncertain_translation = True

        if src == "uncertain":
            raise ValueError(
                "Source language could not be determined unambiguously. Please provide explicit source_language."
            )

        if src == tgt:
            return TranslationResult(
                original_text=text,
                translated_text=text,
                source_language=src,
                target_language=tgt,
                confidence=None,
                provider="local_indictrans",
                is_mock=False,
                disclaimer=REAL_TRANSLATION_DISCLAIMER,
                uncertain_translation=False,
            )

        direction = self._get_direction(src, tgt)
        model, tokenizer = self._load_model(direction)

        src_tag = INDICTRANS2_LANG_MAP[src]
        tgt_tag = INDICTRANS2_LANG_MAP[tgt]

        try:
            inputs = tokenizer(f"{src_tag} {text}", return_tensors="pt")
            outputs = model.generate(**inputs, max_length=256)
            translated = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        except Exception as exc:
            logger.error(f"IndicTrans2 translation failed: {exc.__class__.__name__}")
            raise RuntimeError(f"IndicTrans2 translation inference failed: {exc.__class__.__name__}") from exc

        return TranslationResult(
            original_text=text,
            translated_text=translated,
            source_language=src,
            target_language=tgt,
            confidence=None,
            provider="local_indictrans",
            is_mock=False,
            disclaimer=REAL_TRANSLATION_DISCLAIMER,
            uncertain_translation=uncertain_translation,
        )
