import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Heart,
  Droplets,
  Thermometer,
  Footprints,
  Moon,
  Sparkles,
  MapPin,
  ShieldAlert,
  BatteryCharging,
  Mic,
  Navigation,
  Users,
  Pill,
  Wifi,
  WifiOff,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';
import { healthService, emergencyService, aiService } from '../api/services';
import { useAuth } from '../context/AuthContext';
import { LiveECGCanvas } from '../components/LiveECGCanvas';
import { VoiceAssistantWidget } from '../components/VoiceAssistantWidget';
import type { DashboardSummary } from '../api/types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, role } = useAuth();

  // State
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [isLiveOnline, setIsLiveOnline] = useState(false);
  const [lastSyncStr, setLastSyncStr] = useState('Syncing...');
  
  // Real or fallback telemetry
  const [heartRate, setHeartRate] = useState<number>(72);
  const [spo2, setSpo2] = useState<number>(98);
  const [temp, setTemp] = useState<number>(36.8);
  const [steps, setSteps] = useState<number>(4820);
  const [sleepStr, setSleepStr] = useState<string>('7h 20m');
  const [batteryPct, setBatteryPct] = useState<number>(92);
  const [aiInsightText, setAiInsightText] = useState<string>(
    'Vital signs are well-balanced. Sub-threshold cardiac drift (+2%) within baseline boundaries.'
  );

  // Live GPS state
  const [gpsLocation, setGpsLocation] = useState<{ lat: number; lng: number; isLive: boolean }>({
    lat: 12.9716,
    lng: 77.5946,
    isLive: false,
  });

  // SOS Press & Hold state
  const [holdingSOS, setHoldingSOS] = useState(false);
  const [holdProgress, setHoldProgress] = useState(0);
  const [sosStatus, setSosStatus] = useState<'idle' | 'transmitting' | 'dispatched' | 'error'>('idle');
  const [sosErrorMsg, setSosErrorMsg] = useState<string | null>(null);
  const holdIntervalRef = useRef<any>(null);

  // Request real browser geolocation on mount
  useEffect(() => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setGpsLocation({
            lat: Number(pos.coords.latitude.toFixed(4)),
            lng: Number(pos.coords.longitude.toFixed(4)),
            isLive: true,
          });
        },
        () => {
          // Geolocation permission denied or unavailable, use patient registered baseline
          setGpsLocation({ lat: 12.9716, lng: 77.5946, isLive: false });
        },
        { timeout: 8000, enableHighAccuracy: true }
      );
    }
  }, []);

  // Fetch live Dashboard data from backend
  const loadDashboardData = async () => {
    try {
      const data = await healthService.getDashboard();
      if (data) {
        setSummary(data);
        if (data.latest_vitals) {
          if (data.latest_vitals.heart_rate) setHeartRate(Math.round(data.latest_vitals.heart_rate));
          if (data.latest_vitals.spo2) setSpo2(Math.round(data.latest_vitals.spo2));
          if (data.latest_vitals.temperature) setTemp(Number(data.latest_vitals.temperature.toFixed(1)));
          if (data.latest_vitals.battery_percentage) setBatteryPct(Math.round(data.latest_vitals.battery_percentage));
        }
        if (data.summary_24h) {
          if (data.summary_24h.total_steps) setSteps(data.summary_24h.total_steps);
        }
        if (data.device_status) {
          setIsLiveOnline(data.device_status.is_online);
          if (data.device_status.last_sync_at) {
            const syncTime = new Date(data.device_status.last_sync_at);
            const diffMin = Math.max(1, Math.round((Date.now() - syncTime.getTime()) / 60000));
            setLastSyncStr(`${diffMin} min ago`);
          } else {
            setLastSyncStr('Just now');
          }
        }
      }
    } catch (err) {
      // Backend offline or error fallback to initialized states
      setIsLiveOnline(false);
      setLastSyncStr('Offline / Demo data');
    } finally {
      setLoading(false);
    }

    // Also fetch AI health baseline drift summary
    try {
      const drift = await aiService.getHealthDriftSummary();
      if (drift && drift.summary_text) {
        setAiInsightText(drift.summary_text);
      }
    } catch {
      // Retain fallback AI text
    }
  };

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 12000);
    return () => clearInterval(interval);
  }, []);

  // SOS Press & Hold mechanics (2.0-second safety hold to prevent accidental activation)
  const startSOSHold = () => {
    if (sosStatus === 'transmitting') return;
    setHoldingSOS(true);
    setHoldProgress(0);
    const startTime = Date.now();
    const DURATION = 2000; // 2.0s hold

    holdIntervalRef.current = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(100, Math.round((elapsed / DURATION) * 100));
      setHoldProgress(progress);

      if (elapsed >= DURATION) {
        clearInterval(holdIntervalRef.current);
        setHoldingSOS(false);
        setHoldProgress(100);
        executeSOSDispatch();
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

  const executeSOSDispatch = async () => {
    setSosStatus('transmitting');
    setSosErrorMsg(null);
    try {
      await emergencyService.triggerSOS({
        latitude: gpsLocation.lat,
        longitude: gpsLocation.lng,
        alert_type: 'manual_sos',
        severity: 'critical',
        assistance_message: `Emergency SOS triggered from PulseGuardian Web App. Coordinates: ${gpsLocation.lat}, ${gpsLocation.lng}.`,
      });
      setSosStatus('dispatched');
      setTimeout(() => {
        setSosStatus('idle');
        setHoldProgress(0);
      }, 7000);
    } catch (err: any) {
      setSosStatus('error');
      setSosErrorMsg(err?.response?.data?.detail || 'Failed to transmit SOS to dispatch server.');
      setTimeout(() => setSosStatus('idle'), 6000);
    }
  };

  const displayName = user?.full_name?.split(' ')[0] || (role === 'caregiver' ? 'Caregiver' : 'Thrisha');

  return (
    <div className="space-y-6 pb-12">
      {/* =========================================================================
          TOP ROW: HERO GREETING WITH SMARTWATCH & EMERGENCY SOS HERO BANNER
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left Hero: Watch Graphic + Greeting */}
        <div className="lg:col-span-8 relative rounded-3xl p-6 overflow-hidden bg-gradient-to-r from-white/90 via-sky-50/80 to-blue-50/70 border border-white/60 shadow-lg backdrop-blur-md flex flex-col md:flex-row items-center justify-between">
          <div className="absolute inset-0 bg-cover bg-center opacity-15 pointer-events-none" />

          {/* Left Watch Graphic */}
          <div className="relative flex items-center justify-center p-2">
            <div className="relative w-36 h-36 flex items-center justify-center">
              <div className="absolute inset-0 rounded-full bg-cyan-400/20 blur-xl animate-pulse" />
              <div className="relative w-28 h-32 bg-slate-900 rounded-3xl border-4 border-slate-700 shadow-2xl flex flex-col items-center justify-center p-2 text-white">
                <div className="absolute -top-3 w-16 h-3 bg-slate-800 rounded-t-md" />
                <div className="w-full h-full bg-gradient-to-b from-[#0b1424] to-[#12223f] rounded-2xl border border-cyan-500/30 flex flex-col items-center justify-center p-1">
                  <Heart className="w-5 h-5 text-rose-500 fill-rose-500 animate-pulse mb-1" />
                  <span className="text-xl font-bold tracking-tight text-white">{heartRate}</span>
                  <span className="text-[9px] text-cyan-300 font-medium tracking-wider">bpm</span>
                </div>
                <div className="absolute -bottom-3 w-16 h-3 bg-slate-800 rounded-b-md" />
              </div>
            </div>
          </div>

          {/* Center Greeting & Status Pills */}
          <div className="flex-1 md:ml-6 mt-4 md:mt-0 space-y-3 text-center md:text-left">
            <div>
              <h1 className="text-2xl md:text-3xl font-extrabold text-slate-800 flex items-center justify-center md:justify-start gap-2">
                Good Morning, {displayName}! 🌸
              </h1>
              <p className="text-slate-500 text-sm mt-0.5">Stay healthy, stay happy, and live longer.</p>
            </div>

            {/* Badges / Pills */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 pt-1">
              {/* Connected Pill */}
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{isLiveOnline ? 'Wearable connected & live' : 'Wearable connected (Demo sync)'}</span>
              </div>

              {/* Battery Pill */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-white/80 text-slate-600 border border-slate-200 shadow-sm">
                <BatteryCharging className="w-3.5 h-3.5 text-emerald-600" />
                <span>{batteryPct}%</span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-500">Last sync: {lastSyncStr}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Hero: Emergency SOS Press & Hold Banner */}
        <div className="lg:col-span-4 relative rounded-3xl p-6 overflow-hidden bg-gradient-to-br from-rose-500 via-rose-600 to-red-700 text-white shadow-xl shadow-rose-500/20 border border-rose-400/40 flex flex-col justify-between select-none">
          <div className="absolute inset-0 opacity-15 pointer-events-none flex items-center justify-center">
            <svg className="w-full h-24" viewBox="0 0 300 80" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M0,40 L90,40 L105,10 L120,70 L135,20 L150,55 L165,40 L300,40" />
            </svg>
          </div>

          <div className="relative flex items-start space-x-3">
            <div className="p-3 bg-white/20 rounded-2xl backdrop-blur-md">
              <ShieldAlert className="w-7 h-7 text-white animate-bounce" />
            </div>
            <div>
              <h3 className="text-lg font-bold">Emergency SOS</h3>
              <p className="text-xs text-rose-100">Hold 2 sec to trigger caregiver escalation</p>
            </div>
          </div>

          {/* Press and Hold Button with Live Fill Bar */}
          <div className="relative mt-4">
            <button
              onMouseDown={startSOSHold}
              onMouseUp={cancelSOSHold}
              onMouseLeave={cancelSOSHold}
              onTouchStart={startSOSHold}
              onTouchEnd={cancelSOSHold}
              disabled={sosStatus === 'transmitting'}
              className="relative w-full py-3.5 px-5 rounded-2xl font-bold text-sm tracking-wide shadow-lg overflow-hidden transition-all transform active:scale-98 flex items-center justify-center space-x-2 bg-white text-rose-600"
            >
              {/* Animated Progress Fill */}
              {holdingSOS && (
                <div
                  className="absolute left-0 top-0 bottom-0 bg-rose-200 transition-all duration-75 ease-linear pointer-events-none"
                  style={{ width: `${holdProgress}%` }}
                />
              )}

              <span className="relative z-10 flex items-center space-x-2">
                {sosStatus === 'transmitting' && (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-rose-600" />
                    <span>Broadcasting SOS to Caregivers...</span>
                  </>
                )}
                {sosStatus === 'dispatched' && (
                  <span className="text-emerald-700 font-extrabold">✓ SOS Dispatched to Contacts</span>
                )}
                {sosStatus === 'error' && (
                  <span className="text-rose-700 font-extrabold">Transmission Failed – Try Again</span>
                )}
                {sosStatus === 'idle' && (
                  <span>{holdingSOS ? `Hold (${holdProgress}%)...` : '📞 Press & Hold ➔'}</span>
                )}
              </span>
            </button>

            {sosErrorMsg && (
              <p className="text-[11px] text-amber-200 mt-1 font-medium text-center">{sosErrorMsg}</p>
            )}
          </div>
        </div>
      </div>

      {/* =========================================================================
          ROW 2: FIVE QUICK HEALTH METRIC CARDS MATCHING DESIGN
         ========================================================================= */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {/* Heart Rate Card */}
        <div
          onClick={() => navigate('/health')}
          className="glass-card rounded-2xl p-4 cursor-pointer hover:shadow-md transition-all border border-slate-100 flex flex-col justify-between"
        >
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-rose-50 text-rose-500">
              <Heart className="w-4 h-4 fill-rose-500" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Heart Rate</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {heartRate} <span className="text-xs font-normal text-slate-500">BPM</span>
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px] text-emerald-600">
              <span>↑ +2%</span>
              <div className="w-12 h-3 text-rose-400">
                <svg viewBox="0 0 40 10" className="w-full h-full fill-none stroke-current stroke-2">
                  <path d="M0,5 Q10,0 20,8 T40,4" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* SpO2 Card */}
        <div
          onClick={() => navigate('/health')}
          className="glass-card rounded-2xl p-4 cursor-pointer hover:shadow-md transition-all border border-slate-100 flex flex-col justify-between"
        >
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-blue-50 text-blue-500">
              <Droplets className="w-4 h-4 fill-blue-500" />
            </div>
            <span className="text-xs font-semibold text-slate-600">SpO2</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {spo2} <span className="text-xs font-normal text-slate-500">%</span>
            </div>
            <div className="flex items-center justify-between mt-1 text-[11px] text-emerald-600">
              <span>↑ +1%</span>
              <div className="w-12 h-3 text-blue-400">
                <svg viewBox="0 0 40 10" className="w-full h-full fill-none stroke-current stroke-2">
                  <path d="M0,7 Q15,2 25,6 T40,3" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Body Temp Card */}
        <div
          onClick={() => navigate('/health')}
          className="glass-card rounded-2xl p-4 cursor-pointer hover:shadow-md transition-all border border-slate-100 flex flex-col justify-between"
        >
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-amber-50 text-amber-500">
              <Thermometer className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Body Temp</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {temp} <span className="text-xs font-normal text-slate-500">°C</span>
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[11px] text-emerald-600 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>Normal Range</span>
            </div>
          </div>
        </div>

        {/* Steps Card */}
        <div
          onClick={() => navigate('/sleep-activity')}
          className="glass-card rounded-2xl p-4 cursor-pointer hover:shadow-md transition-all border border-slate-100 flex flex-col justify-between"
        >
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-cyan-50 text-cyan-600">
              <Footprints className="w-4 h-4" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Steps</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {steps.toLocaleString()} <span className="text-xs font-normal text-slate-500">/ 6,000</span>
            </div>
            <div className="w-full bg-slate-100 rounded-full h-1.5 mt-2 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-500 h-1.5 rounded-full"
                style={{ width: `${Math.min(100, Math.round((steps / 6000) * 100))}%` }}
              />
            </div>
          </div>
        </div>

        {/* Sleep Card */}
        <div
          onClick={() => navigate('/sleep-activity')}
          className="glass-card rounded-2xl p-4 cursor-pointer hover:shadow-md transition-all border border-slate-100 flex flex-col justify-between"
        >
          <div className="flex items-center space-x-2">
            <div className="p-2 rounded-xl bg-indigo-50 text-indigo-500">
              <Moon className="w-4 h-4 fill-indigo-500" />
            </div>
            <span className="text-xs font-semibold text-slate-600">Sleep</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {sleepStr}
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[11px] text-amber-500 font-medium">
              <span>★ Excellent</span>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          ROW 3: THREE PANELS (Live ECG Monitor, AI Health Insights, Your Location)
                 + 3D ROBOT VOICE ASSISTANT (Spans Row 3 & 4 on right)
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        <div className="lg:col-span-9 space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
            {/* Live ECG Monitor */}
            <div className="md:col-span-5">
              <LiveECGCanvas heartRate={heartRate} />
            </div>

            {/* AI Health Insights */}
            <div className="md:col-span-4 glass-card rounded-2xl p-4 border border-slate-100 flex flex-col justify-between shadow-sm bg-gradient-to-br from-white via-white to-sky-50/40">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-600" />
                    <span>AI Health Insights</span>
                  </div>
                  <button
                    onClick={() => navigate('/ai-insights')}
                    className="text-[11px] text-cyan-600 font-semibold hover:underline flex items-center"
                  >
                    View Details ➔
                  </button>
                </div>

                <div className="flex items-center justify-around my-2">
                  <div className="w-14 h-14 rounded-full bg-amber-100/60 border border-amber-300 flex items-center justify-center text-amber-500 shadow-inner">
                    💡
                  </div>
                  <div className="flex items-end space-x-1 h-10">
                    <div className="w-2.5 h-6 bg-cyan-200 rounded-t"></div>
                    <div className="w-2.5 h-8 bg-cyan-400 rounded-t"></div>
                    <div className="w-2.5 h-10 bg-cyan-600 rounded-t"></div>
                  </div>
                </div>

                <p className="text-xs text-slate-600 mt-2 leading-relaxed">
                  {aiInsightText}
                </p>
              </div>
            </div>

            {/* Your Location */}
            <div className="md:col-span-3 glass-card rounded-2xl p-4 border border-slate-100 flex flex-col justify-between shadow-sm">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700">
                    <MapPin className="w-3.5 h-3.5 text-blue-600" />
                    <span>Your Location</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
                    {gpsLocation.isLive ? '● Live GPS' : '● Registered'}
                  </span>
                </div>

                <div className="relative w-full h-24 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center">
                  <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:10px_10px]" />
                  <div className="w-16 h-16 rounded-full bg-blue-500/15 border border-blue-400 flex items-center justify-center animate-pulse">
                    <div className="w-4 h-4 rounded-full bg-blue-600 border-2 border-white shadow-md"></div>
                  </div>
                  <div className="absolute bottom-1 bg-white/90 px-2 py-0.5 rounded text-[10px] font-bold text-slate-700 shadow-sm">
                    {gpsLocation.lat}, {gpsLocation.lng}
                  </div>
                </div>
              </div>

              <div className="mt-2 text-center">
                <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span>✓</span>
                  <span>Safe Zone: Active</span>
                </span>
              </div>
            </div>
          </div>

          {/* ROW 4 */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
            {/* Sleep & Activity Card */}
            <div className="md:col-span-4 glass-card rounded-2xl p-4 border border-slate-100 flex flex-col justify-between shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700">
                  <Moon className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Sleep & Activity</span>
                </div>
                <button
                  onClick={() => navigate('/sleep-activity')}
                  className="text-[11px] text-cyan-600 font-semibold hover:underline"
                >
                  View Details ➔
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 items-center my-1">
                <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-indigo-50/50">
                  <span className="text-xl font-black text-indigo-950">{sleepStr}</span>
                  <span className="text-[10px] text-indigo-600 font-medium">Sleep</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-600 font-medium">
                    <span className="p-1 rounded bg-indigo-100 text-indigo-600">🛌</span>
                    <span>88% Quality</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-600 font-medium">
                    <span className="p-1 rounded bg-cyan-100 text-cyan-600">🏃</span>
                    <span>2.4 km Activity</span>
                  </div>
                </div>
              </div>

              <div className="relative h-14 rounded-xl overflow-hidden bg-gradient-to-r from-blue-900 to-indigo-950 flex items-center justify-center text-white text-xs">
                <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:8px_8px]" />
                <span className="z-10 font-medium">✨ Peaceful Deep Sleep Monitored</span>
              </div>
            </div>

            {/* Health Digital Twin Card */}
            <div className="md:col-span-5 bg-gradient-to-br from-[#0c182b] via-[#0f2444] to-[#081224] rounded-2xl p-4 text-white border border-cyan-500/30 shadow-xl flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-cyan-300">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Your Health Digital Twin</span>
                </div>
              </div>

              <div className="flex items-center justify-between my-2">
                <div className="relative w-24 h-28 flex items-center justify-center">
                  <div className="absolute inset-0 rounded-full bg-cyan-400/20 blur-lg animate-pulse" />
                  <svg className="w-16 h-28 stroke-cyan-400 fill-cyan-400/10 drop-shadow-[0_0_8px_#00F0FF]" viewBox="0 0 100 200">
                    <circle cx="50" cy="20" r="14" strokeWidth="2" />
                    <line x1="50" y1="34" x2="50" y2="44" strokeWidth="2" />
                    <polygon points="35,44 65,44 58,110 42,110" strokeWidth="2" />
                    <line x1="35" y1="46" x2="20" y2="80" strokeWidth="2" />
                    <line x1="20" y1="80" x2="16" y2="115" strokeWidth="2" />
                    <line x1="65" y1="46" x2="80" y2="80" strokeWidth="2" />
                    <line x1="80" y1="80" x2="84" y2="115" strokeWidth="2" />
                    <line x1="44" y1="110" x2="40" y2="155" strokeWidth="2" />
                    <line x1="40" y1="155" x2="38" y2="195" strokeWidth="2" />
                    <line x1="56" y1="110" x2="60" y2="155" strokeWidth="2" />
                    <line x1="60" y1="155" x2="62" y2="195" strokeWidth="2" />
                    <circle cx="50" cy="65" r="4" fill="#00FFA3" className="animate-ping" />
                  </svg>
                </div>

                <div className="flex-1 ml-3 space-y-2">
                  <div className="text-[11px] text-slate-300 font-medium">Health Status</div>
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    <span>✓</span>
                    <span>Stable</span>
                  </div>
                  <div className="text-[10px] text-slate-400">vs. your baseline</div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-gradient-to-r from-emerald-400 to-cyan-400 h-1.5 rounded-full w-[85%]" />
                  </div>
                  <div className="text-right text-[10px] text-cyan-300 font-bold">+2% Sub-threshold</div>
                </div>
              </div>

              <div className="text-right pt-1">
                <button
                  onClick={() => navigate('/health')}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40"
                >
                  View Details ➔
                </button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="md:col-span-3 glass-card rounded-2xl p-4 border border-slate-100 flex flex-col justify-between shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Quick Actions</span>
                </div>
                <button
                  onClick={() => navigate('/settings')}
                  className="text-[11px] text-cyan-600 font-semibold hover:underline"
                >
                  View All ➔
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 my-auto">
                <button
                  onClick={() => navigate('/communication')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Mic className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    Voice Assistant
                  </span>
                </button>

                <button
                  onClick={() => navigate('/gps')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Navigation className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    Find My Location
                  </span>
                </button>

                <button
                  onClick={() => navigate('/communication')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Users className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    Contact Caregiver
                  </span>
                </button>

                <button
                  onClick={() => navigate('/notifications')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group"
                >
                  <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Pill className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    Medication Reminder
                  </span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: 3D Robot AI Voice Assistant Widget */}
        <div className="lg:col-span-3 flex flex-col">
          <VoiceAssistantWidget userName={displayName} className="flex-1" />
        </div>
      </div>
    </div>
  );
};
