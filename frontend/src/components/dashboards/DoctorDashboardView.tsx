import React, { useState, useEffect } from 'react';
import {
  Stethoscope,
  Activity,
  Heart,
  FileText,
  Pill,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Plus,
  QrCode,
  Users,
  Shield,
  Search,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { caregiverPortalService } from '../../api/services';
import { QRScannerModal } from '../QRScannerModal';

interface DoctorDashboardViewProps {
  onNavigateToEcg?: () => void;
}

export const DoctorDashboardView: React.FC<DoctorDashboardViewProps> = ({ onNavigateToEcg }) => {
  const [assignedPatients, setAssignedPatients] = useState<any[]>([]);
  const [activePatientId, setActivePatientId] = useState<string>('');
  const [dashboardData, setDashboardData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // New Prescription Form state
  const [showRxModal, setShowRxModal] = useState(false);
  const [rxName, setRxName] = useState('');
  const [rxDosage, setRxDosage] = useState('1 Tablet');
  const [rxFreq, setRxFreq] = useState('Twice daily');
  const [rxTimes, setRxTimes] = useState('08:00,20:00');
  const [rxInstructions, setRxInstructions] = useState('After meals with water');
  const [rxQty, setRxQty] = useState(30);
  const [rxSubmitting, setRxSubmitting] = useState(false);

  // Clinical Notes state
  const [clinicalNotes, setClinicalNotes] = useState('');
  const [notesSaving, setNotesSaving] = useState(false);
  const [notesToast, setNotesToast] = useState<string | null>(null);

  // Assign Patient ID Modal
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [candidatePatientId, setCandidatePatientId] = useState('');
  const [candidateDesignation, setCandidateDesignation] = useState('Attending Cardiologist');
  const [candidatePreview, setCandidatePreview] = useState<any | null>(null);
  const [assigningLoading, setAssigningLoading] = useState(false);

  // QR Scanner Modal
  const [showQRScanner, setShowQRScanner] = useState(false);

  useEffect(() => {
    loadDoctorData();
  }, []);

  const loadDoctorData = async () => {
    setLoading(true);
    setError(null);
    try {
      const patients = await caregiverPortalService.getMyLinkedPatients();
      setAssignedPatients(patients);
      if (patients.length > 0) {
        const firstId = patients[0].patient_id;
        setActivePatientId(firstId);
        loadPatientClinicalDashboard(firstId);
      } else {
        setLoading(false);
        // Prompt to assign patient by ID
        setShowAssignModal(true);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to initialize physician portal.');
      setLoading(false);
    }
  };

  const loadPatientClinicalDashboard = async (patientId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await caregiverPortalService.getDoctorDashboard(patientId);
      setDashboardData(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unauthorized or unable to load clinical telemetry.');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCandidate = async () => {
    if (!candidatePatientId.trim()) return;
    setAssigningLoading(true);
    try {
      const res = await caregiverPortalService.verifyPatientId(candidatePatientId.trim());
      setCandidatePreview(res);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Patient ID not found in system database.');
    } finally {
      setAssigningLoading(false);
    }
  };

  const handleConfirmAssignment = async () => {
    if (!candidatePreview) return;
    setAssigningLoading(true);
    try {
      await caregiverPortalService.requestLink(
        candidatePreview.patient_id,
        candidateDesignation,
        'Physician Clinical Roster Assignment'
      );
      setShowAssignModal(false);
      setCandidatePreview(null);
      setCandidatePatientId('');
      loadDoctorData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to assign patient to clinical roster.');
    } finally {
      setAssigningLoading(false);
    }
  };

  const handleSaveClinicalNote = async () => {
    if (!clinicalNotes.trim() || !activePatientId) return;
    setNotesSaving(true);
    try {
      await caregiverPortalService.saveDoctorClinicalNote({
        patient_id: activePatientId,
        notes: clinicalNotes.trim(),
      });
      setNotesToast('✓ Clinical consultation note documented in patient health record.');
      setClinicalNotes('');
      setTimeout(() => setNotesToast(null), 5000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save clinical note.');
    } finally {
      setNotesSaving(false);
    }
  };

  const handleCreatePrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rxName.trim() || !activePatientId) return;
    setRxSubmitting(true);
    try {
      await caregiverPortalService.addDoctorPrescription({
        patient_id: activePatientId,
        medicine_name: rxName.trim(),
        dosage: rxDosage.trim(),
        frequency: rxFreq.trim(),
        scheduled_times: rxTimes.trim(),
        instructions: rxInstructions.trim(),
        total_quantity: Number(rxQty) || 30,
      });
      setShowRxModal(false);
      setRxName('');
      setNotesToast(`✓ Prescription '${rxName}' prescribed to patient successfully.`);
      loadPatientClinicalDashboard(activePatientId);
      setTimeout(() => setNotesToast(null), 5000);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to write prescription.');
    } finally {
      setRxSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Physician Credentials Banner */}
      <div className="bg-gradient-to-r from-blue-950 via-slate-900 to-indigo-950 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 border border-blue-500/30">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-blue-500/20 text-blue-300 border border-blue-500/30 text-xs font-black uppercase tracking-wider">
              Role: Doctor / Healthcare Professional
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold">
              ● Verified Physician
            </span>
          </div>
          <h1 className="text-2xl font-black tracking-tight mt-2 flex items-center gap-2">
            <span>Clinical Telemetry & Prescription Portal</span>
          </h1>
          <p className="text-xs text-slate-300 mt-1">
            Official medical records, real-time cardiac & vitals telemetry, clinical note charting, and electronic prescriptions.
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
            onClick={() => setShowAssignModal(true)}
            className="px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
          >
            <Users className="w-4 h-4" />
            + Assign Patient ID
          </button>
        </div>
      </div>

      {/* Feedback Toast */}
      {notesToast && (
        <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-xs font-bold text-emerald-900 flex items-center gap-2 animate-fadeIn shadow-sm">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{notesToast}</span>
        </div>
      )}

      {/* Assigned Patients Selector */}
      {assignedPatients.length > 0 && (
        <div className="flex items-center gap-3 overflow-x-auto pb-2">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider shrink-0">
            Assigned Patients Roster:
          </span>
          {assignedPatients.map((p) => (
            <button
              key={p.patient_id}
              type="button"
              onClick={() => {
                setActivePatientId(p.patient_id);
                loadPatientClinicalDashboard(p.patient_id);
              }}
              className={`px-4 py-2 rounded-2xl text-xs font-bold transition-all flex items-center gap-2 border cursor-pointer ${
                activePatientId === p.patient_id
                  ? 'bg-blue-600 text-white border-blue-600 shadow-md shadow-blue-600/20'
                  : 'bg-white text-slate-700 border-slate-200 hover:border-slate-300'
              }`}
            >
              <span>{p.full_name}</span>
              <span className="font-mono text-[10px] opacity-80">({p.patient_id})</span>
              <span className="text-[10px] bg-emerald-100 text-emerald-800 px-1.5 py-0.5 rounded-full">
                HR: {p.last_heart_rate ?? 72}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* Main Clinical Dashboard */}
      {loading ? (
        <div className="bg-white rounded-3xl p-12 border border-slate-200 text-center space-y-3">
          <div className="w-8 h-8 border-3 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-bold text-slate-600">Verifying clinical assignment and retrieving telemetry bundle...</p>
        </div>
      ) : error ? (
        <div className="bg-white rounded-3xl p-8 border border-rose-200 text-center space-y-4">
          <AlertTriangle className="w-10 h-10 text-rose-500 mx-auto" />
          <h3 className="text-base font-black text-slate-900">Clinical Authorization Notice</h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto">{error}</p>
          <button
            type="button"
            onClick={() => setShowAssignModal(true)}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl text-xs font-bold transition-all cursor-pointer"
          >
            Assign Patient by Patient ID
          </button>
        </div>
      ) : dashboardData ? (
        <div className="space-y-6">
          {/* Patient Header & Quick Actions */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white flex items-center justify-center font-black text-xl shadow-md shadow-blue-500/20">
                {dashboardData.patient_clinical_overview.full_name.charAt(0)}
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-black text-slate-900">
                    {dashboardData.patient_clinical_overview.full_name}
                  </h2>
                  <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 font-mono text-xs font-bold">
                    {dashboardData.patient_clinical_overview.patient_id}
                  </span>
                  <span className="px-2 py-0.5 rounded-full bg-rose-100 text-rose-800 text-[10px] font-bold">
                    Blood Group: {dashboardData.patient_clinical_overview.blood_group}
                  </span>
                </div>
                <div className="text-xs text-slate-500 flex items-center gap-3 mt-1">
                  <span>Age: <strong>{dashboardData.patient_clinical_overview.age} yrs</strong></span>
                  <span>Gender: <strong>{dashboardData.patient_clinical_overview.gender}</strong></span>
                  <span>Phone: <strong>{dashboardData.patient_clinical_overview.contact_number}</strong></span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowRxModal(true)}
                className="px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs rounded-2xl shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                Write Prescription
              </button>
              {onNavigateToEcg && (
                <button
                  type="button"
                  onClick={onNavigateToEcg}
                  className="px-4 py-2.5 bg-slate-900 hover:bg-slate-800 text-cyan-300 font-bold text-xs rounded-2xl shadow-md transition-all flex items-center gap-1.5 cursor-pointer"
                >
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Live ECG Monitor
                </button>
              )}
            </div>
          </div>

          {/* Clinical Telemetry Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase text-slate-500 block">Resting Heart Rate</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.clinical_telemetry?.heart_rate ?? 72}
                </span>
                <span className="text-xs font-bold text-slate-400">BPM</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Normal Sinus Rhythm
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase text-slate-500 block">Blood Pressure</span>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-black text-slate-900">
                  {dashboardData.clinical_telemetry?.blood_pressure_sys ?? 120}/
                  {dashboardData.clinical_telemetry?.blood_pressure_dia ?? 80}
                </span>
                <span className="text-xs font-bold text-slate-400">mmHg</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Normotensive
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase text-slate-500 block">Blood Oxygen (SPO2)</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.clinical_telemetry?.spo2 ?? 98}
                </span>
                <span className="text-xs font-bold text-slate-400">%</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Adequate Oxygenation
              </span>
            </div>

            <div className="bg-white rounded-3xl p-5 border border-slate-200 shadow-sm space-y-2">
              <span className="text-xs font-bold uppercase text-slate-500 block">Core Temperature</span>
              <div className="flex items-baseline gap-1">
                <span className="text-3xl font-black text-slate-900">
                  {dashboardData.clinical_telemetry?.temperature ?? 36.8}
                </span>
                <span className="text-xs font-bold text-slate-400">°C</span>
              </div>
              <span className="text-[10px] font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full inline-block">
                Afebrile
              </span>
            </div>
          </div>

          {/* Clinical Prescriptions & Consultation Notes Editor */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
            {/* Active Prescriptions Table */}
            <div className="lg:col-span-7 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div className="flex items-center gap-2.5">
                  <Pill className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-base font-extrabold text-slate-900">Prescription Authoring & Inventory</h3>
                </div>
                <button
                  type="button"
                  onClick={() => setShowRxModal(true)}
                  className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-xl text-xs font-bold border border-emerald-200 cursor-pointer"
                >
                  + Add Prescription
                </button>
              </div>

              <div className="space-y-3">
                {(!dashboardData.prescriptions || dashboardData.prescriptions.length === 0) ? (
                  <div className="text-xs text-slate-400 py-6 text-center">
                    No active prescriptions authored for this patient. Click <strong>+ Add Prescription</strong> above.
                  </div>
                ) : (
                  dashboardData.prescriptions.map((p: any) => (
                    <div
                      key={p.id}
                      className="p-4 rounded-2xl border border-slate-200 bg-slate-50/70 flex items-start justify-between gap-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-black text-slate-900">{p.medicine_name}</span>
                          <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                            {p.dosage}
                          </span>
                          <span className="text-[10px] font-bold bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full">
                            {p.frequency}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1 flex items-center gap-3">
                          <span>Scheduled Times: <strong>{p.scheduled_times}</strong></span>
                          <span>Stock: <strong>{p.remaining_quantity} / {p.total_quantity}</strong></span>
                        </div>
                        {p.notes && (
                          <div className="text-[11px] text-slate-600 mt-1 italic">
                            Instructions: {p.notes}
                          </div>
                        )}
                      </div>
                      <span className="text-xs font-bold px-2.5 py-1 rounded-xl bg-emerald-100 text-emerald-800 shrink-0">
                        Active Rx
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Clinical Notes Editor */}
            <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
              <div className="flex items-center gap-2.5 pb-3 border-b border-slate-100">
                <FileText className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-extrabold text-slate-900">Document Clinical Consultation</h3>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-700 block">
                  Physician Assessment & Treatment Plan
                </label>
                <textarea
                  value={clinicalNotes}
                  onChange={(e) => setClinicalNotes(e.target.value)}
                  rows={4}
                  placeholder="Record resting telemetry review, medication adjustments, lifestyle guidance, or differential diagnosis..."
                  className="w-full bg-slate-50 border border-slate-300 rounded-2xl p-3 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-500"
                />
                <button
                  type="button"
                  disabled={notesSaving || !clinicalNotes.trim()}
                  onClick={handleSaveClinicalNote}
                  className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
                >
                  {notesSaving ? 'Documenting Note...' : 'Save Clinical Note to Patient Profile'}
                </button>
              </div>

              {/* Documented Conditions & Allergies */}
              <div className="pt-2 border-t border-slate-100 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-500">Documented Conditions:</span>
                  <span className="text-slate-800 font-medium">
                    {dashboardData.conditions?.map((c: any) => c.condition_name).join(', ') || 'None recorded'}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-bold text-slate-500">Documented Drug Allergies:</span>
                  <span className="text-rose-600 font-bold">
                    {dashboardData.allergies?.map((a: any) => a.allergen).join(', ') || 'No known drug allergies'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Prescription Authoring Modal */}
      {showRxModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <form
            onSubmit={handleCreatePrescription}
            className="bg-white rounded-3xl max-w-lg w-full p-6 text-slate-900 shadow-2xl space-y-4 border border-slate-200"
          >
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Pill className="w-5 h-5 text-emerald-600" />
                <h3 className="text-base font-black">Author Medical Prescription</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowRxModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div>
                <label className="font-bold text-slate-700 block mb-1">Medication Name</label>
                <input
                  type="text"
                  required
                  value={rxName}
                  onChange={(e) => setRxName(e.target.value)}
                  placeholder="e.g. Atorvastatin 20mg or Metformin 500mg"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Dosage Form</label>
                  <input
                    type="text"
                    required
                    value={rxDosage}
                    onChange={(e) => setRxDosage(e.target.value)}
                    placeholder="1 Tablet"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Frequency</label>
                  <input
                    type="text"
                    required
                    value={rxFreq}
                    onChange={(e) => setRxFreq(e.target.value)}
                    placeholder="Once daily / Twice daily"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Scheduled Times (HH:MM)</label>
                  <input
                    type="text"
                    required
                    value={rxTimes}
                    onChange={(e) => setRxTimes(e.target.value)}
                    placeholder="08:00,20:00"
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium font-mono"
                  />
                </div>
                <div>
                  <label className="font-bold text-slate-700 block mb-1">Total Quantity (Tablets)</label>
                  <input
                    type="number"
                    min={1}
                    max={365}
                    value={rxQty}
                    onChange={(e) => setRxQty(Number(e.target.value))}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium"
                  />
                </div>
              </div>

              <div>
                <label className="font-bold text-slate-700 block mb-1">Clinical Instructions</label>
                <input
                  type="text"
                  value={rxInstructions}
                  onChange={(e) => setRxInstructions(e.target.value)}
                  placeholder="e.g. After meals with a glass of water"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-slate-900 font-medium"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={rxSubmitting || !rxName.trim()}
              className="w-full py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-xs rounded-xl shadow-md transition-all cursor-pointer disabled:opacity-50"
            >
              {rxSubmitting ? 'Prescribing...' : 'Prescribe & Update Schedule'}
            </button>
          </form>
        </div>
      )}

      {/* Assign Patient Modal */}
      {showAssignModal && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 text-slate-900 shadow-2xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-blue-600" />
                <h3 className="text-base font-black">Assign Patient to Clinical Roster</h3>
              </div>
              <button
                type="button"
                onClick={() => setShowAssignModal(false)}
                className="text-slate-400 hover:text-slate-600 font-bold"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-600">
              Enter the patient's verified <strong>Patient ID</strong> to assign them to your physician telemetry roster.
            </p>

            <div className="space-y-3">
              <div>
                <label className="text-xs font-bold text-slate-700 block mb-1">Patient ID</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={candidatePatientId}
                    onChange={(e) => setCandidatePatientId(e.target.value)}
                    placeholder="PT-2026-000001"
                    className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs font-mono text-slate-900"
                  />
                  <button
                    type="button"
                    disabled={assigningLoading || !candidatePatientId.trim()}
                    onClick={handleVerifyCandidate}
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl transition-all disabled:opacity-50"
                  >
                    Check
                  </button>
                </div>
              </div>

              {candidatePreview && (
                <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-xs space-y-2">
                  <div className="font-bold text-blue-900 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-blue-600" />
                    Patient Record Verified
                  </div>
                  <div className="text-slate-700 space-y-1">
                    <div><strong>ID:</strong> <span className="font-mono">{candidatePreview.patient_id}</span></div>
                    <div><strong>Patient Name:</strong> {candidatePreview.masked_name}</div>
                  </div>

                  <button
                    type="button"
                    disabled={assigningLoading}
                    onClick={handleConfirmAssignment}
                    className="w-full mt-2 py-2.5 bg-blue-600 hover:bg-blue-700 text-white font-extrabold text-xs rounded-xl shadow-md transition-all cursor-pointer"
                  >
                    Confirm Assignment to Clinical Roster
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
        roleScope="doctor"
        onPatientVerified={(pid) => {
          setActivePatientId(pid);
          loadPatientClinicalDashboard(pid);
        }}
      />
    </div>
  );
};
