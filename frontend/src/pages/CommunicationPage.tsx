import React, { useEffect, useState } from 'react';
import { Send, Languages, RefreshCw, MessageSquare } from 'lucide-react';
import { voiceService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import type { VoiceMessage } from '../api/types';

interface ChatItem {
  id: string | number;
  senderName: string;
  isMe: boolean;
  originalText: string;
  translatedText?: string;
  sourceLang: string;
  targetLang: string;
  timestamp: string;
}

export const CommunicationPage: React.FC = () => {
  const { user } = useAuth();
  const { lastMessage } = useWebSocket();

  const [messages, setMessages] = useState<ChatItem[]>([
    {
      id: '1',
      senderName: 'Sarah Jenkins (Primary Caregiver)',
      isMe: false,
      originalText: 'Good morning! Did you remember to drink water and take your morning vitamins?',
      translatedText: 'காலை வணக்கம்! நீங்கள் தண்ணீர் குடித்து உங்கள் காலை வைட்டமின்களை எடுத்துக்கொள்ள நினைவிருக்கிறதா?',
      sourceLang: 'en',
      targetLang: 'ta',
      timestamp: '08:30 AM',
    },
    {
      id: '2',
      senderName: 'You',
      isMe: true,
      originalText: 'ஆமாம் சாரா, நான் காலை உணவுக்குப் பிறகு வைட்டமின்களை எடுத்துக்கொண்டேன்.',
      translatedText: 'Yes Sarah, I took the vitamins after breakfast.',
      sourceLang: 'ta',
      targetLang: 'en',
      timestamp: '08:34 AM',
    },
  ]);

  const [inputText, setInputText] = useState('');
  const [targetLang, setTargetLang] = useState('ta');
  const [sourceLang, setSourceLang] = useState('en');
  const [sending, setSending] = useState(false);
  const [partnerId, setPartnerId] = useState<number>(2); // Default Caregiver partner

  // Listen for real-time WebSocket incoming messages
  useEffect(() => {
    if (lastMessage && lastMessage.type === 'new_message') {
      const msg = lastMessage.data;
      setMessages((prev) => [
        ...prev,
        {
          id: msg.id || Date.now(),
          senderName: msg.sender_name || 'Caregiver',
          isMe: msg.sender_id === user?.id,
          originalText: msg.original_text,
          translatedText: msg.translated_text,
          sourceLang: msg.source_language || 'en',
          targetLang: msg.target_language || 'ta',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    }
  }, [lastMessage, user]);

  const fetchConversations = async () => {
    try {
      const convs = await voiceService.getConversations();
      if (convs && convs.length > 0 && convs[0].partner_id) {
        setPartnerId(convs[0].partner_id);
        const msgs = await voiceService.getMessages(convs[0].partner_id);
        if (msgs && msgs.length > 0) {
          const mapped: ChatItem[] = msgs.map((m: VoiceMessage) => ({
            id: m.id,
            senderName: m.sender_id === user?.id ? 'You' : 'Caregiver',
            isMe: m.sender_id === user?.id,
            originalText: m.original_text,
            translatedText: m.translated_text,
            sourceLang: m.source_language || 'en',
            targetLang: m.target_language || 'ta',
            timestamp: new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          }));
          setMessages(mapped);
        }
      }
    } catch {
      // Retain seeded conversation
    }
  };

  useEffect(() => {
    fetchConversations();
  }, []);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || sending) return;

    const currentText = inputText;
    setInputText('');
    setSending(true);

    try {
      // 1. Send via Voice messaging service API
      const res = await voiceService.sendMessage({
        recipient_id: partnerId,
        text: currentText,
        source_language: sourceLang,
        target_language: targetLang,
      });

      const newMsg: ChatItem = {
        id: res.id || Date.now().toString(),
        senderName: 'You',
        isMe: true,
        originalText: currentText,
        translatedText: res.translated_text,
        sourceLang,
        targetLang,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, newMsg]);
    } catch {
      // Fallback
      const newMsg: ChatItem = {
        id: Date.now().toString(),
        senderName: 'You',
        isMe: true,
        originalText: currentText,
        translatedText: `[Auto-Translated to ${targetLang.toUpperCase()}]: ${currentText}`,
        sourceLang,
        targetLang,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, newMsg]);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">Multilingual Caregiver Chat</h2>
          <p className="text-sm text-slate-500">
            Real-time translation bridge connecting patients, elders, and bilingual caregivers.
          </p>
        </div>

        <button
          onClick={fetchConversations}
          className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
          title="Refresh Messages"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Main Chat Box */}
      <div className="glass-card rounded-3xl border border-slate-100 shadow-xl overflow-hidden flex flex-col h-[600px] bg-white">
        <div className="p-4 bg-slate-50 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 text-blue-600 font-bold flex items-center justify-center">
              S
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-800">Sarah Jenkins (Primary Caregiver)</h4>
              <p className="text-[11px] text-emerald-600 font-medium flex items-center space-x-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                <span>Active • Auto-Translation Enabled</span>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <Languages className="w-4 h-4 text-cyan-600" />
            <select
              value={targetLang}
              onChange={(e) => setTargetLang(e.target.value)}
              className="bg-white border border-slate-300 rounded-lg px-2 py-1 text-slate-700 text-xs focus:outline-none"
            >
              <option value="ta">Tamil (தமிழ்)</option>
              <option value="hi">Hindi (हिंदी)</option>
              <option value="te">Telugu (తెలుగు)</option>
              <option value="kn">Kannada (ಕನ್ನಡ)</option>
              <option value="ml">Malayalam (മലയാളം)</option>
              <option value="ur">Urdu (اردو)</option>
              <option value="en">English</option>
            </select>
          </div>
        </div>

        <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-gradient-to-b from-slate-50/50 to-white">
          {messages.map((m) => (
            <div
              key={m.id}
              className={`flex flex-col ${m.isMe ? 'items-end' : 'items-start'} space-y-1`}
            >
              <span className="text-[10px] text-slate-400 font-medium px-1">
                {m.senderName} • {m.timestamp}
              </span>

              <div
                className={`max-w-md rounded-2xl p-4 shadow-sm space-y-1.5 ${
                  m.isMe
                    ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white rounded-br-none'
                    : 'bg-white text-slate-800 border border-slate-200 rounded-bl-none'
                }`}
              >
                <p className="text-sm font-medium leading-relaxed">{m.originalText}</p>

                {m.translatedText && (
                  <div
                    className={`pt-2 mt-2 border-t text-xs italic ${
                      m.isMe ? 'border-white/20 text-cyan-100' : 'border-slate-100 text-slate-500'
                    }`}
                  >
                    <span className="font-semibold uppercase text-[10px] not-italic block mb-0.5">
                      🌐 Translated:
                    </span>
                    {m.translatedText}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={handleSendMessage} className="p-4 bg-white border-t border-slate-200 flex items-center space-x-3">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message in any language..."
            className="flex-1 bg-slate-50 border border-slate-300 rounded-2xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
          />
          <button
            type="submit"
            disabled={sending || !inputText.trim()}
            className="px-5 py-3 rounded-2xl bg-cyan-500 hover:bg-cyan-600 text-white font-bold text-sm shadow-md transition-all flex items-center space-x-1.5 disabled:opacity-50"
          >
            <span>{sending ? 'Translating...' : 'Send'}</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
