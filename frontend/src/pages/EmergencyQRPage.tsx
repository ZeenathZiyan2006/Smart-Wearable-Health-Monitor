import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  AlertTriangle,
  Phone,
  FileText,
  ExternalLink,
  Download,
  Printer,
  Heart,
  Pill,
  User,
  Clock,
  RefreshCw,
  CheckCircle2,
  Stethoscope,
  ChevronLeft,
  X,
} from 'lucide-react';
import { patientDashboardService } from '../api/services';
import type { EmergencyQRPublicView } from '../api/types';

export const EmergencyQRPage: React.FC = () => {
  const { qrToken } = useParams<{ qrToken: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<EmergencyQRPublicView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDocPreview, setSelectedDocPreview] = useState<any | null>(null);

  useEffect(() => {
    const fetchQRData = async () => {
      if (!qrToken) {
        setError('Missing Emergency QR Token.');
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const res = await patientDashboardService.getPublicEmergencyQRProfile(qrToken);
        setData(res);
      } catch (err: any) {
        setError(
          err.response?.data?.detail ||
          'Emergency QR Pass could not be verified. It may be inactive or invalid.'
        );
      } finally {
        setLoading(false);
      }
    };

    fetchQRData();
  }, [qrToken]);

  const handleOpenReportPdf = (doc: any) => {
    if (doc.file_url && doc.file_url.startsWith('data:application/pdf')) {
      // Direct base64 PDF: Open in new tab or download
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
      // Open in interactive medical report viewer
      setSelectedDocPreview(doc);
    }
  };

  return (
    <div className="min-h-screen bg-[#070e1c] text-slate-100 p-4 sm:p-6 lg:p-10 font-sans selection:bg-cyan-500 selection:text-white">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Navigation & Brand Header */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-xs font-bold text-slate-400 hover:text-cyan-400 transition-colors cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </button>

          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono font-bold text-emerald-400 uppercase tracking-wider">
              Verified Emergency Pass
            </span>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-12 text-center space-y-4 shadow-2xl backdrop-blur-md">
            <RefreshCw className="w-10 h-10 text-cyan-400 animate-spin mx-auto" />
            <h2 className="text-lg font-bold text-white">Verifying Emergency QR Credentials...</h2>
            <p className="text-xs text-slate-400">Querying hospital secure patient registry for Token: {qrToken}</p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="bg-rose-950/40 border border-rose-500/50 rounded-3xl p-8 text-center space-y-4 shadow-2xl backdrop-blur-md">
            <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto" />
            <h2 className="text-xl font-bold text-rose-200">Emergency Pass Verification Failed</h2>
            <p className="text-xs text-slate-300 max-w-md mx-auto">{error}</p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="px-5 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-lg cursor-pointer"
            >
              Retry Verification
            </button>
          </div>
        )}

        {/* Main Verified Emergency View */}
        {!loading && data && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Top Identity Banner */}
            <div className="bg-gradient-to-br from-slate-900 via-[#0e1d35] to-[#0a1526] rounded-3xl p-6 sm:p-8 border border-cyan-500/40 shadow-2xl relative overflow-hidden">
              <div className="absolute -top-16 -right-16 w-64 h-64 bg-cyan-500/15 rounded-full blur-3xl pointer-events-none" />

              <div className="relative z-10 flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="space-y-2">
                  <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs font-extrabold">
                    <ShieldCheck className="w-4 h-4 text-emerald-400" />
                    <span>AUTHENTICATED EMERGENCY MEDICAL PROFILE</span>
                  </div>

                  <h1 className="text-3xl font-black text-white tracking-tight flex flex-wrap items-center gap-3">
                    <span>{data.patient_name}</span>
                    {data.blood_group && (
                      <span className="text-sm px-3 py-1 rounded-xl bg-rose-600 text-white font-mono font-black shadow-md shadow-rose-600/30">
                        Blood: {data.blood_group}
                      </span>
                    )}
                  </h1>

                  <div className="flex flex-wrap items-center gap-2 pt-1 text-xs font-mono text-cyan-200">
                    <span className="bg-white/10 px-3 py-1 rounded-lg border border-white/10">
                      Patient ID: {data.patient_id_readable}
                    </span>
                    <span className="bg-white/10 px-3 py-1 rounded-lg border border-white/10">
                      Token: {qrToken}
                    </span>
                    <span className="bg-emerald-500/20 text-emerald-300 px-3 py-1 rounded-lg border border-emerald-500/30 font-bold">
                      ● Active Status
                    </span>
                  </div>
                </div>

                <div className="flex gap-2 w-full md:w-auto shrink-0">
                  <button
                    type="button"
                    onClick={() => window.print()}
                    className="flex-1 md:flex-initial px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white font-bold text-xs border border-white/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    <Printer className="w-4 h-4" />
                    <span>Print Record</span>
                  </button>
                </div>
              </div>
            </div>

            {/* Critical Emergency First Responder Banner */}
            {data.emergency_instructions && (
              <div className="bg-gradient-to-r from-rose-950/70 via-rose-900/60 to-rose-950/70 border border-rose-500/60 rounded-3xl p-5 shadow-xl space-y-2">
                <div className="flex items-center gap-2 text-rose-300 font-extrabold text-xs tracking-wider uppercase">
                  <AlertTriangle className="w-4 h-4 text-rose-400" />
                  <span>Immediate Action & Medical Guidance</span>
                </div>
                <p className="text-white text-sm font-semibold leading-relaxed">
                  {data.emergency_instructions}
                </p>
                {data.doctor_contact && (
                  <p className="text-xs text-rose-200/90 font-medium pt-1 border-t border-rose-500/30">
                    <strong>Attending Physician:</strong> {data.doctor_contact}
                  </p>
                )}
              </div>
            )}

            {/* Emergency Contacts Station */}
            <div className="bg-slate-900/80 rounded-3xl p-6 border border-slate-800 shadow-xl space-y-4">
              <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                <Phone className="w-5 h-5 text-emerald-400" />
                <span>Emergency Contacts & Caregivers</span>
              </h2>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {data.emergency_contacts && data.emergency_contacts.length > 0 ? (
                  data.emergency_contacts.map((c, i) => (
                    <div
                      key={i}
                      className="p-4 rounded-2xl bg-slate-800/80 border border-slate-700/80 flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="text-sm font-bold text-white">{c.name}</div>
                        <div className="text-xs text-slate-400 font-medium">{c.relation}</div>
                        <div className="text-xs text-emerald-400 font-mono mt-0.5">{c.phone}</div>
                      </div>

                      <a
                        href={`tel:${c.phone}`}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold shadow-md transition-all flex items-center gap-1.5 cursor-pointer shrink-0"
                      >
                        <Phone className="w-3.5 h-3.5" />
                        <span>Call</span>
                      </a>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400">No emergency contacts listed.</p>
                )}
              </div>
            </div>

            {/* Uploaded Digital Health Reports & AI Clinical Analysis */}
            <div className="bg-slate-900/80 rounded-3xl p-6 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-extrabold text-white flex items-center gap-2">
                    <FileText className="w-5 h-5 text-cyan-400" />
                    <span>Uploaded Digital Health Reports & Lab Diagnostics</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-0.5">
                    Scannable original copies with extracted clinical biomarkers and AI summaries
                  </p>
                </div>
                <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                  {data.uploaded_documents?.length || 0} Reports
                </span>
              </div>

              <div className="space-y-3.5">
                {data.uploaded_documents && data.uploaded_documents.length > 0 ? (
                  data.uploaded_documents.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-5 rounded-2xl bg-gradient-to-br from-slate-800/90 via-slate-800/60 to-slate-900 border border-slate-700/80 hover:border-cyan-500/60 transition-all space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-black text-white">{doc.document_name}</span>
                            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-400/30">
                              {doc.document_type}
                            </span>
                          </div>
                          <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-1">
                            <Clock className="w-3.5 h-3.5 text-slate-500" />
                            <span>Uploaded: {doc.uploaded_at}</span>
                            <span>•</span>
                            <span className="text-emerald-400 font-semibold">
                              AI Confidence: {Math.round(doc.ai_confidence_score * 100)}%
                            </span>
                          </div>
                        </div>

                        {/* Open Report PDF Link / Button */}
                        <button
                          type="button"
                          onClick={() => handleOpenReportPdf(doc)}
                          className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-extrabold text-xs rounded-xl shadow-md shadow-cyan-500/20 transition-all flex items-center gap-1.5 cursor-pointer shrink-0"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                          <span>Open Report PDF</span>
                        </button>
                      </div>

                      {/* AI Diagnostic Summary */}
                      <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-700/60 text-xs space-y-1">
                        <span className="text-[10px] font-bold text-cyan-300 uppercase tracking-wider block">
                          AI Diagnostic Summary
                        </span>
                        <p className="text-slate-300 leading-relaxed">{doc.ai_summary}</p>
                      </div>

                      {/* Key Findings Badges */}
                      <div className="flex flex-wrap gap-2 text-xs">
                        <span className="px-2.5 py-1 rounded-lg bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 font-medium">
                          <strong>Identified:</strong> {doc.ai_detected_conditions}
                        </span>
                        <span className="px-2.5 py-1 rounded-lg bg-blue-500/15 text-blue-300 border border-blue-500/30 font-medium">
                          <strong>Biomarkers:</strong> {doc.ai_key_biomarkers}
                        </span>
                      </div>

                      {/* Clinical Recommendations */}
                      <div className="p-3 rounded-xl bg-indigo-950/40 border border-indigo-500/30 text-xs text-indigo-200">
                        <strong className="text-indigo-300">Clinical Recommendation: </strong>
                        {doc.ai_clinical_suggestions}
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-400 py-4 text-center">No digital reports available on this profile.</p>
                )}
              </div>
            </div>

            {/* Prescriptions & Allergies Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Active Prescriptions */}
              <div className="bg-slate-900/80 rounded-3xl p-6 border border-slate-800 shadow-xl space-y-3">
                <h2 className="text-sm font-extrabold text-white flex items-center gap-2">
                  <Pill className="w-4 h-4 text-teal-400" />
                  <span>Active Prescriptions ({data.active_medicines?.length || 0})</span>
                </h2>
                <div className="space-y-2">
                  {data.active_medicines && data.active_medicines.length > 0 ? (
                    data.active_medicines.map((m, i) => (
                      <div key={i} className="p-3 rounded-xl bg-slate-800/70 border border-slate-700 text-xs text-slate-200 font-medium">
                        {m}
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-slate-400">No active prescriptions.</p>
                  )}
                </div>
              </div>

              {/* Known Allergies & Clinical Conditions */}
              <div className="bg-slate-900/80 rounded-3xl p-6 border border-slate-800 shadow-xl space-y-3">
                <h2 className="text-sm font-extrabold text-white flex items-center gap-2">
                  <Heart className="w-4 h-4 text-rose-400" />
                  <span>Medical Conditions & Allergies</span>
                </h2>
                <div className="space-y-2">
                  <div className="text-xs text-slate-400 font-bold uppercase tracking-wider">Conditions:</div>
                  {data.medical_conditions && data.medical_conditions.length > 0 ? (
                    data.medical_conditions.map((c, i) => (
                      <span key={i} className="inline-block mr-2 mb-2 px-2.5 py-1 rounded-lg bg-purple-500/20 text-purple-300 border border-purple-500/30 text-xs font-semibold">
                        {c}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">None recorded</span>
                  )}

                  <div className="text-xs text-slate-400 font-bold uppercase tracking-wider pt-2">Allergies:</div>
                  {data.allergies && data.allergies.length > 0 ? (
                    data.allergies.map((a, i) => (
                      <span key={i} className="inline-block mr-2 mb-2 px-2.5 py-1 rounded-lg bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-semibold">
                        {a}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">No known allergies (NKDA)</span>
                  )}
                </div>
              </div>
            </div>

            {/* Legal Notice Footer */}
            <div className="text-center text-[11px] text-slate-500 py-4 border-t border-slate-800/80">
              {data.notice}
            </div>
          </div>
        )}
      </div>

      {/* Interactive PDF / Medical Report Fullscreen Modal Viewer */}
      {selectedDocPreview && (
        <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
          <div className="bg-slate-900 border border-slate-700 max-w-3xl w-full rounded-3xl p-6 shadow-2xl my-auto space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-sm font-bold text-white">{selectedDocPreview.document_name}</h3>
                  <span className="text-[10px] text-slate-400 uppercase">{selectedDocPreview.document_type}</span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedDocPreview(null)}
                className="p-1 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Document Report Body */}
            <div className="bg-slate-950 p-4 rounded-2xl border border-slate-800 space-y-3 font-mono text-xs max-h-96 overflow-y-auto">
              <div className="text-cyan-300 font-bold border-b border-slate-800 pb-2">
                DIGITAL HEALTH REPORT • CLINICAL LABORATORY SPECIFICATION
              </div>
              <div className="text-slate-300 whitespace-pre-wrap leading-relaxed">
                {selectedDocPreview.file_text_content ||
                  `Document: ${selectedDocPreview.document_name}
Status: Verified by Clinical AI Diagnostic Engine
Summary: ${selectedDocPreview.ai_summary}
Conditions Identified: ${selectedDocPreview.ai_detected_conditions}
Key Biomarkers: ${selectedDocPreview.ai_key_biomarkers}
Suggestions: ${selectedDocPreview.ai_clinical_suggestions}`}
              </div>
            </div>

            <div className="flex justify-between items-center pt-2">
              <span className="text-xs text-slate-400 font-mono">Date: {selectedDocPreview.uploaded_at}</span>
              <button
                type="button"
                onClick={() => setSelectedDocPreview(null)}
                className="px-5 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs cursor-pointer shadow-md"
              >
                Close Viewer
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
