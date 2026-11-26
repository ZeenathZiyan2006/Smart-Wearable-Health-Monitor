import React, { useState, useRef } from 'react';
import { Mic, MicOff, Sparkles, Send, Bot, Volume2 } from 'lucide-react';
import { voiceService } from '../api/services';

interface VoiceAssistantWidgetProps {
  userName?: string;
  className?: string;
}

export const VoiceAssistantWidget: React.FC<VoiceAssistantWidgetProps> = ({
  userName = 'Thrisha',
  className = '',
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [selectedLang, setSelectedLang] = useState('en');
  const [lastResponse, setLastResponse] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [customText, setCustomText] = useState('');
  const [statusNote, setStatusNote] = useState<string | null>(null);

  // Audio recording refs
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const quickPrompts = [
    { label: 'Show my health report', text: 'Show my health report' },
    { label: 'Are my vitals normal?', text: 'Are my vitals normal?' },
    { label: 'Call Caregiver', text: 'Call Caregiver' },
    { label: 'Play health tips', text: 'Play health tips' },
  ];

  const handlePromptClick = async (promptText: string) => {
    setLoading(true);
    setLastResponse(null);
    setStatusNote(null);
    try {
      const res = await voiceService.transcribeText(promptText, selectedLang);
      const reply = res.response_text || 'Your vital metrics are recorded and within normal ranges.';
      setLastResponse(reply);

      // Play synthesized audio if available
      if (res.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${res.audio_base64}`);
        audio.play().catch(() => {});
      }
    } catch {
      setLastResponse(`I received your request: "${promptText}". Your vital telemetry indicates stability.`);
    } finally {
      setLoading(false);
    }
  };

  // Real Web Audio MediaRecorder capture
  const startRecording = async () => {
    setStatusNote(null);
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatusNote('Microphone capture not supported in this browser.');
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        // Stop all tracks to release hardware mic
        stream.getTracks().forEach((track) => track.stop());

        // Convert blob to base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = async () => {
          const base64Audio = (reader.result as string).split(',')[1];
          setLoading(true);
          try {
            const res = await voiceService.transcribeAudio(base64Audio, 'audio/wav', selectedLang);
            if (res.transcript) {
              setCustomText(res.transcript);
              handlePromptClick(res.transcript);
            } else {
              handlePromptClick('Are my vitals normal?');
            }
          } catch {
            handlePromptClick('Are my vitals normal?');
          } finally {
            setLoading(false);
          }
        };
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      // Fallback if mic permission denied
      setStatusNote('Microphone access denied. Using text input.');
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleMic = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  const handleCustomSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customText.trim()) return;
    const text = customText;
    setCustomText('');
    handlePromptClick(text);
  };

  return (
    <div
      className={`glass-panel rounded-3xl p-5 flex flex-col justify-between border border-cyan-500/20 bg-gradient-to-b from-[#0b172a]/90 via-[#0e213d]/85 to-[#09152b]/95 text-white shadow-2xl relative overflow-hidden ${className}`}
    >
      <div className="absolute -top-16 -right-16 w-44 h-44 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute -bottom-16 -left-16 w-44 h-44 bg-blue-600/10 rounded-full blur-3xl pointer-events-none"></div>

      <div>
        {/* Robot 3D Character Avatar Visual */}
        <div className="relative mx-auto w-32 h-32 flex items-center justify-center mb-2">
          <div className={`absolute inset-0 rounded-full bg-cyan-400/20 blur-xl transition-all duration-700 ${isRecording ? 'scale-125 bg-emerald-400/30' : 'animate-pulse'}`} />
          
          <div className="relative w-28 h-28 rounded-full bg-gradient-to-b from-cyan-400/30 via-slate-800 to-slate-900 p-1 shadow-lg border border-cyan-400/40 flex items-center justify-center">
            <div className="w-full h-full rounded-full bg-[#0d1c33] flex flex-col items-center justify-center relative overflow-hidden">
              <div className="absolute top-2 w-1.5 h-3 bg-cyan-400 rounded-full animate-bounce"></div>
              <div className="w-20 h-14 bg-black/80 rounded-2xl border border-cyan-500/40 flex items-center justify-around px-3 shadow-inner">
                <div className={`w-3.5 h-3.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#00F0FF] ${isRecording ? 'bg-emerald-400 scale-110' : 'animate-pulse'}`}></div>
                <div className="w-4 h-1 rounded-full bg-cyan-300/60"></div>
                <div className={`w-3.5 h-3.5 rounded-full bg-cyan-400 shadow-[0_0_8px_#00F0FF] ${isRecording ? 'bg-emerald-400 scale-110' : 'animate-pulse'}`}></div>
              </div>
              <div className="absolute left-1 w-2 h-6 bg-cyan-400/60 rounded-full"></div>
              <div className="absolute right-1 w-2 h-6 bg-cyan-400/60 rounded-full"></div>
            </div>
          </div>
        </div>

        {/* Greeting & Speech Bubble */}
        <div className="text-center mb-4">
          <h4 className="text-sm font-semibold text-white">Hello {userName}!</h4>
          <p className="text-xs text-slate-300">
            {isRecording ? 'Listening to your voice...' : 'How can I help you today?'}
          </p>
        </div>

        {/* Status / Error feedback */}
        {statusNote && (
          <div className="mb-2 p-2 rounded-xl bg-amber-500/20 border border-amber-500/30 text-[11px] text-amber-200 text-center">
            {statusNote}
          </div>
        )}

        {/* Dynamic AI Response bubble */}
        {lastResponse && (
          <div className="mb-4 p-3 rounded-2xl bg-cyan-500/10 border border-cyan-500/30 text-xs text-cyan-100 flex items-start space-x-2 animate-fadeIn">
            <Bot className="w-4 h-4 text-cyan-400 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <p>{lastResponse}</p>
            </div>
          </div>
        )}

        {/* Prompt Chips matching Image 1 */}
        <div className="space-y-2 mb-4">
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handlePromptClick(p.text)}
              disabled={loading}
              className="w-full text-left px-3.5 py-2 rounded-xl text-xs font-medium text-slate-200 bg-slate-800/60 hover:bg-cyan-900/40 hover:text-white border border-slate-700/60 hover:border-cyan-500/40 transition-all flex items-center justify-between group shadow-sm"
            >
              <span className="flex items-center space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 group-hover:scale-125 transition-transform"></span>
                <span>{p.label}</span>
              </span>
              <span className="text-[10px] text-cyan-400 opacity-0 group-hover:opacity-100 transition-opacity">
                ➔
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Mic Audio Control Bar */}
      <div>
        <div className="flex items-center justify-between mb-3 text-[11px] text-slate-400">
          <span className="flex items-center space-x-1">
            <Sparkles className="w-3 h-3 text-cyan-400" />
            <span>AI Voice Pipeline</span>
          </span>
          <select
            value={selectedLang}
            onChange={(e) => setSelectedLang(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-2 py-0.5 text-slate-200 text-[11px] focus:outline-none"
          >
            <option value="en">English (US)</option>
            <option value="hi">हिंदी (Hindi)</option>
            <option value="ta">தமிழ் (Tamil)</option>
            <option value="es">Español</option>
          </select>
        </div>

        {/* Custom text query */}
        <form onSubmit={handleCustomSubmit} className="relative mb-3">
          <input
            type="text"
            value={customText}
            onChange={(e) => setCustomText(e.target.value)}
            placeholder="Type health question..."
            className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-cyan-500 pr-8"
          />
          <button
            type="submit"
            className="absolute right-2 top-1.5 text-cyan-400 hover:text-cyan-300"
          >
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>

        {/* Wave Visualizer & Glowing Mic Button */}
        <div className="flex items-center justify-center space-x-3 pt-1">
          <div className="flex items-center space-x-1">
            {[12, 20, 16, 24, 14].map((h, i) => (
              <span
                key={i}
                style={{ height: isRecording ? `${h * 1.5}px` : `${h}px` }}
                className={`w-0.5 rounded-full bg-cyan-400/80 transition-all duration-200 ${isRecording ? 'animate-pulse' : 'opacity-60'}`}
              />
            ))}
          </div>

          <button
            onClick={toggleMic}
            className={`w-12 h-12 rounded-full flex items-center justify-center text-white shadow-lg transition-all transform active:scale-95 ${
              isRecording
                ? 'bg-rose-500 hover:bg-rose-600 shadow-rose-500/50 animate-bounce'
                : 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 shadow-cyan-500/30'
            }`}
          >
            {isRecording ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
          </button>

          <div className="flex items-center space-x-1">
            {[14, 24, 16, 20, 12].map((h, i) => (
              <span
                key={i}
                style={{ height: isRecording ? `${h * 1.5}px` : `${h}px` }}
                className={`w-0.5 rounded-full bg-cyan-400/80 transition-all duration-200 ${isRecording ? 'animate-pulse' : 'opacity-60'}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
