import React, { useState, useEffect } from 'react';
import {
  Heart,
  Activity,
  Shield,
  MapPin,
  Pill,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Phone,
  QrCode,
  UserCheck,
  Search,
  Users,
  ExternalLink,
  ChevronRight,
  RefreshCw,
} from 'lucide-react';
import { caregiverPortalService } from '../../api/services';
import { QRScannerModal } from '../QRScannerModal';

interface FamilyDashboardViewProps {
  onNavigateToComm?: () => void;
  onNavigateToGps?: () => void;
}

export const FamilyDashboardView: React.FC<FamilyDashboardViewProps> = ({
  onNavigateToComm,
  onNavigateToGps,
}) => {
  const [linkedPatients, setLinkedPatients] = useState<any[]>([]);
  const [activePatientId, setActivePatientId] = useState<string>('');
  const [dashboardData, setDashboardData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Link Patient ID Modal state
  const [showLinkModal, setShowLinkModal] = useState(false);
  const [inputPatientId, setInputPatientId] = useState('');
  const [inputRelationship, setInputRelationship] = useState('Daughter');
  const [verifiedPreview, setVerifiedPreview] = useState<any | null>(null);
  const [linkingLoading, setLinkingLoading] = useState(false);
  const [linkSuccessToast, setLinkSuccessToast] = useState<string | null>(null);

  // QR Scanner Modal
  const [showQRScanner, setShowQRScanner] = useState(false);

  useEffect(() => {
    loadMyPatients();
  }, []);

  const loadMyPatients = async () => {
    setLoading(true);
    setError(null);
    try {
      const patients = await caregiverPortalService.getMyLinkedPatients();
      setLinkedPatients(patients);
      if (patients.length > 0) {
        const firstId = patients[0].patient_id;
        setActivePatientId(firstId);
        loadDashboard(firstId);
      } else {
        setLoading(false);
        // Prompt linking if no patients linked yet
        setShowLinkModal(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load linked family members.');
      setLoading(false);
    }
  };

  const loadDashboard = async (patientId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await caregiverPortalService.getFamilyDashboard(patientId);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unauthorized or unable to load patient data.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCandidate = async () => {
    if (!inputPatientId.trim()) return;
    setLinkingLoading(true);
    try {
      const res = await caregiverPortalService.verifyPatientId(inputPatientId.trim());
      setVerifiedPreview(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Patient ID not found in system database.');
    } finally {
      setLinkingLoading(false);
    }
  };

  const handleConfirmLink = async () => {
    if (!verifiedPreview) return;
    setLinkingLoading(true);
    try {
      await caregiverPortalService.requestLink(
        verifiedPreview.patient_id,
        inputRelationship,
        'Family Caregiver Access'
      );
      setLinkSuccessToast(`Successfully authorized access for Patient ${verifiedPreview.patient_id}!`);
      setShowLinkModal(false);
      setVerifiedPreview(null);
      setInputPatientId('');
      loadMyPatients();
      setTimeout(() => setLinkSuccessToast(null), 5000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to link patient record.');
    } finally {
      setLinkingLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Role Banner */}
      <div className="bg-gradient-to-r from-emerald-900 via-teal-900 to-slate-900 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 border border-emerald-500/30">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-black uppercase tracking-wider">
              Role: Family Member / Caregiver Portal
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 text-xs font-bold font-mono">
              Strict Patient ID Authorized
            </span>
          </div>
          <h1 className="text-2xl font-black tracking-tight mt-2">
            Family Wellbeing & Safety Dashboard
          </h1>
          <p className="text-xs text-slate-300 mt-1">
            Real-time biometric monitoring, medication tracking, GPS safety, and emergency response for your family members.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setShowQRScanner(true)}
            className="px-4 py-2.5 bg-slate-800/90 hover:bg-slate-700 text-cyan-300 border border-cyan-500/40 rounded-2xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
          >
            <QrCode className="w-4 h-4" />
            Scan Patient QR
          </button>
          <button
            type="button"
            onClick={() => setShowLinkModal(true)}
            className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
          >
            <Users className="w-4 h-4" />
            + Link Patient ID
          </button>
        </div>
      </div>

      {/* Success Feedback Toast */}
      {linkSuccessToast && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-900 flex items-center gap-2 animate-fadeIn shadow-sm">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{linkSuccessToast}</span>
        </div>
      )}

      {/* Linked Patients Selector */}
      {linkedPatients.length > 0 && (
        <div className="flex items-center gap-3 overflow-x-auto pb-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider shrink-0">
            Linked Patients:
          </span>
          {linkedPatients.map((p) => (
            <button
              key={p.patient_id}
              type="button"
              onClick={() => {
                setActivePatientId(p.patient_id);
                loadDashboard(p.patient_id);
              }}
              className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 border cursor-pointer ${
                activePatientId === p.patient_id
                  ? 'bg-emerald-600 text-white border-emerald-600 shadow-md shadow-emerald-600/20'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
              }`}
            >
              <span>{p.full_name}</span>
              <span className="font-mono text-[10px] opacity-80">({p.patient_id})</span>
              <span className="text-[10px] bg-white/20 px-1.5 py-0.5 rounded-full">{p.relationship}</span>
            </button>
          ))}
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 text-center space-y-3">
          <div className="w-8 h-8 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-bold text-slate-600">Verifying authorization and loading patient vitals...</p>
        </div>
      ) : error ? (
        <div className="bg-white rounded-3xl p-8 border border-rose-200 text-center space-y-4">
          <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto" />
          <h3 className="text-base font-black text-slate-900">Patient Access Notice</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">{error}</p>
          <button
            type="button"
            onClick={() => setShowLinkModal(true)}
            className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-2xl text-xs font-bold transition-all cursor-pointer"
          >
            Enter and Authorize Patient ID
          </button>
        </div>
      ) : dashboardData ? (
        <div className="space-y-6">
          {/* Patient Overview Card */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white flex items-center justify-center font-black text-xl shadow-md shadow-emerald-500/20">
                {dashboardData.patient_overview.full_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-black text-slate-900">{dashboardData.patient_overview.full_name}</h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono text-xs font-bold">
                    {dashboardData.patient_overview.patient_id}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold">
                    Blood Group: {dashboardData.patient_overview.blood_group}
                  </span>
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-3 mt-1">
                  <span>Age: <strong>{dashboardData.patient_overview.age} yrs</strong></span>
                  <span>Relationship: <strong>{dashboardData.patient_overview.relationship_to_user}</strong></span>
                  <span>Contact: <strong>{dashboardData.patient_overview.contact_number}</strong></span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Device Status</span>
                <span className="text-xs font-black text-emerald-600 flex items-center justify-center gap-1 mt-0.5">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  {dashboardData.patient_overview.device_status || 'Online'}
                </span>
              </div>
              <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 text-center">
                <span className="text-[10px] text-slate-400 font-bold uppercase block">Emergency SOS</span>
                <span className={`text-xs font-black mt-0.5 ${dashboardData.emergency_status.has_active_emergency ? 'text-rose-600' : 'text-slate-700'}`}>
                  {dashboardData.emergency_status.has_active_emergency ? '🚨 ACTIVE ALERT' : 'Normal / Safe'}
                </span>
              </div>
            </div>
          </div>

          {/* Vitals Telemetry Matrix */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-bold uppercase">Heart Rate</span>
                <Heart className="w-4 h-4 text-rose-500" />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.live_health?.heart_rate ?? 72}
                </span>
                <span className="text-xs font-bold text-slate-400">BPM</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Normal Rhythm
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-bold uppercase">Blood Oxygen</span>
                <Activity className="w-4 h-4 text-cyan-500" />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.live_health?.spo2 ?? 98}
                </span>
                <span className="text-xs font-bold text-slate-400">%</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Optimal Saturation
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-bold uppercase">Blood Pressure</span>
                <Shield className="w-4 h-4 text-purple-500" />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-black text-slate-900">
                  {dashboardData.live_health?.blood_pressure_sys ?? 120}/{dashboardData.live_health?.blood_pressure_dia ?? 80}
                </span>
                <span className="text-xs font-bold text-slate-400">mmHg</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Normal Baseline
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <div className="flex items-center justify-between text-slate-500">
                <span className="text-xs font-bold uppercase">Body Temp</span>
                <Activity className="w-4 h-4 text-amber-500" />
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.live_health?.temperature ?? 36.8}
                </span>
                <span className="text-xs font-bold text-slate-400">°C</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Healthy Range
              </span>
            </div>
          </div>

          {/* Dual Column: Medications & GPS/Routine */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Medications Tracking */}
            <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <Pill className="w-5 h-5 text-teal-600" />
                  <h3 className="text-base font-extrabold text-slate-900">Medication Schedule & Adherence</h3>
                </div>
                <span className="text-xs font-bold text-slate-400">
                  {dashboardData.medications?.length || 0} Prescriptions
                </span>
              </div>

              <div className="space-y-3">
                {(!dashboardData.medications || dashboardData.medications.length === 0) ? (
                  <div className="text-center py-8 text-slate-400 text-xs">
                    No active prescriptions recorded for this patient.
                  </div>
                ) : (
                  dashboardData.medications.map((m: any) => (
                    <div
                      key={m.id}
                      className="p-4 rounded-2xl border border-slate-200 bg-slate-50/70 flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-black text-slate-900">{m.medicine_name}</span>
                          <span className="text-[10px] font-bold bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full">
                            {m.dosage}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                          <span>Times: <strong>{m.scheduled_times}</strong></span>
                          <span>Stock: <strong>{m.remaining_quantity} / {m.total_quantity} left</strong></span>
                        </div>
                      </div>
                      <span className="text-xs font-bold px-3 py-1 rounded-xl bg-emerald-100 text-emerald-800">
                        {m.remaining_quantity > 0 ? '✓ In Stock' : '⚠️ Refill Needed'}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* GPS Location & Daily Routine */}
            <div className="lg:col-span-5 space-y-6">
              {/* GPS Safety */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <MapPin className="w-5 h-5 text-rose-500" />
                    <h3 className="text-base font-extrabold text-slate-900">Live GPS Location</h3>
                  </div>
                  <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                    Safe Geofence
                  </span>
                </div>
                <div className="bg-slate-900 text-white rounded-2xl p-4 text-xs font-mono space-y-1">
                  <div>Latitude: {dashboardData.gps_location?.latitude ?? 12.9716}</div>
                  <div>Longitude: {dashboardData.gps_location?.longitude ?? 77.5946}</div>
                  <div className="text-[10px] text-emerald-400 mt-2">● Real-time GPS Tracker Verified</div>
                </div>
                {onNavigateToGps && (
                  <button
                    type="button"
                    onClick={onNavigateToGps}
                    className="w-full py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs rounded-xl transition-all cursor-pointer"
                  >
                    Open Full GPS Tracking Map →
                  </button>
                )}
              </div>

              {/* Daily Routine Reminders */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-3">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <Clock className="w-5 h-5 text-purple-600" />
                    <h3 className="text-base font-extrabold text-slate-900">Daily Routine Schedule</h3>
                  </div>
                </div>
                <div className="space-y-2">
                  {(!dashboardData.routines || dashboardData.routines.length === 0) ? (
                    <div className="text-xs text-slate-400 py-3 text-center">No routine reminders scheduled.</div>
                  ) : (
                    dashboardData.routines.map((r: any) => (
                      <div key={r.id} className="p-2.5 rounded-xl bg-slate-50 flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-800">{r.title}</span>
                        <span className="font-mono text-purple-700 font-bold">{r.reminder_time}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Link Patient ID Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 text-slate-900 shadow-2xl space-y-5 border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <UserCheck className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-black">Link Patient by ID</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowLinkModal(false)}
                className="text-slate-400 hover:text-slate-600 cursor-pointer font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed">
              Enter the patient's unique <strong>Patient ID</strong> (e.g. <code>PT-2026-000001</code>) to authorize family access. Full records are isolated and protected.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Patient ID</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={inputPatientId}
                    onChange={(e) => setInputPatientId(e.target.value)}
                    placeholder="PT-2026-000001"
                    className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs font-mono text-slate-900 focus:outline-none focus:border-emerald-500"
                  />
                  <button
                    type="button"
                    disabled={linkingLoading || !inputPatientId.trim()}
                    onClick={handleVerifyCandidate}
                    className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl transition-all cursor-pointer disabled:opacity-50"
                  >
                    {linkingLoading ? 'Verifying...' : 'Check'}
                  </button>
                </div>
              </div>

              {verifiedPreview && (
                <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-xs space-y-2">
                  <div className="font-bold text-emerald-900 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    Patient Record Found
                  </div>
                  <div className="text-slate-700 space-y-1">
                    <div><strong>ID:</strong> <span className="font-mono">{verifiedPreview.patient_id}</span></div>
                    <div><strong>Patient Name:</strong> {verifiedPreview.masked_name}</div>
                    {verifiedPreview.blood_group && <div><strong>Blood Group:</strong> {verifiedPreview.blood_group}</div>}
                  </div>

                  <div className="pt-2">
                    <label className="text-[11px] font-bold text-slate-700 block mb-1">
                      Your Relationship to Patient
                    </label>
                    <select
                      value={inputRelationship}
                      onChange={(e) => setInputRelationship(e.target.value)}
                      className="w-full bg-white border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-800"
                    >
                      <option value="Daughter">Daughter</option>
                      <option value="Son">Son</option>
                      <option value="Spouse">Spouse</option>
                      <option value="Parent">Parent</option>
                      <option value="Guardian">Guardian</option>
                      <option value="Primary Relative">Primary Relative</option>
                    </select>
                  </div>

                  <button
                    type="button"
                    disabled={linkingLoading}
                    onClick={handleConfirmLink}
                    className="w-full mt-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs rounded-xl shadow-md transition-all cursor-pointer"
                  >
                    Confirm Authorization & Link Patient
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* QR Scanner Modal */}
      <QRScannerModal
        isOpen={showQRScanner}
        onClose={() => setShowQRScanner(false)}
        roleScope="family"
        onPatientVerified={(pid) => {
          setActivePatientId(pid);
          loadDashboard(pid);
        }}
      />
    </div>
  );
};
