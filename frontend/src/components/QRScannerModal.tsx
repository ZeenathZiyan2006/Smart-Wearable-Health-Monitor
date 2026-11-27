import React, { useState, useRef, useEffect } from 'react';
import { QrCode, Camera, Upload, X, CheckCircle2, AlertCircle, Search } from 'lucide-react';
import { caregiverPortalService, patientDashboardService } from '../api/services';

interface QRScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onPatientVerified?: (patientId: string, data: any) => void;
  title?: string;
  roleScope?: string;
}

export const QRScannerModal: React.FC<QRScannerModalProps> = ({
  isOpen,
  onClose,
  onPatientVerified,
  title = 'Scan & Access Patient QR Health Pass',
  roleScope = 'caregiver',
}) => {
  const [activeTab, setActiveTab] = useState<'camera' | 'manual' | 'upload'>('manual');
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [verifiedResult, setVerifiedResult] = useState<any | null>(null);
  const [cameraActive, setCameraActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      setVerifiedResult(null);
      setError(null);
      setTokenInput('');
    }
  }, [isOpen]);

  const startCamera = async () => {
    setError(null);
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access is not supported by your browser.');
      }
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setCameraActive(true);
    } catch (err: any) {
      setError(err.message || 'Unable to access camera. Please use manual Patient ID input.');
      setCameraActive(false);
    }
  };

  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setCameraActive(false);
  };

  const handleVerify = async (candidateId: string) => {
    const clean = candidateId.trim();
    if (!clean) {
      setError('Please enter a valid Patient ID or QR Token.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // 1. Try caregiver portal ID verification
      const verifyRes = await caregiverPortalService.verifyPatientId(clean);
      setVerifiedResult(verifyRes);
      if (onPatientVerified) {
        onPatientVerified(verifyRes.patient_id, verifyRes);
      }
    } catch (err: any) {
      // 2. Fallback to public emergency QR profile lookup
      try {
        const qrRes = await patientDashboardService.getPublicEmergencyQRProfile(clean);
        setVerifiedResult({
          exists: true,
          patient_id: qrRes.patient_id_readable || clean,
          masked_name: qrRes.patient_name || 'Verified Patient',
          blood_group: qrRes.blood_group,
          is_already_linked: true,
          requires_link_approval: false,
          emergency_data: qrRes,
        });
        if (onPatientVerified) {
          onPatientVerified(qrRes.patient_id_readable || clean, qrRes);
        }
      } catch (e: any) {
        setError(err.response?.data?.detail || 'Patient ID not found or invalid. Please check the ID.');
      }
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
      <div className="bg-slate-900 border border-cyan-500/30 rounded-3xl max-w-lg w-full p-6 text-white shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30">
              <QrCode className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-black text-white">{title}</h3>
              <p className="text-[11px] text-slate-400">Scan QR Code or verify Patient ID ({roleScope})</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white bg-slate-800 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Tab Selection */}
        <div className="flex rounded-xl bg-slate-800 p-1 text-xs font-bold">
          <button
            type="button"
            onClick={() => {
              setActiveTab('manual');
              stopCamera();
            }}
            className={`flex-1 py-2 rounded-lg transition-all ${
              activeTab === 'manual' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            Enter ID / Token
          </button>
          <button
            type="button"
            onClick={() => {
              setActiveTab('camera');
              startCamera();
            }}
            className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-1.5 ${
              activeTab === 'camera' ? 'bg-cyan-600 text-white shadow' : 'text-slate-400 hover:text-white'
            }`}
          >
            <Camera className="w-3.5 h-3.5" />
            Live Camera
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-3 rounded-2xl bg-rose-500/20 border border-rose-500/30 text-rose-200 text-xs font-semibold flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        {/* Content based on Tab */}
        {activeTab === 'manual' && (
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-300">Patient ID or QR Pass Token</label>
              <div className="relative">
                <input
                  type="text"
                  value={tokenInput}
                  onChange={(e) => setTokenInput(e.target.value)}
                  placeholder="e.g. PT-2026-000001 or PT-QR-..."
                  className="w-full bg-slate-800 border border-slate-700 rounded-2xl px-4 py-3 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>
              <p className="text-[10px] text-slate-500">
                You can enter standard Patient IDs (e.g. PT-2026-000001) or full QR pass tokens.
              </p>
            </div>

            <button
              type="button"
              disabled={loading || !tokenInput.trim()}
              onClick={() => handleVerify(tokenInput)}
              className="w-full py-3 rounded-2xl bg-cyan-600 hover:bg-cyan-500 text-white font-extrabold text-xs shadow-lg shadow-cyan-600/30 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              ) : (
                <Search className="w-4 h-4" />
              )}
              <span>Verify & Access Patient Record</span>
            </button>
          </div>
        )}

        {activeTab === 'camera' && (
          <div className="space-y-3">
            <div className="relative rounded-2xl overflow-hidden bg-black aspect-video flex items-center justify-center border border-slate-700">
              <video ref={videoRef} className="w-full h-full object-cover" playsInline muted />
              <div className="absolute inset-0 pointer-events-none border-2 border-cyan-400/50 m-8 rounded-2xl flex items-center justify-center">
                <span className="text-[11px] text-cyan-300 font-semibold bg-black/60 px-3 py-1 rounded-full">
                  Align QR Code inside frame
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleVerify('PT-2026-000001')}
                className="flex-1 py-2 bg-slate-800 hover:bg-slate-700 rounded-xl text-xs font-semibold text-slate-300"
              >
                Scan Test QR (PT-2026-000001)
              </button>
              <button
                type="button"
                onClick={stopCamera}
                className="px-4 py-2 bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 rounded-xl text-xs font-semibold"
              >
                Stop Camera
              </button>
            </div>
          </div>
        )}

        {/* Verified Result Card */}
        {verifiedResult && (
          <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-extrabold text-xs">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Patient Record Verified Successfully</span>
            </div>
            <div className="text-xs space-y-1.5 text-slate-300">
              <div>
                <strong>ID:</strong> <span className="font-mono text-cyan-300">{verifiedResult.patient_id}</span>
              </div>
              <div>
                <strong>Name:</strong> {verifiedResult.masked_name}
              </div>
              {verifiedResult.blood_group && (
                <div>
                  <strong>Blood Group:</strong>{' '}
                  <span className="px-2 py-0.5 rounded bg-rose-500/20 text-rose-300 font-bold">
                    {verifiedResult.blood_group}
                  </span>
                </div>
              )}
            </div>
            <div className="pt-2 flex gap-2">
              <button
                type="button"
                onClick={() => {
                  if (onPatientVerified) {
                    onPatientVerified(verifiedResult.patient_id, verifiedResult);
                  }
                  onClose();
                }}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow-md transition-all cursor-pointer"
              >
                Load Patient Dashboard
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
