import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  HeartPulse,
  Moon,
  Sparkles,
  MapPin,
  AlertTriangle,
  Bell,
  MessageSquare,
  History,
  Settings,
  ShieldCheck,
  LogOut
} from 'lucide-react';
import { PulseGuardianLogo } from './PulseGuardianLogo';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';

export const Sidebar: React.FC = () => {
  const { logout, user } = useAuth();
  const { t } = useLanguage();

  const navItems = [
    { to: '/', label: t('nav.dashboard', 'Dashboard'), icon: LayoutDashboard },
    { to: '/health', label: t('nav.health', 'Health Monitor'), icon: Activity },
    { to: '/ecg', label: t('nav.ecg', 'ECG Monitor'), icon: HeartPulse },
    { to: '/sleep-activity', label: t('nav.sleepActivity', 'Sleep & Activity'), icon: Moon },
    { to: '/ai-insights', label: t('nav.aiInsights', 'AI Insights'), icon: Sparkles },
    { to: '/gps', label: t('nav.gps', 'GPS Tracking'), icon: MapPin },
    { to: '/emergency', label: t('nav.emergency', 'Emergency SOS'), icon: AlertTriangle, badge: '1', badgeColor: 'bg-rose-500' },
    { to: '/notifications', label: t('nav.notifications', 'Notifications'), icon: Bell, badge: '3', badgeColor: 'bg-rose-500' },
    { to: '/communication', label: t('nav.communication', 'Communication'), icon: MessageSquare },
    { to: '/history', label: t('nav.history', 'Health History'), icon: History },
    { to: '/devices', label: t('nav.devices', 'Devices'), icon: Activity },
    { to: '/settings', label: t('nav.settings', 'Settings'), icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#0a1526] text-slate-300 flex flex-col justify-between p-4 flex-shrink-0 min-h-screen border-r border-slate-800/80 select-none">
      {/* Top Brand Logo */}
      <div className="pt-2 pb-6 px-2">
        <PulseGuardianLogo size="md" lightText tagline={t('app.subtagline', 'Care. Protect. Live Better.')} />
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1.5 overflow-y-auto pr-1">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center justify-between px-3.5 py-2.5 rounded-full text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-[#1864ab] text-white shadow-lg shadow-blue-500/25 font-bold'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <div className="flex items-center gap-3">
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span className="tracking-wide">{item.label}</span>
              </div>
              {item.badge && (
                <span
                  className={`${item.badgeColor} text-white text-[10px] font-black px-1.5 py-0.2 rounded-full min-w-4 text-center leading-tight shadow`}
                >
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Safe Hands Trust Card & Logout */}
      <div className="pt-4 space-y-3">
        {/* You're in Safe Hands Banner directly from Image 1 */}
        <div className="p-3.5 rounded-2xl bg-gradient-to-b from-cyan-950/40 to-slate-900/80 border border-cyan-500/20 text-center relative overflow-hidden group">
          <div className="w-9 h-9 rounded-xl bg-cyan-500/10 border border-cyan-400/30 flex items-center justify-center mx-auto mb-2 text-cyan-400 shadow-glow-cyan">
            <ShieldCheck className="w-5 h-5 text-cyan-400" />
          </div>
          <p className="text-xs font-bold text-white tracking-wide">{t('brand.safeHands', "You're in Safe Hands")}</p>
          <p className="text-[10px] text-cyan-200/70 mt-0.5">{t('brand.stayHealthy', 'Stay healthy & happy!')}</p>
        </div>

        {/* User Mini Profile & Logout */}
        <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 px-1">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-full bg-cyan-600 flex items-center justify-center text-white text-xs font-bold">
              {user?.full_name?.charAt(0) || 'T'}
            </div>
            <div className="text-left overflow-hidden">
              <p className="text-xs font-semibold text-white truncate max-w-[110px]">
                {user?.full_name || 'Thrisha'}
              </p>
              <p className="text-[10px] text-slate-400 capitalize">
                {user?.role === 'caregiver' ? t('role.caregiver', 'Caregiver') : t('role.patient', 'Patient')}
              </p>
            </div>
          </div>

          <button
            onClick={logout}
            title={t('nav.logout', 'Log Out')}
            className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800 rounded-lg transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
};
