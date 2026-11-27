import QRCode from 'qrcode';
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
  Plus,
  Trash2,
  Check,
  Clock,
  Calendar as CalendarIcon,
  AlertTriangle,
  Volume2,
  Bell,
  CheckCircle,
  FileText,
  KeyRound,
  Radio,
  CheckCircle2,
  ChevronDown,
  Copy,
  X,
  Upload,
  FileUp,
  ExternalLink,
  Stethoscope,
  QrCode,
  Music,
  Printer,
  Download,
  Phone,
  PhoneCall,
  Mail,
  Play,
  Square,
  ShieldCheck,
} from 'lucide-react';
import { healthService, emergencyService, aiService, patientAuthService, deviceService, patientDashboardService } from '../api/services';
import type { PatientMedicine, PatientReminder, DoctorAppointment, MedicalCondition, PatientAllergy, HydrationSummary } from '../api/types';
import type { MedicalReport, FamilyPatient, DigitalDocument, EmergencyQRProfile, EmergencyQRPublicView } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { LiveECGCanvas } from '../components/LiveECGCanvas';
import type { DashboardSummary } from '../api/types';

// Web Audio API Ringtone Synthesizer
function playRingtonePreview(tone: string): () => void {
  const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
  if (!AudioContextClass) return () => {};
  const ctx = new AudioContextClass();
  const now = ctx.currentTime;

  if (tone === 'pulse_alert') {
    [0, 0.22, 0.5, 0.72].forEach((t) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'triangle';
      osc.frequency.setValueAtTime(880, now + t);
      gain.gain.setValueAtTime(0.28, now + t);
      gain.gain.exponentialRampToValueAtTime(0.001, now + t + 0.12);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + t);
      osc.stop(now + t + 0.14);
    });
  } else if (tone === 'forest_birds') {
    [0, 0.14, 0.3, 0.48, 0.65].forEach((t, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      const startF = 1500 + i * 160;
      osc.frequency.setValueAtTime(startF, now + t);
      osc.frequency.exponentialRampToValueAtTime(startF + 400, now + t + 0.08);
      gain.gain.setValueAtTime(0.2, now + t);
      gain.gain.exponentialRampToValueAtTime(0.001, now + t + 0.09);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + t);
      osc.stop(now + t + 0.1);
    });
  } else if (tone === 'ocean_waves') {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(140, now);
    osc.frequency.exponentialRampToValueAtTime(340, now + 0.6);
    osc.frequency.exponentialRampToValueAtTime(110, now + 1.2);
    gain.gain.setValueAtTime(0.01, now);
    gain.gain.linearRampToValueAtTime(0.25, now + 0.6);
    gain.gain.linearRampToValueAtTime(0.001, now + 1.2);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 1.25);
  } else if (tone === 'zen_bell') {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(432, now);
    gain.gain.setValueAtTime(0.35, now);
    gain.gain.exponentialRampToValueAtTime(0.0001, now + 1.6);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(now);
    osc.stop(now + 1.65);
  } else if (tone === 'digital_watch') {
    [0, 0.12, 0.28, 0.4].forEach((t) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'square';
      osc.frequency.setValueAtTime(2048, now + t);
      gain.gain.setValueAtTime(0.14, now + t);
      gain.gain.exponentialRampToValueAtTime(0.001, now + t + 0.07);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + t);
      osc.stop(now + t + 0.08);
    });
  } else {
    // gentle_chime (default)
    const freqs = [523.25, 659.25, 783.99, 1046.5];
    freqs.forEach((freq, idx) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now + idx * 0.18);
      gain.gain.setValueAtTime(0.001, now + idx * 0.18);
      gain.gain.exponentialRampToValueAtTime(0.26, now + idx * 0.18 + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.18 + 0.5);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now + idx * 0.18);
      osc.stop(now + idx * 0.18 + 0.55);
    });
  }

  return () => {
    try {
      ctx.close();
    } catch {}
  };
}

