import React, { useState, useEffect, useRef } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from '../components/Sidebar';
import { Header } from '../components/Header';
import { NovaVoiceAssistantModal } from '../components/NovaVoiceAssistantModal';
import { Mic, Sparkles } from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const [isNovaOpen, setIsNovaOpen] = useState(false);
  const longPressTimerRef = useRef<any>(null);
  const wakeWordRecognitionRef = useRef<any>(null);

  // Background passive wake-word listener for "Nova"
  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      try {
        const recognizer = new SpeechRecognition();
        recognizer.continuous = true;
        recognizer.interimResults = true;
        recognizer.lang = 'en-US';

        recognizer.onresult = (e: any) => {
          for (let i = e.resultIndex; i < e.results.length; i++) {
            const word = e.results[i][0].transcript.toLowerCase();
            if (word.includes('nova') || word.includes('ನೋವಾ') || word.includes('नोवा')) {
              setIsNovaOpen(true);
            }
          }
        };

        recognizer.onend = () => {
          // Keep listening for codeword unless user explicitly stops
          try {
            recognizer.start();
          } catch {}
        };

        recognizer.start();
        wakeWordRecognitionRef.current = recognizer;
      } catch {}
    }

    return () => {
      if (wakeWordRecognitionRef.current) {
        try {
          wakeWordRecognitionRef.current.stop();
        } catch {}
      }
    };
  }, []);

  // Long-press screen activation handlers (hold anywhere for 1.2s to activate Nova)
  const handleTouchStart = () => {
    longPressTimerRef.current = setTimeout(() => {
      setIsNovaOpen(true);
    }, 1200);
  };

  const handleTouchEnd = () => {
    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
    }
  };

  return (
    <div
      onTouchStart={handleTouchStart}
      onTouchEnd={handleTouchEnd}
      onMouseDown={handleTouchStart}
      onMouseUp={handleTouchEnd}
      className="min-h-screen bg-[#F0F5FA] flex flex-col md:flex-row font-sans text-slate-800 antialiased selection:bg-cyan-500 selection:text-white relative"
    >
      {/* Left Sidebar */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-y-auto">
        {/* Top Header */}
        <Header />

        {/* Dynamic Route Body */}
        <main className="flex-1 p-4 md:p-6 lg:p-8 max-w-[1600px] w-full mx-auto">
          <Outlet />
        </main>
      </div>

      {/* Floating Nova Voice Assistant Pill Button */}
      <div className="fixed bottom-6 right-6 z-40">
        <button
          type="button"
          onClick={() => setIsNovaOpen(true)}
          className="group relative px-4 py-3 bg-gradient-to-r from-slate-900 via-cyan-950 to-slate-900 text-white rounded-full shadow-2xl border border-cyan-400/40 hover:border-cyan-400 flex items-center gap-2.5 transition-all transform hover:scale-105 active:scale-95 cursor-pointer ring-4 ring-cyan-500/10"
        >
          <div className="w-8 h-8 rounded-full bg-cyan-500 text-slate-950 flex items-center justify-center font-black animate-pulse">
            <Mic className="w-4 h-4" />
          </div>
          <div className="text-left hidden sm:block pr-1">
            <div className="text-xs font-black text-cyan-300 flex items-center gap-1">
              <span>Nova</span>
              <Sparkles className="w-3 h-3 text-cyan-400 animate-spin-slow" />
            </div>
            <div className="text-[10px] text-slate-400">Say "Nova" or Long-Press</div>
          </div>
        </button>
      </div>

      {/* Multilingual Voice Assistant Modal */}
      <NovaVoiceAssistantModal
        isOpen={isNovaOpen}
        onClose={() => setIsNovaOpen(false)}
      />
    </div>
  );
};
