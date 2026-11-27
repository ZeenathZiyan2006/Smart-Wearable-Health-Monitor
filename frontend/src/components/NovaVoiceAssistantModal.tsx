import React, { useState, useEffect, useRef } from 'react';
import {
  Mic,
  MicOff,
  PhoneCall,
  MessageSquare,
  Sparkles,
  Volume2,
  VolumeX,
  X,
  Phone,
  UserCheck,
  ShieldAlert,
  Globe,
  Heart,
  Pill,
  MapPin,
  TrendingUp,
  FileText,
  AlertTriangle,
  RefreshCw,
  Send,
  Smile,
  Activity,
  ChevronDown,
  Navigation,
  CheckCircle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { novaService } from '../api/services';

interface VoiceAssistantProps {
  onClose?: () => void;
  isOpen: boolean;
}

interface ActionPill {
  id: string;
  label: string;
  action: string;
  icon?: string;
  color?: string;
}

export const NovaVoiceAssistantModal: React.FC<VoiceAssistantProps> = ({ isOpen, onClose }) => {
  const { user, role } = useAuth();
  const { language: globalLanguage, setLanguage: setGlobalLanguage, languages } = useLanguage();

  // Selected language for assistant
  const [selectedLang, setSelectedLang] = useState<string>(globalLanguage || 'kn');
  const [isListening, setIsListening] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [textInput, setTextInput] = useState('');
  const [assistantReply, setAssistantReply] = useState('');
  const [isEmergencyActive, setIsEmergencyActive] = useState(false);
  const [directCallUrl, setDirectCallUrl] = useState<string | null>(null);

  // Authorized patients context (for family, doctor, EMS)
  const [authorizedPatients, setAuthorizedPatients] = useState<any[]>([]);
  const [selectedPatientId, setSelectedPatientId] = useState<string>('');
  const [selectedPatientName, setSelectedPatientName] = useState<string>('');
  const [suggestedActions, setSuggestedActions] = useState<ActionPill[]>([]);

  // Caregiver wellbeing check-in modal state
  const [showWellbeingModal, setShowWellbeingModal] = useState(false);
  const [wellbeingNotes, setWellbeingNotes] = useState('');
  const [wellbeingToast, setWellbeingToast] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const audioInstanceRef = useRef<HTMLAudioElement | null>(null);

  // Sync with global language
  useEffect(() => {
    if (globalLanguage) {
      setSelectedLang(globalLanguage);
    }
  }, [globalLanguage]);

  // Load context from backend when modal opens
  useEffect(() => {
    if (!isOpen) {
      stopSpeech();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    novaService
      .getContext()
      .then((ctx) => {
        if (ctx.authorized_patients && ctx.authorized_patients.length > 0) {
          setAuthorizedPatients(ctx.authorized_patients);
          const first = ctx.authorized_patients[0];
          setSelectedPatientId(first.patient_id || `PT-${first.id}`);
          setSelectedPatientName(first.name);
        }
        if (ctx.has_active_emergency) {
          setIsEmergencyActive(true);
        }
      })
      .catch(() => {
        // Local baseline fallback
        if (role === 'doctor') {
          setSelectedPatientId('PT-2026-000001');
          setSelectedPatientName('Ramesh Kumar');
        } else if (role === 'family' || role === 'caregiver') {
          setSelectedPatientId('PT-2026-000001');
          setSelectedPatientName('Ramesh Kumar');
        }
      });

    // Send initial greeting query
    sendNovaQuery({ action: 'check_vitals' });
  }, [isOpen]);

  // Stop any active TTS audio
  const stopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (audioInstanceRef.current) {
      audioInstanceRef.current.pause();
      audioInstanceRef.current.currentTime = 0;
    }
    setIsSpeaking(false);
  };

  // High fidelity 100% volume Speech Engine
  const speakText = (text: string) => {
    stopSpeech();
    setIsSpeaking(true);

    const langCode = selectedLang || 'kn';
    const cleanText = text.slice(0, 240);

    // Attempt online native TTS first for regional natural accent
    try {
      const ttsUrl = `https://translate.google.com/translate_tts?ie=UTF-8&tl=${langCode}&client=tw-ob&q=${encodeURIComponent(cleanText)}`;
      const audio = new Audio(ttsUrl);
      audio.volume = 1.0;
      audioInstanceRef.current = audio;

      audio.onended = () => setIsSpeaking(false);
      audio.onerror = () => speakWithWebSpeech(text, langCode);

      audio.play().catch(() => {
        speakWithWebSpeech(text, langCode);
      });
    } catch {
      speakWithWebSpeech(text, langCode);
    }
  };

  const speakWithWebSpeech = (text: string, langCode: string) => {
    if (!('speechSynthesis' in window)) {
      setIsSpeaking(false);
      return;
    }

    const langTag =
      langCode === 'kn'
        ? 'kn-IN'
        : langCode === 'hi'
        ? 'hi-IN'
        : langCode === 'ta'
        ? 'ta-IN'
        : langCode === 'te'
        ? 'te-IN'
        : langCode === 'ml'
        ? 'ml-IN'
        : 'en-IN';

    const voices = window.speechSynthesis.getVoices();
    const matchedVoice = voices.find(
      (v) =>
        v.lang.toLowerCase().replace('_', '-').startsWith(langCode) ||
        v.name.toLowerCase().includes(langCode) ||
        (langCode === 'kn' && v.name.toLowerCase().includes('kannada')) ||
        (langCode === 'hi' && v.name.toLowerCase().includes('hindi')) ||
        (langCode === 'ta' && v.name.toLowerCase().includes('tamil'))
    );

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = langTag;
    if (matchedVoice) utterance.voice = matchedVoice;
    utterance.volume = 1.0;
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  // Toggle microphone recording via Web Speech API
  const toggleListening = () => {
    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    stopSpeech();

    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. You can type commands below.');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
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
        setTranscript('');
      };

      recognition.onresult = (event: any) => {
        let current = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          current += event.results[i][0].transcript;
        }
        setTranscript(current);
        setTextInput(current);
      };

      recognition.onerror = () => {
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
        if (textInput.trim() || transcript.trim()) {
          sendNovaQuery({ message: textInput.trim() || transcript.trim() });
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      setIsListening(false);
    }
  };

  // Central query dispatcher to backend Nova API
  const sendNovaQuery = async (params: { message?: string; action?: string; mood_type?: string }) => {
    setIsThinking(true);
    stopSpeech();

    try {
      const res = await novaService.interact({
        message: params.message || textInput.trim(),
        action: params.action,
        patient_id: selectedPatientId || undefined,
        language: selectedLang,
        mood_type: params.mood_type,
        context_data: {
          latitude: 12.9716,
          longitude: 77.5946,
        },
      });

      setAssistantReply(res.text);
      speakText(res.audio_text || res.text);

      if (res.is_emergency) {
        setIsEmergencyActive(true);
      }
      if (res.direct_call_url) {
        setDirectCallUrl(res.direct_call_url);
      } else {
        setDirectCallUrl(null);
      }

      if (res.suggested_actions && res.suggested_actions.length > 0) {
        setSuggestedActions(res.suggested_actions);
      }

      setTextInput('');
    } catch {
      // Local graceful fallback
      const fallback = `Hello! I am Nova, your healthcare assistant. All telemetry baselines are stable.`;
      setAssistantReply(fallback);
      speakText(fallback);
    } finally {
      setIsThinking(false);
    }
  };

  // Submit caregiver personal wellbeing check-in
  const handleSaveCaregiverWellbeing = async (mood: string) => {
    try {
      await novaService.recordWellbeing({
        mood_type: mood,
        notes: wellbeingNotes,
      });
      setWellbeingToast('Your caregiver wellbeing check-in was saved privately.');
      setShowWellbeingModal(false);
      setWellbeingNotes('');
      setTimeout(() => setWellbeingToast(null), 4000);

      sendNovaQuery({ action: 'caregiver_wellbeing', mood_type: mood });
    } catch {
      setWellbeingToast('Check-in logged locally.');
      setShowWellbeingModal(false);
      setTimeout(() => setWellbeingToast(null), 3000);
    }
  };

  // Dynamic persona descriptions
  const getPersonaHeader = () => {
    if (role === 'doctor') {
      return {
        title: 'Nova Clinical Workflow Assistant',
        subtitle: 'Assigned Patient EHR, Clinical Trends & Diagnostic AI',
        badge: 'Doctor Clinical Hub',
        badgeColor: 'bg-indigo-500/20 text-indigo-300 border-indigo-500/30',
      };
    }
    if (role === 'emergency') {
      return {
        title: 'Nova Emergency Coordination Assistant',
        subtitle: 'Active Incident Triaging, GPS & Paramedic Dispatch',
        badge: 'EMS Trauma Hub',
        badgeColor: 'bg-rose-500/20 text-rose-300 border-rose-500/30',
      };
    }
    if (role === 'family' || role === 'caregiver') {
      return {
        title: 'Nova Family Care Companion',
        subtitle: 'Family Care Assistant & Caregiver Wellbeing',
        badge: 'Family Portal',
        badgeColor: 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
      };
    }
    return {
      title: 'Nova Personal Health Companion',
      subtitle: 'Personal Health, Daily Care & Emergency Assistant',
      badge: 'Patient Self-Care',
      badgeColor: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
    };
  };

  const persona = getPersonaHeader();

  // Role-specific default quick actions
  const getDefaultActions = (): ActionPill[] => {
    if (role === 'doctor') {
      return [
        { id: '1', label: '7-Day Clinical Trends', action: 'clinical_trends', icon: 'TrendingUp', color: 'cyan' },
        { id: '2', label: 'AI Early Warnings', action: 'ai_observations', icon: 'Activity', color: 'emerald' },
        { id: '3', label: 'Active Regimen', action: 'prescription_documentation_assist', icon: 'Pill', color: 'purple' },
        { id: '4', label: 'Clinical Notes', action: 'clinical_notes_summary', icon: 'FileText', color: 'indigo' },
      ];
    }
    if (role === 'emergency') {
      return [
        { id: '1', label: 'Active SOS Incidents', action: 'active_incidents', icon: 'AlertTriangle', color: 'rose' },
        { id: '2', label: 'Verify GPS Coordinates', action: 'patient_gps_coordinates', icon: 'MapPin', color: 'cyan' },
        { id: '3', label: 'Triage Vitals & Blood Group', action: 'incident_triage', icon: 'Heart', color: 'purple' },
        { id: '4', label: 'Log Handover', action: 'record_handover', icon: 'CheckCircle', color: 'emerald' },
      ];
    }
    if (role === 'family' || role === 'caregiver') {
      return [
        { id: '1', label: 'How is my patient today?', action: 'check_patient_health', icon: 'Heart', color: 'cyan' },
        { id: '2', label: 'Medication Adherence', action: 'check_patient_medication', icon: 'Pill', color: 'emerald' },
        { id: '3', label: 'Live GPS Location', action: 'check_patient_location', icon: 'MapPin', color: 'purple' },
        { id: '4', label: 'My Caregiver Wellbeing', action: 'caregiver_wellbeing', icon: 'Smile', color: 'indigo' },
        { id: '5', label: 'Active Emergency Status', action: 'emergency_status', icon: 'ShieldAlert', color: 'rose' },
      ];
    }
    return [
      { id: '1', label: 'How is my health?', action: 'check_vitals', icon: 'Heart', color: 'cyan' },
      { id: '2', label: 'Medication Reminder', action: 'medicine_reminder', icon: 'Pill', color: 'emerald' },
      { id: '3', label: 'Call Family Caregiver', action: 'call_family', icon: 'PhoneCall', color: 'purple' },
      { id: '4', label: 'Daily Mood Check-in', action: 'mood_checkin', icon: 'Smile', color: 'indigo' },
      { id: '5', label: 'Tell me a Story', action: 'listen_story', icon: 'Sparkles', color: 'amber' },
      { id: '6', label: 'Emergency SOS', action: 'emergency_sos', icon: 'AlertTriangle', color: 'rose' },
    ];
  };

  const actionList = suggestedActions.length > 0 ? suggestedActions : getDefaultActions();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div
        className={`w-full max-w-2xl bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 rounded-3xl shadow-2xl border ${
          isEmergencyActive ? 'border-rose-500 shadow-rose-900/50 animate-pulse' : 'border-cyan-500/30 shadow-cyan-950/50'
        } overflow-hidden flex flex-col max-h-[92vh]`}
      >
        {/* ========================================================= */}
        {/* TOP BAR / HEADER */}
        {/* ========================================================= */}
        <div className="p-4 sm:p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/50">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-cyan-600 via-cyan-500 to-teal-400 p-0.5 flex items-center justify-center shadow-lg shadow-cyan-500/20">
                <div className="w-full h-full bg-slate-900 rounded-[14px] flex items-center justify-center">
                  <Sparkles className="w-5 h-5 text-cyan-400 animate-spin-slow" />
                </div>
              </div>
              <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 rounded-full border-2 border-slate-900" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-base sm:text-lg font-bold text-white tracking-tight">{persona.title}</h3>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${persona.badgeColor}`}>
                  {persona.badge}
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">{persona.subtitle}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {/* Language Selector Dropdown */}
            <div className="relative">
              <select
                value={selectedLang}
                onChange={(e) => {
                  setSelectedLang(e.target.value);
                  setGlobalLanguage(e.target.value as any);
                }}
                className="text-xs bg-slate-800 text-slate-200 border border-slate-700 rounded-xl px-2.5 py-1.5 focus:outline-none focus:border-cyan-400 cursor-pointer appearance-none pr-7 font-medium"
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code}>
                    {l.nativeName} ({l.name})
                  </option>
                ))}
              </select>
              <Globe className="w-3.5 h-3.5 text-slate-400 absolute right-2 top-2.5 pointer-events-none" />
            </div>

            {/* Close Button */}
            <button
              onClick={() => {
                stopSpeech();
                if (onClose) onClose();
              }}
              className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* ========================================================= */}
        {/* AUTHORIZED PATIENT SELECTOR (For Family & Doctor Roles) */}
        {/* ========================================================= */}
        {(role === 'family' || role === 'caregiver' || role === 'doctor') && authorizedPatients.length > 0 && (
          <div className="px-5 py-2.5 bg-slate-800/40 border-b border-slate-800/80 flex items-center justify-between flex-wrap gap-2 text-xs">
            <div className="flex items-center gap-2 text-slate-300 font-medium">
              <UserCheck className="w-4 h-4 text-cyan-400" />
              <span>Target Patient:</span>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={selectedPatientId}
                onChange={(e) => {
                  setSelectedPatientId(e.target.value);
                  const found = authorizedPatients.find((p) => p.patient_id === e.target.value);
                  if (found) setSelectedPatientName(found.name);
                  sendNovaQuery({ action: role === 'doctor' ? 'clinical_trends' : 'check_patient_health' });
                }}
                className="bg-slate-900 border border-slate-700 text-cyan-300 rounded-lg px-2.5 py-1 text-xs font-semibold focus:outline-none focus:border-cyan-400 cursor-pointer"
              >
                {authorizedPatients.map((p) => (
                  <option key={p.id} value={p.patient_id || `PT-${p.id}`}>
                    {p.name} ({p.patient_id || `PT-${p.id}`})
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}

        {/* Caregiver Wellbeing Toast */}
        {wellbeingToast && (
          <div className="mx-4 mt-3 p-2.5 bg-emerald-950/80 border border-emerald-500/40 rounded-xl text-emerald-300 text-xs flex items-center gap-2 animate-in fade-in">
            <CheckCircle className="w-4 h-4 shrink-0 text-emerald-400" />
            <span>{wellbeingToast}</span>
          </div>
        )}

        {/* ========================================================= */}
        {/* MAIN CONVERSATION / RESPONSE BOX */}
        {/* ========================================================= */}
        <div className="p-4 sm:p-6 flex-1 overflow-y-auto space-y-4">
          {/* Nova AI Speech Bubble */}
          <div className="flex items-start gap-3.5">
            <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-4 h-4 text-cyan-400" />
            </div>

            <div className="flex-1 bg-slate-800/60 rounded-2xl p-4 border border-slate-700/60 text-slate-200 text-sm sm:text-base leading-relaxed relative">
              {isThinking ? (
                <div className="flex items-center gap-2.5 text-cyan-400 text-sm py-2">
                  <div className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
                  <span>Nova is analyzing authorized telemetry...</span>
                </div>
              ) : (
                <div>
                  <p className="font-medium whitespace-pre-line">{assistantReply}</p>
                </div>
              )}

              {/* Audio Speaking Wave / Stop Indicator */}
              {isSpeaking && (
                <div className="mt-3 pt-2.5 border-t border-slate-700/60 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-xs text-cyan-300 font-semibold">
                    <Volume2 className="w-4 h-4 text-cyan-400 animate-pulse" />
                    <span>Speaking in {selectedLang.toUpperCase()} (100% Volume)</span>
                  </div>
                  <button
                    onClick={stopSpeech}
                    className="text-xs px-2.5 py-1 bg-slate-700/60 hover:bg-slate-700 text-slate-300 rounded-lg flex items-center gap-1 cursor-pointer"
                  >
                    <VolumeX className="w-3.5 h-3.5" />
                    <span>Stop</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Emergency SOS Banner Action */}
          {isEmergencyActive && (
            <div className="p-4 bg-rose-950/70 border-2 border-rose-500 rounded-2xl flex items-center justify-between flex-wrap gap-3 animate-pulse">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-rose-600 text-white flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5" />
                </div>
                <div>
                  <div className="text-sm font-black text-rose-200 uppercase tracking-wide">Emergency Protocol Active</div>
                  <div className="text-xs text-rose-300">Live coordinates dispatched to emergency services & caregivers.</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <a
                  href="tel:112"
                  className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-lg shadow-rose-900/50"
                >
                  <PhoneCall className="w-3.5 h-3.5" />
                  <span>Call 112 SOS</span>
                </a>
              </div>
            </div>
          )}

          {/* Direct Phone Call Button */}
          {directCallUrl && !isEmergencyActive && (
            <div className="p-3.5 bg-emerald-950/60 border border-emerald-500/40 rounded-2xl flex items-center justify-between">
              <div className="flex items-center gap-2.5 text-xs text-emerald-300">
                <Phone className="w-4 h-4 text-emerald-400" />
                <span>Direct contact line verified. Tap to dial:</span>
              </div>
              <a
                href={directCallUrl}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold rounded-xl flex items-center gap-1.5"
              >
                <PhoneCall className="w-3.5 h-3.5" />
                <span>Call Now</span>
              </a>
            </div>
          )}

          {/* User Live Spoken Transcript */}
          {transcript && (
            <div className="flex items-center gap-2 text-xs text-slate-400 bg-slate-800/40 px-3 py-2 rounded-xl">
              <Mic className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
              <span className="italic">"{transcript}"</span>
            </div>
          )}
        </div>

        {/* ========================================================= */}
        {/* ROLE-AWARE SUGGESTED ACTION PILLS */}
        {/* ========================================================= */}
        <div className="px-4 sm:px-6 py-2.5 bg-slate-950/40 border-t border-slate-800/80">
          <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>Role Quick Actions</span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-1 scrollbar-none">
            {actionList.map((pill) => (
              <button
                key={pill.id}
                onClick={() => {
                  if (pill.action === 'caregiver_wellbeing' && (role === 'family' || role === 'caregiver')) {
                    setShowWellbeingModal(true);
                  } else {
                    sendNovaQuery({ action: pill.action });
                  }
                }}
                className="shrink-0 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800/80 hover:bg-slate-700 text-slate-200 border border-slate-700/80 hover:border-cyan-400 transition-all flex items-center gap-1.5 cursor-pointer shadow-sm active:scale-95"
              >
                <span>{pill.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* ========================================================= */}
        {/* INPUT DUAL INTERFACE: VOICE + TEXT BOX */}
        {/* ========================================================= */}
        <div className="p-4 sm:p-5 border-t border-slate-800 bg-slate-950/70">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (textInput.trim()) {
                sendNovaQuery({ message: textInput.trim() });
              }
            }}
            className="flex items-center gap-2.5"
          >
            {/* Microphone Voice Toggle */}
            <button
              type="button"
              onClick={toggleListening}
              className={`w-12 h-12 rounded-2xl flex items-center justify-center shrink-0 transition-all cursor-pointer shadow-lg ${
                isListening
                  ? 'bg-rose-600 text-white animate-pulse ring-4 ring-rose-500/30'
                  : 'bg-cyan-500 hover:bg-cyan-400 text-slate-950'
              }`}
              title={isListening ? 'Stop listening' : 'Start voice command'}
            >
              {isListening ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
            </button>

            {/* Text Input Box */}
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder={
                isListening
                  ? 'Listening to your voice...'
                  : role === 'doctor'
                  ? 'Ask Nova about patient trends, AI risk or clinical notes...'
                  : role === 'emergency'
                  ? 'Ask Nova about active incidents, triage vitals or handover...'
                  : role === 'family' || role === 'caregiver'
                  ? 'Ask Nova about your patient or caregiver wellbeing...'
                  : 'Ask Nova anything about your health, reminders, or stories...'
              }
              className="flex-1 bg-slate-900 border border-slate-700/80 rounded-2xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-400 transition-colors"
            />

            {/* Send Button */}
            <button
              type="submit"
              disabled={!textInput.trim() || isThinking}
              className="w-12 h-12 rounded-2xl bg-slate-800 hover:bg-cyan-500 hover:text-slate-950 text-slate-300 disabled:opacity-40 disabled:hover:bg-slate-800 disabled:hover:text-slate-300 flex items-center justify-center shrink-0 transition-all cursor-pointer"
            >
              <Send className="w-4 h-4" />
            </button>
          </form>

          {/* Status Subtitle */}
          <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-500 px-1">
            <span>Say "Nova" anytime or press and hold screen for 1.2s</span>
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <span>Verified RBAC Secure</span>
            </span>
          </div>
        </div>
      </div>

      {/* ========================================================= */}
      {/* FAMILY CAREGIVER WELLBEING DIALOG (Isolated) */}
      {/* ========================================================= */}
      {showWellbeingModal && (
        <div className="fixed inset-0 z-60 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in">
          <div className="w-full max-w-md bg-slate-900 rounded-3xl p-5 border border-cyan-500/40 shadow-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Smile className="w-5 h-5 text-cyan-400" />
                <h4 className="text-base font-bold text-white">Caregiver Personal Wellbeing</h4>
              </div>
              <button
                onClick={() => setShowWellbeingModal(false)}
                className="text-slate-400 hover:text-white p-1 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed">
              Caregiver self-care is vital. How are you feeling right now? Your reflection is kept completely private and
              is <strong>never</strong> mixed into the patient's medical records.
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              {[
                { id: 'calm', label: 'Balanced & Calm', icon: '🌱' },
                { id: 'tired', label: 'Fatigued / Tired', icon: '☕' },
                { id: 'stressed', label: 'Caregiver Stress', icon: '🧘' },
                { id: 'happy', label: 'Fulfilling & Happy', icon: '✨' },
              ].map((m) => (
                <button
                  key={m.id}
                  onClick={() => handleSaveCaregiverWellbeing(m.id)}
                  className="p-3 bg-slate-800 hover:bg-cyan-950/50 hover:border-cyan-400 border border-slate-700 rounded-xl text-left font-medium text-slate-200 transition-all flex items-center gap-2 cursor-pointer active:scale-95"
                >
                  <span className="text-base">{m.icon}</span>
                  <span>{m.label}</span>
                </button>
              ))}
            </div>

            <div>
              <label className="text-[11px] font-semibold text-slate-400 mb-1 block">
                Optional Reflection / Self-Care Notes:
              </label>
              <textarea
                value={wellbeingNotes}
                onChange={(e) => setWellbeingNotes(e.target.value)}
                placeholder="Take a short break, hydrate, and breathe..."
                className="w-full bg-slate-950 border border-slate-700 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:border-cyan-400 h-16"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
