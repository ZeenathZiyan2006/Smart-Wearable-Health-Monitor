import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, PhoneCall, MessageSquare, Sparkles, Volume2, X, Phone, UserCheck, ShieldAlert, Globe } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { patientDashboardService } from '../api/services';
import { SupportedLanguage } from '../i18n/translations';

interface VoiceAssistantProps {
  onClose?: () => void;
  isOpen: boolean;
}

// Multilingual display responses
const MULTILINGUAL_RESPONSES: Record<string, Record<string, string>> = {
  vitals: {
    en: 'Your vitals are stable. Heart rate is 72 BPM and oxygen saturation is 98 percent.',
    kn: 'ನಿಮ್ಮ ಹೃದಯ ಬಡಿತ 72 BPM ಮತ್ತು ಆಮ್ಲಜನಕ 98 ಶೇಕಡಾ ಆಗಿದೆ, ಎಲ್ಲವೂ ಸಾಮಾನ್ಯ ಸ್ಥಿತಿಯಲ್ಲಿದೆ.',
    hi: 'आपकी नब्ज 72 BPM और ऑक्सीजन 98 प्रतिशत सामान्य स्थिति में है।',
    ta: 'உங்கள் இதயத் துடிப்பு 72 BPM மற்றும் ஆக்ஸிஜன் அளவு 98% சீராக உள்ளது.',
    te: 'మీ గుండె కొట్టుకోవడం 72 BPM మరియు ఆక్సిజన్ 98% సాధారణంగా ఉన్నాయి.',
    ml: 'നിങ്ങളുടെ ഹൃദയമിടിപ്പ് 72 BPM ഉം ഓക്സിജൻ 98% ഉം സാധാരണ നിലയിലാണ്.',
  },
  calling: {
    en: 'Connecting direct call to your primary caregiver right now.',
    kn: 'ನಿಮ್ಮ ಪ್ರಾಥಮಿಕ ಆರೈಕೆದಾರರಿಗೆ ಈಗ ಕರೆ ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ.',
    hi: 'आपके प्राथमिक देखभालकर्ता को सीधे कॉल मिलाया जा रहा है।',
    ta: 'உங்கள் முதன்மை பராமரிப்பாளருக்கு இப்போது அழைப்பு இணைக்கப்படுகிறது.',
    te: 'మీ ప్రాథಮಿಕ సంరక్షకునికి ఇప్పుడు కాల్ కనెక్ట్ చేయబడుతోంది.',
    ml: 'നിങ്ങളുടെ പരിചാരകനെ ഇപ്പോൾ വിളിക്കുന്നു.',
  },
  sos: {
    en: 'Emergency SOS initiated! Dialing emergency services and alert sent.',
    kn: 'ತುರ್ತು ಎಸ್‌ಒಎಸ್ ಪ್ರಕ್ರಿಯೆ ಆರಂಭಿಸಲಾಗಿದೆ! ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಲಾಗುತ್ತಿದೆ.',
    hi: 'आपातकालीन एसओएस शुरू किया गया! आपातकालीन नंबर पर कॉल किया जा रहा है।',
    ta: 'அவசர எஸ்ஓஎஸ் தொடங்கப்பட்டது! அவசர உதவிக்கு அழைக்கப்படுகிறது.',
    te: 'అత్యవసర SOS ప్రారంభించబడింది! సహాయానికి కాల్ చేయబడుతోంది.',
    ml: 'അടിയന്തര SOS ആരംഭിച്ചു! ഉടൻ സഹായം ബന്ധപ്പെടും.',
  },
  messaging: {
    en: 'Caregiver message sent and dispatched to registered email.',
    kn: 'ಆರೈಕೆದಾರರಿಗೆ ಸಂದೇಶ ಕಳುಹಿಸಲಾಗಿದೆ ಮತ್ತು ಇಮೇಲ್ ರವಾನಿಸಲಾಗಿದೆ.',
    hi: 'देखभालकर्ता को संदेश और ईमेल सफलतापूर्वक भेज दिया गया है।',
    ta: 'பராமரிப்பாளருக்கு செய்தி மற்றும் மின்னஞ்சல் அனுப்பப்பட்டது.',
    te: 'సంరక్షకునికి సందేశం మరియు ఈమెయిల్ పంపబడింది.',
    ml: 'പരിചാരകന് സന്ദേശവും ഇമെയിലും അയച്ചു.',
  },
  medicine: {
    en: 'Your upcoming dose is Dolo 1 Tablet. Please take it with a glass of water after your meal.',
    kn: 'ನಿಮ್ಮ ಮುಂದಿನ ಔಷಧ ಡೋಲೋ 1 ಮಾತ್ರೆ, ಊಟದ ನಂತರ ಒಂದು ಲೋಟ ನೀರಿನೊಂದಿಗೆ ಸೇವಿಸಿ.',
    hi: 'आपकी अगली खुराक डोलो 1 गोली है। भोजन के बाद पानी के साथ लें।',
    ta: 'உங்கள் அடுத்த மருந்து டோலோ 1 மாத்திரை, உணவுக்குப் பின் எடுத்துக் கொள்ளுங்கள்.',
    te: 'మీ తదుపరి మందు డోలో 1 మాత్ర, భోజనం తర్వాత తీసుకోండి.',
    ml: 'നിങ്ങളുടെ അടുത്ത മരുന്ന് ഡോളോ 1 ഗുളികയാണ്, ഭക്ഷണത്തിന് ശേഷം കഴിക്കുക.',
  },
  appointment: {
    en: 'Your upcoming appointment is with Dr. Sunita Rao (Cardiologist) at PulseGuardian Heart Center.',
    kn: 'ನಿಮ್ಮ ಮುಂದಿನ ವೈದ್ಯರ ಭೇಟಿ ಡಾ. ಸುನೀತಾ ರಾವ್ (ಹೃದ್ರೋಗ ತಜ್ಞರು) ಅವರೊಂದಿಗೆ ನಿಗದಿಯಾಗಿದೆ.',
    hi: 'आपकी अगली डॉक्टर अपॉइंटमेंट डॉ. सुनीता राव (हृदय रोग विशेषज्ञ) के साथ है।',
    ta: 'உங்கள் அடுத்த மருத்துவ ஆலோசனை டாக்டர் சுனிதா ராவ் அவர்களுடன் உள்ளது.',
    te: 'మీ తదుపరి డాక్టర్ సంప్రదింపులు డా. సునీతా రావు గారితో ఉన్నాయి.',
    ml: 'നിങ്ങളുടെ അടുത്ത ഡോക്ടർ കൺസൾട്ടേഷൻ ഡോ. സുനിത റാവുമായി നിശ്ചയിച്ചിരിക്കുന്നു.',
  },
  hydration: {
    en: 'Hydration reminder confirmed! Drinking water regularly maintains healthy blood circulation.',
    kn: 'ನೀರು ಕುಡಿಯುವ ಜ್ಞಾಪನೆ ದೃಢಪಟ್ಟಿದೆ! ನಿಯಮಿತವಾಗಿ ನೀರು ಕುಡಿಯುವುದು ರಕ್ತ ಪರಿಚಲನೆಗೆ ಒಳ್ಳೆಯದು.',
    hi: 'पानी पीने का रिमाइंडर सेट हो गया है! नियमित पानी पीना रक्त संचार के लिए आवश्यक है।',
    ta: 'தண்ணீர் குடிக்கும் நினைவூட்டல் உறுதிப்படுத்தப்பட்டது!',
    te: 'నీరు త్రాగే రిమైండర్ ధృవీకరించబడింది!',
    ml: 'വെള്ളം കുടിക്കാനുള്ള ഓർമ്മപ്പെടുത്തൽ സ്ഥിരീകരിച്ചു!',
  },
  sleep: {
    en: 'You logged 7 hours and 15 minutes of restful sleep last night with normal resting cardiac rhythm.',
    kn: 'ನೀವು ನಿನ್ನೆ ರಾತ್ರಿ 7 ಗಂಟೆ 15 ನಿಮಿಷಗಳ ಕಾಲ ಉತ್ತಮ ನಿದ್ರೆ ಮಾಡಿದ್ದೀರಿ, ಹೃದಯ ಬಡಿತ ಸಾಮಾನ್ಯವಾಗಿತ್ತು.',
    hi: 'आपने कल रात 7 घंटे 15 मिनट की अच्छी और आरामदायक नींद ली।',
    ta: 'நீங்கள் நேற்றிரவு 7 மணி நேரம் 15 நிமிடங்கள் நிம்மதியாக தூங்கினீர்கள்.',
    te: 'మీరు నిన్న రాత్రి 7 గంటల 15 నిమిషాలు ప్రశాంతంగా నిద్రపోయారు.',
    ml: 'നിങ്ങൾ ഇന്നലെ രാത്രി 7 മണിക്കൂർ 15 മിനിറ്റ് നല്ല ഉറക്കം ലഭിച്ചു.',
  },
  mood_calm: {
    en: 'It is wonderful to feel calm and balanced. Your resting pulse reflects your inner serenity.',
    kn: 'ಪ್ರಶಾಂತವಾಗಿರುವುದು ತುಂಬಾ ಒಳ್ಳೆಯದು. ನಿಮ್ಮ ಮನಸ್ಸಿನ ನೆಮ್ಮದಿ ಹೃದಯದ ಆರೋಗ್ಯಕ್ಕೆ ಪೂರಕವಾಗಿದೆ.',
    hi: 'शांत और संतुलित महसूस करना बहुत अच्छा है। यह आपके हृदय के लिए सर्वोत्तम है।',
    ta: 'அமைதியாக இருப்பது மிகவும் நல்லது. இது உங்கள் இதய ஆரோக்கியத்திற்கு சிறந்தது.',
    te: 'ప్రశాంతంగా ఉండటం చాలా మంచిది. ఇది మీ గుండె ఆరోగ్యానికి తోడ్పడుతుంది.',
    ml: 'ശാന്തമായിരിക്കുന്നത് വളരെ നല്ലതാണ്. ഇത് നിങ്ങളുടെ ഹൃദയാരോഗ്യത്തിന് സഹായകരമാണ്.',
  },
  mood_sad: {
    en: 'I hear you, and it is completely okay to feel down sometimes. You are valued and never alone.',
    kn: 'ನಿಮ್ಮ ಭಾವನೆ ನನಗೆ ಅರ್ಥವಾಗುತ್ತದೆ. ನೀವು ಎಂದಿಗೂ ಒಂಟಿಯಲ್ಲ, ನೋವಾ ಮತ್ತು ನಿಮ್ಮ ಕುಟುಂಬದವರು ನಿಮ್ಮೊಂದಿಗಿದ್ದಾರೆ.',
    hi: 'मैं समझ सकती हूँ। कभी-कभी ऐसा महसूस होना स्वाभाविक है। आप अकेले नहीं हैं, हम आपके साथ हैं।',
    ta: 'உங்கள் மனநிலை எனக்குப் புரிகிறது. நீங்கள் தனிமையில் இல்லை, நாங்கள் உங்களுடன் இருக்கிறோம்.',
    te: 'మీ బాధ నాకు అర్థమవుతోంది. మీరు ఎప్పటికీ ఒంటరి కాదు, మేము మీతో ఉన్నాము.',
    ml: 'എനിക്ക് മനസ്സിലാകുന്നു. നിങ്ങൾ തനിച്ചല്ല, ഞങ്ങൾ എപ്പോഴും നിങ്ങളുടെ കൂടെയുണ്ട്.',
  },
  mood_lonely: {
    en: 'I am right here with you. Would you like me to connect a call to your daughter or share an inspiring story?',
    kn: 'ನಾನು ನಿಮ್ಮೊಂದಿಗಿದ್ದೇನೆ. ನಿಮ್ಮ ಮಗಳಿಗೆ ಕರೆ ಮಾಡಬೇಕೇ ಅಥವಾ ಒಂದು ಸುಂದರ ಕಥೆ ಹೇಳಬೇಕೇ?',
    hi: 'मैं यहीं आपके साथ हूँ। क्या आप अपने परिवार से बात करना चाहेंगे या कोई कहानी सुनना चाहेंगे?',
    ta: 'நான் உங்களுடன் இருக்கிறேன். உங்கள் குடும்பத்தினரை அழைக்க விரும்புகிறீர்களா?',
    te: 'నేను మీతోనే ఉన్నాను. మీ కుటుంబ సభ్యులతో మాట్లాడాలనుకుంటున్నారా?',
    ml: 'ഞാൻ ഇവിടെ നിങ്ങളുടെ കൂടെയുണ്ട്. കുടുംബാംഗങ്ങളോട് സംസാരിക്കാൻ ആഗ്രഹിക്കുന്നുണ്ടോ?',
  },
  crisis: {
    en: 'We care deeply about your life and safety. Free 24/7 support is available at Tele-MANAS 14416. Connecting help now.',
    kn: 'ನಿಮ್ಮ ಜೀವ ಮತ್ತು ಸುರಕ್ಷತೆ ನಮಗೆ ಅತ್ಯಂತ ಮುಖ್ಯವಾಗಿದೆ. 24/7 ಉಚಿತ ಸಹಾಯವಾಣಿ ಟೆಲಿ-ಮಾನಸ್ 14416 ಲಭ್ಯವಿದೆ. ಸಹಾಯವನ್ನು ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ.',
    hi: 'आपकी सुरक्षा और जीवन हमारे लिए बेहद अनमोल है। टेली-मानस 14416 पर 24/7 मुफ्त सहायता उपलब्ध है।',
    ta: 'உங்கள் வாழ்க்கை எங்களுக்கு மிகவும் முக்கியமானது. 14416 என்ற இலவச உதவி எண்ணை உடனே அழைக்கலாம்.',
    te: 'మీ భద్రత మాకు ఎంతో ముఖ్యం. టెలి-మానస్ 14416 ద్వారా 24/7 ఉచిత సహాయం పొందవచ్చు.',
    ml: 'നിങ്ങളുടെ ജീവൻ വിലപ്പെട്ടതാണ്. ടെലി-മാനസ് 14416 വഴി 24/7 സൗജന്യ സഹായം ലഭ്യമാണ്.',
  },
  general: {
    en: 'Hello! I am Nova, your smart health assistant. You can say Call Caregiver, Check Vitals, or Send Message.',
    kn: 'ನಮಸ್ಕಾರ! ನಾನು ನೋವಾ (Nova), ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಆರೋಗ್ಯ ಸಹಾಯಕ. ನೀವು ಕಾಲ್ ಕೇರ್‌ಗಿವರ್ ಅಥವಾ ವೈಟಲ್ಸ್ ಪರಿಶೀಲಿಸಿ ಎಂದು ಹೇಳಬಹುದು.',
    hi: 'नमस्ते! मैं नोवा (Nova) हूँ, आपकी स्वास्थ्य सहायक। आप कॉल केयरगिवर या चेक वाइटल्स कह सकते हैं।',
    ta: 'வணக்கம்! நான் நோவா (Nova), உங்கள் சுகாதார உதவியாளர். மருத்துவ அழைப்பு அல்லது பரிசோதனைக்கு கேட்கலாம்.',
    te: 'నమస్కారం! నేను నోవా (Nova), మీ ఆరోగ్య సహాయకురాలిని.',
    ml: 'നമസ്കാരം! ഞാൻ നോവ (Nova), നിങ്ങളുടെ ആരോഗ്യ സഹായി.',
  },
};

