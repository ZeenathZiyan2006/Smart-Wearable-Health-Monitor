"""
Draft Emergency Fallback Phrases Dictionary.

MANDATORY SAFETY NOTICE:
The multilingual text strings below are DEVELOPMENT PLACEHOLDERS and DRAFT REFERENCES ONLY.
They have not yet been reviewed or certified by certified clinical translators or native speakers.
They must not be considered clinically verified emergency translations.
"""

DRAFT_DICTIONARY_STATUS = "draft_unverified_development_placeholder"

DRAFT_EMERGENCY_DICTIONARY = {
    "EMERGENCY_TRIGGERED": {
        "en": "Emergency alert triggered. Assigned caregiver has been notified.",
        "kn": "ತುರ್ತು ಎಚ್ಚರಿಕೆ ರವಾನೆಯಾಗಿದೆ. ಆರೈಕೆದಾರರಿಗೆ ತಿಳಿಸಲಾಗಿದೆ.",
        "hi": "आपातकालीन अलर्ट सक्रिय हुआ। देखभालकर्ता को सूचित कर दिया गया है।",
        "ml": "അടിയന്തര മുന്നറിയിപ്പ് സജീവമായി. പരിചാരകനെ അറിയിച്ചിട്ടുണ്ട്.",
        "ta": "அவசர எச்சரிக்கை தூண்டப்பட்டது. பராமரிப்பாளருக்கு அறிவிக்கப்பட்டுள்ளது.",
        "te": "అత్యవసర హెచ్చరిక ప్రేరేపించబడింది. సంరక్షకుడికి తెలియజేయబడింది.",
        "ur": "ہنگامی الرٹ فعال ہو گیا۔ نگہداشت کنندہ کو مطلع کر دیا گیا ہے۔",
    },
    "FALL_DETECTED": {
        "en": "Fall impact detected. Are you okay?",
        "kn": "ಬಿದ್ದಿರುವುದು ಪತ್ತೆಯಾಗಿದೆ. ನೀವು ಕ್ಷೇಮವಾಗಿದ್ದೀರಾ?",
        "hi": "गिरने का झटका लगा है। क्या आप ठीक हैं?",
        "ml": "വീഴ്ച കണ്ടെത്തി. താങ്കൾക്ക് കുഴപ്പമൊന്നുമില്ലല്ലോ?",
        "ta": "கீழே விழுந்தது கண்டறியப்பட்டது. நீங்கள் நலமாக உள்ளீர்களா?",
        "te": "కిందపడటం గుర్తించబడింది. మీరు క్షేమంగా ఉన్నారా?",
        "ur": "گرنے کا پتہ چلا ہے۔ کیا آپ خیریت سے ہیں؟",
    },
    "VITAL_ANOMALY": {
        "en": "High heart rate observed. Please sit down and rest.",
        "kn": "ಹೆಚ್ಚಿನ ಹೃದಯ ಬಡಿತ ಕಂಡುಬಂದಿದೆ. ದಯವಿಟ್ಟು ಕುಳಿತು ವಿಶ್ರಾಂತಿ ಪಡೆಯಿರಿ.",
        "hi": "उच्च हृदय गति देखी गई। कृपया बैठें और आराम करें।",
        "ml": "ഉയർന്ന ഹൃദയമിടിപ്പ് രേഖപ്പെടുത്തി. ദയവായി ഇരുന്ന് വിശ്രമിക്കുക.",
        "ta": "அதிக இதயத் துடிப்பு கண்டறியப்பட்டது. தயவுசெய்து அமர்ந்து ஓய்வெடுக்கவும்.",
        "te": "అధిక హృదయ స్పందన గమనించబడింది. దయచేసి కూర్చుని విశ్రాంతి తీసుకోండి.",
        "ur": "دل کی تیز دھڑکن دیکھی گئی۔ برائے کرم بیٹھ کر آرام کریں۔",
    },
    "SAFE_NORMAL": {
        "en": "All vital signs are normal and stable.",
        "kn": "ಎಲ್ಲಾ ಆರೋಗ್ಯ ಲಕ್ಷಣಗಳು ಸಾಮಾನ್ಯ ಮತ್ತು ಸ್ಥಿರವಾಗಿವೆ.",
        "hi": "सभी स्वास्थ्य संकेत सामान्य और स्थिर हैं।",
        "ml": "എല്ലാ ആരോഗ്യ സൂചകങ്ങളും സാധാരണ നിലയിലാണ്.",
        "ta": "அனைத்து உடல்நிலைக் குறிகளும் இயல்பாகவும் சீராகவும் உள்ளன.",
        "te": "అన్ని కీలక ఆరోగ్య సంకేతాలు సాధారణంగా ఉన్నాయి.",
        "ur": "تمام علامات صحت معمول پر ہیں۔",
    },
}


def get_draft_emergency_phrase(phrase_key: str, language_code: str) -> str:
    """
    Returns draft reference localized phrase for standard safety notifications.
    Falls back to English if language or key is unmapped.
    """
    lang = language_code.lower()
    phrase_dict = DRAFT_EMERGENCY_DICTIONARY.get(phrase_key)
    if not phrase_dict:
        return f"[Draft safety notice]: {phrase_key}"

    return phrase_dict.get(lang, phrase_dict.get("en", f"[Draft safety notice]: {phrase_key}"))
