import React, { useState, useEffect } from 'react';
import { Search, Globe, Bell, Menu, X, MapPin, Clock } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useNavigate } from 'react-router-dom';
import { SupportedLanguage } from '../i18n/translations';
import { locationService } from '../api/services';

interface HeaderProps {
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileMenu, isMobileMenuOpen }) => {
  const { user } = useAuth();
  const { language, setLanguage, t, languages } = useLanguage();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  // Live real-time clock based on patient's GPS tracker location
  const [gpsData, setGpsData] = useState<{
    city: string;
    coords: string;
    timeStr: string;
    dateStr: string;
  }>({
    city: 'Bengaluru, IN',
    coords: '12.9716° N, 77.5946° E',
    timeStr: '',
    dateStr: '',
  });

  useEffect(() => {
    // 1. Update clock every second in patient's real time
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const dateStr = now.toLocaleDateString([], { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
      setGpsData((prev) => ({ ...prev, timeStr, dateStr }));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    // 2. Fetch actual GPS tracker coords from device / browser
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          const lat = pos.coords.latitude;
          const lng = pos.coords.longitude;
          setGpsData((prev) => ({
            ...prev,
            coords: `${lat.toFixed(4)}° N, ${lng.toFixed(4)}° E`,
          }));
        },
        () => {
          // If browser permission denied or offline, query backend location log
          locationService.getLatest().then((loc: any) => {
            if (loc && loc.latitude && loc.longitude) {
              setGpsData((prev) => ({
                ...prev,
                coords: `${Number(loc.latitude).toFixed(4)}° N, ${Number(loc.longitude).toFixed(4)}° E`,
                city: loc.city || 'Bengaluru, IN',
              }));
            }
          }).catch(() => {});
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    }

    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 px-4 sm:px-8 flex items-center justify-between border-b border-slate-200/60 bg-white/80 backdrop-blur-md sticky top-0 z-30 gap-4">
      {/* Left: Mobile Toggle & Search Input matching design */}
      <div className="flex items-center gap-3 flex-1 max-w-md">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100 cursor-pointer"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Search bar */}
        <div className="relative w-full max-w-sm hidden sm:block">
          <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder={t('dash.searchPlaceholder', 'Search anything... (e.g. heart rate, location)')}
            className="w-full pl-10 pr-4 py-2 bg-slate-100/90 hover:bg-slate-100 focus:bg-white border border-transparent focus:border-cyan-500/40 rounded-full text-xs font-medium text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/20 transition-all shadow-inner"
          />
        </div>
      </div>

      {/* Center: GPS Tracker Real-Time Location & Clock Sentinel */}
      <div className="hidden md:flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-slate-100/90 border border-slate-200/80 text-[11px] font-semibold text-slate-700 shadow-sm shrink-0">
        <div className="flex items-center gap-1.5 text-emerald-600 font-bold">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <MapPin className="w-3.5 h-3.5 text-emerald-600" />
          <span>{gpsData.city}</span>
        </div>
        <span className="text-slate-300">|</span>
        <span className="font-mono text-[10px] text-slate-500">{gpsData.coords}</span>
        <span className="text-slate-300">|</span>
        <div className="flex items-center gap-1 text-cyan-700 font-mono font-bold">
          <Clock className="w-3.5 h-3.5 text-cyan-600" />
          <span>{gpsData.timeStr || '--:--:--'}</span>
          <span className="text-[10px] text-slate-400 font-sans font-medium">({gpsData.dateStr})</span>
        </div>
      </div>

      {/* Right: Language Picker, Notification Bell, User Avatar */}
      <div className="flex items-center gap-3 sm:gap-4 shrink-0">
        {/* Language dropdown with translate="no" to prevent duplicate naming */}
        <div className="relative">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200/90 bg-white/90 shadow-sm text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
            <Globe className="w-3.5 h-3.5 text-slate-500" />
            <select
              translate="no"
              value={language}
              onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
              className="notranslate bg-transparent border-none text-xs font-semibold focus:outline-none cursor-pointer pr-1"
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code} translate="no" className="notranslate">
                  {l.code === 'en' ? 'English' : `${l.nativeName} (${l.name})`}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Notifications Icon with Red Badge (3) */}
        <button
          onClick={() => navigate('/notifications')}
          className="relative p-2 rounded-full hover:bg-slate-100 text-slate-600 transition-colors cursor-pointer"
          title={t('nav.notifications', 'Notifications')}
        >
          <Bell className="w-5 h-5 text-slate-700" />
          <span className="absolute top-1 right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[9px] font-black flex items-center justify-center ring-2 ring-white">
            3
          </span>
        </button>

        {/* User Avatar with Green Online Status Dot */}
        <div
          onClick={() => navigate('/settings')}
          className="flex items-center gap-2 cursor-pointer group"
          title={t('nav.settings', 'Settings')}
        >
          <div className="relative">
            <img
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=150&q=80"
              alt="Thrisha Profile Avatar"
              className="w-9 h-9 rounded-full object-cover ring-2 ring-white shadow-sm group-hover:ring-cyan-500 transition-all"
            />
            {/* Green Online Dot */}
            <span className="absolute bottom-0 right-0 w-2.5 h-2.5 bg-emerald-500 rounded-full ring-2 ring-white" />
          </div>
        </div>
      </div>
    </header>
  );
};