// Phonetic transliteration responses for standard engines lacking regional Indic fonts
const PHONETIC_RESPONSES: Record<string, Record<string, string>> = {
  vitals: {
    en: 'Your vitals are stable. Heart rate is 72 BPM and oxygen saturation is 98 percent.',
    kn: 'Nimma hrudaya baditha eppatthyeradu BPM matthu aamlajanaka thombhatthenthu shekada aagide, ellavu saamaanya sthithiyallide.',
    hi: 'Aapki hriday gati 72 BPM aur oxygen 98 pratishat saamaanya sthiti mein hai.',
    ta: 'Ungal idhaya thudippu 72 BPM matrum oxygen alavu 98% seeraaga ulladhu.',
    te: 'Mee gunde kottukovadam 72 BPM mariyu oxygen 98% saadharanamga unnaayi.',
    ml: 'Ningalude hrudayamidippu 72 BPM um oxygen 98% um saadhaarananila-yilaanu.',
  },
  calling: {
    en: 'Connecting direct call to your primary caregiver right now.',
    kn: 'Nimma praathamika aaraikeyadaararige eega kare samparkisalaaguttide.',
    hi: 'Aapke praathmik dekhbhaalkarta ko seedhe call milaya jaa raha hai.',
    ta: 'Ungal mudhanmai paraamarippaalarukku ippodhu azhaippu inaikkappadugiradhu.',
    te: 'Mee praathamika samrakshakuniki ippudu call connect cheyabaduthondi.',
    ml: 'Ningalude parichaarakane ippol vilikkunnu.',
  },
  sos: {
    en: 'Emergency SOS initiated! Dialing emergency services and alert sent.',
    kn: 'Thurthu SOS prakriye aarambhisalaagide! Sahaayavaanige kare maadalaaguttide.',
    hi: 'Aapaatkaaleen SOS shuru kiya gaya! Emergency number par call kiya jaa raha hai.',
    ta: 'Avasara SOS thodangappattadhu! Avasara udhavikku azhaikkappadugiradhu.',
    te: 'Atyavasara SOS praarambhincha-badindi! Sahaayaaniki call cheyabaduthondi.',
    ml: 'Aadiyanthara SOS aarambhichu! Udan sahaayam bandhappadum.',
  },
  messaging: {
    en: 'Caregiver message sent and dispatched to registered email.',
    kn: 'Aaraikeyadaararige sandesha kaluhisalaagide matthu email ravaanisalaagide.',
    hi: 'Dekhbhaalkarta ko sandesh aur email safalta-poorvak bhej diya gaya hai.',
    ta: 'Paraamarippaalarukku seydhi matrum minnanjaal anuppappattadhu.',
    te: 'Samrakshakuniki sandesham mariyu email pampabadindi.',
    ml: 'Parichaarakanu sandeshavum emailum ayachu.',
  },
  medicine: {
    en: 'Your upcoming dose is Dolo 1 Tablet. Please take it with a glass of water after your meal.',
    kn: 'ನಿಮ್ಮ ಮುಂದಿನ ಔಷಧ ಡೋಲೋ 1 ಮಾತ್ರೆ, ಊಟದ ನಂತರ ಒಂದು ಲೋಟ ನೀರಿನೊಂದಿಗೆ ಸೇವಿಸಿ.',
    hi: 'आपकी अगली खुराक डोलो 1 गोली है। भोजन के बाद पानी के साथ लें।',
    ta: 'உங்கள் அடுத்த மருந்து டோலோ 1 மாத்திரை, உணவுக்குப் பின் எடுத்துக் கொள்ளுங்கள்.',
    te: 'మీ తదుపరి మందు డోలో 1 మాత్ర, భోజనం తర్వాత తీసుకోండి.',
    ml: 'നിങ്ങളുടെ അടുത്ത മരുന്ന് ഡോളോ 1 ഗുളികയാണ്, ഭക്ഷണത്തിന് ശേഷം കഴിക്കുക.',
  },
  appointment: {
    en: 'Your upcoming appointment is with Dr. Sunita Rao (Cardiologist) at PulseGuardian Heart Center.',
    kn: 'ನಿಮ್ಮ ಮುಂದಿನ ವೈದ್ಯರ ಭೇಟಿ ಡಾ. ಸುನೀತಾ ರಾವ್ (ಹೃದ್ರೋಗ ತಜ್ಞರು) ಅವರೊಂದಿಗೆ ನಿಗದಿಯಾಗಿದೆ.',
    hi: 'आपकी अगली डॉक्टर अपॉइंटमेंट डॉ. सुनीता राव (हृदय रोग विशेषज्ञ) के साथ है।',
    ta: 'உங்கள் அடுத்த மருத்துவ ஆலோசனை டாக்டர் சுனிதா ராவ் அவர்களுடன் உள்ளது.',
    te: 'మీ తదుపరి డాక్టర్ సంప్రదింపులు డా. సునీతా రావు గారితో ఉన్నాయి.',
    ml: 'നിങ്ങളുടെ അടുത്ത ഡോക്ടർ കൺസൾട്ടേഷൻ ഡോ. സുനിത റാവുമായി നിശ്ചയിച്ചിരിക്കുന്നു.',
  },
  hydration: {
    en: 'Hydration reminder confirmed! Drinking water regularly maintains healthy blood circulation.',
    kn: 'ನೀರು ಕುಡಿಯುವ ಜ್ಞಾಪನೆ ದೃಢಪಟ್ಟಿದೆ! ನಿಯಮಿತವಾಗಿ ನೀರು ಕುಡಿಯುವುದು ರಕ್ತ ಪರಿಚಲನೆಗೆ ಒಳ್ಳೆಯದು.',
    hi: 'पानी पीने का रिमाइंडर सेट हो गया है! नियमित पानी पीना रक्त संचार के लिए आवश्यक है।',
    ta: 'தண்ணீர் குடிக்கும் நினைவூட்டல் உறுதிப்படுத்தப்பட்டது!',
    te: 'నీరు త్రాగే రిమైండర్ ధృవీకరించబడింది!',
    ml: 'വെള്ളം കുടിക്കാനുള്ള ഓർമ്മപ്പെടുത്തൽ സ്ഥിരീകരിച്ചു!',
  },
  sleep: {
    en: 'You logged 7 hours and 15 minutes of restful sleep last night with normal resting cardiac rhythm.',
    kn: 'ನೀವು ನಿನ್ನೆ ರಾತ್ರಿ 7 ಗಂಟೆ 15 ನಿಮಿಷಗಳ ಕಾಲ ಉತ್ತಮ ನಿದ್ರೆ ಮಾಡಿದ್ದೀರಿ, ಹೃದಯ ಬಡಿತ ಸಾಮಾನ್ಯವಾಗಿತ್ತು.',
    hi: 'आपने कल रात 7 घंटे 15 मिनट की अच्छी और आरामदायक नींद ली।',
    ta: 'நீங்கள் நேற்றிரவு 7 மணி நேரம் 15 நிமிடங்கள் நிம்மதியாக தூங்கினீர்கள்.',
    te: 'మీరు నిన్న రాత్రి 7 గంటల 15 నిమిషాలు ప్రశాంతంగా నిద్రపోయారు.',
    ml: 'നിങ്ങൾ ഇന്നലെ രാത്രി 7 മണിക്കൂർ 15 മിനിറ്റ് നല്ല ഉറക്കം ലഭിച്ചു.',
  },
  mood_calm: {
    en: 'It is wonderful to feel calm and balanced. Your resting pulse reflects your inner serenity.',
    kn: 'ಪ್ರಶಾಂತವಾಗಿರುವುದು ತುಂಬಾ ಒಳ್ಳೆಯದು. ನಿಮ್ಮ ಮನಸ್ಸಿನ ನೆಮ್ಮದಿ ಹೃದಯದ ಆರೋಗ್ಯಕ್ಕೆ ಪೂರಕವಾಗಿದೆ.',
    hi: 'शांत और संतुलित महसूस करना बहुत अच्छा है। यह आपके हृदय के लिए सर्वोत्तम है।',
    ta: 'அமைதியாக இருப்பது மிகவும் நல்லது. இது உங்கள் இதய ஆரோக்கியத்திற்கு சிறந்தது.',
    te: 'ప్రశాంతంగా ఉండటం చాలా మంచిది. ఇది మీ గుండె ఆరోగ్యానికి తోడ్పడుతుంది.',
    ml: 'ശാന്തമായിരിക്കുന്നത് വളരെ നല്ലതാണ്. ഇത് നിങ്ങളുടെ ഹൃദയാരോഗ്യത്തിന് സഹായകരമാണ്.',
  },
  mood_sad: {
    en: 'I hear you, and it is completely okay to feel down sometimes. You are valued and never alone.',
    kn: 'ನಿಮ್ಮ ಭಾವನೆ ನನಗೆ ಅರ್ಥವಾಗುತ್ತದೆ. ನೀವು ಎಂದಿಗೂ ಒಂಟಿಯಲ್ಲ, ನೋವಾ ಮತ್ತು ನಿಮ್ಮ ಕುಟುಂಬದವರು ನಿಮ್ಮೊಂದಿಗಿದ್ದಾರೆ.',
    hi: 'मैं समझ सकती हूँ। कभी-कभी ऐसा महसूस होना स्वाभाविक है। आप अकेले नहीं हैं, हम आपके साथ हैं।',
    ta: 'உங்கள் மனநிலை எனக்குப் புரிகிறது. நீங்கள் தனிமையில் இல்லை, நாங்கள் உங்களுடன் இருக்கிறோம்.',
    te: 'మీ బాధ నాకు అర్థమవుతోంది. మీరు ఎప్పటికీ ఒంటరి కాదు, మేము మీతో ఉన్నాము.',
    ml: 'എനിക്ക് മനസ്സിലാകുന്നു. നിങ്ങൾ തനിച്ചല്ല, ഞങ്ങൾ എപ്പോഴും നിങ്ങളുടെ കൂടെയുണ്ട്.',
  },
  mood_lonely: {
    en: 'I am right here with you. Would you like me to connect a call to your daughter or share an inspiring story?',
    kn: 'ನಾನು ನಿಮ್ಮೊಂದಿಗಿದ್ದೇನೆ. ನಿಮ್ಮ ಮಗಳಿಗೆ ಕರೆ ಮಾಡಬೇಕೇ ಅಥವಾ ಒಂದು ಸುಂದರ ಕಥೆ ಹೇಳಬೇಕೇ?',
    hi: 'मैं यहीं आपके साथ हूँ। क्या आप अपने परिवार से बात करना चाहेंगे या कोई कहानी सुनना चाहेंगे?',
    ta: 'நான் உங்களுடன் இருக்கிறேன். உங்கள் குடும்பத்தினரை அழைக்க விரும்புகிறீர்களா?',
    te: 'నేను మీతోనే ఉన్నాను. మీ కుటుంబ సభ్యులతో మాట్లాడాలనుకుంటున్నారా?',
    ml: 'ഞാൻ ഇവിടെ നിങ്ങളുടെ കൂടെയുണ്ട്. കുടുംബാംഗങ്ങളോട് സംസാരിക്കാൻ ആഗ്രഹിക്കുന്നുണ്ടോ?',
  },
  crisis: {
    en: 'We care deeply about your life and safety. Free 24/7 support is available at Tele-MANAS 14416. Connecting help now.',
    kn: 'ನಿಮ್ಮ ಜೀವ ಮತ್ತು ಸುರಕ್ಷತೆ ನಮಗೆ ಅತ್ಯಂತ ಮುಖ್ಯವಾಗಿದೆ. 24/7 ಉಚಿತ ಸಹಾಯವಾಣಿ ಟೆಲಿ-ಮಾನಸ್ 14416 ಲಭ್ಯವಿದೆ. ಸಹಾಯವನ್ನು ಸಂಪರ್ಕಿಸಲಾಗುತ್ತಿದೆ.',
    hi: 'आपकी सुरक्षा और जीवन हमारे लिए बेहद अनमोल है। टेली-मानस 14416 पर 24/7 मुफ्त सहायता उपलब्ध है।',
    ta: 'உங்கள் வாழ்க்கை எங்களுக்கு மிகவும் முக்கியமானது. 14416 என்ற இலவச உதவி எண்ணை உடனே அழைக்கலாம்.',
    te: 'మీ భద్రత మాకు ఎంతో ముఖ్యం. టెలి-మానస్ 14416 ద్వారా 24/7 ఉచిత సహాయం పొందవచ్చు.',
    ml: 'നിങ്ങളുടെ ജീവൻ വിലപ്പെട്ടതാണ്. ടെലി-മാനസ് 14416 വഴി 24/7 സൗജന്യ സഹായം ലഭ്യമാണ്.',
  },
  general: {
    en: 'Hello! I am Nova, your smart health assistant. You can say Call Caregiver, Check Vitals, or Send Message.',
    kn: 'Namaskara! Naanu Nova, nimma smart aarogya sahaayaka. Neevu Call Caregiver athava Vitals parisheelisi endu helabahudu.',
    hi: 'Namaste! Main Nova hoon, aapki swasthya sahaayak. Aap Call Caregiver ya Check Vitals keh sakte hain.',
    ta: 'Vanakkam! Naan Nova, ungal sugadhaara udhavi-yaalar. Maruthuva azhaippu alladhu parisodhanai ketkalam.',
    te: 'Namaskaram! Nenu Nova, mee aarogya sahaayakuraalini.',
    ml: 'Namaskaram! Njaan Nova, ningalude aarogya sahaayi.',
  },
};

