import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  AlertTriangle,
  Phone,
  MapPin,
  Ambulance,
  Heart,
  Clock,
  CheckCircle2,
  Lock,
  FileCheck,
  QrCode,
  Search,
  ExternalLink,
  Radio,
  FileText,
} from 'lucide-react';
import { caregiverPortalService } from '../../api/services';
import { QRScannerModal } from '../QRScannerModal';

export const EmergencyDashboardView: React.FC = () => {
  const [incidents, setIncidents] = useState<any[]>([]);
  const [loadingIncidents, setLoadingIncidents] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Selected Incident & Triage Bundle
  const [selectedIncident, setSelectedIncident] = useState<any | null>(null);
  const [accessReason, setAccessReason] = useState('Active 112 SOS Dispatch Response Unit 4');
  const [triageBundle, setTriageBundle] = useState<any | null>(null);
  const [triageLoading, setTriageLoading] = useState(false);
  const [auditRef, setAuditRef] = useState<string | null>(null);

  // Ambulance Simulation State
  const [ambulanceStage, setAmbulanceStage] = useState<'idle' | 'dispatched' | 'en_route' | 'on_scene' | 'transporting' | 'arrived'>('dispatched');
  const [ambulanceEta, setAmbulanceEta] = useState(5);

  // QR Scanner Modal
  const [showQRScanner, setShowQRScanner] = useState(false);

  useEffect(() => {
    loadIncidents();
    const interval = setInterval(loadIncidents, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadIncidents = async () => {
    try {
      const data = await caregiverPortalService.getEmergencyIncidents();
      setIncidents(data);
      if (data.length > 0 && !selectedIncident) {
        setSelectedIncident(data[0]);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Unauthorized or unable to load emergency incidents queue.');
    } finally {
      setLoadingIncidents(false);
    }
  };

  const handleFetchTriageBundle = async (patientId: string, incId?: string) => {
    if (!accessReason.trim()) {
      alert('Official reason for emergency access is mandatory for legal audit logging.');
      return;
    }
    setTriageLoading(true);
    try {
      const res = await caregiverPortalService.getEmergencyPatientTriage(patientId, accessReason.trim(), incId);
      setTriageBundle(res.emergency_triage_bundle);
      setAuditRef(res.audit_reference_id);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to retrieve emergency triage bundle.');
    } finally {
      setTriageLoading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-7xl mx-auto">
      {/* Emergency Responder Badge */}
      <div className="bg-gradient-to-r from-rose-950 via-slate-900 to-red-950 rounded-3xl p-6 text-white shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4 border border-rose-500/40">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-black uppercase tracking-wider flex items-center gap-1.5 animate-pulse">
              <Radio className="w-3.5 h-3.5 text-rose-400" />
              Role: Emergency Response Team & Triage
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 text-xs font-bold font-mono">
              Certified EMS Unit • Duty Station Active
            </span>
          </div>
          <h1 className="text-2xl font-black tracking-tight mt-2 flex items-center gap-2">
            <span>112 Emergency Medical Dispatch & Triage Desk</span>
          </h1>
          <p className="text-xs text-slate-300 mt-1">
            Real-time emergency incident queue, critical biometric triage cards, ambulance coordination, and mandatory HIPAA-grade audit logging.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            type="button"
            onClick={() => setShowQRScanner(true)}
            className="px-4 py-2.5 bg-slate-800/90 hover:bg-slate-700 text-rose-300 border border-rose-500/40 rounded-2xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
          >
            <QrCode className="w-4 h-4" />
            Scan Incident QR
          </button>
          <button
            type="button"
            onClick={loadIncidents}
            className="px-4 py-2.5 bg-rose-600 hover:bg-rose-500 text-white rounded-2xl text-xs font-bold transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
          >
            Refresh Queue
          </button>
        </div>
      </div>

      {/* Main Grid: Incident Queue & Emergency Triage View */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Active Incidents Queue */}
        <div className="lg:col-span-5 bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2.5">
              <ShieldAlert className="w-5 h-5 text-rose-600" />
              <h3 className="text-base font-extrabold text-slate-900">Active Incident Triage Queue</h3>
            </div>
            <span className="px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800 text-xs font-black">
              {incidents.length} Pending
            </span>
          </div>

          <div className="space-y-3">
            {loadingIncidents ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading incident queue...</div>
            ) : incidents.length === 0 ? (
              <div className="py-8 text-center text-xs text-slate-400">
                ✓ No active SOS incidents. All patients currently in normal baseline.
              </div>
            ) : (
              incidents.map((inc) => (
                <div
                  key={inc.id}
                  onClick={() => {
                    setSelectedIncident(inc);
                    handleFetchTriageBundle(inc.patient_id, `INC-${inc.id}`);
                  }}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col gap-2 ${
                    selectedIncident?.id === inc.id
                      ? 'border-rose-500 bg-rose-50/70 shadow-md shadow-rose-500/10'
                      : 'border-slate-200 hover:border-slate-300 bg-slate-50/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-black text-slate-900 flex items-center gap-1.5">
                      <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping" />
                      Patient: {inc.patient_name}
                    </span>
                    <span className="px-2 py-0.5 rounded-full bg-rose-600 text-white font-mono text-[10px] font-bold">
                      {inc.tier || 'Tier 1 Critical'}
                    </span>
                  </div>

                  <div className="text-[11px] text-slate-500 flex items-center justify-between font-mono">
                    <span>ID: <strong>{inc.patient_id}</strong></span>
                    <span>Alert Time: {inc.alert_time ? new Date(inc.alert_time).toLocaleTimeString() : 'Just now'}</span>
                  </div>

                  <div className="text-[11px] text-slate-600 flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-rose-500 shrink-0" />
                    <span>GPS: {inc.latitude?.toFixed(4)}, {inc.longitude?.toFixed(4)}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Protected Triage Bundle & Ambulance Coordination */}
        <div className="lg:col-span-7 space-y-6">
          {/* Access Reason Authorization Box */}
          <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-100">
              <Lock className="w-4 h-4 text-amber-600" />
              <h4 className="text-xs font-black uppercase tracking-wider text-slate-700">
                Audited Clinical Access Gate (Mandatory)
              </h4>
            </div>
            <div className="text-xs text-slate-500">
              Emergency responders must supply an official operation reason to access protected patient triage records. Every access is logged in the regulatory audit trail.
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={accessReason}
                onChange={(e) => setAccessReason(e.target.value)}
                placeholder="e.g. Active 112 SOS Dispatch Response Unit 4"
                className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-3 py-2 text-xs text-slate-900 font-medium"
              />
              <button
                type="button"
                disabled={triageLoading || !selectedIncident}
                onClick={() => handleFetchTriageBundle(selectedIncident?.patient_id, `INC-${selectedIncident?.id}`)}
                className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white font-bold text-xs rounded-xl transition-all cursor-pointer disabled:opacity-50"
              >
                {triageLoading ? 'Auditing...' : 'Retrieve Triage Bundle'}
              </button>
            </div>
          </div>

          {/* Emergency Triage Bundle Cards */}
          {triageBundle ? (
            <div className="space-y-6">
              {/* Patient Core Triage Card */}
              <div className="bg-slate-900 text-white rounded-3xl p-6 shadow-xl border border-rose-500/30 space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 block">
                      Emergency Triage Bundle • Audit Ref: {auditRef}
                    </span>
                    <h3 className="text-lg font-black text-white mt-1">
                      {triageBundle.full_name} ({triageBundle.patient_id})
                    </h3>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-rose-500/20 text-rose-300 border border-rose-500/40 text-xs font-black">
                    Blood: {triageBundle.blood_group}
                  </div>
                </div>

                {/* Critical Vitals At Alert Time */}
                <div className="grid grid-cols-3 gap-3 text-center">
                  <div className="bg-slate-800/80 p-3 rounded-2xl border border-slate-700">
                    <span className="text-[10px] text-slate-400 font-bold block">Heart Rate</span>
                    <span className="text-xl font-black text-rose-400">
                      {triageBundle.vitals_at_alert?.heart_rate ?? 72} BPM
                    </span>
                  </div>
                  <div className="bg-slate-800/80 p-3 rounded-2xl border border-slate-700">
                    <span className="text-[10px] text-slate-400 font-bold block">Oxygen SPO2</span>
                    <span className="text-xl font-black text-cyan-400">
                      {triageBundle.vitals_at_alert?.spo2 ?? 98}%
                    </span>
                  </div>
                  <div className="bg-slate-800/80 p-3 rounded-2xl border border-slate-700">
                    <span className="text-[10px] text-slate-400 font-bold block">Blood Pressure</span>
                    <span className="text-xl font-black text-purple-400">
                      {triageBundle.vitals_at_alert?.blood_pressure ?? '120/80'}
                    </span>
                  </div>
                </div>

                {/* Critical Allergies & Conditions */}
                <div className="space-y-2 text-xs border-t border-slate-800 pt-3">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-400">Critical Drug Allergies:</span>
                    <span className="font-bold text-rose-300">
                      {triageBundle.critical_allergies?.join(', ') || 'No known allergies'}
                    </span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-400">Documented Conditions:</span>
                    <span className="text-slate-200">
                      {triageBundle.medical_conditions?.join(', ') || 'None recorded'}
                    </span>
                  </div>
                </div>

                {/* Next of Kin Emergency Contacts */}
                <div className="border-t border-slate-800 pt-3 space-y-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block">
                    Verified Emergency Contacts:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {triageBundle.emergency_contacts?.map((c: any, idx: number) => (
                      <a
                        key={idx}
                        href={`tel:${c.phone}`}
                        className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs flex items-center justify-between border border-slate-700 transition-all text-slate-200"
                      >
                        <div>
                          <div className="font-bold">{c.name}</div>
                          <div className="text-[10px] text-slate-400">{c.relation}</div>
                        </div>
                        <Phone className="w-4 h-4 text-emerald-400 shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              </div>

              {/* Ambulance Coordination Simulation */}
              <div className="bg-white rounded-3xl p-6 border border-slate-200 shadow-sm space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div className="flex items-center gap-2.5">
                    <Ambulance className="w-5 h-5 text-rose-600" />
                    <div>
                      <h4 className="text-base font-extrabold text-slate-900">Ambulance Coordination</h4>
                      <span className="text-[10px] font-mono font-bold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full">
                        [SIMULATION MODE]
                      </span>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-bold text-slate-600">
                    Unit: EMS-BLR-402
                  </span>
                </div>

                {/* Progress Pipeline */}
                <div className="grid grid-cols-5 gap-2 text-center text-[10px] font-bold">
                  {[
                    { id: 'dispatched', label: '1. Dispatched' },
                    { id: 'en_route', label: '2. En Route' },
                    { id: 'on_scene', label: '3. On Scene' },
                    { id: 'transporting', label: '4. Transport' },
                    { id: 'arrived', label: '5. Hospital ER' },
                  ].map((s) => (
                    <button
                      key={s.id}
                      type="button"
                      onClick={() => setAmbulanceStage(s.id as any)}
                      className={`py-2 px-1 rounded-xl transition-all cursor-pointer ${
                        ambulanceStage === s.id
                          ? 'bg-rose-600 text-white shadow-md'
                          : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                </div>

                <div className="p-3 rounded-2xl bg-slate-50 border border-slate-200 flex items-center justify-between text-xs">
                  <div>
                    <span className="font-bold text-slate-700">Dispatch Status:</span>{' '}
                    <span className="font-mono text-rose-700 font-bold uppercase">{ambulanceStage}</span>
                  </div>
                  <div className="text-slate-500">
                    Target ER: <strong>Metropolitan Trauma Center</strong>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-3xl p-12 border border-slate-200 text-center space-y-3">
              <FileText className="w-8 h-8 text-slate-400 mx-auto" />
              <p className="text-xs font-bold text-slate-600">
                Select an incident from the queue and click <strong>Retrieve Triage Bundle</strong> to view verified emergency medical cards.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* QR Scanner Modal */}
      <QRScannerModal
        isOpen={showQRScanner}
        onClose={() => setShowQRScanner(false)}
        roleScope="emergency"
        onPatientVerified={(pid) => {
          handleFetchTriageBundle(pid, `INC-QR-${Date.now().toString().slice(-4)}`);
        }}
      />
    </div>
  );
};
