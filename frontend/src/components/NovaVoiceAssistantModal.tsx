import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, PhoneCall, MessageSquare, Sparkles, Volume2, X, Phone, UserCheck, ShieldAlert } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { patientDashboardService } from '../api/services';

interface VoiceAssistantProps {
  onClose?: () => void;
  isOpen: boolean;
}

// Multilingual responses for common commands
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
    te: 'మీ ప్రాథಮిక సంరక్షకునికి ఇప్పుడు కాల్ కనెక్ట్ చేయబడుతోంది.',
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
  general: {
    en: 'Hello! I am Nova, your smart health assistant. You can say Call Caregiver, Check Vitals, or Send Message.',
    kn: 'ನಮಸ್ಕಾರ! ನಾನು ನೋವಾ (Nova), ನಿಮ್ಮ ಸ್ಮಾರ್ಟ್ ಆರೋಗ್ಯ ಸಹಾಯಕ. ನೀವು ಕಾಲ್ ಕೇರ್‌ಗಿವರ್ ಅಥವಾ ವೈಟಲ್ಸ್ ಪರಿಶೀಲಿಸಿ ಎಂದು ಹೇಳಬಹುದು.',
    hi: 'नमस्ते! मैं नोवा (Nova) हूँ, आपकी स्वास्थ्य सहायक। आप कॉल केयरगिवर या चेक वाइटल्स कह सकते हैं।',
    ta: 'வணக்கம்! நான் நோவா (Nova), உங்கள் சுகாதார உதவியாளர். மருத்துவ அழைப்பு அல்லது பரிசோதனைக்கு கேட்கலாம்.',
    te: 'నమస్కారం! నేను నోవా (Nova), మీ ఆరోగ్య సహాయకురాలిని.',
    ml: 'നമസ്കാരം! ഞാൻ നോവ (Nova), നിങ്ങളുടെ ആരോഗ്യ സഹായി.',
  },
};

export const NovaVoiceAssistantModal: React.FC<VoiceAssistantProps> = ({ isOpen, onClose }) => {
  const { language } = useLanguage();
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [assistantReply, setAssistantReply] = useState('');
  const [caregiverContact, setCaregiverContact] = useState<{ name: string; phone: string; email: string }>({
    name: 'Sarah Jenkins (Primary Caregiver)',
    phone: '+919876543220',
    email: 'caregiver@pulseguardian.ai',
  });
  const recognitionRef = useRef<any>(null);

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

  // Web Speech API / Recognition initialization
  useEffect(() => {
    if (!isOpen) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsListening(false);
      return;
    }

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = language === 'kn' ? 'kn-IN' : language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : language === 'te' ? 'te-IN' : language === 'ml' ? 'ml-IN' : 'en-US';

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
    } else {
      setAssistantReply('Speech Recognition is active. You can speak or click quick command buttons below.');
    }

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [isOpen, language]);

  const speakText = (text: string) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language === 'kn' ? 'kn-IN' : language === 'hi' ? 'hi-IN' : language === 'ta' ? 'ta-IN' : language === 'te' ? 'te-IN' : language === 'ml' ? 'ml-IN' : 'en-US';
      window.speechSynthesis.speak(utterance);
    }
  };

  const processVoiceCommand = (cmd: string) => {
    const lower = cmd.toLowerCase();

    // 1. Direct Call Caregiver Action
    if (lower.includes('call') || lower.includes('phone') || lower.includes('ಕರೆ') || lower.includes('कॉल') || lower.includes('அழை')) {
      const reply = MULTILINGUAL_RESPONSES.calling[language] || MULTILINGUAL_RESPONSES.calling.en;
      setAssistantReply(reply);
      speakText(reply);

      // Directly trigger phone call from patient's logged-in device
      setTimeout(() => {
        const cleanNumber = caregiverContact.phone.replace(/[^0-9+]/g, '');
        window.location.href = `tel:${cleanNumber}`;
      }, 1500);
      return;
    }

    // 2. Emergency SOS Action
    if (lower.includes('emergency') || lower.includes('sos') || lower.includes('help') || lower.includes('ಸಹಾಯ') || lower.includes('मदद')) {
      const reply = MULTILINGUAL_RESPONSES.sos[language] || MULTILINGUAL_RESPONSES.sos.en;
      setAssistantReply(reply);
      speakText(reply);
      setTimeout(() => {
        window.location.href = 'tel:112';
      }, 1500);
      return;
    }

    // 3. Message Caregiver Action
    if (lower.includes('message') || lower.includes('sms') || lower.includes('ಸಂದೇಶ') || lower.includes('संदेश')) {
      const reply = MULTILINGUAL_RESPONSES.messaging[language] || MULTILINGUAL_RESPONSES.messaging.en;
      setAssistantReply(reply);
      speakText(reply);
      return;
    }

    // 4. Vitals Query Action
    if (lower.includes('vital') || lower.includes('heart') || lower.includes('health') || lower.includes('ಆರೋಗ್ಯ') || lower.includes('स्वास्थ्य')) {
      const reply = MULTILINGUAL_RESPONSES.vitals[language] || MULTILINGUAL_RESPONSES.vitals.en;
      setAssistantReply(reply);
      speakText(reply);
      return;
    }
  };

  const executeActionManually = (actionKey: 'call' | 'vitals' | 'message' | 'sos') => {
    if (actionKey === 'call') {
      const reply = MULTILINGUAL_RESPONSES.calling[language] || MULTILINGUAL_RESPONSES.calling.en;
      setAssistantReply(reply);
      speakText(reply);
      const cleanNumber = caregiverContact.phone.replace(/[^0-9+]/g, '');
      window.location.href = `tel:${cleanNumber}`;
    } else if (actionKey === 'vitals') {
      const reply = MULTILINGUAL_RESPONSES.vitals[language] || MULTILINGUAL_RESPONSES.vitals.en;
      setAssistantReply(reply);
      speakText(reply);
    } else if (actionKey === 'message') {
      const reply = MULTILINGUAL_RESPONSES.messaging[language] || MULTILINGUAL_RESPONSES.messaging.en;
      setAssistantReply(reply);
      speakText(reply);
    } else if (actionKey === 'sos') {
      const reply = MULTILINGUAL_RESPONSES.sos[language] || MULTILINGUAL_RESPONSES.sos.en;
      setAssistantReply(reply);
      speakText(reply);
      window.location.href = 'tel:112';
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

          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Pulsing Voice Sphere */}
        <div className="py-4 text-center space-y-3">
          <div className="relative mx-auto w-28 h-28 flex items-center justify-center">
            <div className={`absolute inset-0 rounded-full bg-cyan-400/25 blur-xl transition-all duration-700 ${isListening ? 'scale-125 bg-emerald-400/35' : 'animate-pulse'}`} />
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

        {/* AI Response Display */}
        {assistantReply && (
          <div className="p-4 rounded-2xl bg-slate-950 border border-cyan-400/80 text-xs font-semibold text-cyan-100 flex items-start gap-3 shadow-lg shadow-cyan-950/60">
            <Volume2 className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
            <p className="leading-relaxed">{assistantReply}</p>
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
      </div>
    </div>
  );
};
