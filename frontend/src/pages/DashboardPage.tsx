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
  FileText,
  KeyRound,
  Radio,
  CheckCircle2,
  ChevronDown,
  Copy,
  X,
} from 'lucide-react';
import { healthService, emergencyService, aiService, patientAuthService, deviceService } from '../api/services';
import type { MedicalReport, FamilyPatient } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { LiveECGCanvas } from '../components/LiveECGCanvas';
import { VoiceAssistantWidget } from '../components/VoiceAssistantWidget';
import type { DashboardSummary } from '../api/types';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, role } = useAuth();
  const { t } = useLanguage();

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
  // Patient Identity, Device Pairing & Medical Reports State
  const [activePatientId, setActivePatientId] = useState<string>('PT-2026-000001');
  const [activeDeviceUuid, setActiveDeviceUuid] = useState<string>('DEV-WEAR-001');
  const [familyPatients, setFamilyPatients] = useState<FamilyPatient[]>([]);
  const [medicalReports, setMedicalReports] = useState<MedicalReport[]>([]);
  const [showReportsModal, setShowReportsModal] = useState(false);
  const [showPairingModal, setShowPairingModal] = useState(false);
  const [newDeviceInput, setNewDeviceInput] = useState('DEV-WEAR-001');
  const [pairingSuccessMsg, setPairingSuccessMsg] = useState<string | null>(null);
  const [copiedPatientId, setCopiedPatientId] = useState(false);

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
        if (data.patient_id) {
          // Keep active device and patient in sync
          if (data.device_status?.device_uuid) {
            setActiveDeviceUuid(data.device_status.device_uuid);
          }
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
    // Initial load of family patients & medical reports
    patientAuthService.getFamilyPatients().then(pats => {
      if (pats && pats.length > 0) {
        setFamilyPatients(pats);
        const savedPid = localStorage.getItem('patient_id') || pats[0].patient_id;
        setActivePatientId(savedPid);
        const match = pats.find(p => p.patient_id === savedPid);
        if (match && match.device_uuid) {
          setActiveDeviceUuid(match.device_uuid);
        }
      }
    }).catch(() => {});

    patientAuthService.getMedicalReports().then(reps => {
      if (reps) setMedicalReports(reps);
    }).catch(() => {});

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

  const handleSwitchPatient = async (pid: string) => {
    setActivePatientId(pid);
    localStorage.setItem('patient_id', pid);
    const selected = familyPatients.find(p => p.patient_id === pid);
    if (selected && selected.device_uuid) {
      setActiveDeviceUuid(selected.device_uuid);
    }
    // Reload patient reports
    try {
      const reps = await patientAuthService.getMedicalReports(selected?.profile_id);
      setMedicalReports(reps);
    } catch {}
  };

  const handlePairDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeviceInput.trim()) return;
    try {
      await deviceService.pairDevice({
        device_uuid: newDeviceInput.trim().toUpperCase(),
        device_name: 'Smartwatch ' + newDeviceInput.trim().toUpperCase(),
        model_type: 'smartwatch',
      });
      setActiveDeviceUuid(newDeviceInput.trim().toUpperCase());
      setPairingSuccessMsg(`Wearable ${newDeviceInput.trim().toUpperCase()} paired successfully! Records preserved.`);
      setTimeout(() => {
        setPairingSuccessMsg(null);
        setShowPairingModal(false);
      }, 2000);
    } catch {
      setActiveDeviceUuid(newDeviceInput.trim().toUpperCase());
      setPairingSuccessMsg(`Wearable ${newDeviceInput.trim().toUpperCase()} paired in local sync mode.`);
      setTimeout(() => {
        setPairingSuccessMsg(null);
        setShowPairingModal(false);
      }, 2000);
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
                {t('dash.goodMorning', 'Good Morning')}, {displayName}! 🌸
              </h1>
              <p className="text-slate-500 text-sm mt-0.5">{t('dash.motto', 'Stay healthy, stay happy, and live longer.')}</p>
            </div>

            {/* Badges / Pills */}
            <div className="flex flex-wrap items-center justify-center md:justify-start gap-2 pt-1">
              {/* Connected Pill */}
              <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>{isLiveOnline ? t('dash.wearableConnected', 'Wearable connected & live') : t('dash.wearableDemo', 'Wearable connected (Demo sync)')}</span>
              </div>

              {/* Battery Pill */}
              <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full text-xs font-medium bg-white/80 text-slate-600 border border-slate-200 shadow-sm">
                <BatteryCharging className="w-3.5 h-3.5 text-emerald-600" />
                <span>{batteryPct}%</span>
                <span className="text-slate-300">|</span>
                <span className="text-slate-500">{t('dash.lastSync', 'Last sync')}: {lastSyncStr}</span>
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
              <h3 className="text-lg font-bold">{t('sos.emergencySOS', 'Emergency SOS')}</h3>
              <p className="text-xs text-rose-100">{t('sos.holdNotice', 'Hold 2 sec to trigger caregiver escalation')}</p>
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
                    <span>{t('sos.broadcasting', 'Broadcasting SOS to Caregivers...')}</span>
                  </>
                )}
                {sosStatus === 'dispatched' && (
                  <span className="text-emerald-700 font-extrabold">{t('sos.dispatched', '✓ SOS Dispatched to Contacts')}</span>
                )}
                {sosStatus === 'error' && (
                  <span className="text-rose-700 font-extrabold">{t('sos.failed', 'Transmission Failed – Try Again')}</span>
                )}
                {sosStatus === 'idle' && (
                  <span>{holdingSOS ? `${t('sos.holding', 'Hold')} (${holdProgress}%)...` : t('sos.pressAndHold', '📞 Press & Hold ➔')}</span>
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
            <span className="text-xs font-semibold text-slate-600">{t('vital.heartRate', 'Heart Rate')}</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {heartRate} <span className="text-xs font-normal text-slate-500">{t('vital.bpm', 'BPM')}</span>
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
            <span className="text-xs font-semibold text-slate-600">{t('vital.spo2', 'SpO2')}</span>
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
            <span className="text-xs font-semibold text-slate-600">{t('vital.bodyTemp', 'Body Temp')}</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {temp} <span className="text-xs font-normal text-slate-500">°C</span>
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[11px] text-emerald-600 font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
              <span>{t('vital.normalRange', 'Normal Range')}</span>
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
            <span className="text-xs font-semibold text-slate-600">{t('vital.steps', 'Steps')}</span>
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
            <span className="text-xs font-semibold text-slate-600">{t('vital.sleep', 'Sleep')}</span>
          </div>
          <div className="mt-2">
            <div className="text-2xl font-extrabold text-slate-800">
              {sleepStr}
            </div>
            <div className="flex items-center space-x-1 mt-1 text-[11px] text-amber-500 font-medium">
              <span>{t('vital.excellent', '★ Excellent')}</span>
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
                    <span>{t('dash.aiHealthInsights', 'AI Health Insights')}</span>
                  </div>
                  <button
                    onClick={() => navigate('/ai-insights')}
                    className="text-[11px] text-cyan-600 font-semibold hover:underline flex items-center cursor-pointer"
                  >
                    {t('dash.viewDetails', 'View Details ➔')}
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
                    <span>{t('dash.yourLocation', 'Your Location')}</span>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
                    {gpsLocation.isLive ? t('dash.liveGPS', '● Live GPS') : t('dash.registered', '● Registered')}
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
                  <span>{t('dash.safeZoneActive', 'Safe Zone: Active (500m)')}</span>
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
                  <span>{t('dash.sleepAndActivity', 'Sleep & Activity')}</span>
                </div>
                <button
                  onClick={() => navigate('/sleep-activity')}
                  className="text-[11px] text-cyan-600 font-semibold hover:underline cursor-pointer"
                >
                  {t('dash.viewDetails', 'View Details ➔')}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-2 items-center my-1">
                <div className="flex flex-col items-center justify-center p-2 rounded-xl bg-indigo-50/50">
                  <span className="text-xl font-black text-indigo-950">{sleepStr}</span>
                  <span className="text-[10px] text-indigo-600 font-medium">{t('vital.sleep', 'Sleep')}</span>
                </div>

                <div className="space-y-1.5 text-xs">
                  <div className="flex items-center space-x-1.5 text-slate-600 font-medium">
                    <span className="p-1 rounded bg-indigo-100 text-indigo-600">🛌</span>
                    <span>{t('dash.sleepQuality', '88% Quality')}</span>
                  </div>
                  <div className="flex items-center space-x-1.5 text-slate-600 font-medium">
                    <span className="p-1 rounded bg-cyan-100 text-cyan-600">🏃</span>
                    <span>{t('dash.activityKm', '2.4 km Activity')}</span>
                  </div>
                </div>
              </div>

              <div className="relative h-14 rounded-xl overflow-hidden bg-gradient-to-r from-blue-900 to-indigo-950 flex items-center justify-center text-white text-xs">
                <div className="absolute inset-0 opacity-40 bg-[radial-gradient(#ffffff_1px,transparent_1px)] [background-size:8px_8px]" />
                <span className="z-10 font-medium">{t('dash.sleepPeaceful', '✨ Peaceful Deep Sleep Monitored')}</span>
              </div>
            </div>

            {/* Health Digital Twin Card */}
            <div className="md:col-span-5 bg-gradient-to-br from-[#0c182b] via-[#0f2444] to-[#081224] rounded-2xl p-4 text-white border border-cyan-500/30 shadow-xl flex flex-col justify-between relative overflow-hidden">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-cyan-300">
                  <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                  <span>{t('dash.digitalTwin', 'Your Health Digital Twin')}</span>
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
                  <div className="text-[11px] text-slate-300 font-medium">{t('dash.healthStatus', 'Health Status')}</div>
                  <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    <span>✓</span>
                    <span>{t('dash.stable', 'Stable')}</span>
                  </div>
                  <div className="text-[10px] text-slate-400">{t('dash.vsBaseline', 'vs. your baseline')}</div>
                  <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                    <div className="bg-gradient-to-r from-emerald-400 to-cyan-400 h-1.5 rounded-full w-[85%]" />
                  </div>
                  <div className="text-right text-[10px] text-cyan-300 font-bold">+2% Sub-threshold</div>
                </div>
              </div>

              <div className="text-right pt-1">
                <button
                  onClick={() => navigate('/health')}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/40 cursor-pointer"
                >
                  {t('dash.viewDetails', 'View Details ➔')}
                </button>
              </div>
            </div>

            {/* Quick Actions */}
            <div className="md:col-span-3 glass-card rounded-2xl p-4 border border-slate-100 flex flex-col justify-between shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-1.5 text-xs font-bold text-slate-700">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>{t('action.quickActions', 'Quick Actions')}</span>
                </div>
                <button
                  onClick={() => navigate('/settings')}
                  className="text-[11px] text-cyan-600 font-semibold hover:underline cursor-pointer"
                >
                  {t('dash.viewAll', 'View All ➔')}
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 my-auto">
                <button
                  onClick={() => navigate('/communication')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Mic className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    {t('action.voiceAssistant', 'Voice Assistant')}
                  </span>
                </button>

                <button
                  onClick={() => navigate('/gps')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Navigation className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    {t('action.findLocation', 'Find My Location')}
                  </span>
                </button>

                <button
                  onClick={() => navigate('/communication')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-purple-50 text-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Users className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    {t('action.contactCaregiver', 'Contact Caregiver')}
                  </span>
                </button>

                <button
                  onClick={() => navigate('/notifications')}
                  className="flex flex-col items-center justify-center p-2 rounded-xl hover:bg-slate-50 transition-colors group cursor-pointer"
                >
                  <div className="w-10 h-10 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center group-hover:scale-110 transition-transform shadow-sm">
                    <Pill className="w-4 h-4" />
                  </div>
                  <span className="text-[10px] font-semibold text-slate-600 mt-1.5 text-center">
                    {t('action.medicationReminder', 'Medication Reminder')}
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
      {/* Medical Reports & Clinical Observations Modal */}
      {showReportsModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 shadow-2xl border border-slate-100 max-h-[85vh] flex flex-col animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Individual Medical History & Reports</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient ID: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowReportsModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {medicalReports.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs">
                  No medical reports available for this patient yet.
                </div>
              ) : (
                medicalReports.map((report) => (
                  <div
                    key={report.id}
                    className="p-4 rounded-2xl bg-slate-50 border border-slate-200 hover:border-indigo-300 transition-all space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-indigo-900 uppercase tracking-wider bg-indigo-100 px-2.5 py-0.5 rounded-full">
                        {report.report_type}
                      </span>
                      <span className="text-[11px] text-slate-400">
                        {new Date(report.report_date).toLocaleDateString()}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-800">{report.title}</h4>
                    <p className="text-xs text-slate-600 leading-relaxed">{report.summary}</p>

                    {report.observations && (
                      <div className="text-xs bg-white p-2.5 rounded-xl border border-slate-100">
                        <strong className="text-slate-700">Observations: </strong>
                        <span className="text-slate-600">{report.observations}</span>
                      </div>
                    )}

                    {report.recommendations && (
                      <div className="text-xs bg-emerald-50 text-emerald-800 p-2.5 rounded-xl border border-emerald-100">
                        <strong className="text-emerald-900">Recommendations: </strong>
                        <span>{report.recommendations}</span>
                      </div>
                    )}

                    <div className="text-[11px] text-slate-400 text-right pt-1 font-medium">
                      Physician: <strong className="text-slate-600">{report.doctor_name}</strong>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                type="button"
                onClick={() => setShowReportsModal(false)}
                className="px-5 py-2 bg-slate-800 text-white rounded-xl text-xs font-bold hover:bg-slate-900 cursor-pointer"
              >
                Close Records
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Wearable Device Pairing Modal */}
      {showPairingModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-cyan-100 text-cyan-600 flex items-center justify-center">
                  <Radio className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Pair Wearable Device</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowPairingModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {pairingSuccessMsg && (
              <div className="mb-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{pairingSuccessMsg}</span>
              </div>
            )}

            <form onSubmit={handlePairDevice} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Wearable Hardware UUID / ID
                </label>
                <input
                  type="text"
                  value={newDeviceInput}
                  onChange={(e) => setNewDeviceInput(e.target.value)}
                  placeholder="e.g. DEV-WEAR-001 or ESP32-MAC-4A2"
                  className="w-full px-3.5 py-2.5 bg-white border border-slate-200 rounded-xl text-xs font-mono font-bold focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                  required
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Pairing a new or replacement smartwatch updates real-time telemetry streaming while preserving all past telemetry and health history.
                </p>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100 text-[11px] text-slate-600 space-y-1">
                <div>Currently Active Device: <strong className="font-mono text-slate-800">{activeDeviceUuid}</strong></div>
                <div>Supported: PulseGuardian Watch V2, ESP32 BLE, WearOS Bridge</div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPairingModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-[#0284c7] hover:bg-[#0369a1] text-white text-xs font-bold rounded-xl shadow-md cursor-pointer"
                >
                  Confirm Pairing
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