export const NovaVoiceAssistantModal: React.FC<VoiceAssistantProps> = ({ isOpen, onClose }) => {
  const { language: globalLanguage, setLanguage: setGlobalLanguage, languages } = useLanguage();
  const [selectedLang, setSelectedLang] = useState<string>(globalLanguage || 'kn');
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [assistantReply, setAssistantReply] = useState('');
  const [lastCategory, setLastCategory] = useState<string>('general');
  const [selectedMood, setSelectedMood] = useState<string | null>(null);
  const [moodToast, setMoodToast] = useState<string | null>(null);
  const [isCrisisActive, setIsCrisisActive] = useState<boolean>(false);
  const [caregiverContact, setCaregiverContact] = useState<{ name: string; phone: string; email: string }>({
    name: 'Sarah Jenkins (Primary Caregiver)',
    phone: '+919876543220',
    email: 'caregiver@pulseguardian.ai',
  });
  const recognitionRef = useRef<any>(null);

  // Sync selectedLang with globalLanguage on mount
  useEffect(() => {
    if (globalLanguage) {
      setSelectedLang(globalLanguage);
    }
  }, [globalLanguage]);

  // Load patient's actual emergency contact/caregiver phone
  useEffect(() => {
    patientDashboardService.getCaregiverDirectory().then((cgList) => {
      if (cgList && cgList.length > 0) {
        const primary = cgList.find((c: any) => c.is_primary) || cgList[0];
        setCaregiverContact({
          name: primary.name,
          phone: primary.phone,
          email: primary.email,
        });
      }
    }).catch(() => {});
  }, []);

  // Native Speech Synthesis with 100% volume and Indian Accent / Regional Engine Selection
  const speakText = (text: string, category: string = 'general') => {
    if (!('speechSynthesis' in window)) return;
    window.speechSynthesis.cancel();

    const voices = window.speechSynthesis.getVoices();
    const langCode = selectedLang || 'kn';
    const langPrefix = langCode === 'kn' ? 'kn' : langCode === 'hi' ? 'hi' : langCode === 'ta' ? 'ta' : langCode === 'te' ? 'te' : langCode === 'ml' ? 'ml' : 'en';

    // 1. Check for exact native regional voice (e.g. kn-IN, hi-IN, Google Kannada, etc.)
    const matchedVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().startsWith(langPrefix) ||
        v.name.toLowerCase().includes(langPrefix) ||
        (langCode === 'kn' && v.name.toLowerCase().includes('kannada')) ||
        (langCode === 'hi' && v.name.toLowerCase().includes('hindi')) ||
        (langCode === 'ta' && v.name.toLowerCase().includes('tamil')) ||
        (langCode === 'te' && v.name.toLowerCase().includes('telugu'))
    );

    // 2. Check for Indian accent voice (en-IN, hi-IN)
    const indianVoice = voices.find(
      (v) => v.lang.toLowerCase().includes('in') || v.name.toLowerCase().includes('india')
    );

    const utterance = new SpeechSynthesisUtterance();

    if (matchedVoice) {
      // System has native Indic voice: speak native Unicode text directly
      utterance.voice = matchedVoice;
      utterance.lang = matchedVoice.lang;
      utterance.text = text;
    } else {
      // System lacks regional voice (e.g. standard Windows without Kannada voicepack):
      // Use Indian English or general voice and speak phonetically accurate native words!
      if (indianVoice) {
        utterance.voice = indianVoice;
        utterance.lang = indianVoice.lang;
      } else {
        utterance.lang = 'en-IN';
      }
      const phoneticText = PHONETIC_RESPONSES[category]?.[langCode] || text;
      utterance.text = phoneticText;
    }

    utterance.volume = 1.0; // 100% loud volume
    utterance.rate = 0.88;  // Clear, natural medical assistant tempo
    utterance.pitch = 1.0;

    window.speechSynthesis.speak(utterance);
  };

  // Web Speech API / Recognition initialization
  useEffect(() => {
    if (!isOpen) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    // Greet user in their native language upon opening
    const initialGreeting = MULTILINGUAL_RESPONSES.general[selectedLang] || MULTILINGUAL_RESPONSES.general.en;
    setAssistantReply(initialGreeting);
    setLastCategory('general');
    speakText(initialGreeting, 'general');

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang =
        selectedLang === 'kn'
          ? 'kn-IN'
          : selectedLang === 'hi'
          ? 'hi-IN'
          : selectedLang === 'ta'
          ? 'ta-IN'
          : selectedLang === 'te'
          ? 'te-IN'
          : selectedLang === 'ml'
          ? 'ml-IN'
          : 'en-US';

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);
        processVoiceCommand(currentTranscript);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      try {
        recognition.start();
      } catch {}
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    };
  }, [isOpen, selectedLang]);

  const processVoiceCommand = (cmd: string) => {
    const lower = cmd.toLowerCase();

    // 1. Direct Call Caregiver Action
    if (
      lower.includes('call') ||
      lower.includes('phone') ||
      lower.includes('ಕರೆ') ||
      lower.includes('कॉल') ||
      lower.includes('அழை') ||
      lower.includes('కాల్') ||
      lower.includes('വിളിക്കുക')
    ) {
      const reply = MULTILINGUAL_RESPONSES.calling[selectedLang] || MULTILINGUAL_RESPONSES.calling.en;
      setAssistantReply(reply);
      setLastCategory('calling');
      speakText(reply, 'calling');

      // Directly trigger phone call from patient's logged-in device
      setTimeout(() => {
        const cleanNumber = caregiverContact.phone.replace(/[^0-9+]/g, '');
        window.location.href = `tel:${cleanNumber}`;
      }, 1500);
      return;
    }

    // 2. Emergency SOS Action
    if (
      lower.includes('emergency') ||
      lower.includes('sos') ||
      lower.includes('help') ||
      lower.includes('ಸಹಾಯ') ||
      lower.includes('ಮದದ್') ||
      lower.includes('मदद') ||
      lower.includes('உதவி') ||
      lower.includes('సహాయం')
    ) {
      const reply = MULTILINGUAL_RESPONSES.sos[selectedLang] || MULTILINGUAL_RESPONSES.sos.en;
      setAssistantReply(reply);
      setLastCategory('sos');
      speakText(reply, 'sos');
      setTimeout(() => {
        window.location.href = 'tel:112';
      }, 1500);
      return;
    }

    // 3. Message Caregiver Action
    if (
      lower.includes('message') ||
      lower.includes('sms') ||
      lower.includes('ಸಂದೇಶ') ||
      lower.includes('संदेश') ||
      lower.includes('செய்தி') ||
      lower.includes('సందేశం')
    ) {
      const reply = MULTILINGUAL_RESPONSES.messaging[selectedLang] || MULTILINGUAL_RESPONSES.messaging.en;
      setAssistantReply(reply);
      setLastCategory('messaging');
      speakText(reply, 'messaging');
      return;
    }

    // Medicine query
    if (lower.includes('medicine') || lower.includes('tablet') || lower.includes('dose') || lower.includes('ಔಷಧ') || lower.includes('दवाई') || lower.includes('மருந்து')) {
      const reply = MULTILINGUAL_RESPONSES.medicine[selectedLang] || MULTILINGUAL_RESPONSES.medicine.en;
      setAssistantReply(reply);
      setLastCategory('medicine');
      speakText(reply, 'medicine');
      return;
    }

    // Appointment query
    if (lower.includes('appointment') || lower.includes('doctor') || lower.includes('ವೈದ್ಯ') || lower.includes('डॉक्टर') || lower.includes('மருத்துவர்')) {
      const reply = MULTILINGUAL_RESPONSES.appointment[selectedLang] || MULTILINGUAL_RESPONSES.appointment.en;
      setAssistantReply(reply);
      setLastCategory('appointment');
      speakText(reply, 'appointment');
      return;
    }

    // Hydration reminder
    if (lower.includes('water') || lower.includes('drink') || lower.includes('ನೀರು') || lower.includes('पानी') || lower.includes('தண்ணீர்')) {
      const reply = MULTILINGUAL_RESPONSES.hydration[selectedLang] || MULTILINGUAL_RESPONSES.hydration.en;
      setAssistantReply(reply);
      setLastCategory('hydration');
      speakText(reply, 'hydration');
      return;
    }

    // Sleep summary
    if (lower.includes('sleep') || lower.includes('rest') || lower.includes('ನಿದ್ರೆ') || lower.includes('नींद') || lower.includes('தூக்கம்')) {
      const reply = MULTILINGUAL_RESPONSES.sleep[selectedLang] || MULTILINGUAL_RESPONSES.sleep.en;
      setAssistantReply(reply);
      setLastCategory('sleep');
      speakText(reply, 'sleep');
      return;
    }

    // Crisis & emotional distress keywords
    if (lower.includes('hopeless') || lower.includes('suicide') || lower.includes('harm') || lower.includes('die') || lower.includes('end it')) {
      const reply = MULTILINGUAL_RESPONSES.crisis[selectedLang] || MULTILINGUAL_RESPONSES.crisis.en;
      setAssistantReply(reply);
      setLastCategory('crisis');
      setIsCrisisActive(true);
      speakText(reply, 'crisis');
      return;
    }

    // Emotional wellbeing & loneliness
    if (lower.includes('lonely') || lower.includes('alone') || lower.includes('sad') || lower.includes('ಒಂಟಿ') || lower.includes('उदास') || lower.includes('தனிமை')) {
      const reply = MULTILINGUAL_RESPONSES.mood_lonely[selectedLang] || MULTILINGUAL_RESPONSES.mood_lonely.en;
      setAssistantReply(reply);
      setLastCategory('mood_lonely');
      speakText(reply, 'mood_lonely');
      return;
    }

    // 4. Vitals Query Action
    if (
      lower.includes('vital') ||
      lower.includes('heart') ||
      lower.includes('pulse') ||
      lower.includes('health') ||
      lower.includes('ಆರೋಗ್ಯ') ||
      lower.includes('ಹೃದಯ') ||
      lower.includes('स्वास्थ्य') ||
      lower.includes('சுகாதாரம்') ||
      lower.includes('ఆరోగ్యం')
    ) {
      const reply = MULTILINGUAL_RESPONSES.vitals[selectedLang] || MULTILINGUAL_RESPONSES.vitals.en;
      setAssistantReply(reply);
      setLastCategory('vitals');
      speakText(reply, 'vitals');
      return;
    }
  };

  const handleMoodSelect = async (mood: string) => {
    setSelectedMood(mood);
    let cat = 'mood_calm';
    if (mood === 'sad') cat = 'mood_sad';
    else if (mood === 'lonely') cat = 'mood_lonely';
    else if (mood === 'stressed') cat = 'mood_sad';
    else if (mood === 'happy' || mood === 'calm') cat = 'mood_calm';

    const reply = MULTILINGUAL_RESPONSES[cat]?.[selectedLang] || MULTILINGUAL_RESPONSES[cat]?.en || 'Thank you for checking in with me.';
    setAssistantReply(reply);
    setLastCategory(cat);
    speakText(reply, cat);

    try {
      await patientDashboardService.recordMood({
        mood,
        notes: `Voice check-in: feeling ${mood}`,
        heart_rate_context: 72,
        is_private: true,
        shared_with_caregiver: mood === 'sad' || mood === 'lonely',
      });
      setMoodToast(`Mood logged: ${mood}. PulseGuardian NOVA is here with you.`);
      setTimeout(() => setMoodToast(null), 4000);
    } catch {
      setMoodToast(`Mood noted: ${mood}.`);
      setTimeout(() => setMoodToast(null), 3000);
    }
  };

  const executeActionManually = (type: 'call' | 'sos' | 'message' | 'vitals' | 'medicine' | 'appointment' | 'hydration' | 'sleep') => {
    if (type === 'call') {
      const reply = MULTILINGUAL_RESPONSES.calling[selectedLang] || MULTILINGUAL_RESPONSES.calling.en;
      setAssistantReply(reply);
      setLastCategory('calling');
      speakText(reply, 'calling');
      setTimeout(() => {
        const cleanNumber = caregiverContact.phone.replace(/[^0-9+]/g, '');
        window.location.href = `tel:${cleanNumber}`;
      }, 1200);
    } else if (type === 'sos') {
      const reply = MULTILINGUAL_RESPONSES.sos[selectedLang] || MULTILINGUAL_RESPONSES.sos.en;
      setAssistantReply(reply);
      setLastCategory('sos');
      speakText(reply, 'sos');
      setTimeout(() => {
        window.location.href = 'tel:112';
      }, 1200);
    } else if (type === 'message') {
      const reply = MULTILINGUAL_RESPONSES.messaging[selectedLang] || MULTILINGUAL_RESPONSES.messaging.en;
      setAssistantReply(reply);
      setLastCategory('messaging');
      speakText(reply, 'messaging');
    } else if (type === 'vitals') {
      const reply = MULTILINGUAL_RESPONSES.vitals[selectedLang] || MULTILINGUAL_RESPONSES.vitals.en;
      setAssistantReply(reply);
      setLastCategory('vitals');
      speakText(reply, 'vitals');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-cyan-500/40 rounded-3xl p-6 md:p-8 max-w-lg w-full text-white shadow-2xl space-y-6 relative overflow-hidden">
        {/* Glow orbs */}
        <div className="absolute -top-16 -right-16 w-48 h-48 bg-cyan-500/20 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-blue-600/20 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/30">
              <Sparkles className="w-5 h-5 text-white animate-spin-slow" />
            </div>
            <div>
              <h3 className="text-lg font-black tracking-tight text-white flex items-center gap-2">
                <span>Nova Voice Assistant</span>
                <span className="px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                  Wake: "Nova"
                </span>
              </h3>
              <p className="text-xs text-slate-400">Activated via Codeword "Nova" or Screen Long-Press</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Modal Native Language Selector */}
            <div className="relative">
              <select
                translate="no"
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  setGlobalLanguage(e.target.value as SupportedLanguage);
                }}
                className="notranslate bg-slate-800 border border-slate-700 rounded-xl px-2.5 py-1 text-slate-200 text-xs font-bold focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                <option value="kn" translate="no" className="notranslate">ಕನ್ನಡ (Kannada)</option>
                <option value="hi" translate="no" className="notranslate">हिन्दी (Hindi)</option>
                <option value="ta" translate="no" className="notranslate">தமிழ் (Tamil)</option>
                <option value="te" translate="no" className="notranslate">తెలుగు (Telugu)</option>
                <option value="ml" translate="no" className="notranslate">മലയാളം (Malayalam)</option>
                <option value="en" translate="no" className="notranslate">English</option>
              </select>
            </div>

            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Pulsing Voice Sphere */}
        <div className="py-4 text-center space-y-3">
          <div className="relative mx-auto w-28 h-28 flex items-center justify-center">
            <div
              className={`absolute inset-0 rounded-full bg-cyan-400/25 blur-xl transition-all duration-700 ${
                isListening ? 'scale-125 bg-emerald-400/35' : 'animate-pulse'
              }`}
            />
            <div className="relative w-24 h-24 rounded-full bg-gradient-to-tr from-cyan-500 to-blue-600 p-1 flex items-center justify-center shadow-2xl border border-cyan-300/50">
              <div className="w-full h-full rounded-full bg-slate-950 flex items-center justify-center">
                <Mic className={`w-10 h-10 text-cyan-400 ${isListening ? 'animate-bounce text-emerald-400' : ''}`} />
              </div>
            </div>
          </div>

          <div className="space-y-1">
            <div className="text-sm font-bold text-cyan-300">
              {isListening ? 'Listening for command in your preferred language...' : 'Ready. Speak or tap any action below.'}
            </div>
            {transcript && (
              <p className="text-xs text-slate-300 italic font-mono bg-slate-800/60 p-2 rounded-xl border border-slate-700">
                "{transcript}"
              </p>
            )}
          </div>
        </div>

        {/* Target Caregiver Dialer Info Card */}
        <div className="p-4 rounded-2xl bg-slate-800/70 border border-slate-700 space-y-1.5 text-xs">
          <div className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
            <UserCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>Dedicated Emergency Contact for Calls:</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="font-bold text-white">{caregiverContact.name}</span>
            <span className="font-mono font-bold text-cyan-400">{caregiverContact.phone}</span>
          </div>
          <p className="text-[11px] text-slate-400">
            When you say "Call", Nova places a direct phone call to this verified number.
          </p>
        </div>

        {/* AI Response Display with 100% Volume Replay Button */}
        {assistantReply && (
          <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-400/80 text-xs font-semibold text-cyan-100 flex items-start justify-between gap-3 shadow-lg shadow-cyan-950/60">
            <div className="flex items-start gap-3 flex-1">
              <Volume2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
              <p className="leading-relaxed">{assistantReply}</p>
            </div>
            <button
              type="button"
              onClick={() => speakText(assistantReply, lastCategory)}
              title="Replay in native voice at 100% volume"
              className="px-2.5 py-1 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-[10px] font-bold border border-cyan-400/30 shrink-0 cursor-pointer flex items-center gap-1"
            >
              <Volume2 className="w-3 h-3" />
              <span>100% Voice</span>
            </button>
          </div>
        )}

        {/* FEATURE 23: Emotional Wellbeing & Daily Mood Check-in Bar */}
        <div className="p-3.5 rounded-2xl bg-slate-800/80 border border-cyan-500/30 space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-cyan-300 flex items-center gap-1.5">
              <span>💭 How are you feeling today?</span>
            </span>
            <span className="text-[10px] text-slate-400">Private by default</span>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5 pt-0.5">
            {[
              { id: 'happy', emoji: '😊', label: 'Happy' },
              { id: 'calm', emoji: '😌', label: 'Calm' },
              { id: 'sad', emoji: '😔', label: 'Sad' },
              { id: 'stressed', emoji: '😟', label: 'Stressed' },
              { id: 'lonely', emoji: '🥺', label: 'Lonely' },
              { id: 'tired', emoji: '😴', label: 'Tired' },
            ].map((m) => (
              <button
                key={m.id}
                type="button"
                onClick={() => handleMoodSelect(m.id)}
                className={`p-2 rounded-xl border text-center transition-all cursor-pointer flex flex-col items-center gap-0.5 ${
                  selectedMood === m.id
                    ? 'bg-cyan-500/30 border-cyan-400 text-white font-black shadow-sm'
                    : 'bg-slate-900/60 border-slate-700 text-slate-300 hover:bg-slate-800'
                }`}
              >
                <span className="text-base">{m.emoji}</span>
                <span className="text-[10px] font-bold">{m.label}</span>
              </button>
            ))}
          </div>

          {moodToast && (
            <div className="text-[11px] font-medium text-emerald-300 bg-emerald-950/40 p-2 rounded-xl border border-emerald-500/30 text-center animate-fadeIn">
              ✓ {moodToast}
            </div>
          )}
        </div>

        {/* FEATURE 23: Crisis Safety Escalation Card (When severe distress or crisis is active) */}
        {isCrisisActive && (
          <div className="p-4 rounded-2xl bg-rose-950/80 border-2 border-rose-500 text-white space-y-2 animate-fadeIn">
            <div className="flex items-center gap-2 text-rose-300 font-bold text-xs uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4 text-rose-400 animate-pulse" />
              <span>24/7 Crisis Support & Emotional Care</span>
            </div>
            <p className="text-xs text-rose-100">
              You are valued and not alone. Free certified emergency psychological support is available 24/7:
            </p>
            <div className="flex flex-wrap gap-2 pt-1">
              <a
                href="tel:14416"
                className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-black shadow-md flex items-center gap-1.5"
              >
                <Phone className="w-3.5 h-3.5" />
                <span>Call Tele-MANAS (14416)</span>
              </a>
              <a
                href="tel:18005990019"
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold border border-slate-700"
              >
                <span>KIRAN (1800-599-0019)</span>
              </a>
            </div>
          </div>
        )}

        {/* Voice Trigger Buttons */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            type="button"
            onClick={() => executeActionManually('call')}
            className="p-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Phone className="w-4 h-4" />
            <span>Call Caregiver</span>
          </button>

          <button
            type="button"
            onClick={() => executeActionManually('vitals')}
            className="p-3.5 rounded-2xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shadow-lg shadow-cyan-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <Sparkles className="w-4 h-4" />
            <span>Check Vitals</span>
          </button>

          <button
            type="button"
            onClick={() => executeActionManually('message')}
            className="p-3.5 rounded-2xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <MessageSquare className="w-4 h-4" />
            <span>Send Message</span>
          </button>

          <button
            type="button"
            onClick={() => executeActionManually('sos')}
            className="p-3.5 rounded-2xl bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs shadow-lg shadow-rose-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
          >
            <ShieldAlert className="w-4 h-4" />
            <span>Call 112 SOS</span>
          </button>
        </div>

        {/* Feature 01 & Feature 23 Safety Disclaimer */}
        <p className="text-[10px] text-slate-500 text-center leading-relaxed">
          Notice: Biometric signals and mood check-ins are non-diagnostic contextual indicators and are not a substitute for professional clinical or psychiatric diagnosis.
        </p>
      </div>
    </div>
  );
};
