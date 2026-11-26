import React, { useEffect, useState, useRef } from 'react';
import { ShieldAlert, PhoneCall, CheckCircle2, Clock, MapPin, RefreshCw, Check } from 'lucide-react';
import { emergencyService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import type { EmergencyAlert } from '../api/types';

export const EmergencySOSPage: React.FC = () => {
  const { role } = useAuth();
  const { lastMessage } = useWebSocket();

  const [alerts, setAlerts] = useState<EmergencyAlert[]>([]);
  const [holdingSOS, setHoldingSOS] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const [sosStatus, setSosStatus] = useState<'idle' | 'transmitting' | 'dispatched' | 'error'>('idle');
  const [sosErrorMsg, setSosErrorMsg] = useState<string | null>(null);
  const [coords, setCoords] = useState<{ lat: number; lng: number }>({ lat: 12.9716, lng: 77.5946 });

  const holdIntervalRef = useRef<any>(null);

  // Acquire live GPS on mount
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setCoords({
            lat: Number(pos.coords.latitude.toFixed(4)),
            lng: Number(pos.coords.longitude.toFixed(4)),
          });
        },
        () => {
          setCoords({ lat: 12.9716, lng: 77.5946 });
        },
        { enableHighAccuracy: true, timeout: 5000 }
      );
    }
  }, []);

  // Fetch active alerts
  const loadAlerts = async () => {
    try {
      const data = await emergencyService.listAlerts();
      setAlerts(data || []);
    } catch {
      // Offline fallback
    }
  };

  useEffect(() => {
    loadAlerts();
  }, []);

  // Listen for real-time WebSocket alert escalation receipts
  useEffect(() => {
    if (lastMessage && (lastMessage.type === 'emergency_alert' || lastMessage.type === 'alert_acknowledged')) {
      loadAlerts();
    }
  }, [lastMessage]);

  // Press & Hold 2.0s to trigger SOS safely
  const startSOSHold = () => {
    if (sosStatus === 'transmitting') return;
    setHoldingSOS(true);
    setHoldProgress(0);
    const startTime = Date.now();
    const DURATION = 2000;

    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(100, Math.round((elapsed / DURATION) * 100));
      setHoldProgress(progress);

      if (elapsed >= DURATION) {
        clearInterval(holdIntervalRef.current);
        setHoldingSOS(false);
        setHoldProgress(100);
        executeSOS();
      }
    }, 50);
  };

  const cancelSOSHold = () => {
    if (holdProgress < 100) {
      clearInterval(holdIntervalRef.current);
      setHoldingSOS(false);
      setHoldProgress(0);
    }
  };

  const executeSOS = async () => {
    setSosStatus('transmitting');
    setSosErrorMsg(null);
    try {
      await emergencyService.triggerSOS({
        latitude: coords.lat,
        longitude: coords.lng,
        alert_type: 'manual_sos',
        severity: 'critical',
        assistance_message: `Emergency SOS triggered from Web App Command Center. Coordinates: ${coords.lat}, ${coords.lng}.`,
      });
      setSosStatus('dispatched');
      loadAlerts();
      setTimeout(() => {
        setSosStatus('idle');
        setHoldProgress(0);
      }, 7000);
    } catch (err: any) {
      setSosStatus('error');
      setSosErrorMsg(err?.response?.data?.detail || 'Failed to dispatch alert to emergency server.');
      setTimeout(() => setSosStatus('idle'), 6000);
    }
  };

  const handleAcknowledge = async (alertId: number) => {
    try {
      await emergencyService.acknowledgeAlert(alertId, 'Caregiver response initiated via Web Portal.');
      loadAlerts();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Could not acknowledge alert.');
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">Emergency Response Command Center</h2>
          <p className="text-sm text-slate-500">
            Multi-channel emergency broadcast, automated alert escalation, and caregiver coordination.
          </p>
        </div>

        <button
          onClick={loadAlerts}
          className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
          title="Refresh Alerts"
        >
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      {/* Hero SOS Trigger Box */}
      <div className="relative rounded-3xl p-8 bg-gradient-to-br from-rose-600 via-rose-700 to-red-800 text-white shadow-2xl shadow-rose-500/30 border border-rose-500/40 text-center overflow-hidden select-none">
        <div className="absolute inset-0 opacity-15 pointer-events-none flex items-center justify-center">
          <svg className="w-full h-44" viewBox="0 0 400 100" fill="none" stroke="currentColor" strokeWidth="2.5">
            <path d="M0,50 L120,50 L140,15 L160,85 L180,30 L200,70 L220,50 L400,50" />
          </svg>
        </div>

        <div className="relative z-10 max-w-xl mx-auto space-y-4">
          <div className="inline-flex p-4 rounded-full bg-white/20 backdrop-blur-md shadow-inner animate-bounce">
            <ShieldAlert className="w-12 h-12 text-white" />
          </div>

          <h3 className="text-3xl font-black">Need Urgent Medical Assistance?</h3>
          <p className="text-sm text-rose-100">
            Hold the button for 2 seconds to broadcast your live GPS coordinates ({coords.lat}, {coords.lng}) and initiate caregiver notification.
          </p>

          <div className="pt-4 max-w-md mx-auto">
            <button
              onMouseDown={startSOSHold}
              onMouseUp={cancelSOSHold}
              onMouseLeave={cancelSOSHold}
              onTouchStart={startSOSHold}
              onTouchEnd={cancelSOSHold}
              disabled={sosStatus === 'transmitting'}
              className="relative w-full py-4 px-8 rounded-2xl font-black text-lg tracking-wider uppercase shadow-2xl overflow-hidden transition-all transform active:scale-98 flex items-center justify-center space-x-3 bg-white text-rose-600"
            >
              {holdingSOS && (
                <div
                  className="absolute left-0 top-0 bottom-0 bg-rose-200 transition-all duration-75 ease-linear pointer-events-none"
                  style={{ width: `${holdProgress}%` }}
                />
              )}

              <span className="relative z-10 flex items-center space-x-2">
                <PhoneCall className="w-5 h-5 animate-pulse" />
                {sosStatus === 'transmitting' && <span>Broadcasting SOS...</span>}
                {sosStatus === 'dispatched' && <span className="text-emerald-700">✓ SOS Dispatched!</span>}
                {sosStatus === 'error' && <span className="text-rose-700">Dispatch Failed</span>}
                {sosStatus === 'idle' && (
                  <span>{holdingSOS ? `Hold (${holdProgress}%)...` : 'Press & Hold to Trigger SOS'}</span>
                )}
              </span>
            </button>

            {sosErrorMsg && (
              <p className="text-xs text-amber-200 mt-2 font-medium">{sosErrorMsg}</p>
            )}
          </div>
        </div>
      </div>

      {/* Active Alerts List */}
      <div className="glass-card rounded-3xl p-6 border border-slate-100 shadow-sm space-y-4 bg-white">
        <h4 className="text-base font-bold text-slate-800">Recent Emergency Broadcasts</h4>

        {alerts.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            No active emergency events. All vital alerts clear.
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((a) => (
              <div
                key={a.id}
                className="p-4 rounded-2xl border border-rose-100 bg-rose-50/40 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-extrabold uppercase bg-rose-500 text-white">
                      {a.alert_type}
                    </span>
                    <span className="text-xs font-bold text-slate-800">Alert #{a.id}</span>
                    <span className="text-xs text-slate-400">• Tier {a.current_escalation_tier}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{a.assistance_message || 'Emergency assistance requested.'}</p>
                  <div className="flex items-center space-x-3 text-[11px] text-slate-400 mt-1 font-mono">
                    <span className="flex items-center space-x-1">
                      <Clock className="w-3 h-3" />
                      <span>{new Date(a.created_at).toLocaleTimeString()}</span>
                    </span>
                    {a.latitude && (
                      <span className="flex items-center space-x-1">
                        <MapPin className="w-3 h-3 text-rose-500" />
                        <span>{a.latitude}, {a.longitude}</span>
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {a.status === 'acknowledged' ? (
                    <span className="inline-flex items-center space-x-1 text-xs font-bold text-emerald-600 bg-emerald-50 px-3 py-1.5 rounded-xl border border-emerald-200">
                      <Check className="w-3.5 h-3.5" />
                      <span>Acknowledged</span>
                    </span>
                  ) : (
                    role === 'caregiver' && (
                      <button
                        onClick={() => handleAcknowledge(a.id)}
                        className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                      >
                        Acknowledge Alert
                      </button>
                    )
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
