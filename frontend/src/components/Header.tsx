import React, { useState } from 'react';
import { Search, Globe, Bell, Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { useNavigate } from 'react-router-dom';
import { SupportedLanguage } from '../i18n/translations';

interface HeaderProps {
  onToggleMobileMenu?: () => void;
  isMobileMenuOpen?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onToggleMobileMenu, isMobileMenuOpen }) => {
  const { user } = useAuth();
  const { language, setLanguage, t, languages } = useLanguage();
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <header className="h-16 px-4 sm:px-8 flex items-center justify-between border-b border-slate-200/60 bg-white/70 backdrop-blur-md sticky top-0 z-30">
      {/* Left: Mobile Toggle & Search Input matching design */}
      <div className="flex items-center gap-3 flex-1 max-w-xl">
        <button
          onClick={onToggleMobileMenu}
          className="lg:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100 cursor-pointer"
        >
          {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>

        {/* Search bar matching Image 1 */}
        <div className="relative w-full max-w-md hidden sm:block">
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

      {/* Right: Language Picker, Notification Bell, User Avatar */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Language dropdown */}
        <div className="relative">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200/90 bg-white/90 shadow-sm text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors">
            <Globe className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
              className="bg-transparent border-none text-xs font-semibold focus:outline-none cursor-pointer pr-1"
            >
              {languages.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.nativeName}
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
