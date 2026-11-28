import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Clock, AlertTriangle, ShieldCheck, Trash2, Check, RotateCcw } from 'lucide-react';
import { notificationService } from '../api/services';
import { useLanguage } from '../context/LanguageContext';
import { formatDisplayDate, formatDisplayTime, formatDisplayDateTime } from '../utils/dateUtils';
import type { NotificationItem } from '../api/types';

export const NotificationsPage: React.FC = () => {
  const { t } = useLanguage();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>('all');

  const defaultSeedNotifications: NotificationItem[] = [
    {
      id: 1,
      user_id: 1,
      title: 'Prescription Schedule: Dolo (1 Tablet)',
      body: 'Scheduled morning dose for Dolo 1 Tablet (08:00, 20:00). Remember to take after meals.',
      notification_type: 'medication',
      severity: 'info',
      is_read: false,
      created_at: new Date(Date.now() - 1800000).toISOString(),
    },
    {
      id: 2,
      user_id: 1,
      title: 'Daily Biometric Baseline Stabilized',
      body: 'Resting Heart Rate (72 BPM) and SpO2 (98%) are within optimal clinical thresholds.',
      notification_type: 'health',
      severity: 'info',
      is_read: false,
      created_at: new Date(Date.now() - 7200000).toISOString(),
    },
    {
      id: 3,
      user_id: 1,
      title: 'Smart Wearable Paired (DEV-WEAR-001)',
      body: 'Continuous BLE / Wi-Fi telemetry sync active with verified 24/7 battery backup.',
      notification_type: 'device',
      severity: 'info',
      is_read: true,
      created_at: new Date(Date.now() - 86400000).toISOString(),
    },
  ];

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getAll();
      if (data && data.length > 0) {
        setNotifications(data);
      } else {
        setNotifications(defaultSeedNotifications);
      }
    } catch {
      setNotifications(defaultSeedNotifications);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, []);

  const handleToggleRead = async (id: number, currentStatus: boolean) => {
    try {
      if (currentStatus) {
        await notificationService.markAsUnread(id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: false } : n))
        );
      } else {
        await notificationService.markAsRead(id);
        setNotifications((prev) =>
          prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
        );
      }
    } catch {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: !currentStatus } : n))
      );
    }
  };

  const handleMarkAllRead = async () => {
    try {
      await notificationService.markAllAsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch {
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    }
  };

  const unreadCount = notifications.filter((n) => !n.is_read).length;
  const filteredNotifications = filterType === 'all'
    ? notifications
    : filterType === 'unread'
    ? notifications.filter((n) => !n.is_read)
    : notifications.filter((n) => n.notification_type === filterType);

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      {/* Top Header Card */}
      <div className="bg-white rounded-3xl p-6 border border-slate-200/90 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <h2 className="text-2xl font-black text-slate-800 tracking-tight">
              {t('notif.title', 'Notifications & Care Alerts')}
            </h2>
            {unreadCount > 0 && (
              <span className="px-2.5 py-0.5 rounded-full text-xs font-black bg-rose-500 text-white shadow-sm">
                {unreadCount} Unread
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {t('notif.subtitle', 'System alerts, medication reminders, vital threshold warnings, and device sync logs.')}
          </p>
        </div>

        <div className="flex items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={handleMarkAllRead}
            disabled={unreadCount === 0}
            className="text-xs font-bold text-cyan-700 hover:text-cyan-800 bg-cyan-50 hover:bg-cyan-100/80 px-3.5 py-2 rounded-xl border border-cyan-200 shadow-sm transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1.5"
          >
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-600" />
            <span>{t('notif.markAllRead', 'Mark all as read')}</span>
          </button>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs font-bold text-slate-600">
        {[
          { key: 'all', label: `All (${notifications.length})` },
          { key: 'unread', label: `Unread (${unreadCount})` },
          { key: 'medication', label: 'Medications' },
          { key: 'health', label: 'Vitals & AI' },
          { key: 'emergency', label: 'Emergency SOS' },
          { key: 'device', label: 'Wearable Sync' },
        ].map((tab) => (
          <button
            key={tab.key}
            type="button"
            onClick={() => setFilterType(tab.key)}
            className={`px-3.5 py-1.5 rounded-xl border transition-all cursor-pointer whitespace-nowrap ${
              filterType === tab.key
                ? 'bg-slate-900 text-white border-slate-900 shadow-sm'
                : 'bg-white hover:bg-slate-50 text-slate-600 border-slate-200'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Notifications List */}
      <div className="space-y-3">
        {loading ? (
          <div className="bg-white rounded-3xl p-10 border border-slate-200 text-center text-slate-400 text-xs">
            Loading notifications and alerts...
          </div>
        ) : filteredNotifications.length === 0 ? (
          <div className="bg-white rounded-3xl p-10 border border-slate-200 text-center space-y-2">
            <div className="w-12 h-12 rounded-2xl bg-slate-100 text-slate-400 mx-auto flex items-center justify-center">
              <Bell className="w-6 h-6" />
            </div>
            <div className="text-sm font-bold text-slate-700">No Notifications in this filter</div>
            <p className="text-xs text-slate-400">All current health, prescription, and emergency updates are cleared.</p>
          </div>
        ) : (
          filteredNotifications.map((n) => (
            <div
              key={n.id}
              className={`rounded-2xl p-4 sm:p-5 border transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${
                n.is_read
                  ? 'bg-white border-slate-200/80 text-slate-600 opacity-90'
                  : 'bg-gradient-to-r from-cyan-50/60 via-white to-white border-cyan-300 shadow-sm ring-1 ring-cyan-200/50'
              }`}
            >
              <div className="flex items-start gap-3.5 min-w-0 flex-1">
                <div
                  className={`p-2.5 rounded-2xl shrink-0 ${
                    n.notification_type === 'medication'
                      ? 'bg-amber-100 text-amber-700'
                      : n.notification_type === 'emergency'
                      ? 'bg-rose-100 text-rose-700 animate-pulse'
                      : n.notification_type === 'health'
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-cyan-100 text-cyan-700'
                  }`}
                >
                  <Bell className="w-5 h-5" />
                </div>

                <div className="min-w-0 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h4 className="text-sm font-bold text-slate-900 leading-snug">{n.title}</h4>
                    {!n.is_read ? (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-black uppercase bg-cyan-500 text-white shadow-xs">
                        <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />
                        Unread
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-100 text-slate-500">
                        Read
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 leading-relaxed">{n.body}</p>

                  <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400 font-mono">
                    <span className="flex items-center gap-1 font-sans">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{formatDisplayDateTime(n.created_at)}</span>
                    </span>
                    <span>•</span>
                    <span className="capitalize font-sans font-bold text-slate-500">{n.notification_type}</span>
                  </div>
                </div>
              </div>

              {/* Action Buttons: Mark Read / Mark Unread */}
              <div className="flex items-center gap-2 self-end sm:self-center shrink-0">
                <button
                  type="button"
                  onClick={() => handleToggleRead(n.id, n.is_read)}
                  className={`text-xs font-bold px-3 py-1.5 rounded-xl border transition-all cursor-pointer flex items-center gap-1.5 ${
                    n.is_read
                      ? 'text-slate-600 bg-slate-50 hover:bg-slate-100 border-slate-200'
                      : 'text-cyan-700 bg-cyan-50 hover:bg-cyan-100 border-cyan-200 shadow-xs'
                  }`}
                >
                  {n.is_read ? (
                    <>
                      <RotateCcw className="w-3.5 h-3.5" />
                      <span>Mark Unread</span>
                    </>
                  ) : (
                    <>
                      <Check className="w-3.5 h-3.5" />
                      <span>Mark Read</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