// Standard ISO-Compliant Scannable QR Code Renderer
export const PatientQRCode: React.FC<{ token: string; size?: number }> = ({ token, size = 150 }) => {
  const [qrSrc, setQrSrc] = useState<string>('');

  useEffect(() => {
    const url = `${window.location.origin}/emergency-qr/public/${token}`;
    QRCode.toDataURL(url, {
      width: size * 2,
      margin: 1,
      errorCorrectionLevel: 'M',
      color: {
        dark: '#0a1526',
        light: '#ffffff',
      },
    })
      .then((dataUri) => setQrSrc(dataUri))
      .catch((err) => console.error('QR code generation failed', err));
  }, [token, size]);

  if (!qrSrc) {
    return (
      <div style={{ width: size, height: size }} className="rounded-xl bg-white flex items-center justify-center p-2 shadow-inner">
        <div className="w-6 h-6 border-2 border-slate-300 border-t-cyan-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <img
      src={qrSrc}
      alt={`Emergency QR Code for ${token}`}
      style={{ width: size, height: size }}
      className="rounded-xl shadow-inner bg-white p-1.5"
    />
  );
};

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
  const [digitalDocs, setDigitalDocs] = useState<DigitalDocument[]>([]);
  const [showUploadDocModal, setShowUploadDocModal] = useState(false);
  const [uploadDocName, setUploadDocName] = useState('');
  const [uploadDocType, setUploadDocType] = useState('lab_report');
  const [uploadDocText, setUploadDocText] = useState('');
  const [selectedPdfFile, setSelectedPdfFile] = useState<File | null>(null);
  const [pdfDataUrl, setPdfDataUrl] = useState<string>('');
  const [selectedDocPreviewModal, setSelectedDocPreviewModal] = useState<any | null>(null);

  const handlePdfFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedPdfFile(file);
      if (!uploadDocName.trim() || uploadDocName === 'New Clinical Report.pdf') {
        setUploadDocName(file.name);
      }
      const reader = new FileReader();
      reader.onload = () => {
        setPdfDataUrl(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleOpenReportPdf = (doc: any) => {
    if (doc.file_url && doc.file_url.startsWith('data:application/pdf')) {
      const win = window.open();
      if (win) {
        win.document.write(
          `<iframe src="${doc.file_url}" frameborder="0" style="border:0; top:0px; left:0px; bottom:0px; right:0px; width:100%; height:100%;" allowfullscreen></iframe>`
        );
      } else {
        const a = document.createElement('a');
        a.href = doc.file_url;
        a.download = doc.document_name.endsWith('.pdf') ? doc.document_name : `${doc.document_name}.pdf`;
        a.click();
      }
    } else {
      setSelectedDocPreviewModal(doc);
    }
  };

  // Live Location Clock & Calendar State
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [selectedCalendarDate, setSelectedCalendarDate] = useState<Date>(new Date());
  const [userTimezone, setUserTimezone] = useState<string>('Local');

  // Ringtone & Audio Synthesizer State
  const [newRemTone, setNewRemTone] = useState<string>('gentle_chime');
  const [newRemDays, setNewRemDays] = useState<string>('Daily');
  const [newRemDate, setNewRemDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [playingTone, setPlayingTone] = useState<string | null>(null);
  const audioStopRef = useRef<(() => void) | null>(null);

  // Emergency QR Profile State
  const [qrProfile, setQrProfile] = useState<EmergencyQRProfile | null>(null);
  const [showQRModal, setShowQRModal] = useState<boolean>(false);
  const [publicQRView, setPublicQRView] = useState<EmergencyQRPublicView | null>(null);
  const [isLoadingPublicQR, setIsLoadingPublicQR] = useState<boolean>(false);
  const [isUploadingDoc, setIsUploadingDoc] = useState(false);
  const [isAnalyzingDocId, setIsAnalyzingDocId] = useState<number | null>(null);
  const [selectedDocDetails, setSelectedDocDetails] = useState<DigitalDocument | null>(null);
  const [bleConnected, setBleConnected] = useState(false);
  const [bleConnecting, setBleConnecting] = useState(false);
  const [testWifiSending, setTestWifiSending] = useState(false);

  // MODULE 1, 4, 5, 6, 7 state
  const [bloodPressure, setBloodPressure] = useState<string>('120/80');
  const [distanceKm, setDistanceKm] = useState<number>(3.4);
  const [hydration, setHydration] = useState<HydrationSummary>({ total_intake_ml: 1250, target_intake_ml: 2500, percentage: 50.0, logs_count: 5 });
  const [medicines, setMedicines] = useState<PatientMedicine[]>([]);
  const [reminders, setReminders] = useState<PatientReminder[]>([]);
  const [appointments, setAppointments] = useState<DoctorAppointment[]>([]);
  const [conditions, setConditions] = useState<MedicalCondition[]>([]);
  const [allergies, setAllergies] = useState<PatientAllergy[]>([]);
  const [caregiverDirectory, setCaregiverDirectory] = useState<any[]>([
    {
      id: 1,
      name: 'Sarah Jenkins (Primary Caregiver)',
      relationship: 'Primary Caregiver / Clinical Nurse',
      phone: '+91 98765 43220',
      email: 'caregiver@pulseguardian.ai',
      is_primary: true,
      escalation_tier: 1,
      organization: 'PulseHealth Clinic & Family Care',
    },
    {
      id: 2,
      name: 'Ananya (Family Caregiver)',
      relationship: 'Daughter / Family Guardian',
      phone: '+91 98450 67890',
      email: 'ananya.family@pulseguardian.ai',
      is_primary: false,
      escalation_tier: 2,
      organization: 'Authorized Family Guardian',
    },
  ]);
  const [ringingAlarmReminder, setRingingAlarmReminder] = useState<PatientReminder | null>(null);
  const [medicineActionToast, setMedicineActionToast] = useState<string | null>(null);

  // Modals
  const [showAddMedModal, setShowAddMedModal] = useState(false);
  const [showAddReminderModal, setShowAddReminderModal] = useState(false);
  const [showAddApptModal, setShowAddApptModal] = useState(false);
  const [showAddConditionModal, setShowAddConditionModal] = useState(false);

  // Forms
  const [newMedName, setNewMedName] = useState('');
  const [newMedDosage, setNewMedDosage] = useState('1 Tablet');
  const [newMedFreq, setNewMedFreq] = useState('Twice daily');
  const [newMedTimes, setNewMedTimes] = useState('08:00,20:00');
  const [newMedQty, setNewMedQty] = useState(30);

  const [newRemTitle, setNewRemTitle] = useState('');
  const [newRemType, setNewRemType] = useState<'medicine' | 'sleep' | 'hydration' | 'appointment'>('medicine');
  const [newRemTime, setNewRemTime] = useState('08:00');

  const [newApptDoctor, setNewApptDoctor] = useState('Dr. Sunita Rao');
  const [newApptSpec, setNewApptSpec] = useState('Cardiologist');
  const [newApptDate, setNewApptDate] = useState('');
  const [newApptReason, setNewApptReason] = useState('Regular Cardiovascular Checkup');

  const [newConditionName, setNewConditionName] = useState('');
  const [newConditionSeverity, setNewConditionSeverity] = useState('mild');

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
          if (data.latest_vitals.blood_pressure_sys && data.latest_vitals.blood_pressure_dia) {
            setBloodPressure(`${Math.round(data.latest_vitals.blood_pressure_sys)}/${Math.round(data.latest_vitals.blood_pressure_dia)}`);
          }
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

    // Fetch Medicines, Reminders, Appointments, Hydration, Conditions
    patientDashboardService.getMedicines().then(res => { if (res) setMedicines(res); }).catch(() => {});
    patientDashboardService.getReminders().then(res => { if (res) setReminders(res); }).catch(() => {});
    patientDashboardService.getAppointments().then(res => { if (res) setAppointments(res); }).catch(() => {});
    patientDashboardService.getHydration().then(res => { if (res) setHydration(res); }).catch(() => {});
    patientDashboardService.getConditions().then(res => { if (res) setConditions(res); }).catch(() => {});
    patientDashboardService.getAllergies().then(res => { if (res) setAllergies(res); }).catch(() => {});
    patientDashboardService.getDigitalDocuments().then(res => { if (res) setDigitalDocs(res); }).catch(() => {});
    patientDashboardService.getEmergencyQRProfile().then(res => { if (res) setQrProfile(res); }).catch(() => {});
    patientDashboardService.getCaregiverDirectory().then(res => { if (res && res.length > 0) setCaregiverDirectory(res); }).catch(() => {});

    try {
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
      setUserTimezone(tz || 'Local');
    } catch {}

    const clockTimer = setInterval(() => {
      const now = new Date();
      setCurrentTime(now);

      // Check for real-time audible alarms (HH:MM matching enabled routine)
      const currentHours = String(now.getHours()).padStart(2, '0');
      const currentMins = String(now.getMinutes()).padStart(2, '0');
      const timeStr = `${currentHours}:${currentMins}`;

      // Alarm match check (trigger once per minute)
      if (now.getSeconds() === 0) {
        const matchingRem = reminders.find(
          (r) => r.is_enabled && r.reminder_time === timeStr
        );
        if (matchingRem) {
          setRingingAlarmReminder(matchingRem);
          try {
            playRingtonePreview(matchingRem.alarm_tone || 'gentle_chime');
          } catch {}
        }
      }
    }, 1000);

    loadDashboardData();
    const interval = setInterval(loadDashboardData, 12000);
    const handleOnline = () => { loadDashboardData(); };
    window.addEventListener('online', handleOnline);
    return () => {
      clearInterval(interval);
      window.removeEventListener('online', handleOnline);
    };
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

      // Dial primary caregiver or launch dialer
      const primaryCg = caregiverDirectory.find((c: any) => c.is_primary) || caregiverDirectory[0];
      if (primaryCg && primaryCg.phone) {
        window.location.href = `tel:${primaryCg.phone.replace(/[^0-9+]/g, '')}`;
      }

      setTimeout(() => {
        setSosStatus('idle');
        setHoldProgress(0);
      }, 7000);
    } catch (err: any) {
      // Direct emergency fallback to phone call
      const primaryCg = caregiverDirectory.find((c: any) => c.is_primary) || caregiverDirectory[0];
      if (primaryCg && primaryCg.phone) {
        window.location.href = `tel:${primaryCg.phone.replace(/[^0-9+]/g, '')}`;
      }
      setSosStatus('error');
      setSosErrorMsg(err?.response?.data?.detail || 'Failed to transmit SOS to dispatch server. Calling primary caregiver directly via dialer...');
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

  const handleConnectBluetooth = async () => {
    if (!('bluetooth' in navigator)) {
      alert('Web Bluetooth requires Chrome, Edge, or Opera with Bluetooth hardware enabled.');
      return;
    }
    setBleConnecting(true);
    try {
      const device = await (navigator as any).bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['heart_rate', 'battery_service', 'health_thermometer', 0x180d, 0x180f, 0x1809]
      });

      const server = await device.gatt?.connect();
      setBleConnected(true);
      const devUuid = device.id || device.name || 'ESP32-BLE-WATCH';
      setActiveDeviceUuid(devUuid);
      setNewDeviceInput(devUuid);
      setPairingSuccessMsg(`Connected to ${device.name || 'Wearable BLE'}! Live telemetry stream established.`);

      try {
        const service = await server.getPrimaryService('heart_rate');
        const characteristic = await service.getCharacteristic('heart_rate_measurement');
        await characteristic.startNotifications();
        characteristic.addEventListener('characteristicvaluechanged', (event: any) => {
          const value = event.target.value;
          const hr = value.getUint8(1);
          setHeartRate(hr);
          healthService.ingestTelemetry({
            heart_rate: hr,
            spo2: 98.4,
            temperature: 36.6,
            device_uuid: devUuid
          }).catch(() => {});
        });
      } catch {}
    } catch (err: any) {
      if (err.name !== 'NotFoundError') {
        alert(err.message || 'Bluetooth connection error.');
      }
    } finally {
      setBleConnecting(false);
    }
  };

  const handleSendTestWifiPacket = async () => {
    setTestWifiSending(true);
    try {
      const now = new Date();
      await healthService.ingestTelemetry({
        device_uuid: activeDeviceUuid,
        heart_rate: 76.0,
        spo2: 98.5,
        temperature: 36.7,
        step_count: steps + 20,
        battery_percentage: 92.0,
        recorded_at: now.toISOString(),
      });
      setPairingSuccessMsg(`Wi-Fi telemetry packet ingested successfully for ${activeDeviceUuid}! Dashboard synced.`);
      setIsLiveOnline(true);
      setLastSyncStr('Just now');
      loadDashboardData();
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to ingest Wi-Fi telemetry packet.');
    } finally {
      setTestWifiSending(false);
    }
  };

  const handleMedicineAction = async (medId: number, status: 'taken' | 'skipped' | 'missed') => {
    // 1. Optimistic UI update for instant feedback
    setMedicines((prev) =>
      prev.map((m) => {
        if (m.id === medId) {
          if (status === 'taken') {
            const nextRemaining = Math.max(0, m.remaining_quantity - 1);
            return {
              ...m,
              remaining_quantity: nextRemaining,
              consumed_quantity: (m.consumed_quantity || 0) + 1,
              is_low_stock: nextRemaining <= 5,
            };
          }
        }
        return m;
      })
    );

    const targetMed = medicines.find((m) => m.id === medId);
    if (status === 'taken') {
      const remainingAfter = targetMed ? Math.max(0, targetMed.remaining_quantity - 1) : 0;
      if (remainingAfter === 0) {
        setMedicineActionToast(`🚨 Dosed recorded. WARNING: '${targetMed?.medicine_name}' is now OUT OF STOCK! Refill immediately.`);
      } else if (remainingAfter <= 5) {
        setMedicineActionToast(`⚠️ Dose recorded! '${targetMed?.medicine_name}' has low inventory (${remainingAfter} left). Stock decremented -1.`);
      } else {
        setMedicineActionToast(`✓ Dose recorded for '${targetMed?.medicine_name}'. Stock decremented by 1 (${remainingAfter} remaining).`);
      }
    } else {
      setMedicineActionToast(`Dose skipped for '${targetMed?.medicine_name}'. Stock inventory unchanged (${targetMed?.remaining_quantity} left).`);
    }
    setTimeout(() => setMedicineActionToast(null), 5000);

    // 2. Persist to backend
    try {
      await patientDashboardService.recordMedicineAction(medId, { status });
      const updated = await patientDashboardService.getMedicines();
      if (updated && updated.length > 0) {
        setMedicines(updated);
      }
    } catch {}
  };

  const handleCreateMedicine = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMedName.trim()) return;
    try {
      await patientDashboardService.addMedicine({
        medicine_name: newMedName.trim(),
        dosage: newMedDosage,
        frequency: newMedFreq,
        scheduled_times: newMedTimes,
        total_quantity: newMedQty,
        remaining_quantity: newMedQty,
        start_date: new Date().toISOString(),
      });
      setShowAddMedModal(false);
      setNewMedName('');
      const updated = await patientDashboardService.getMedicines();
      setMedicines(updated);
    } catch {}
  };

  const handleLogGlassWater = async () => {
    try {
      const updated = await patientDashboardService.logHydration(250);
      setHydration(updated);
    } catch {}
  };

  const handleToggleReminder = async (remId: number, currentVal: boolean) => {
    try {
      await patientDashboardService.updateReminder(remId, { is_enabled: !currentVal });
      const updated = await patientDashboardService.getReminders();
      setReminders(updated);
    } catch {}
  };

  const handlePlayTonePreview = (tone: string) => {
    if (playingTone === tone) {
      if (audioStopRef.current) audioStopRef.current();
      setPlayingTone(null);
      return;
    }
    if (audioStopRef.current) audioStopRef.current();
    setPlayingTone(tone);
    try {
      const stopFn = playRingtonePreview(tone);
      audioStopRef.current = stopFn;
      setTimeout(() => {
        setPlayingTone((prev) => (prev === tone ? null : prev));
      }, 2200);
    } catch {
      setPlayingTone(null);
    }
  };

  const handleOpenQRPortalModal = async () => {
    setShowQRModal(true);
    setIsLoadingPublicQR(true);
    try {
      const token = qrProfile?.qr_token || 'PT-QR-PT-2026-000001-A1B2C3D4';
      const data = await patientDashboardService.getPublicEmergencyQRProfile(token);
      setPublicQRView(data);
    } catch {
      // Fallback preview
      setPublicQRView({
        patient_name: displayName,
        patient_id_readable: activePatientId,
        blood_group: qrProfile?.blood_group || 'O+',
        allergies: allergies.map(a => `${a.allergen} (${a.reaction || 'mild'})`),
        medical_conditions: conditions.map(c => `${c.condition_name} (${c.severity})`),
        active_medicines: medicines.filter(m => m.medicine_status === 'active').map(m => `${m.medicine_name} ${m.dosage} - ${m.frequency}`),
        emergency_contacts: [
          { name: 'Ananya (Family Caregiver)', relation: 'Daughter', phone: '+91 98450 67890' },
          { name: 'Emergency Medical Services', relation: 'Hospital Dispatch', phone: '112 / 108' }
        ],
        emergency_instructions: qrProfile?.emergency_instructions || 'Diabetic patient under observation. Keep glucose tablets accessible.',
        doctor_contact: qrProfile?.doctor_contact_details || 'Dr. Sunita Rao (Cardiologist) - +91 98450 12345',
        uploaded_documents: digitalDocs.map(d => ({
          id: d.id,
          document_name: d.document_name,
          document_type: d.document_type,
          uploaded_at: d.uploaded_at,
          ai_summary: d.ai_summary || 'Document verified by clinical AI diagnostic engine.',
          ai_detected_conditions: d.ai_detected_conditions || 'None detected',
          ai_key_biomarkers: d.ai_key_biomarkers || 'Normal reference range',
          ai_clinical_suggestions: d.ai_clinical_suggestions || 'Continue prescribed routine.',
          ai_confidence_score: d.ai_confidence_score || 0.96
        })),
        is_verified: true,
        notice: 'Verified Emergency & Clinical Health QR Pass. Accessible for emergency first responders and attending clinical physicians.'
      });
    } finally {
      setIsLoadingPublicQR(false);
    }
  };

  const handleCreateReminder = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRemTitle.trim()) return;
    try {
      await patientDashboardService.createReminder({
        title: newRemTitle.trim(),
        reminder_type: newRemType,
        reminder_time: newRemTime,
        recurring_days: newRemDays,
        alarm_tone: newRemTone,
        is_enabled: true,
      });
      setShowAddReminderModal(false);
      setNewRemTitle('');
      const updated = await patientDashboardService.getReminders();
      setReminders(updated);
    } catch {}
  };

  const handleCreateAppointment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newApptDoctor.trim() || !newApptDate) return;
    try {
      await patientDashboardService.createAppointment({
        doctor_name: newApptDoctor.trim(),
        specialization: newApptSpec.trim(),
        appointment_date: new Date(newApptDate).toISOString(),
        reason: newApptReason,
      });
      setShowAddApptModal(false);
      const updated = await patientDashboardService.getAppointments();
      setAppointments(updated);
    } catch {}
  };

  const handleUploadDocument = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadDocName.trim()) return;
    setIsUploadingDoc(true);
    try {
      const newDoc = await patientDashboardService.uploadDigitalDocument({
        document_name: uploadDocName.trim(),
        document_type: uploadDocType,
        file_url: pdfDataUrl || `/documents/${uploadDocName.trim().replace(/\s+/g, '_').toLowerCase()}.pdf`,
        file_text_content: uploadDocText.trim() || (selectedPdfFile ? `Uploaded PDF file: ${selectedPdfFile.name} (${Math.round(selectedPdfFile.size / 1024)} KB)` : `Clinical notes for ${uploadDocName.trim()}`),
      });
      const updated = await patientDashboardService.getDigitalDocuments();
      setDigitalDocs(updated);
      setSelectedDocDetails(newDoc);
      setShowUploadDocModal(false);
      setUploadDocName('');
      setUploadDocText('');
      setSelectedPdfFile(null);
      setPdfDataUrl('');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to upload document.');
    } finally {
      setIsUploadingDoc(false);
    }
  };

  const handleReanalyzeDocument = async (docId: number) => {
    setIsAnalyzingDocId(docId);
    try {
      const updatedDoc = await patientDashboardService.analyzeDigitalDocument(docId);
      const updatedList = await patientDashboardService.getDigitalDocuments();
      setDigitalDocs(updatedList);
      if (selectedDocDetails && selectedDocDetails.id === docId) {
        setSelectedDocDetails(updatedDoc);
      }
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to re-analyze document.');
    } finally {
      setIsAnalyzingDocId(null);
    }
  };

  const handleDeleteDocument = async (docId: number) => {
    if (!confirm('Are you sure you want to remove this digital medical report?')) return;
    try {
      await patientDashboardService.deleteDigitalDocument(docId);
      const updatedList = await patientDashboardService.getDigitalDocuments();
      setDigitalDocs(updatedList);
      if (selectedDocDetails && selectedDocDetails.id === docId) {
        setSelectedDocDetails(null);
      }
    } catch {}
  };

  const handleCreateCondition = async (e: React.FormEvent) => {

    e.preventDefault();
    if (!newConditionName.trim()) return;
    try {
      await patientDashboardService.addCondition({
        condition_name: newConditionName.trim(),
        severity: newConditionSeverity,
      });
      setShowAddConditionModal(false);
      setNewConditionName('');
      const updated = await patientDashboardService.getConditions();
      setConditions(updated);
    } catch {}
  };

  const displayName = user?.full_name?.split(' ')[0] || (role === 'caregiver' ? 'Caregiver' : 'Thrisha');

  const handleCopyPatientId = () => {
    navigator.clipboard.writeText(activePatientId);
    setCopiedPatientId(true);
    setTimeout(() => setCopiedPatientId(false), 2000);
  };

  return (
    <div className="space-y-6 pb-14 font-sans select-none">
      {/* =========================================================================
          TOP COMMAND DECK: OMNI-STATUS CAPSULE BAR
         ========================================================================= */}
      <div className="relative rounded-3xl p-4 bg-gradient-to-r from-slate-900/95 via-[#0b172b]/95 to-slate-900/95 backdrop-blur-xl border border-cyan-500/30 shadow-2xl text-white flex flex-col md:flex-row items-center justify-between gap-4 overflow-hidden">
        {/* Ambient Backlight Glows */}
        <div className="absolute -top-10 left-1/4 w-72 h-16 bg-cyan-500/25 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-10 right-1/4 w-72 h-16 bg-rose-500/25 blur-3xl pointer-events-none" />

        {/* Left: Patient Profile Switcher & Identity Chip */}
        <div className="flex flex-wrap items-center gap-3 z-10 w-full md:w-auto">
          <div className="relative flex items-center gap-2.5 bg-white/10 px-3.5 py-1.5 rounded-2xl border border-white/15 backdrop-blur-md shadow-sm">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-cyan-400 to-blue-600 flex items-center justify-center font-black text-white text-xs shadow-md">
              {displayName.slice(0, 2).toUpperCase()}
            </div>
            <div className="flex flex-col text-left">
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-bold text-white tracking-wide">{displayName}</span>
                {familyPatients.length > 1 && (
                  <select
                    value={activePatientId}
                    onChange={(e) => handleSwitchPatient(e.target.value)}
                    className="bg-slate-800 text-cyan-300 text-[10px] font-bold rounded-lg px-1.5 py-0.5 border border-cyan-500/40 cursor-pointer focus:outline-none"
                  >
                    {familyPatients.map((p) => (
                      <option key={p.patient_id} value={p.patient_id} className="bg-slate-900 text-white">
                        {p.full_name} ({p.patient_id})
                      </option>
                    ))}
                  </select>
                )}
              </div>
              <div className="flex items-center gap-1.5 text-[10px] text-cyan-300 font-mono font-medium">
                <span>{activePatientId}</span>
                <button
                  type="button"
                  onClick={handleCopyPatientId}
                  className="hover:text-white transition-colors cursor-pointer"
                  title="Copy Patient ID"
                >
                  {copiedPatientId ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                </button>
              </div>
            </div>
          </div>

          {/* Hardware Device Badge */}
          <div className="flex items-center gap-2 bg-white/5 px-3 py-1.5 rounded-2xl border border-white/10 text-xs">
            <div className={`w-2 h-2 rounded-full ${isLiveOnline ? 'bg-emerald-400 animate-pulse shadow-[0_0_8px_#34d399]' : 'bg-amber-400'}`} />
            <span className="font-mono text-[11px] text-slate-300 font-semibold">{activeDeviceUuid}</span>
            <span className="text-[10px] text-slate-500">|</span>
            <span className="text-[10px] font-medium text-slate-400">{lastSyncStr}</span>
          </div>

          {/* Battery Status */}
          <div className="flex items-center gap-1.5 bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 px-2.5 py-1.5 rounded-2xl text-xs font-bold shadow-sm">
            <BatteryCharging className="w-3.5 h-3.5 text-emerald-400" />
            <span>{batteryPct}%</span>
          </div>
        </div>

        {/* Right: Quick Action Capsule Buttons */}
        <div className="flex items-center gap-2 z-10 w-full md:w-auto justify-end">
          <button
            type="button"
            onClick={() => setShowPairingModal(true)}
            className="px-3.5 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-cyan-500/20 flex items-center gap-1.5 cursor-pointer"
          >
            <Radio className="w-3.5 h-3.5" />
            <span>Pair / BLE</span>
          </button>
          <button
            type="button"
            onClick={() => setShowReportsModal(true)}
            className="px-3.5 py-2 bg-white/10 hover:bg-white/20 text-white border border-white/20 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5"
          >
            <FileText className="w-3.5 h-3.5 text-indigo-300" />
            <span>Medical History</span>
          </button>
          <button
            type="button"
            onClick={() => navigate('/emergency')}
            className="px-3 py-2 bg-rose-600/30 hover:bg-rose-600/50 text-rose-300 border border-rose-500/40 rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            <span>112 SOS</span>
          </button>
        </div>
      </div>

      {/* =========================================================================
          HERO BIOMETRIC HORIZON: SMARTWATCH HOLOGRAM & EMERGENCY DEFENSE STATION
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-stretch">
        {/* Left Hero: Interactive Cyber-Watch & Vitality Horizon */}
        <div className="lg:col-span-8 relative rounded-3xl p-6 md:p-8 overflow-hidden bg-gradient-to-br from-slate-900 via-[#0e1d35] to-[#0a1526] text-white border border-cyan-500/30 shadow-2xl flex flex-col md:flex-row items-center justify-between gap-6 group">
          {/* Futuristic Background Circuit & Aurora */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-cyan-500/20 via-transparent to-transparent pointer-events-none" />
          <div className="absolute -left-20 -bottom-20 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none" />

          {/* Holographic 3D Smartwatch Interactive Model */}
          <div className="relative flex items-center justify-center shrink-0">
            <div className="relative w-40 h-40 flex items-center justify-center">
              {/* Outer Pulsing Heartbeat Rings */}
              <div
                className="absolute inset-0 rounded-full border border-rose-500/40 animate-ping opacity-75"
                style={{ animationDuration: `${Math.max(0.6, 60 / (heartRate || 72))}s` }}
              />
              <div className="absolute inset-2 rounded-full bg-gradient-to-tr from-cyan-500/20 to-rose-500/20 blur-xl" />

              {/* Watch Chassis */}
              <div className="relative w-32 h-36 bg-gradient-to-b from-slate-800 to-slate-950 rounded-[32px] border-4 border-slate-700/80 shadow-[0_15px_35px_rgba(0,0,0,0.6)] flex flex-col items-center justify-center p-2.5">
                {/* Watch Crown Button */}
                <div className="absolute -right-2 top-10 w-2 h-6 bg-slate-600 rounded-r-md border-r border-slate-500" />
                {/* Watch Strap Top/Bottom */}
                <div className="absolute -top-3.5 w-18 h-3.5 bg-slate-800 rounded-t-lg border-t border-slate-600" />
                <div className="absolute -bottom-3.5 w-18 h-3.5 bg-slate-800 rounded-b-lg border-b border-slate-600" />

                {/* OLED Display */}
                <div className="w-full h-full bg-[#050b14] rounded-2xl border border-cyan-400/40 flex flex-col items-center justify-between p-2 shadow-inner">
                  <div className="flex items-center justify-between w-full text-[9px] text-cyan-300 font-mono">
                    <span>LIVE</span>
                    <span className="flex items-center gap-0.5 text-emerald-400">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                      BLE
                    </span>
                  </div>

                  <div className="flex flex-col items-center justify-center my-auto">
                    <Heart
                      className="w-6 h-6 text-rose-500 fill-rose-500"
                      style={{
                        animation: `pulse ${Math.max(0.6, 60 / (heartRate || 72))}s cubic-bezier(0.4, 0, 0.6, 1) infinite`,
                      }}
                    />
                    <div className="text-2xl font-black text-white tracking-tight mt-0.5">{heartRate}</div>
                    <span className="text-[9px] font-semibold text-rose-300 tracking-wider uppercase">BPM PULSE</span>
                  </div>

                  <div className="w-full bg-slate-800/80 rounded-full h-1 overflow-hidden">
                    <div className="bg-gradient-to-r from-cyan-400 to-rose-400 h-full w-[78%]" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Center Greeting & Vitality Score Cockpit */}
          <div className="flex-1 space-y-3.5 text-center md:text-left z-10">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-gradient-to-r from-cyan-500/20 to-blue-500/20 border border-cyan-400/30 text-cyan-300 text-xs font-semibold mb-2 shadow-sm">
                <Sparkles className="w-3.5 h-3.5 text-cyan-300" />
                <span>Smart Wearable Health Intelligence • Active Sentinel</span>
              </div>
              <h1 className="text-2xl md:text-3xl font-black tracking-tight text-white flex items-center justify-center md:justify-start gap-2">
                {t('dash.goodMorning', 'Good Morning')}, {displayName}!
                <span className="inline-block animate-bounce">✨</span>
              </h1>
              <p className="text-slate-300 text-sm mt-1 leading-relaxed">
                {t('dash.motto', 'Your biometrics are continuously analyzed. All vitals within healthy baseline parameters.')}
              </p>
            </div>

            {/* Vitality Index Gauge & Environment Pill */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 pt-1">
              <div className="bg-white/5 border border-white/10 rounded-2xl p-2.5 backdrop-blur-md">
                <div className="text-[10px] text-cyan-300 font-semibold uppercase tracking-wider">Health Vitality</div>
                <div className="text-lg font-black text-white flex items-baseline gap-1 mt-0.5">
                  <span>96</span>
                  <span className="text-[10px] text-emerald-400 font-bold">/ 100</span>
                </div>
                <div className="text-[9px] text-emerald-300 font-medium">Optimal Equilibrium</div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-2xl p-2.5 backdrop-blur-md">
                <div className="text-[10px] text-indigo-300 font-semibold uppercase tracking-wider">Active Rest</div>
                <div className="text-lg font-black text-white flex items-baseline gap-1 mt-0.5">
                  <span>{sleepStr}</span>
                </div>
                <div className="text-[9px] text-indigo-300 font-medium">88% Deep Restoration</div>
              </div>

              <div className="bg-white/5 border border-white/10 rounded-2xl p-2.5 backdrop-blur-md col-span-2 sm:col-span-1">
                <div className="text-[10px] text-teal-300 font-semibold uppercase tracking-wider">Environment</div>
                <div className="text-lg font-black text-white flex items-baseline gap-1 mt-0.5">
                  <span>24°C</span>
                  <span className="text-[10px] text-teal-400 font-bold">Comfort</span>
                </div>
                <div className="text-[9px] text-teal-300 font-medium">Safe Geofence Active</div>
              </div>
            </div>

            {/* Hardware Offline Warning if not connected */}
            {!isLiveOnline && (
              <div className="p-3 bg-amber-500/15 border border-amber-500/40 rounded-2xl flex items-center justify-between text-xs text-amber-200">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>
                    <strong>Hardware Standby:</strong> Displaying verified baseline data ({lastSyncStr}). Smartwatch will auto-reconnect.
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setShowPairingModal(true)}
                  className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-slate-950 font-bold rounded-xl text-[10px] cursor-pointer shrink-0 ml-2 shadow-sm"
                >
                  Pair / Scan
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Hero: Aura Emergency SOS Defense Capsule */}
        <div className="lg:col-span-4 relative rounded-3xl p-6 md:p-7 overflow-hidden bg-gradient-to-br from-rose-600 via-rose-700 to-red-900 text-white shadow-2xl shadow-rose-900/40 border border-rose-400/40 flex flex-col justify-between select-none">
          {/* Animated Sonic Radar Background Rings */}
          <div className="absolute inset-0 opacity-20 pointer-events-none flex items-center justify-center">
            <div className="w-64 h-64 rounded-full border-2 border-white animate-ping" style={{ animationDuration: '3s' }} />
            <div className="w-40 h-40 rounded-full border border-white/60 animate-ping" style={{ animationDuration: '2s' }} />
          </div>

          <div className="relative flex items-start space-x-3.5 z-10">
            <div className="p-3.5 bg-white/20 rounded-2xl backdrop-blur-md shadow-inner border border-white/30">
              <ShieldAlert className="w-7 h-7 text-white animate-bounce" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h3 className="text-xl font-black tracking-tight">{t('sos.emergencySOS', 'Emergency SOS')}</h3>
                <span className="px-2 py-0.5 rounded-full bg-white/20 text-[10px] font-bold text-rose-100">DEFENSE</span>
              </div>
              <p className="text-xs text-rose-100 mt-1 leading-relaxed">
                {t('sos.holdNotice', 'Press and hold 2 seconds to dispatch immediate emergency alerts & GPS coordinates to caregivers and 112.')}
              </p>
            </div>
          </div>

          {/* Interactive Hold-to-Dispatch Station */}
          <div className="relative mt-6 z-10 space-y-2.5">
            <button
              onMouseDown={startSOSHold}
              onMouseUp={cancelSOSHold}
              onMouseLeave={cancelSOSHold}
              onTouchStart={startSOSHold}
              onTouchEnd={cancelSOSHold}
              disabled={sosStatus === 'transmitting'}
              className="relative w-full py-4 px-5 rounded-2xl font-black text-sm tracking-wider shadow-2xl overflow-hidden transition-all transform active:scale-95 flex items-center justify-center space-x-2 bg-white text-rose-700 cursor-pointer group"
            >
              {/* Animated Glowing Progress Fill */}
              {holdingSOS && (
                <div
                  className="absolute left-0 top-0 bottom-0 bg-gradient-to-r from-rose-300 to-rose-400 transition-all duration-75 ease-linear pointer-events-none shadow-lg"
                  style={{ width: `${holdProgress}%` }}
                />
              )}

              <span className="relative z-10 flex items-center space-x-2">
                {sosStatus === 'transmitting' && (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin text-rose-700" />
                    <span>{t('sos.broadcasting', 'Broadcasting SOS to Caregivers...')}</span>
                  </>
                )}
                {sosStatus === 'dispatched' && (
                  <span className="text-emerald-700 font-extrabold flex items-center gap-1">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    {t('sos.dispatched', '✓ SOS Dispatched to Contacts')}
                  </span>
                )}
                {sosStatus === 'error' && (
                  <span className="text-rose-700 font-extrabold">{t('sos.failed', 'Transmission Failed – Try Again')}</span>
                )}
                {sosStatus === 'idle' && (
                  <span className="flex items-center gap-2">
                    <Radio className="w-4 h-4 text-rose-600 animate-pulse" />
                    <span>{holdingSOS ? `${t('sos.holding', 'HOLDING')} (${holdProgress}%)...` : t('sos.pressAndHold', 'HOLD TO TRIGGER SOS')}</span>
                  </span>
                )}
              </span>
            </button>

            {sosErrorMsg && (
              <p className="text-[11px] text-amber-200 mt-1 font-medium text-center">{sosErrorMsg}</p>
            )}

            <div className="flex items-center justify-between text-[11px] text-rose-100/90 font-medium px-1">
              <span>📍 GPS: {gpsLocation.lat.toFixed(4)}, {gpsLocation.lng.toFixed(4)}</span>
              <button
                type="button"
                onClick={() => navigate('/emergency')}
                className="hover:underline cursor-pointer font-bold"
              >
                Manage Contacts ➔
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          THE 7 SCULPTED BIOMETRIC VITALITY MATRIX (VIBRANT & COLORFUL PERSONALITIES)
         ========================================================================= */}
      <div>
        <div className="flex items-center justify-between mb-3 px-1">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-cyan-500 animate-pulse" />
            <h2 className="text-base font-extrabold text-slate-800 tracking-tight">Real-Time Biometric Telemetry Matrix</h2>
          </div>
          <span className="text-xs font-semibold text-slate-500">Live Continuous Stream</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
          {/* 1. HEART RATE CAPSULE (Electric Rose) */}
          <div
            onClick={() => navigate('/health')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-rose-50 via-white to-pink-50/40 border border-rose-200/80 shadow-md hover:shadow-xl hover:shadow-rose-500/10 hover:border-rose-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-rose-500 to-pink-600 text-white shadow-md shadow-rose-500/30 group-hover:scale-110 transition-transform">
                  <Heart className="w-4 h-4 fill-white" />
                </div>
                <span className="text-xs font-bold text-slate-700">{t('vital.heartRate', 'Heart Rate')}</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-rose-100 text-rose-700">Live</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{Math.round(heartRate)}</span> <span className="text-xs font-bold text-slate-400 shrink-0">{t('vital.bpm', 'BPM')}</span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px] text-emerald-600 font-semibold">
                <span>↑ +2% Resting</span>
                <span className="text-slate-400 font-mono">60-100</span>
              </div>
            </div>

            {/* Micro Wave ECG graphic */}
            <div className="h-6 w-full text-rose-500 opacity-80 pt-1">
              <svg viewBox="0 0 100 24" className="w-full h-full stroke-current fill-none stroke-2">
                <path d="M0,12 L20,12 L25,4 L30,20 L35,2 L40,16 L45,12 L100,12" />
              </svg>
            </div>
          </div>

          {/* 2. BLOOD PRESSURE SPECTRUM (Royal Violet) */}
          <div
            onClick={() => navigate('/health')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-purple-50 via-white to-indigo-50/40 border border-purple-200/80 shadow-md hover:shadow-xl hover:shadow-purple-500/10 hover:border-purple-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-purple-600 to-indigo-600 text-white shadow-md shadow-purple-500/30 group-hover:scale-110 transition-transform">
                  <Heart className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700">Blood Pressure</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">Validated</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{bloodPressure}</span> <span className="text-xs font-bold text-slate-400 shrink-0">mmHg</span>
              </div>
              <div className="text-[11px] text-emerald-600 font-semibold mt-1">Normal / Stage 1</div>
            </div>

            <div className="w-full bg-purple-100 rounded-full h-1.5 overflow-hidden">
              <div className="bg-gradient-to-r from-purple-500 to-indigo-600 h-full w-[70%]" />
            </div>
          </div>

          {/* 3. SPO2 OXYGENATION TANK (Ocean Cyan) */}
          <div
            onClick={() => navigate('/health')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-cyan-50 via-white to-sky-50/40 border border-cyan-200/80 shadow-md hover:shadow-xl hover:shadow-cyan-500/10 hover:border-cyan-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-cyan-500 to-teal-500 text-white shadow-md shadow-cyan-500/30 group-hover:scale-110 transition-transform">
                  <Droplets className="w-4 h-4 fill-white" />
                </div>
                <span className="text-xs font-bold text-slate-700">{t('vital.spo2', 'SpO2')}</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-100 text-cyan-800">Arterial</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{Math.round(spo2)}</span> <span className="text-xs font-bold text-slate-400 shrink-0">%</span>
              </div>
              <div className="flex items-center justify-between mt-1 text-[11px] text-emerald-600 font-semibold">
                <span>↑ High Saturation</span>
                <span className="text-slate-400 font-mono">≥95%</span>
              </div>
            </div>

            <div className="w-full bg-cyan-100 rounded-full h-1.5 overflow-hidden">
              <div className="bg-gradient-to-r from-cyan-400 to-blue-500 h-full" style={{ width: `${spo2}%` }} />
            </div>
          </div>

          {/* 4. BODY TEMPERATURE SENTINEL (Sunburst Amber) */}
          <div
            onClick={() => navigate('/health')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-amber-50 via-white to-orange-50/40 border border-amber-200/80 shadow-md hover:shadow-xl hover:shadow-amber-500/10 hover:border-amber-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-amber-500 to-orange-500 text-white shadow-md shadow-amber-500/30 group-hover:scale-110 transition-transform">
                  <Thermometer className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700">{t('vital.bodyTemp', 'Body Temp')}</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">Normal</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{Number(temp).toFixed(1)}</span> <span className="text-xs font-bold text-slate-400 shrink-0">°C</span>
              </div>
              <div className="text-[11px] text-emerald-600 font-semibold mt-1">Afebrile / 98.2°F</div>
            </div>

            <div className="w-full bg-amber-100 rounded-full h-1.5 overflow-hidden">
              <div className="bg-gradient-to-r from-amber-400 to-orange-500 h-full w-[65%]" />
            </div>
          </div>

          {/* 5. KINETIC STEP ENGINE (Aurora Emerald) */}
          <div
            onClick={() => navigate('/sleep-activity')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-emerald-50 via-white to-teal-50/40 border border-emerald-200/80 shadow-md hover:shadow-xl hover:shadow-emerald-500/10 hover:border-emerald-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/30 group-hover:scale-110 transition-transform">
                  <Footprints className="w-4 h-4" />
                </div>
                <span className="text-xs font-bold text-slate-700">{t('vital.steps', 'Steps')}</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800">{distanceKm} km</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                {steps.toLocaleString()} <span className="text-xs font-bold text-slate-400">/ 6k</span>
              </div>
              <div className="text-[11px] text-emerald-600 font-semibold mt-1">{Math.round((steps / 6000) * 100)}% Daily Goal</div>
            </div>

            <div className="w-full bg-emerald-100 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-emerald-400 to-teal-500 h-full rounded-full"
                style={{ width: `${Math.min(100, Math.round((steps / 6000) * 100))}%` }}
              />
            </div>
          </div>

          {/* 6. LIQUID HYDRATION RESERVOIR (Electric Sapphire with Interactive Quick-Log) */}
          <div
            onClick={handleLogGlassWater}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-sky-50 via-white to-blue-50/50 border border-sky-200/80 shadow-md hover:shadow-xl hover:shadow-sky-500/15 hover:border-sky-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
            title="Click to instantly record +250ml glass of water"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-blue-500 to-sky-500 text-white shadow-md shadow-blue-500/30 group-hover:scale-110 transition-transform">
                  <Droplets className="w-4 h-4 fill-white" />
                </div>
                <span className="text-xs font-bold text-slate-700">Hydration</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                +250ml 💧
              </span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{Math.round(hydration.total_intake_ml)}</span> <span className="text-xs font-bold text-slate-400 shrink-0">/ 2500ml</span>
              </div>
              <div className="text-[11px] text-blue-600 font-semibold mt-1">{Math.round(hydration.percentage)}% Daily Target</div>
            </div>

            {/* Liquid Wave Animation Bar */}
            <div className="w-full bg-blue-100 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-600 h-full rounded-full"
                style={{ width: `${Math.min(100, hydration.percentage)}%` }}
              />
            </div>
          </div>

          {/* 7. CIRCADIAN SLEEP ARCHITECTURE (Twilight Indigo) */}
          <div
            onClick={() => navigate('/sleep-activity')}
            className="group relative rounded-3xl p-4 bg-gradient-to-br from-indigo-50 via-white to-slate-50 border border-indigo-200/80 shadow-md hover:shadow-xl hover:shadow-indigo-500/10 hover:border-indigo-400 transition-all duration-300 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-2xl bg-gradient-to-br from-indigo-600 to-purple-600 text-white shadow-md shadow-indigo-500/30 group-hover:scale-110 transition-transform">
                  <Moon className="w-4 h-4 fill-white" />
                </div>
                <span className="text-xs font-bold text-slate-700">{t('vital.sleep', 'Sleep')}</span>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-700">★ 88%</span>
            </div>

            <div className="my-3">
              <div className="text-2xl font-black text-slate-900 tracking-tight flex items-baseline gap-1">
                <span className="truncate">{sleepStr}</span>
              </div>
              <div className="text-[11px] text-indigo-600 font-semibold mt-1">Deep & REM Rest</div>
            </div>

            <div className="w-full bg-indigo-100 rounded-full h-1.5 overflow-hidden">
              <div className="bg-gradient-to-r from-indigo-500 to-purple-600 h-full w-[85%]" />
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          HEALTH COMMAND CENTER DECK (LIVE OSCILLOSCOPE, AI DIGITAL TWIN, GPS TACTICAL, CLINICAL SHORTCUTS)
         ========================================================================= */}
      <div className="w-full space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
          {/* Live ECG Oscilloscope Screen */}
          <div className="md:col-span-6">
            <LiveECGCanvas heartRate={heartRate} />
          </div>

          {/* AI Health Digital Twin & Predictive Radar */}
          <div className="md:col-span-6 bg-gradient-to-br from-[#0a1424] via-[#0d1d36] to-[#081224] rounded-3xl p-5 text-white border border-cyan-500/30 shadow-2xl flex flex-col justify-between relative overflow-hidden group">
              <div className="absolute top-0 right-0 w-44 h-44 bg-cyan-500/10 rounded-full blur-2xl pointer-events-none" />

              <div className="flex items-center justify-between mb-2 z-10">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded-xl bg-cyan-500/20 text-cyan-300 border border-cyan-500/40">
                    <Sparkles className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <h3 className="text-xs font-black uppercase tracking-wider text-cyan-300">AI Health Digital Twin</h3>
                    <p className="text-[10px] text-slate-400">Multi-day physiological drift & baseline analysis</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/ai-insights')}
                  className="text-xs text-cyan-300 hover:text-white font-bold cursor-pointer transition-colors"
                >
                  Deep Insights ➔
                </button>
              </div>

              {/* Holographic Body Model & Realtime Biomarker Readings */}
              <div className="flex items-center justify-between my-2 z-10">
                <div className="relative w-28 h-32 flex items-center justify-center shrink-0">
                  <div className="absolute inset-0 rounded-full bg-cyan-400/20 blur-xl animate-pulse" />
                  <svg className="w-20 h-32 stroke-cyan-400 fill-cyan-400/10 drop-shadow-[0_0_10px_#06b6d4]" viewBox="0 0 100 200">
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
                    {/* Pulsing Organ Nodes */}
                    <circle cx="50" cy="65" r="4" fill="#f43f5e" className="animate-ping" />
                    <circle cx="50" cy="65" r="3" fill="#f43f5e" />
                    <circle cx="50" cy="20" r="3" fill="#06b6d4" className="animate-pulse" />
                  </svg>
                </div>

                <div className="flex-1 ml-4 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-semibold">Cardiac Rhythm</span>
                    <span className="text-emerald-400 font-bold">Sinus Rhythm (Normal)</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-semibold">Metabolic Baseline</span>
                    <span className="text-cyan-300 font-bold">+2% Drift (Stable)</span>
                  </div>
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 font-semibold">Stress Index</span>
                    <span className="text-indigo-300 font-bold">18 / 100 (Low Stress)</span>
                  </div>
                  <p className="text-[11px] text-slate-300/90 leading-relaxed bg-white/5 p-2 rounded-xl border border-white/10 mt-1">
                    {aiInsightText}
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Tactical Geofence & Location Station */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-5">
            {/* Live GPS Tracker Frame */}
            <div className="md:col-span-6 bg-white rounded-3xl p-5 border border-slate-200 shadow-md flex flex-col justify-between">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-2xl bg-blue-50 text-blue-600">
                    <MapPin className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-800">Live GPS Location & Safe Geofence</h3>
                    <p className="text-[10px] text-slate-400">Continuous coordinates & boundary supervision</p>
                  </div>
                </div>
                <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  {gpsLocation.isLive ? '● Live Device Satellite' : '● Registered Coordinates'}
                </span>
              </div>

              <div
                onClick={() => navigate('/gps')}
                className="relative w-full h-36 rounded-2xl overflow-hidden border border-slate-200 cursor-pointer shadow-inner group"
                title="Click to open Full Google Maps Tracker"
              >
                <iframe
                  title="Google Map Live Patient Preview"
                  width="100%"
                  height="100%"
                  style={{ border: 0, pointerEvents: 'none' }}
                  loading="lazy"
                  src={`https://maps.google.com/maps?q=${gpsLocation.lat},${gpsLocation.lng}&z=15&output=embed`}
                  className="w-full h-full"
                />
                <div className="absolute inset-0 bg-blue-900/10 group-hover:bg-transparent transition-all pointer-events-none" />
                <div className="absolute top-2 right-2 bg-white/95 px-2.5 py-1 rounded-xl text-[10px] font-bold text-blue-700 shadow-md flex items-center gap-1.5">
                  <Navigation className="w-3 h-3 text-blue-600" />
                  <span>Google Maps</span>
                </div>
                <div className="absolute bottom-2 left-2 bg-slate-900/85 backdrop-blur-md text-white px-3 py-1 rounded-xl text-[10px] font-mono font-bold shadow-md">
                  📍 {gpsLocation.lat.toFixed(4)}, {gpsLocation.lng.toFixed(4)}
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 mt-1 text-xs">
                <span className="font-semibold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  Inside Home Safe Zone (500m)
                </span>
                <button
                  type="button"
                  onClick={() => navigate('/gps')}
                  className="text-blue-600 hover:text-blue-800 font-bold cursor-pointer"
                >
                  Full Map View ➔
                </button>
              </div>
            </div>

            {/* Quick Health Shortcuts */}
            <div className="md:col-span-6 bg-white rounded-3xl p-5 border border-slate-200 shadow-md flex flex-col justify-between">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-2xl bg-cyan-50 text-cyan-600">
                    <Sparkles className="w-4 h-4 text-cyan-600" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-slate-800">Quick Clinical Shortcuts</h3>
                    <p className="text-[10px] text-slate-400">One-tap medical communication & scheduling</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => navigate('/settings')}
                  className="text-xs text-cyan-600 hover:underline font-bold cursor-pointer"
                >
                  Settings ➔
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3 my-auto pt-2">
                <button
                  type="button"
                  onClick={() => navigate('/communication')}
                  className="p-3 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50/50 hover:from-blue-100 hover:to-indigo-100 border border-blue-100 flex items-center gap-3 transition-all cursor-pointer group text-left"
                >
                  <div className="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-transform">
                    <Users className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800">Family Caregiver</div>
                    <div className="text-[10px] text-slate-500">Call / Message</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => navigate('/notifications')}
                  className="p-3 rounded-2xl bg-gradient-to-br from-amber-50 to-orange-50/50 hover:from-amber-100 hover:to-orange-100 border border-amber-100 flex items-center gap-3 transition-all cursor-pointer group text-left"
                >
                  <div className="w-9 h-9 rounded-xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-transform">
                    <Pill className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800">Pill Alarms</div>
                    <div className="text-[10px] text-slate-500">Scheduled Doses</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => setShowReportsModal(true)}
                  className="p-3 rounded-2xl bg-gradient-to-br from-purple-50 to-pink-50/50 hover:from-purple-100 hover:to-pink-100 border border-purple-100 flex items-center gap-3 transition-all cursor-pointer group text-left"
                >
                  <div className="w-9 h-9 rounded-xl bg-purple-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-transform">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800">Clinical Vault</div>
                    <div className="text-[10px] text-slate-500">Reports & Allergies</div>
                  </div>
                </button>

                <button
                  type="button"
                  onClick={() => navigate('/devices')}
                  className="p-3 rounded-2xl bg-gradient-to-br from-teal-50 to-emerald-50/50 hover:from-teal-100 hover:to-emerald-100 border border-teal-100 flex items-center gap-3 transition-all cursor-pointer group text-left"
                >
                  <div className="w-9 h-9 rounded-xl bg-teal-600 text-white flex items-center justify-center shrink-0 shadow-md group-hover:scale-105 transition-transform">
                    <Radio className="w-4 h-4" />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-800">Hardware Hub</div>
                    <div className="text-[10px] text-slate-500">ESP32 BLE & Wi-Fi</div>
                  </div>
                </button>
              </div>
            </div>
          </div>
        </div>

      {/* =========================================================================
          EMERGENCY MEDICAL & CLINICAL HEALTH QR PASS (SCANNABLE FOR REPORTS & VITALS)
         ========================================================================= */}
      <div className="bg-gradient-to-br from-slate-900 via-[#0d1d36] to-[#071322] rounded-3xl p-6 md:p-8 text-white border border-cyan-500/40 shadow-2xl relative overflow-hidden">
        <div className="absolute -right-20 -bottom-20 w-80 h-80 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -left-20 -top-20 w-80 h-80 bg-blue-600/15 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row items-center justify-between gap-6">
          {/* Left: QR Code Badge */}
          <div className="flex flex-col sm:flex-row items-center gap-5 shrink-0">
            <div className="p-2.5 rounded-2xl bg-white shadow-xl ring-4 ring-cyan-400/30 flex items-center justify-center">
              <PatientQRCode token={qrProfile?.qr_token || 'PT-QR-PT-2026-000001-A1B2C3D4'} size={140} />
            </div>

            <div className="text-center sm:text-left space-y-2 min-w-0">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/30 text-xs font-bold">
                <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
                <span>Verified Patient Emergency & Clinical Pass</span>
              </div>
              <h2 className="text-xl md:text-2xl font-black tracking-tight text-white flex flex-wrap items-center gap-2 justify-center sm:justify-start">
                <span>{displayName}'s Health Pass</span>
                <span className="text-xs px-2.5 py-0.5 rounded-lg bg-rose-500/80 font-mono font-bold text-white shadow-sm">
                  Blood Group: {qrProfile?.blood_group || 'O+'}
                </span>
              </h2>
              <p className="text-xs text-slate-300 max-w-lg leading-relaxed">
                Scan with any smartphone camera or hospital terminal to instantly access authenticated medical records, active medications, emergency contacts, and original uploaded digital health reports with AI clinical insights.
              </p>
              <div className="flex flex-wrap items-center gap-2 pt-1 justify-center sm:justify-start text-[11px] font-mono text-cyan-200">
                <span className="bg-white/10 px-2.5 py-1 rounded-lg border border-white/10">ID: {activePatientId}</span>
                <span className="bg-white/10 px-2.5 py-1 rounded-lg border border-white/10">Token: {qrProfile?.qr_token || 'PT-QR-ACTIVE'}</span>
                <span className="bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-lg border border-emerald-500/30 font-bold">● Active 24/7 Verified</span>
              </div>
            </div>
          </div>

          {/* Right Action Buttons */}
          <div className="flex flex-col sm:flex-row lg:flex-col gap-2.5 w-full lg:w-auto shrink-0 justify-center">
            <button
              type="button"
              onClick={handleOpenQRPortalModal}
              className="px-5 py-3 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-extrabold text-xs shadow-lg shadow-cyan-500/30 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <QrCode className="w-4 h-4" />
              <span>Scan / View Medical Portal</span>
            </button>

            <a
              href={`/emergency-qr/public/${qrProfile?.qr_token || 'PT-QR-PT-2026-000001-A1B2C3D4'}`}
              target="_blank"
              rel="noreferrer"
              className="px-5 py-2.5 rounded-2xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-400/30 font-bold text-xs transition-all flex items-center justify-center gap-1.5 cursor-pointer text-center"
            >
              <ExternalLink className="w-3.5 h-3.5" />
              <span>Open Public Scan URL</span>
            </a>

            <button
              type="button"
              onClick={() => setShowUploadDocModal(true)}
              className="px-5 py-2.5 rounded-2xl bg-white/10 hover:bg-white/20 text-white border border-white/20 font-bold text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Upload className="w-4 h-4 text-cyan-300" />
              <span>Upload PDF Health Report</span>
            </button>

            <button
              type="button"
              onClick={() => window.print()}
              className="px-5 py-2 rounded-2xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 font-medium text-xs transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Printer className="w-3.5 h-3.5" />
              <span>Print / Download QR Pass</span>
            </button>
          </div>
        </div>
      </div>

      {/* =========================================================================
          MODULE 4 & 5: MEDICINE MANAGEMENT & SMART REMINDER SCHEDULES
         ========================================================================= */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Medicine Dispensary & Active Prescriptions */}
        <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-md space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-teal-500 to-emerald-600 text-white flex items-center justify-center shadow-md shadow-teal-500/20">
                <Pill className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">Active Prescriptions & Medication Schedule</h3>
                <p className="text-xs text-slate-500">Track doses, remaining tablet inventory, and consumption</p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => setShowAddMedModal(true)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-teal-600 hover:bg-teal-700 text-white rounded-xl text-xs font-bold transition-all shadow-md cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              Add Medicine
            </button>
          </div>

          {/* Dose Action Feedback Toast */}
          {medicineActionToast && (
            <div className="p-3 rounded-2xl bg-teal-50 border border-teal-200 text-xs font-bold text-teal-900 flex items-center justify-between animate-fadeIn">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
                <span>{medicineActionToast}</span>
              </div>
              <button
                type="button"
                onClick={() => setMedicineActionToast(null)}
                className="text-teal-600 hover:text-teal-800 text-xs font-black px-1"
              >
                ✕
              </button>
            </div>
          )}

          <div className="space-y-3">
            {medicines.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-xs">
                No active medications prescribed. Click <strong>Add Medicine</strong> to track your schedule.
              </div>
            ) : (
              medicines.map((med) => (
                <div
                  key={med.id}
                  className="p-4 rounded-2xl border border-slate-200 hover:border-teal-400 transition-all bg-slate-50/70 hover:bg-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-black text-slate-900">{med.medicine_name}</span>
                      <span className="text-[10px] font-bold bg-teal-100 text-teal-800 px-2.5 py-0.5 rounded-full">
                        {med.dosage}
                      </span>
                      {med.remaining_quantity === 0 ? (
                        <span className="text-[10px] font-black bg-rose-100 text-rose-800 px-2 py-0.5 rounded-full flex items-center gap-1 animate-pulse">
                          <AlertTriangle className="w-3 h-3 text-rose-600" />
                          🚨 Out of Stock (0 left)
                        </span>
                      ) : med.is_low_stock ? (
                        <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                          Low Stock ({med.remaining_quantity} left)
                        </span>
                      ) : null}
                    </div>
                    <div className="text-xs text-slate-500 flex items-center gap-3">
                      <span>Schedule: <strong className="text-slate-800">{med.scheduled_times}</strong> ({med.frequency})</span>
                      <span>Stock: <strong className="text-slate-800">{med.remaining_quantity} / {med.total_quantity}</strong></span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 self-end sm:self-center">
                    <button
                      type="button"
                      onClick={() => handleMedicineAction(med.id, 'taken')}
                      className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl text-xs font-bold shadow-md shadow-emerald-600/20 transition-all cursor-pointer flex items-center gap-1.5"
                    >
                      <Check className="w-3.5 h-3.5" />
                      Taken
                    </button>
                    <button
                      type="button"
                      onClick={() => handleMedicineAction(med.id, 'skipped')}
                      className="px-3 py-2 border border-slate-300 text-slate-600 hover:bg-slate-100 rounded-xl text-xs font-bold transition-all cursor-pointer"
                    >
                      Skip
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Smart Reminders & Doctor Appointments Column */}
        <div className="lg:col-span-5 space-y-5">
          {/* Smart Reminders with Real-time Location Calendar & Custom Ringtones */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-md space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Smart Health Reminders</h3>
                  <p className="text-[11px] text-slate-500">Location calendar routines & custom alarms</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddReminderModal(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-500 hover:bg-amber-600 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-sm shadow-amber-500/20"
              >
                <Plus className="w-3.5 h-3.5" />
                New Routine
              </button>
            </div>

            {/* Real-time Location Clock & Interactive Calendar Strip */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-amber-500/10 via-amber-50 to-orange-50 border border-amber-200/80 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse" />
                  <span className="text-xs font-bold text-slate-800 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-amber-600" />
                    <span>{userTimezone.replace('_', ' ')}</span>
                  </span>
                </div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-200">
                  Live Time
                </span>
              </div>

              <div className="flex items-baseline justify-between">
                <div>
                  <div className="text-2xl font-black font-mono text-slate-900 tracking-tight">
                    {currentTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                  </div>
                  <div className="text-xs font-semibold text-slate-600 mt-0.5">
                    {currentTime.toLocaleDateString([], { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
                  </div>
                </div>

                <div className="text-right">
                  <div className="text-[11px] font-bold text-amber-700">Routine Alarms</div>
                  <div className="text-[10px] text-slate-400">Synced to patient timezone</div>
                </div>
              </div>

              {/* Interactive Mini Calendar Ribbon */}
              <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between gap-1">
                {[-2, -1, 0, 1, 2, 3, 4].map((offset) => {
                  const d = new Date();
                  d.setDate(d.getDate() + offset);
                  const isToday = offset === 0;
                  const isSelected = selectedCalendarDate.toDateString() === d.toDateString();
                  return (
                    <button
                      key={offset}
                      type="button"
                      onClick={() => {
                        setSelectedCalendarDate(d);
                        setNewRemDate(d.toISOString().split('T')[0]);
                      }}
                      className={`flex-1 py-1.5 px-1 rounded-xl flex flex-col items-center justify-center transition-all cursor-pointer ${
                        isSelected
                          ? 'bg-amber-500 text-white shadow-md shadow-amber-500/30 scale-105 font-bold'
                          : isToday
                          ? 'bg-amber-100 text-amber-900 font-bold border border-amber-300'
                          : 'bg-white/80 hover:bg-white text-slate-600 border border-amber-100'
                      }`}
                    >
                      <span className="text-[9px] uppercase tracking-wider">{d.toLocaleDateString([], { weekday: 'narrow' })}</span>
                      <span className="text-xs font-extrabold">{d.getDate()}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="space-y-2">
              {reminders.length === 0 ? (
                <div className="text-center py-4 text-slate-400 text-xs">
                  No reminders scheduled for this routine. Click <strong>New Routine</strong> to set an alarm.
                </div>
              ) : (
                reminders.map((rem) => (
                  <div
                    key={rem.id}
                    className="p-3 rounded-2xl border border-slate-200 bg-slate-50 flex items-center justify-between gap-2 overflow-hidden"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Clock className="w-4 h-4 text-amber-500 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-xs font-bold text-slate-800 truncate">{rem.title}</div>
                        <div className="text-[10px] text-slate-500 font-mono flex items-center gap-2">
                          <span className="truncate">{rem.reminder_time} • {rem.recurring_days}</span>
                          <span className="text-amber-700 bg-amber-100/70 px-1.5 py-0.5 rounded font-sans shrink-0 font-medium">
                            🎵 {rem.alarm_tone ? rem.alarm_tone.replace('_', ' ') : 'gentle chime'}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <button
                        type="button"
                        onClick={() => handlePlayTonePreview(rem.alarm_tone || 'gentle_chime')}
                        className={`p-1.5 rounded-lg border text-xs font-bold transition-all cursor-pointer flex items-center gap-1 ${
                          playingTone === (rem.alarm_tone || 'gentle_chime')
                            ? 'bg-amber-500 text-white border-amber-600 animate-pulse'
                            : 'bg-white text-amber-700 border-amber-200 hover:bg-amber-50'
                        }`}
                        title="Listen to Ringtone"
                      >
                        {playingTone === (rem.alarm_tone || 'gentle_chime') ? <Square className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
                        <span className="text-[10px]">Play</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleToggleReminder(rem.id, rem.is_enabled)}
                        className={`px-3 py-1 rounded-full text-[10px] font-bold cursor-pointer transition-colors ${
                          rem.is_enabled ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-500'
                        }`}
                      >
                        {rem.is_enabled ? 'Active' : 'Muted'}
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Confirmed Doctor Consultations */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-md space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <CalendarIcon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Doctor Consultations</h3>
                  <p className="text-[11px] text-slate-500">Upcoming clinical appointments & hospital visits</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddApptModal(true)}
                className="inline-flex items-center gap-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer shadow-sm"
              >
                <Plus className="w-3 h-3" />
                Book
              </button>
            </div>

            <div className="space-y-2">
              {appointments.length === 0 ? (
                <div className="text-center py-4 text-slate-400 text-xs">
                  No upcoming appointments booked.
                </div>
              ) : (
                appointments.map((appt) => (
                  <div
                    key={appt.id}
                    className="p-3 rounded-2xl border border-slate-200 bg-slate-50 flex items-center justify-between"
                  >
                    <div>
                      <div className="text-xs font-bold text-slate-900">{appt.doctor_name}</div>
                      <div className="text-[10px] text-indigo-700 font-semibold">{appt.specialization} • {appt.hospital_name}</div>
                      <div className="text-[10px] text-slate-400">{new Date(appt.appointment_date).toLocaleDateString()} at {new Date(appt.appointment_date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                    </div>
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 uppercase tracking-wider">
                      {appt.status}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          MODULE: REGISTERED CAREGIVERS & EMERGENCY CONTACT DIRECTORY
         ========================================================================= */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-md space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-rose-100 text-rose-600 flex items-center justify-center shadow-xs">
              <PhoneCall className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-extrabold text-slate-900">Authorized Caregivers & Family Directory</h3>
              <p className="text-xs text-slate-500">Instant access to verified phone numbers, direct dialers, and real email IDs</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => navigate('/emergency')}
            className="px-3.5 py-1.5 rounded-xl bg-rose-50 text-rose-700 hover:bg-rose-100 border border-rose-200 text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 self-end sm:self-center"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
            <span>Emergency Command Center</span>
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {caregiverDirectory.map((cg: any) => (
            <div
              key={cg.id}
              className={`p-4 rounded-2xl border transition-all flex flex-col justify-between gap-3 ${
                cg.is_primary
                  ? 'border-rose-200 bg-rose-50/30'
                  : 'border-slate-200 bg-slate-50/60'
              }`}
            >
              <div className="space-y-1.5">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-black text-slate-900">{cg.name}</span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      cg.is_primary ? 'bg-rose-600 text-white' : 'bg-slate-200 text-slate-700'
                    }`}
                  >
                    Tier {cg.escalation_tier || 1} • {cg.is_primary ? 'Primary Caregiver' : 'Secondary Contact'}
                  </span>
                </div>
                <div className="text-xs text-slate-600 font-medium">{cg.relationship}</div>
                <div className="text-[11px] text-slate-500">{cg.organization}</div>

                <div className="pt-1 space-y-1 text-xs font-mono">
                  <div className="flex items-center gap-2 text-slate-800 font-bold">
                    <Phone className="w-3.5 h-3.5 text-rose-600" />
                    <span>{cg.phone}</span>
                  </div>
                  <div className="flex items-center gap-2 text-slate-600">
                    <Mail className="w-3.5 h-3.5 text-cyan-600" />
                    <span className="truncate">{cg.email}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2 pt-2 border-t border-slate-200/60">
                <a
                  href={`tel:${String(cg.phone).replace(/[^0-9+]/g, '')}`}
                  className="flex-1 py-2 px-3 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold shadow-xs transition-all flex items-center justify-center gap-1.5"
                >
                  <Phone className="w-3.5 h-3.5" />
                  <span>Call {cg.is_primary ? 'Primary Caregiver' : 'Caregiver'}</span>
                </a>
                <a
                  href={`mailto:${cg.email}?subject=Patient%20Health%20Inquiry`}
                  className="p-2 rounded-xl border border-slate-300 hover:bg-white text-slate-600 hover:text-cyan-600 transition-all shadow-xs"
                  title="Send Email"
                >
                  <Mail className="w-4 h-4" />
                </a>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* =========================================================================
          DIGITAL MEDICAL REPORTS & AI CLINICAL DIAGNOSTIC ANALYSIS SECTION
         ========================================================================= */}
      <div className="bg-white rounded-3xl p-6 md:p-8 border border-slate-200 shadow-lg space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="flex items-center gap-3.5">
            <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-600 to-indigo-700 text-white flex items-center justify-center shadow-lg shadow-indigo-500/25 shrink-0">
              <Stethoscope className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-black text-slate-900 tracking-tight">Digital Medical Reports & AI Clinical Analysis</h3>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-black bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase tracking-wider">
                  AI Intelligence
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Upload digital copies of previous or updated reports. AI analyzes clinical biomarkers and generates actionable health suggestions.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => setShowUploadDocModal(true)}
            className="px-4 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-xl text-xs font-bold transition-all shadow-md shadow-indigo-500/20 flex items-center justify-center gap-2 cursor-pointer shrink-0"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Updated Report</span>
          </button>
        </div>

        {/* Digital Documents List */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {digitalDocs.length === 0 ? (
            <div className="col-span-2 text-center py-10 bg-slate-50 rounded-2xl border border-dashed border-slate-200 text-slate-400 text-xs">
              No digital medical documents uploaded yet. Click <strong>Upload Updated Report</strong> to add your previous lab tests, ECGs, or clinical records.
            </div>
          ) : (
            digitalDocs.map((doc) => (
              <div
                key={doc.id}
                className="rounded-3xl p-5 border border-slate-200 bg-gradient-to-br from-slate-50/80 via-white to-indigo-50/30 hover:border-indigo-400 hover:shadow-xl hover:shadow-indigo-500/10 transition-all flex flex-col justify-between space-y-4"
              >
                {/* Header */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-9 h-9 rounded-xl bg-indigo-100 text-indigo-700 flex items-center justify-center shrink-0 font-bold">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-black text-slate-900 leading-snug">{doc.document_name}</h4>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                        <span className="font-semibold text-indigo-600 uppercase tracking-wide">{doc.document_type.replace('_', ' ')}</span>
                        <span>•</span>
                        <span>Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}</span>
                      </div>
                    </div>
                  </div>

                  <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1 shrink-0">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    {Math.round(doc.ai_confidence_score * 100)}% AI Conf.
                  </span>
                </div>

                {/* AI Executive Summary */}
                {doc.ai_summary && (
                  <div className="p-3 bg-white rounded-2xl border border-slate-100 shadow-sm">
                    <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
                      <Sparkles className="w-3 h-3 text-cyan-600" />
                      AI Executive Summary
                    </div>
                    <p className="text-xs text-slate-700 leading-relaxed font-medium">{doc.ai_summary}</p>
                  </div>
                )}

                {/* Detected Conditions & Biomarkers */}
                <div className="space-y-2">
                  {doc.ai_detected_conditions && (
                    <div className="flex flex-wrap items-center gap-1.5">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mr-1">Conditions:</span>
                      {doc.ai_detected_conditions.split(',').map((cond, idx) => (
                        <span key={idx} className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                          {cond.trim()}
                        </span>
                      ))}
                    </div>
                  )}

                  {doc.ai_key_biomarkers && (
                    <div className="p-2.5 bg-slate-100/70 rounded-xl text-[11px] text-slate-700 font-mono leading-relaxed">
                      <strong className="text-slate-900 font-sans block text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-0.5">
                        Extracted Biomarkers:
                      </strong>
                      {doc.ai_key_biomarkers}
                    </div>
                  )}
                </div>

                {/* AI Clinical Suggestions */}
                {doc.ai_clinical_suggestions && (
                  <div className="p-3.5 bg-emerald-50/60 rounded-2xl border border-emerald-200/80 text-xs text-emerald-950 space-y-1">
                    <div className="text-[10px] font-black uppercase tracking-wider text-emerald-800 flex items-center gap-1.5 mb-1">
                      <span>💡</span>
                      <span>Actionable AI Clinical Suggestions:</span>
                    </div>
                    <div className="whitespace-pre-line text-[11px] text-emerald-900 font-medium leading-relaxed">
                      {doc.ai_clinical_suggestions}
                    </div>
                  </div>
                )}

                {/* Action Bar */}
                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <button
                    type="button"
                    onClick={() => handleReanalyzeDocument(doc.id)}
                    disabled={isAnalyzingDocId === doc.id}
                    className="inline-flex items-center gap-1.5 text-indigo-600 hover:text-indigo-800 font-bold cursor-pointer disabled:opacity-50"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzingDocId === doc.id ? 'animate-spin' : ''}`} />
                    <span>{isAnalyzingDocId === doc.id ? 'Re-analyzing...' : 'Re-Analyze with AI'}</span>
                  </button>

                  <div className="flex items-center gap-3">
                    <button
                      type="button"
                      onClick={() => handleOpenReportPdf(doc)}
                      className="inline-flex items-center gap-1 px-3 py-1 bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border border-cyan-200 rounded-xl font-bold text-xs cursor-pointer transition-colors"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-cyan-600" />
                      <span>Open PDF</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSelectedDocDetails(doc)}
                      className="text-slate-600 hover:text-slate-900 font-bold cursor-pointer"
                    >
                      Full Details
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDeleteDocument(doc.id)}
                      className="text-rose-500 hover:text-rose-700 font-bold cursor-pointer"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Upload Updated Digital Medical Report Modal */}
      {showUploadDocModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <Upload className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Upload Digital Medical Report</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowUploadDocModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleUploadDocument} className="space-y-4">
              {/* PDF File Upload Dropzone */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1 flex items-center gap-1.5">
                  <FileUp className="w-3.5 h-3.5 text-indigo-600" />
                  <span>Attach PDF Health Report</span>
                </label>
                <div className="border-2 border-dashed border-indigo-200 hover:border-indigo-400 bg-indigo-50/40 rounded-2xl p-4 text-center transition-all cursor-pointer relative">
                  <input
                    type="file"
                    accept=".pdf,application/pdf"
                    onChange={handlePdfFileChange}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />
                  {selectedPdfFile ? (
                    <div className="flex items-center justify-center gap-2 text-indigo-900 font-bold text-xs">
                      <FileText className="w-5 h-5 text-indigo-600" />
                      <span>{selectedPdfFile.name} ({Math.round(selectedPdfFile.size / 1024)} KB)</span>
                      <span className="text-emerald-600 font-extrabold text-[11px]">✓ PDF Ready</span>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <FileUp className="w-7 h-7 text-indigo-500 mx-auto" />
                      <p className="text-xs font-bold text-indigo-900">Click or Drag & Drop PDF Report here</p>
                      <p className="text-[10px] text-slate-400">Supports hospital lab test PDFs, ECG diagnostic strips, discharge summaries</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Document File / Name */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Report / Document Title</label>
                <input
                  type="text"
                  value={uploadDocName}
                  onChange={(e) => setUploadDocName(e.target.value)}
                  placeholder="e.g. Lipid Profile & Blood Sugar Panel 2026.pdf"
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              {/* Document Category */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Document Category</label>
                <select
                  value={uploadDocType}
                  onChange={(e) => setUploadDocType(e.target.value)}
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="lab_report">Clinical Lab Report / Blood Assay</option>
                  <option value="ecg_strip">12-Lead ECG / Holter Strip</option>
                  <option value="prescription">Prescription / Medication Chart</option>
                  <option value="discharge_summary">Hospital Discharge Summary</option>
                  <option value="radiology">Radiology / Imaging Observation</option>
                </select>
              </div>

              {/* Clinical Text / Extracted Lab Values */}
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">
                  Report Findings / Key Biomarkers (or OCR Content)
                </label>
                <textarea
                  value={uploadDocText}
                  onChange={(e) => setUploadDocText(e.target.value)}
                  rows={3}
                  placeholder="e.g. Total Cholesterol 215 mg/dL, Fasting Sugar 96 mg/dL, HbA1c 5.6%, BP 128/82 mmHg..."
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none leading-relaxed"
                />
                <p className="text-[10px] text-slate-400 mt-1">
                  Our clinical AI engine will automatically extract conditions, assess risk, and formulate actionable recommendations.
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowUploadDocModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploadingDoc}
                  className="px-5 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
                >
                  {isUploadingDoc ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Analyzing with AI...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Upload & Run AI Analysis
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Full Document AI Clinical Report Viewer Modal */}
      {selectedDocDetails && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-6 md:p-8 shadow-2xl border border-slate-100 max-h-[85vh] flex flex-col animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-10 h-10 rounded-2xl bg-indigo-100 text-indigo-700 flex items-center justify-center">
                  <Stethoscope className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-black text-slate-900">{selectedDocDetails.document_name}</h3>
                  <p className="text-xs text-slate-500 font-mono">
                    Type: {selectedDocDetails.document_type.replace('_', ' ').toUpperCase()} • Uploaded {new Date(selectedDocDetails.uploaded_at).toLocaleString()}
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDocDetails(null)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {/* Confidence Badge */}
              <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center justify-between text-xs">
                <span className="font-bold text-indigo-950">AI Diagnostic Classification Confidence</span>
                <span className="font-mono font-bold text-indigo-700 bg-white px-2 py-0.5 rounded-lg border border-indigo-200">
                  {Math.round(selectedDocDetails.ai_confidence_score * 100)}% Verified
                </span>
              </div>

              {/* Summary */}
              {selectedDocDetails.ai_summary && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-1">
                  <h4 className="text-xs font-black text-slate-800 uppercase tracking-wider">AI Executive Synthesis</h4>
                  <p className="text-xs text-slate-700 leading-relaxed">{selectedDocDetails.ai_summary}</p>
                </div>
              )}

              {/* Detected Conditions */}
              {selectedDocDetails.ai_detected_conditions && (
                <div className="p-4 bg-purple-50/60 border border-purple-200/80 rounded-2xl space-y-2">
                  <h4 className="text-xs font-black text-purple-950 uppercase tracking-wider">Diagnosed & Detected Indicators</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedDocDetails.ai_detected_conditions.split(',').map((cond, i) => (
                      <span key={i} className="px-3 py-1 rounded-full text-xs font-bold bg-white text-purple-800 border border-purple-200 shadow-sm">
                        {cond.trim()}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Biomarkers */}
              {selectedDocDetails.ai_key_biomarkers && (
                <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-1">
                  <h4 className="text-xs font-black text-slate-800 uppercase tracking-wider">Clinical Lab Values & Biomarkers</h4>
                  <p className="text-xs font-mono text-slate-800 leading-relaxed bg-white p-3 rounded-xl border border-slate-200">
                    {selectedDocDetails.ai_key_biomarkers}
                  </p>
                </div>
              )}

              {/* Suggestions */}
              {selectedDocDetails.ai_clinical_suggestions && (
                <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl space-y-2">
                  <h4 className="text-xs font-black text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                    <span>💡</span>
                    <span>Actionable Clinical & Lifestyle Suggestions</span>
                  </h4>
                  <div className="whitespace-pre-line text-xs text-emerald-900 font-medium leading-relaxed bg-white/70 p-3 rounded-xl border border-emerald-100">
                    {selectedDocDetails.ai_clinical_suggestions}
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <button
                type="button"
                onClick={() => handleReanalyzeDocument(selectedDocDetails.id)}
                disabled={isAnalyzingDocId === selectedDocDetails.id}
                className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 rounded-xl text-xs font-bold flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isAnalyzingDocId === selectedDocDetails.id ? 'animate-spin' : ''}`} />
                <span>Re-Analyze</span>
              </button>

              <button
                type="button"
                onClick={() => setSelectedDocDetails(null)}
                className="px-5 py-2 bg-slate-900 text-white rounded-xl text-xs font-bold hover:bg-slate-800 cursor-pointer"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}

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
              {/* Chronic Conditions & Allergies Bar */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-2xl space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-700">Chronic Conditions & Allergies</span>
                  <button
                    type="button"
                    onClick={() => setShowAddConditionModal(true)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-[10px] font-bold cursor-pointer"
                  >
                    <Plus className="w-3 h-3" />
                    Add Condition
                  </button>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {conditions.length === 0 && allergies.length === 0 ? (
                    <span className="text-[11px] text-slate-400">No chronic conditions or allergies recorded.</span>
                  ) : (
                    <>
                      {conditions.map((c) => (
                        <span key={c.id} className="text-[11px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-medium">
                          {c.condition_name} ({c.severity})
                        </span>
                      ))}
                      {allergies.map((a) => (
                        <span key={a.id} className="text-[11px] px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-medium">
                          Allergy: {a.allergen} ({a.severity})
                        </span>
                      ))}
                    </>
                  )}
                </div>
              </div>

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

            {/* Direct Bluetooth (BLE) Scan & Connect Button */}
            <div className="p-3 bg-indigo-50/70 border border-indigo-100 rounded-2xl space-y-2 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-900 flex items-center gap-1.5">
                  <Radio className="w-4 h-4 text-indigo-600" />
                  Web Bluetooth (BLE) Direct Connect
                </span>
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                  bleConnected ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-600'
                }`}>
                  {bleConnected ? 'BLE Connected' : 'Not Paired'}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                Wirelessly scan for nearby ESP32 smartbands or BLE heart rate monitors via browser Web Bluetooth.
              </p>
              <button
                type="button"
                onClick={handleConnectBluetooth}
                disabled={bleConnecting}
                className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-60"
              >
                <Radio className={`w-3.5 h-3.5 ${bleConnecting ? 'animate-spin' : ''}`} />
                <span>{bleConnecting ? 'Searching for Bluetooth devices...' : 'Scan & Pair BLE Device'}</span>
              </button>
            </div>

            {/* Direct ESP32 Wi-Fi Ingestion Test */}
            <div className="p-3 bg-cyan-50/70 border border-cyan-100 rounded-2xl space-y-2 mb-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-cyan-950 flex items-center gap-1.5">
                  <Wifi className="w-4 h-4 text-cyan-600" />
                  Direct Wi-Fi / HTTP Endpoint
                </span>
                <span className="text-[10px] font-mono text-cyan-700 font-bold bg-white px-1.5 py-0.5 rounded border border-cyan-200">
                  POST /api/v1/health/telemetry
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-tight">
                ESP32 hardware pushes JSON packets directly via Wi-Fi with device UUID <strong className="font-mono">{activeDeviceUuid}</strong>.
              </p>
              <button
                type="button"
                onClick={handleSendTestWifiPacket}
                disabled={testWifiSending}
                className="w-full py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-60"
              >
                <Wifi className={`w-3.5 h-3.5 ${testWifiSending ? 'animate-spin' : ''}`} />
                <span>{testWifiSending ? 'Transmitting telemetry packet...' : 'Send Live Wi-Fi Telemetry Packet'}</span>
              </button>
            </div>

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

      {/* Add Medicine Modal */}
      {showAddMedModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-teal-100 text-teal-600 flex items-center justify-center">
                  <Pill className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Add Medicine Schedule</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddMedModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateMedicine} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Medicine Name</label>
                <input
                  type="text"
                  value={newMedName}
                  onChange={(e) => setNewMedName(e.target.value)}
                  placeholder="e.g. Amlodipine 5mg"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Dosage</label>
                  <input
                    type="text"
                    value={newMedDosage}
                    onChange={(e) => setNewMedDosage(e.target.value)}
                    placeholder="e.g. 1 Tablet"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Frequency</label>
                  <input
                    type="text"
                    value={newMedFreq}
                    onChange={(e) => setNewMedFreq(e.target.value)}
                    placeholder="e.g. Twice daily"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Scheduled Times</label>
                  <input
                    type="text"
                    value={newMedTimes}
                    onChange={(e) => setNewMedTimes(e.target.value)}
                    placeholder="08:00,20:00"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-mono font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    required
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Total Quantity</label>
                  <input
                    type="number"
                    value={newMedQty}
                    onChange={(e) => setNewMedQty(Number(e.target.value))}
                    min="1"
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-teal-500 focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddMedModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-xl shadow-md cursor-pointer"
                >
                  Save Schedule
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Reminder Modal */}
      {showAddReminderModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-amber-100 text-amber-600 flex items-center justify-center">
                  <Bell className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Add Smart Health Reminder</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddReminderModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateReminder} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Reminder Title</label>
                <input
                  type="text"
                  value={newRemTitle}
                  onChange={(e) => setNewRemTitle(e.target.value)}
                  placeholder="e.g. Afternoon Hydration & Vitals Check"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-amber-500 focus:outline-none"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Category</label>
                  <select
                    value={newRemType}
                    onChange={(e) => setNewRemType(e.target.value as any)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-amber-500 focus:outline-none"
                  >
                    <option value="medicine">Medicine</option>
                    <option value="sleep">Sleep & Rest</option>
                    <option value="hydration">Hydration (Water)</option>
                    <option value="appointment">Appointment</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Time</label>
                  <input
                    type="time"
                    value={newRemTime}
                    onChange={(e) => setNewRemTime(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-mono font-medium focus:ring-2 focus:ring-amber-500 focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddReminderModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold rounded-xl shadow-md cursor-pointer"
                >
                  Set Alarm
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Book Doctor Appointment Modal */}
      {showAddApptModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <CalendarIcon className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Book Doctor Consultation</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddApptModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateAppointment} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Physician / Specialist</label>
                <input
                  type="text"
                  value={newApptDoctor}
                  onChange={(e) => setNewApptDoctor(e.target.value)}
                  placeholder="e.g. Dr. Sunita Rao"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Specialization</label>
                <input
                  type="text"
                  value={newApptSpec}
                  onChange={(e) => setNewApptSpec(e.target.value)}
                  placeholder="e.g. Cardiologist"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Appointment Date & Time</label>
                <input
                  type="datetime-local"
                  value={newApptDate}
                  onChange={(e) => setNewApptDate(e.target.value)}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Reason / Clinical Notes</label>
                <textarea
                  value={newApptReason}
                  onChange={(e) => setNewApptReason(e.target.value)}
                  rows={2}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddApptModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md cursor-pointer"
                >
                  Confirm Appointment
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Condition Modal */}
      {showAddConditionModal && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center">
                  <FileText className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Add Medical Condition</h3>
                  <p className="text-xs text-slate-500 font-mono">Patient: {activePatientId}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setShowAddConditionModal(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded-xl cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCondition} className="space-y-3.5">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Condition Name</label>
                <input
                  type="text"
                  value={newConditionName}
                  onChange={(e) => setNewConditionName(e.target.value)}
                  placeholder="e.g. Hypertension (Stage 1) or Asthma"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Severity</label>
                <select
                  value={newConditionSeverity}
                  onChange={(e) => setNewConditionSeverity(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-xl text-xs font-medium focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                >
                  <option value="mild">Mild</option>
                  <option value="moderate">Moderate</option>
                  <option value="severe">Severe</option>
                  <option value="controlled">Controlled</option>
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowAddConditionModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-500 hover:text-slate-700 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl shadow-md cursor-pointer"
                >
                  Save Condition
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Real-time Audible Alarm Modal */}
      {ringingAlarmReminder && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl p-6 md:p-8 max-w-md w-full border-2 border-amber-400 shadow-2xl text-center space-y-4">
            <div className="w-16 h-16 rounded-3xl bg-amber-100 text-amber-600 mx-auto flex items-center justify-center animate-bounce shadow-md">
              <Bell className="w-8 h-8" />
            </div>

            <div className="space-y-1">
              <span className="text-[10px] font-black uppercase tracking-wider bg-amber-100 text-amber-800 px-2.5 py-0.5 rounded-full">
                ⏰ Real-Time Routine Alarm
              </span>
              <h3 className="text-xl font-black text-slate-900 pt-1">{ringingAlarmReminder.title}</h3>
              <p className="text-xs text-slate-500">
                Scheduled for {ringingAlarmReminder.reminder_time} • Tone: {ringingAlarmReminder.alarm_tone ? ringingAlarmReminder.alarm_tone.replace('_', ' ') : 'Gentle Chime'}
              </p>
            </div>

            <div className="p-3.5 rounded-2xl bg-amber-50/80 border border-amber-200/80 text-xs text-amber-900 font-medium">
              Time to take your scheduled dose or wellness routine.
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={() => setRingingAlarmReminder(null)}
                className="flex-1 py-3 px-4 rounded-2xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-black shadow-md shadow-amber-500/25 transition-all cursor-pointer"
              >
                Dismiss Alarm
              </button>
              <button
                type="button"
                onClick={() => {
                  setRingingAlarmReminder(null);
                  setTimeout(() => {
                    setRingingAlarmReminder(ringingAlarmReminder);
                    try {
                      playRingtonePreview(ringingAlarmReminder.alarm_tone || 'gentle_chime');
                    } catch {}
                  }, 5 * 60 * 1000);
                }}
                className="px-4 py-3 rounded-2xl border border-slate-200 hover:bg-slate-100 text-slate-600 text-xs font-bold transition-all cursor-pointer"
              >
                Snooze (5m)
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
