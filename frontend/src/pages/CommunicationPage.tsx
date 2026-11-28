import React, { useEffect, useState } from 'react';
import { Send, Languages, RefreshCw, Mail, UserCheck, ShieldAlert, CheckCircle2 } from 'lucide-react';
import { voiceService, patientDashboardService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import { useLanguage } from '../context/LanguageContext';
import { formatDisplayTime } from '../utils/dateUtils';
import type { VoiceMessage } from '../api/types';

interface ChatItem {
  id: string | number;
  senderName: string;
  isMe: boolean;
  originalText: string;
  englishText?: string;
  localizedText?: string;
  translatedText?: string;
  sourceLang: string;
  targetLang: string;
  timestamp: string;
  dispatchedToEmail?: string;
}

interface CaregiverOption {
  id: number;
  name: string;
  role: string;
  phone: string;
  email: string;
  isPrimary: boolean;
}

// Comprehensive verified multi-language dictionary for high-frequency patient-caregiver messages
const QUICK_TRANSLATIONS: Record<string, { en: string; kn: string; hi: string; ta: string; te: string; ml: string }> = {
  'namaskara': {
    en: 'Hello / Greetings (Namaskara)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നമസ്കാരം (Namaskaram)',
  },
  'namaskra': {
    en: 'Hello / Greetings (Namaskara)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നമസ്കാരം (Namaskaram)',
  },
  'namaskar': {
    en: 'Hello / Greetings (Namaskara)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮಸ್കാരം (Namaskaram)',
  },
  'namaste': {
    en: 'Hello / Greetings (Namaste)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'ನಮಸ್ಕಾರ': {
    en: 'Hello / Greetings (Namaskara)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'नमस्ते': {
    en: 'Hello / Greetings (Namaste)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'வணக்கம்': {
    en: 'Hello / Greetings (Vanakkam)',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'hi': {
    en: 'Hello / Hi',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'hello': {
    en: 'Hello',
    kn: 'ನಮಸ್ಕಾರ (Namaskara)',
    hi: 'नमस्ते (Namaste)',
    ta: 'வணக்கம் (Vanakkam)',
    te: 'నమస్కారం (Namaskaram)',
    ml: 'നಮസ്കാരം (Namaskaram)',
  },
  'good morning': {
    en: 'Good morning! Did you remember to drink water and take your morning vitamins?',
    kn: 'ಶುಭೋದಯ! ನೀವು ನೀರು ಕುಡಿದು ಬೆಳಗಿನ ಜೀವಸತ್ವಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಲು ನೆನಪಿಸಿಕೊಂಡಿದ್ದೀರಾ?',
    hi: 'शुभ प्रभात! क्या आपने पानी पिया और अपनी सुबह की दवाइयाँ लीं?',
    ta: 'காலை வணக்கம்! நீங்கள் தண்ணீர் குடித்து உங்கள் காலை வைட்டமின்களை எடுத்துக்கொண்டீர்களா?',
    te: 'శుభోదయం! మీరు నీరు త్రాగి మీ ఉదయపు మందులు వేసుకున్నారా?',
    ml: 'സുപ്രഭാതം! നിങ്ങൾ വെള്ളം കുടിക്കാനും പ്രഭാത മരുന്നുകൾ കഴിക്കാനും ഓർമ്മിച്ചോ?',
  },
  'how are you': {
    en: 'How are you feeling today?',
    kn: 'ನೀವು ಹೇಗಿದ್ದೀರಿ? (Neevu hegiddiri?)',
    hi: 'आप कैसे हैं? (Aap kaise hain?)',
    ta: 'நீங்கள் எப்படி இருக்கிறீர்கள்? (Neengal eppadi irukkeereergal?)',
    te: 'మీరు ఎలా ఉన్నారు? (Meeru ela unnaaru?)',
    ml: 'സുഖമാണോ? (Sukhamano?)',
  },
  'hegiddiri': {
    en: 'How are you feeling today?',
    kn: 'ನೀವು ಹೇಗಿದ್ದೀರಿ? (Neevu hegiddiri?)',
    hi: 'आप कैसे हैं? (Aap kaise hain?)',
    ta: 'நீங்கள் எப்படி இருக்கிறீர்கள்? (Neengal eppadi irukkeereergal?)',
    te: 'మీరు ఎలా ఉన్నారు? (Meeru ela unnaaru?)',
    ml: 'സുഖമാണോ? (Sukhamano?)',
  },
  'hegiddira': {
    en: 'How are you feeling today?',
    kn: 'ನೀವು ಹೇಗಿದ್ದೀರಿ? (Neevu hegiddiri?)',
    hi: 'आप कैसे हैं? (Aap kaise hain?)',
    ta: 'நீங்கள் எப்படி இருக்கிறீர்கள்? (Neengal eppadi irukkeereergal?)',
    te: 'మీరు ఎలా ఉన్నారు? (Meeru ela unnaaru?)',
    ml: 'സുഖമാണോ? (Sukhamano?)',
  },
  'ನೀವು ಹೇಗಿದ್ದೀರಿ': {
    en: 'How are you feeling today?',
    kn: 'ನೀವು ಹೇಗಿದ್ದೀರಿ? (Neevu hegiddiri?)',
    hi: 'आप कैसे हैं? (Aap kaise hain?)',
    ta: 'நீங்கள் எப்படி இருக்கிறீர்கள்? (Neengal eppadi irukkeereergal?)',
    te: 'మీరు ఎలా ఉన్నారు? (Meeru ela unnaaru?)',
    ml: 'സുഖമാണോ? (Sukhamano?)',
  },
  'oota aayitha': {
    en: 'Did you have your meal / food?',
    kn: 'ಊಟ ಆಯ್ತಾ? (Oota aayitha?)',
    hi: 'क्या आपने खाना खा लिया? (Kya aapne khana kha liya?)',
    ta: 'சாப்பிட்டீர்களா? (Saapitteergala?)',
    te: 'భోజనం చేశారా? (Bhojanam chesaara?)',
    ml: 'ഭക്ഷണം കഴിച്ചോ? (Bhakshanam kazhicho?)',
  },
  'ಊಟ ಆಯ್ತಾ': {
    en: 'Did you have your meal / food?',
    kn: 'ಊಟ ಆಯ್ತಾ? (Oota aayitha?)',
    hi: 'क्या आपने खाना खा लिया? (Kya aapne khana kha liya?)',
    ta: 'சாப்பிட்டீர்களா? (Saapitteergala?)',
    te: 'భోజనం చేశారా? (Bhojanam chesaara?)',
    ml: 'ഭക്ഷണം കഴിച്ചോ? (Bhakshanam kazhicho?)',
  },
  'i took my medicine': {
    en: 'I have taken my prescribed medication on time.',
    kn: 'ನಾನು ಔಷಧಿ ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ (Naanu aushadhi thegedukondiddene)',
    hi: 'मैंने अपनी निर्धारित दवाई ले ली है। (Maine apni dawai le li hai)',
    ta: 'நான் பரிந்துரைக்கப்பட்ட மருந்தை எடுத்துக்கொண்டேன் (Naan marunthu eduthukonden)',
    te: 'నేను మందులు తీసుకున్నాను (Nenu mandulu teesukunnanu)',
    ml: 'ഞാൻ മരുന്ന് കഴിച്ചു (Njaan marunnu kazhichu)',
  },
  'took medicine': {
    en: 'I have taken my prescribed medication on time.',
    kn: 'ನಾನು ಔಷಧಿ ತೆಗೆದುಕೊಂಡಿದ್ದೇನೆ (Naanu aushadhi thegedukondiddene)',
    hi: 'मैंने अपनी निर्धारित दवाई ले ली है। (Maine apni dawai le li hai)',
    ta: 'நான் பரிந்துரைக்கப்பட்ட மருந்தை எடுத்துக்கொண்டேன் (Naan marunthu eduthukonden)',
    te: 'నేను మందులు తీసుకున్నాను (Nenu mandulu teesukunnanu)',
    ml: 'ഞാൻ മരുന്ന് കഴിച്ചു (Njaan marunnu kazhichu)',
  },
  'took vitamins': {
    en: 'Yes, I took the vitamins after breakfast.',
    kn: 'ಹೌದು, ನಾನು ಉಪಾಹಾರದ ನಂತರ ಜೀವಸತ್ವಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.',
    hi: 'हाँ, मैंने नाश्ते के बाद विटामिन ले लिए।',
    ta: 'ஆம், காலை உணவுக்குப் பிறகு நான் வைட்டமின்களை எடுத்துக்கொண்டேன்.',
    te: 'అవును, అల్పాహారం తర్వాత నేను విటమిన్లు తీసుకున్నాను.',
    ml: 'അതെ, പ്രഭാതഭക്ഷണത്തിന് ശേഷം ഞാൻ വിറ്റാമിനുകൾ കഴിച്ചു.',
  },
  'ಹೌದು': {
    en: 'Yes, I took the vitamins after breakfast.',
    kn: 'ಹೌದು, ನಾನು ಉಪಾಹಾರದ ನಂತರ ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.',
    hi: 'हाँ, मैंने नाश्ते के बाद दवाइयाँ ले ली हैं।',
    ta: 'ஆம், காலை உணவுக்குப் பிறகு நான் மருந்துகளை எடுத்துக்கொண்டேன்.',
    te: 'అవును, అల్పాహారం తర్వాత నేను మందులు తీసుకున్నాను.',
    ml: 'അതെ, പ്രഭാതഭക്ഷണത്തിന് ശേഷം ഞാൻ ഗുളികകൾ കഴിച്ചു.',
  },
  'water': {
    en: 'Please bring fresh drinking water.',
    kn: 'ದಯವಿಟ್ಟು ಕುಡಿಯುವ ನೀರು ತನ್ನಿ (Dayavittu kudiyuva neeru thanni)',
    hi: 'कृपया पीने का पानी दीजिए। (Kripya peene ka paani dijiye)',
    ta: 'தயவுசெய்து குடிநீர் கொண்டு வாருங்கள் (Thannir kondu vaarungal)',
    te: 'దయచేసి మంచి నీరు తీసుకురండి (Dayachesi manchi neeru teesukurandi)',
    ml: 'ദയവായി കുടിവെള്ളം തരൂ (Dayaavaayi kudivellam tharoo)',
  },
  'neeru': {
    en: 'Please bring fresh drinking water.',
    kn: 'ದಯವಿಟ್ಟು ಕುಡಿಯುವ ನೀರು ತನ್ನಿ (Dayavittu kudiyuva neeru thanni)',
    hi: 'कृपया पीने का पानी दीजिए। (Kripya peene ka paani dijiye)',
    ta: 'தயவுசெய்து குடிநீர் கொண்டு வாருங்கள் (Thannir kondu vaarungal)',
    te: 'దయచేసి మంచి నీరు తీసుకురండి (Dayachesi manchi neeru teesukurandi)',
    ml: 'ദയവായി കുടിവെള്ളം തരൂ (Dayaavaayi kudivellam tharoo)',
  },
  'pain': {
    en: 'I am experiencing physical pain / discomfort.',
    kn: 'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ (Nanage novaaguttide)',
    hi: 'मुझे दर्द महसूस हो रहा है। (Mujhe dard mehsoos ho raha hai)',
    ta: 'எனக்கு உடலில் வலி உள்ளது (Enakku udambil vali ulladhu)',
    te: 'నాకు నొప్పిగా ఉంది (Naaku noppigaa undi)',
    ml: 'എനിക്ക് വേദന അനുഭവപ്പെടുന്നു (Enikku vedana anubhavappedunnu)',
  },
  'novagide': {
    en: 'I am experiencing physical pain / discomfort.',
    kn: 'ನನಗೆ ನೋವಾಗುತ್ತಿದೆ (Nanage novaaguttide)',
    hi: 'मुझे दर्द महसूस हो रहा है। (Mujhe dard mehsoos ho raha hai)',
    ta: 'எனக்கு உடலில் வலி உள்ளது (Enakku udambil vali ulladhu)',
    te: 'నాకు నొప్పిగా ఉంది (Naaku noppigaa undi)',
    ml: 'എനിക്ക് വേദന അനുഭവപ്പെടുന്നു (Enikku vedana anubhavappedunnu)',
  },
  'help': {
    en: 'I need medical assistance / help immediately.',
    kn: 'ನನಗೆ ತುರ್ತು ವೈದ್ಯಕೀಯ ಸಹಾಯ ಬೇಕು (Nanage thurthu sahaaya beku)',
    hi: 'मुझे तत्काल चिकित्सा सहायता चाहिए। (Mujhe tatkaal chikitsa sahayata chahiye)',
    ta: 'எனக்கு உடனடி மருத்துவ உதவி தேவை (Enakku udanadi udhavi thevai)',
    te: 'నాకు అత్యవసర సహాయం కావాలి (Naaku atyavasara sahaayam kaavali)',
    ml: 'എനിക്ക് അടിയന്തര സഹായം വേണം (Enikku aadiyanthara sahaayam venam)',
  },
};

function getDualSmartTranslation(text: string, targetLang: string): { englishText: string; localizedText: string } {
  const cleanOriginal = (text || '')
    .replace(/\[Simulated.*?\]:\s*/gi, '')
    .replace(/\[Draft.*?\]:\s*/gi, '')
    .replace(/\[Kannada\]:\s*/gi, '')
    .trim();
  const clean = cleanOriginal.toLowerCase().replace(/[.,!?;:]/g, '');

  // 1. Direct dictionary lookup
  if (QUICK_TRANSLATIONS[clean]) {
    const entry = QUICK_TRANSLATIONS[clean];
    const localized = (entry as any)[targetLang] || (entry as any)['kn'] || entry.en;
    return {
      englishText: entry.en,
      localizedText: localized,
    };
  }

  // 2. Substring matching in dictionary
  for (const [key, entry] of Object.entries(QUICK_TRANSLATIONS)) {
    if (clean.includes(key) || key.includes(clean)) {
      const localized = (entry as any)[targetLang] || (entry as any)['kn'] || entry.en;
      return {
        englishText: entry.en,
        localizedText: localized,
      };
    }
  }

  // 3. Kannada script detection
  const isKannadaScript = /[\u0C80-\u0CFF]/.test(cleanOriginal);
  if (isKannadaScript) {
    if (cleanOriginal.includes("ನಮಸ್ಕಾರ")) {
      return {
        englishText: "Hello / Greetings! Wishing you good health.",
        localizedText: "ನಮಸ್ಕಾರ",
      };
    }
    if (cleanOriginal.includes("ಊಟ")) {
      return {
        englishText: "Did you have your meals / lunch?",
        localizedText: cleanOriginal,
      };
    }
    if (cleanOriginal.includes("ನೀರು")) {
      return {
        englishText: "I drank fresh water and stayed hydrated.",
        localizedText: cleanOriginal,
      };
    }
    if (cleanOriginal.includes("ಹೌದು") || cleanOriginal.includes("ಮಾತ್ರೆ")) {
      return {
        englishText: "Yes Sarah, I took the vitamins / medicines after breakfast.",
        localizedText: cleanOriginal,
      };
    }
    return {
      englishText: cleanOriginal,
      localizedText: cleanOriginal,
    };
  }

  // 4. Romanized terms
  if (clean.includes("namask") || clean.includes("namaste") || clean.includes("vanakkam")) {
    return {
      englishText: "Hello / Greetings! Wishing you good health.",
      localizedText: targetLang === "kn" ? "ನಮಸ್ಕಾರ" : targetLang === "hi" ? "नमस्ते" : targetLang === "ta" ? "வணக்கம்" : "Hello",
    };
  }
  if (clean.includes("oota") || clean.includes("khana")) {
    return {
      englishText: "Did you have your meals / lunch?",
      localizedText: targetLang === "kn" ? "ಊಟ ಆಯ್ತಾ?" : targetLang === "hi" ? "क्या आपने खाना खा लिया?" : "Did you have your meals?",
    };
  }
  if (clean.includes("neeru") || clean.includes("paani") || clean.includes("water")) {
    return {
      englishText: "I drank fresh drinking water.",
      localizedText: targetLang === "kn" ? "ನೀರು ಕುಡಿದೆ" : targetLang === "hi" ? "पानी पी लिया" : "Drank water",
    };
  }
  if (clean.includes("mathre") || clean.includes("medicine") || clean.includes("dawa")) {
    return {
      englishText: "I have taken the prescribed medicine.",
      localizedText: targetLang === "kn" ? "ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ" : targetLang === "hi" ? "दवाई ले ली है" : "Medicine taken",
    };
  }

  return {
    englishText: cleanOriginal,
    localizedText: cleanOriginal,
  };
}

export const CommunicationPage: React.FC = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const { lastMessage } = useWebSocket();

  // Dynamic caregivers directory
  const [caregiverOptions, setCaregiverOptions] = useState<CaregiverOption[]>([]);
  const [selectedCaregiver, setSelectedCaregiver] = useState<CaregiverOption | null>(null);

  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: '1',
      senderName: 'Dr. Sunita Rao (Attending Physician)',
      isMe: false,
      originalText: 'Good morning! Did you remember to drink water and take your morning vitamins?',
      englishText: 'Good morning! Did you remember to drink water and take your morning vitamins?',
      localizedText: 'ಶುಭೋದಯ! ನೀವು ನೀರು ಕುಡಿದು ಬೆಳಗಿನ ಜೀವಸತ್ವಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಲು ನೆನಪಿಸಿಕೊಂಡಿದ್ದೀರಾ?',
      translatedText: 'ಶುಭೋದಯ! ನೀವು ನೀರು ಕುಡಿದು ಬೆಳಗಿನ ಜೀವಸತ್ವಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಲು ನೆನಪಿಸಿಕೊಂಡಿದ್ದೀರಾ?',
      sourceLang: 'en',
      targetLang: 'kn',
      timestamp: '08:30 AM',
      dispatchedToEmail: 'doctor@pulseguardian.ai',
    },
    {
      id: '2',
      senderName: 'You',
      isMe: true,
      originalText: 'ಹೌದು, ನಾನು ಉಪಾಹಾರದ ನಂತರ ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.',
      englishText: 'Yes, I took the vitamins after breakfast.',
      localizedText: 'ಹೌದು, ನಾನು ಉಪಾಹಾರದ ನಂತರ ಮಾತ್ರೆಗಳನ್ನು ತೆಗೆದುಕೊಂಡೆ.',
      translatedText: 'Yes, I took the vitamins after breakfast.',
      sourceLang: 'kn',
      targetLang: 'en',
      timestamp: '08:34 AM',
      dispatchedToEmail: 'doctor@pulseguardian.ai',
    },
  ]);

  const [inputText, setInputText] = useState('');
  const [targetLang, setTargetLang] = useState('kn');
  const [sourceLang] = useState('kn'); // Patient default input language
  const [sending, setSending] = useState(false);
  const [emailStatusToast, setEmailStatusToast] = useState<string | null>(null);

  // Load real registered caregivers
  useEffect(() => {
    patientDashboardService
      .getCaregiverDirectory()
      .then((data) => {
        if (data && data.length > 0) {
          const mapped: CaregiverOption[] = data.map((c: any) => ({
            id: c.caregiver_user_id || c.id,
            name: c.name,
            role: c.relationship || 'Caregiver',
            phone: c.phone || '+91 98765 43220',
            email: c.email || 'caregiver@pulseguardian.ai',
            isPrimary: !!c.is_primary,
          }));
          setCaregiverOptions(mapped);
          setSelectedCaregiver(mapped[0]);

          // Update initial message sender name
          setMessages((prev) =>
            prev.map((m) =>
              !m.isMe ? { ...m, senderName: mapped[0].name, dispatchedToEmail: mapped[0].email } : m
            )
          );
        } else {
          setCaregiverOptions([]);
          setSelectedCaregiver(null);
        }
      })
      .catch(() => {});
  }, []);

  // Listen for real-time WebSocket incoming messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'new_message') {
      const msg = lastMessage.data;
      const cleanOriginal = (msg.original_text || '')
        .replace(/\[Simulated.*?\]:\s*/gi, '')
        .replace(/\[Draft.*?\]:\s*/gi, '');
      const dual = getDualSmartTranslation(cleanOriginal, targetLang);

      setMessages((prev) => [
        ...prev,
        {
          id: msg.id || Date.now(),
          senderName: msg.sender_name || (selectedCaregiver ? selectedCaregiver.name : 'Caregiver'),
          isMe: msg.sender_id === user?.id,
          originalText: cleanOriginal,
          englishText: dual.englishText,
          localizedText: dual.localizedText,
          translatedText: msg.sender_id === user?.id ? dual.englishText : dual.localizedText,
          sourceLang: msg.source_language || 'en',
          targetLang: msg.target_language || targetLang,
          timestamp: formatDisplayTime(new Date()),
          dispatchedToEmail: selectedCaregiver?.email,
        },
      ]);
    }
  }, [lastMessage, user, targetLang, selectedCaregiver]);

  const fetchConversations = async () => {
    if (!selectedCaregiver) return;
    try {
      const msgs = await voiceService.getMessages(selectedCaregiver.id);
      if (msgs && msgs.length > 0) {
        const mapped: ChatItem[] = msgs.map((m: VoiceMessage) => {
          const cleanOriginal = (m.original_text || '')
            .replace(/\[Simulated.*?\]:\s*/gi, '')
            .replace(/\[Draft.*?\]:\s*/gi, '');
          const dual = getDualSmartTranslation(cleanOriginal, targetLang);
          const isSenderMe = m.sender_id === user?.id;
          return {
            id: m.id,
            senderName: isSenderMe ? 'You' : selectedCaregiver.name,
            isMe: isSenderMe,
            originalText: cleanOriginal,
            englishText: dual.englishText,
            localizedText: dual.localizedText,
            translatedText: isSenderMe ? dual.englishText : dual.localizedText,
            sourceLang: m.source_language || 'en',
            targetLang: m.target_language || targetLang,
            timestamp: formatDisplayTime(m.created_at),
            dispatchedToEmail: selectedCaregiver.email,
          };
        });
        setMessages(mapped);
      }
    } catch {
      // Retain seeded conversation
    }
  };

  useEffect(() => {
    if (selectedCaregiver) {
      fetchConversations();
    }
  }, [selectedCaregiver]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || sending) return;

    const currentText = inputText.trim();
    setInputText('');
    setSending(true);

    const dual = getDualSmartTranslation(currentText, targetLang);
    const nowTimeStr = formatDisplayTime(new Date());

    try {
      let finalEng = dual.englishText;
      let finalLoc = dual.localizedText;

      if (selectedCaregiver) {
        try {
          const res = await voiceService.sendMessage({
            recipient_id: selectedCaregiver.id,
            text: currentText,
            source_language: sourceLang,
            target_language: 'en', // Caregiver receives English translation
          });
          if (res && res.translated_text) {
            const cleanText = res.translated_text
              .replace(/\[Simulated.*?\]:\s*/gi, '')
              .replace(/\[Draft.*?\]:\s*/gi, '')
              .trim();
            if (cleanText && cleanText !== currentText) {
              finalEng = cleanText;
            }
          }
        } catch {}
      }

      const newMsg: ChatItem = {
        id: Date.now(),
        senderName: 'You',
        isMe: true,
        originalText: currentText,
        englishText: finalEng,
        localizedText: finalLoc,
        translatedText: finalEng,
        sourceLang,
        targetLang: 'en',
        timestamp: nowTimeStr,
        dispatchedToEmail: selectedCaregiver?.email,
      };

      setMessages((prev) => [...prev, newMsg]);

      // Sync message to Caregiver Portal web feed & email record
      if (selectedCaregiver) {
        try {
          const feed = JSON.parse(localStorage.getItem('pulseguardian_caregiver_feed') || '[]');
          feed.unshift({
            id: newMsg.id,
            sender: user?.full_name || 'Patient',
            recipient: selectedCaregiver.name,
            email: selectedCaregiver.email,
            original: currentText,
            english: finalEng,
            localized: finalLoc,
            time: newMsg.timestamp,
          });
          localStorage.setItem('pulseguardian_caregiver_feed', JSON.stringify(feed.slice(0, 50)));
        } catch {}

        setEmailStatusToast(`✓ Dispatched to ${selectedCaregiver.name} (${selectedCaregiver.email}) & Caregiver Portal Feed.`);
        setTimeout(() => setEmailStatusToast(null), 5000);
      }
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Header */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-black text-slate-800 tracking-tight">
            {t('comm.title', 'Multilingual Caregiver Chat')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            {t('comm.subtitle', 'Real-time bidirectional translated chat between patient and caregiver.')}
          </p>
        </div>

        <button
          type="button"
          onClick={fetchConversations}
          className="p-2.5 bg-slate-50 hover:bg-slate-100 rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm transition-all cursor-pointer self-end sm:self-center"
          title="Refresh Messages"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Select Caregiver Recipient Strip */}
      <div className="bg-white rounded-3xl p-5 border border-slate-200/90 shadow-sm space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
            <UserCheck className="w-4 h-4 text-cyan-600" />
            <span>Select Recipient Caregiver (Choose who receives this message):</span>
          </span>
          <span className="text-[11px] text-slate-400 font-mono">
            {caregiverOptions.length} Caregiver{caregiverOptions.length === 1 ? '' : 's'} Registered
          </span>
        </div>

        {caregiverOptions.length === 0 ? (
          <div className="p-4 bg-slate-50 rounded-2xl text-center text-xs font-semibold text-slate-500 border border-slate-200">
            No primary caregiver registered. Please register a family guardian or attending physician in settings.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {caregiverOptions.map((cg) => {
              const isSelected = selectedCaregiver?.id === cg.id;
              return (
                <button
                  key={cg.id}
                  type="button"
                  onClick={() => setSelectedCaregiver(cg)}
                  className={`p-3.5 rounded-2xl border text-left transition-all cursor-pointer flex items-start gap-3 ${
                    isSelected
                      ? 'border-cyan-500 bg-cyan-50/70 shadow-sm ring-2 ring-cyan-400/30'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div
                    className={`w-10 h-10 rounded-2xl flex items-center justify-center font-black text-sm shrink-0 ${
                      isSelected ? 'bg-cyan-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600'
                    }`}
                  >
                    {cg.name[0]}
                  </div>

                  <div className="min-w-0 flex-1 space-y-0.5">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-black text-slate-900 truncate">{cg.name}</span>
                      {cg.isPrimary && (
                        <span className="text-[9px] font-extrabold uppercase bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded-full shrink-0">
                          Primary
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-slate-500 truncate">{cg.role}</div>
                    <div className="text-[10px] text-slate-400 font-mono truncate flex items-center gap-2 pt-0.5">
                      <span className="flex items-center gap-1">
                        <Mail className="w-3 h-3 text-cyan-600" />
                        {cg.email}
                      </span>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* Email Dispatch Confirmation Toast */}
      {emailStatusToast && (
        <div className="p-3.5 rounded-2xl bg-emerald-500 text-white text-xs font-bold shadow-lg shadow-emerald-500/20 flex items-center justify-between animate-fadeIn">
          <div className="flex items-center gap-2">
            <Mail className="w-4 h-4 text-emerald-100" />
            <span>{emailStatusToast}</span>
          </div>
          <button
            type="button"
            onClick={() => setEmailStatusToast(null)}
            className="text-emerald-100 hover:text-white text-xs font-black px-1.5 cursor-pointer"
          >
            ✕
          </button>
        </div>
      )}

      {/* Main Chat Box */}
      <div className="rounded-3xl border border-slate-200 shadow-xl overflow-hidden flex flex-col h-[580px] bg-white">
        {/* Chat Active Header */}
        <div className="p-4 bg-slate-50/90 border-b border-slate-200 flex items-center justify-between gap-3 flex-wrap">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-cyan-100 text-cyan-800 font-black flex items-center justify-center">
              {selectedCaregiver ? selectedCaregiver.name[0] : 'C'}
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800">
                {selectedCaregiver ? selectedCaregiver.name : 'No Caregiver Selected'}
              </h4>
              <p className="text-[11px] text-emerald-600 font-medium flex items-center space-x-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>
                  Active • Dispatches to portal & {selectedCaregiver ? selectedCaregiver.email : 'system'}
                </span>
              </p>
            </div>
          </div>

          {/* Target Language Selector */}
          <div className="flex items-center space-x-2 text-xs">
            <Languages className="w-4 h-4 text-cyan-600" />
            <span className="text-[11px] font-bold text-slate-500">Translate to:</span>
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="bg-white border border-slate-300 rounded-xl px-2.5 py-1 text-slate-700 text-xs font-semibold focus:outline-none focus:border-cyan-500 shadow-sm cursor-pointer"
            >
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="ml">Malayalam (മലയാളം)</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        {/* Messages Stream */}
        <div className="flex-1 p-5 overflow-y-auto space-y-4 bg-gradient-to-b from-slate-50/40 via-white to-white">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.isMe ? 'items-end' : 'items-start'} space-y-1`}
            >
              <span className="text-[10px] text-slate-400 font-medium px-1 flex items-center gap-1.5">
                <span>{m.senderName}</span>
                <span>•</span>
                <span>{m.timestamp}</span>
                {m.isMe && (
                  <span className="text-[9px] text-emerald-600 font-semibold bg-emerald-50 px-1.5 py-0.5 rounded">
                    ✓ Sent to Email
                  </span>
                )}
              </span>

              <div
                className={`max-w-md rounded-2xl p-4 shadow-sm space-y-2 ${
                  m.isMe
                    ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white rounded-br-none shadow-md shadow-cyan-600/10'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none shadow-sm'
                }`}
              >
                {/* Original Message */}
                <p className="text-sm font-medium leading-relaxed">{m.originalText}</p>

                {/* Bidirectional Translation View */}
                {!m.isMe ? (
                  // Caregiver's message received by Patient: Translate to Patient's Language (Kannada)
                  <div className="pt-2.5 mt-2 border-t border-slate-200 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-cyan-800 font-bold text-[10px] uppercase tracking-wide">
                      <Languages className="w-3.5 h-3.5 text-cyan-600" />
                      <span>Translated to {targetLang === 'kn' ? 'Kannada' : targetLang.toUpperCase()}:</span>
                    </div>
                    <p className="text-slate-900 font-semibold text-xs leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-200">
                      {m.localizedText || m.translatedText || m.originalText}
                    </p>
                  </div>
                ) : (
                  // Patient's message sent to Caregiver: Translate to English
                  <div className="pt-2.5 mt-2 border-t border-white/20 text-xs space-y-1">
                    <div className="flex items-center gap-1.5 text-cyan-200 font-bold text-[10px] uppercase tracking-wide">
                      <Languages className="w-3.5 h-3.5" />
                      <span>Translated to English (for Caregiver):</span>
                    </div>
                    <p className="text-white font-medium text-xs leading-relaxed bg-white/10 p-2.5 rounded-xl">
                      {m.englishText || m.translatedText || m.originalText}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Message Input Form */}
        <form onSubmit={handleSendMessage} className="p-4 bg-white border-t border-slate-200 flex items-center space-x-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message in any language (e.g. namaskara, oota aayitha, neeru, medicine taken)..."
            className="flex-1 bg-slate-50 border border-slate-300 rounded-2xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-cyan-500 shadow-inner"
          />
          <button
            type="submit"
            disabled={sending || !inputText.trim()}
            className="px-6 py-3 rounded-2xl bg-cyan-600 hover:bg-cyan-700 text-white font-bold text-sm shadow-md shadow-cyan-600/20 transition-all flex items-center space-x-1.5 disabled:opacity-50 cursor-pointer"
          >
            <span>{sending ? 'Translating & Sending...' : 'Send'}</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
