import React, { useEffect, useState } from 'react';
import { Bell, CheckCircle2, Clock, AlertTriangle, ShieldCheck, Trash2 } from 'lucide-react';
import { notificationService } from '../api/services';
import { useLanguage } from '../context/LanguageContext';
import type { NotificationItem } from '../api/types';

export const NotificationsPage: React.FC = () => {
  const { t } = useLanguage();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchNotifs = async () => {
    setLoading(true);
    try {
      const data = await notificationService.getAll();
      setNotifications(data);
    } catch {
      // Demo notifications if offline
      setNotifications([
        {
          id: 1,
          user_id: 1,
          title: 'Medication Reminder',
          body: 'Time to take morning blood pressure prescription (Amlodipine 5mg).',
          notification_type: 'medication',
          severity: 'medium',
          is_read: false,
          created_at: new Date(Date.now() - 3600000).toISOString(),
        },
        {
          id: 2,
          user_id: 1,
          title: 'Daily Step Goal Achieved',
          body: 'Congratulations! You reached 80% of your daily steps target.',
          notification_type: 'goal',
          severity: 'low',
          is_read: false,
          created_at: new Date(Date.now() - 14400000).toISOString(),
        },
        {
          id: 3,
          user_id: 1,
          title: 'Wearable Sync Successful',
          body: 'PulseGuardian Smart Band synced 2,400 biometric data points.',
          notification_type: 'device',
          severity: 'low',
          is_read: true,
          created_at: new Date(Date.now() - 86400000).toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifs();
  }, []);

  const handleMarkAsRead = async (id: number) => {
    try {
      await notificationService.markAsRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch {
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">{t('notif.title', 'Notifications & Care Alerts')}</h2>
          <p className="text-sm text-slate-500">
            {t('notif.subtitle', 'System alerts, medication reminders, vital threshold warnings, and device sync logs.')}
          </p>
        </div>

        <button
          onClick={fetchNotifs}
          className="text-xs font-semibold text-cyan-600 hover:text-cyan-700 bg-white px-3 py-1.5 rounded-xl border border-slate-200 shadow-sm"
        >
          {t('notif.markAllRead', 'Mark all as read')}
        </button>
      </div>

      <div className="space-y-3">
        {notifications.map((n) => (
          <div
            key={n.id}
            className={`glass-card rounded-2xl p-5 border transition-all flex items-start justify-between gap-4 ${
              n.is_read
                ? 'border-slate-100 opacity-75'
                : 'border-cyan-200 bg-gradient-to-r from-cyan-50/20 via-white to-white shadow-sm'
            }`}
          >
            <div className="flex items-start space-x-3.5">
              <div
                className={`p-2.5 rounded-xl ${
                  n.notification_type === 'medication'
                    ? 'bg-amber-50 text-amber-600'
                    : n.notification_type === 'emergency'
                    ? 'bg-rose-50 text-rose-600'
                    : 'bg-cyan-50 text-cyan-600'
                }`}
              >
                <Bell className="w-5 h-5" />
              </div>

              <div>
                <div className="flex items-center space-x-2">
                  <h4 className="text-sm font-bold text-slate-800">{n.title}</h4>
                  {!n.is_read && (
                    <span className="w-2 h-2 rounded-full bg-cyan-500 animate-pulse" />
                  )}
                </div>
                <p className="text-xs text-slate-600 mt-1">{n.body}</p>
                <div className="flex items-center space-x-3 mt-2 text-[11px] text-slate-400">
                  <span className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                  </span>
                  <span>•</span>
                  <span className="capitalize">{n.notification_type}</span>
                </div>
              </div>
            </div>

            {!n.is_read && (
              <button
                onClick={() => handleMarkAsRead(n.id)}
                className="text-xs text-cyan-600 font-semibold hover:underline flex items-center space-x-1"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Mark Read</span>
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
