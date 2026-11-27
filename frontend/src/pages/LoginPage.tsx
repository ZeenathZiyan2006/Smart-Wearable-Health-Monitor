import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Heart,
  Shield,
  Brain,
  Globe,
  Mail,
  Lock,
  Eye,
  EyeOff,
  ArrowRight,
  ShieldCheck,
  User,
  Users,
  AlertCircle,
  X,
  Plus,
  KeyRound,
  UserPlus,
  LogIn,
  Copy,
  Calendar,
  Phone,
  Home,
  CheckCircle2,
  AlertTriangle,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useLanguage } from '../context/LanguageContext';
import { SupportedLanguage } from '../i18n/translations';
import { PulseGuardianLogo } from '../components/PulseGuardianLogo';
import { patientAuthService } from '../api/services';
import type { RecoveredPatientProfile, PatientRegisterResponse } from '../api/types';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, patientLogin, socialLogin, selectedRole, setSelectedRole } = useAuth();
  const { language, setLanguage, t, languages } = useLanguage();

  const [patientMode, setPatientMode] = useState<'login' | 'register' | 'forgot_id'>('login');
  const [email, setEmail] = useState('patient@pulseguardian.ai');
  const [patientIdInput, setPatientIdInput] = useState('PT-2026-000001');
  const [password, setPassword] = useState('Patient@123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [regFullName, setRegFullName] = useState('');
  const [regDob, setRegDob] = useState('');
  const [regGender, setRegGender] = useState('Male');
  const [regContact, setRegContact] = useState('');
  const [regIndividualEmail, setRegIndividualEmail] = useState('');
  const [regFamilyEmail, setRegFamilyEmail] = useState('family.care@pulseguardian.ai');
  const [regAddress, setRegAddress] = useState('');
  const [regEmergencyContact, setRegEmergencyContact] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regConfirmPassword, setRegConfirmPassword] = useState('');
  const [showRegPassword, setShowRegPassword] = useState(false);
  const [regLoading, setRegLoading] = useState(false);
  const [regError, setRegError] = useState<string | null>(null);

  const [duplicateWarning, setDuplicateWarning] = useState<{
    isOpen: boolean;
    matchedName?: string;
    matchedId?: string;
    message: string;
  }>({ isOpen: false, message: '' });

  const [regSuccessData, setRegSuccessData] = useState<PatientRegisterResponse | null>(null);
  const [copiedSuccess, setCopiedSuccess] = useState(false);

  const [forgotRecoveryContact, setForgotRecoveryContact] = useState('');
  const [forgotOtpCode, setForgotOtpCode] = useState('');
  const [forgotOtpSent, setForgotOtpSent] = useState(false);
  const [forgotDemoOtp, setForgotDemoOtp] = useState<string | null>(null);
  const [forgotRecoveredPatients, setForgotRecoveredPatients] = useState<RecoveredPatientProfile[]>([]);
  const [forgotLoading, setForgotLoading] = useState(false);
  const [forgotError, setForgotError] = useState<string | null>(null);

  const [socialModalProvider, setSocialModalProvider] = useState<'google' | 'microsoft' | null>(null);
  const [socialStep, setSocialStep] = useState<'choose_account' | 'enter_password'>('choose_account');
  const [selectedSocialAccount, setSelectedSocialAccount] = useState<{ email: string; name: string } | null>(null);
  const [socialPassword, setSocialPassword] = useState('');
  const [socialPasswordError, setSocialPasswordError] = useState<string | null>(null);
  const [isVerifyingSocial, setIsVerifyingSocial] = useState(false);
  const [customSocialEmail, setCustomSocialEmail] = useState('');
  const [showCustomEmailInput, setShowCustomEmailInput] = useState(false);

  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSuccess, setForgotSuccess] = useState<string | null>(null);

  const handleRoleSelect = (role: 'patient' | 'caregiver') => {
    setSelectedRole(role);
    setErrorMessage(null);
    if (role === 'patient') {
      setEmail('PT-2026-000001');
      setPatientIdInput('PT-2026-000001');
      setPassword('Patient@123');
    } else {
      setEmail('caregiver@pulseguardian.ai');
      setPassword('Caregiver@123');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    const loginIdentifier = selectedRole === 'patient' ? (patientIdInput || email) : email;
    if (!loginIdentifier || !password) {
      setErrorMessage('Please provide both identification and password.');
      return;
    }
    setIsLoading(true);
    try {
      if (selectedRole === 'patient') {
        await patientLogin(loginIdentifier, password);
      } else {
        await login(loginIdentifier, password);
      }
      navigate('/');
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || 'Authentication failed. Please verify your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRegisterSubmit = async (e: React.FormEvent, force: boolean = false) => {
    e.preventDefault();
    setRegError(null);
    if (!regFullName.trim()) { setRegError('Please provide the patient full name.'); return; }
    if (!regContact.trim()) { setRegError('Please provide a contact number.'); return; }
    if (!regFamilyEmail.trim()) { setRegError('Please provide the family/caretaker email.'); return; }
    if (!regPassword || regPassword.length < 6) { setRegError('Password must be at least 6 characters long.'); return; }
    if (regPassword !== regConfirmPassword) { setRegError('Passwords do not match.'); return; }

    setRegLoading(true);
    try {
      if (!force) {
        const dupRes = await patientAuthService.checkDuplicate({
          full_name: regFullName.trim(),
          family_email: regFamilyEmail.trim().toLowerCase(),
          date_of_birth: regDob || undefined,
        });
        if (dupRes.has_duplicate) {
          setDuplicateWarning({
            isOpen: true,
            matchedName: dupRes.matched_name,
            matchedId: dupRes.matched_patient_id,
            message: dupRes.message,
          });
          setRegLoading(false);
          return;
        }
      }

      const payload = {
        full_name: regFullName.trim(),
        date_of_birth: regDob || undefined,
        gender: regGender,
        contact_number: regContact.trim(),
        individual_email: regIndividualEmail.trim().toLowerCase() || undefined,
        family_email: regFamilyEmail.trim().toLowerCase(),
        address: regAddress.trim() || undefined,
        emergency_contact: regEmergencyContact.trim() || undefined,
        password: regPassword,
        confirm_password: regConfirmPassword,
        force_duplicate: force,
      };

      const res: PatientRegisterResponse = await patientAuthService.register(payload);
      setRegSuccessData(res);
      setDuplicateWarning({ isOpen: false, message: '' });
    } catch (err: any) {
      setRegError(err.response?.data?.detail || 'Registration failed. Please check the provided information.');
    } finally {
      setRegLoading(false);
    }
  };

  const handleRequestForgotOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);
    if (!forgotRecoveryContact.trim()) {
      setForgotError('Please enter family email or contact phone.');
      return;
    }
    setForgotLoading(true);
    try {
      const res = await patientAuthService.requestForgotIdOtp(forgotRecoveryContact.trim());
      setForgotOtpSent(true);
      if (res.otp_demo) {
        setForgotDemoOtp(res.otp_demo);
        setForgotOtpCode(res.otp_demo);
      }
    } catch (err: any) {
      setForgotError(err.response?.data?.detail || 'Unable to dispatch verification code. Please check your contact detail.');
    } finally {
      setForgotLoading(false);
    }
  };

  const handleVerifyForgotOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setForgotError(null);
    if (!forgotOtpCode.trim()) {
      setForgotError('Please enter the 6-digit OTP code.');
      return;
    }
    setForgotLoading(true);
    try {
      const res = await patientAuthService.verifyForgotIdOtp(forgotRecoveryContact.trim(), forgotOtpCode.trim());
      setForgotRecoveredPatients(res.patients || []);
      if (!res.patients || res.patients.length === 0) {
        setForgotError('No patient profiles found under this family contact.');
      }
    } catch (err: any) {
      setForgotError(err.response?.data?.detail || 'Verification code invalid or expired. Please retry.');
    } finally {
      setForgotLoading(false);
    }
  };

  const handleCopyPatientId = (id: string) => {
    navigator.clipboard.writeText(id);
    setCopiedSuccess(true);
    setTimeout(() => setCopiedSuccess(false), 2000);
  };

  const handleSelectRecoveredPatient = async (pid: string) => {
    try {
      await patientAuthService.confirmPatientIdSelection(forgotRecoveryContact.trim(), pid);
    } catch {}
    setPatientIdInput(pid);
    setEmail(pid);
    setPatientMode('login');
    setForgotOtpSent(false);
    setForgotRecoveredPatients([]);
  };

  const handleOpenSocialModal = (provider: 'google' | 'microsoft') => {
    setSocialModalProvider(provider);
    setSocialStep('choose_account');
    setSelectedSocialAccount(null);
    setSocialPassword('');
    setSocialPasswordError(null);
    setShowCustomEmailInput(false);
    setCustomSocialEmail('');
  };

  const handleSelectSocialAccount = (acc: { email: string; name: string }) => {
    setSelectedSocialAccount(acc);
    setSocialStep('enter_password');
    setSocialPassword('');
    setSocialPasswordError(null);
  };

  const handleConfirmCustomEmail = (e: React.FormEvent) => {
    e.preventDefault();
    if (!customSocialEmail || !customSocialEmail.includes('@')) {
      setSocialPasswordError('Please enter a valid email address.');
      return;
    }
    const namePart = customSocialEmail.split('@')[0].replace('.', ' ');
    const formattedName = namePart.charAt(0).toUpperCase() + namePart.slice(1);
    setSelectedSocialAccount({
      email: customSocialEmail.trim(),
      name: formattedName,
    });
    setSocialStep('enter_password');
    setSocialPassword('');
    setSocialPasswordError(null);
  };

  const handleVerifyAndCompleteSocialLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedSocialAccount) return;
    if (!socialPassword || socialPassword.length < 6) {
      setSocialPasswordError('Password must be at least 6 characters.');
      return;
    }
    setIsVerifyingSocial(true);
    setSocialPasswordError(null);
    try {
      if (socialModalProvider) {
        await socialLogin(
          socialModalProvider,
          selectedRole,
          selectedSocialAccount.email,
          selectedSocialAccount.name,
          socialPassword
        );
        setSocialModalProvider(null);
        navigate('/');
      }
    } catch (err: any) {
      setSocialPasswordError(err.response?.data?.detail || 'Authentication failed. Please verify credentials.');
    } finally {
      setIsVerifyingSocial(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#f4f7fb] flex items-center justify-center p-3 sm:p-6 lg:p-10 font-sans">
      <div className="w-full max-w-[1240px] bg-white rounded-[32px] shadow-2xl shadow-slate-200/60 border border-slate-100 overflow-hidden grid grid-cols-1 lg:grid-cols-12 min-h-[720px]">
        {/* LEFT COLUMN: BRANDING & HERO IMAGE */}
        <div className="lg:col-span-6 bg-gradient-to-br from-white via-slate-50 to-[#edf4fc] p-6 sm:p-10 flex flex-col justify-between border-b lg:border-b-0 lg:border-r border-slate-100 relative overflow-hidden">
          <div className="z-10">
            <PulseGuardianLogo
              size="md"
              tagline={t('brand.tagline', 'Smart Care. Safer Tomorrow.')}
            />
          </div>

          <div className="my-6 z-10">
            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-black tracking-tight leading-[1.15]">
              <span className="text-[#0f2942]">{t('brand.quote', 'Your Health. Our Priority.').split('.')[0]}.</span>
              <br />
              <span className="text-[#0284c7]">{t('brand.quote', 'Your Health. Our Priority.').split('.')[1] || t('brand.quote')}</span>
            </h1>
            <p className="mt-3 text-slate-600 text-sm sm:text-base max-w-md font-medium leading-relaxed">
              {t('brand.description', 'Advanced wearable monitoring for a healthier, happier and safer life.')}
            </p>
          </div>

          {/* Hero Graphic */}
          <div className="relative w-full my-auto flex items-center justify-center min-h-[300px] sm:min-h-[360px]">
            <div className="absolute w-72 h-72 sm:w-88 sm:h-88 rounded-full bg-cyan-400/15 blur-3xl -z-0 pointer-events-none" />

            <div className="relative z-10 w-full max-w-md rounded-2xl overflow-hidden shadow-lg border border-white/60 bg-white/40 backdrop-blur-sm">
              <div className="relative aspect-[4/3] w-full bg-gradient-to-tr from-cyan-900/10 to-teal-500/10 flex items-center justify-center overflow-hidden">
                <img
                  src="/doctor-patient-hero.jpg"
                  alt="Confident smiling doctor and happy elderly patient wearing health monitoring smartwatch"
                  className="w-full h-full object-cover object-center filter brightness-[1.02]"
                />
                
                <div className="absolute bottom-6 left-12 bg-black/85 text-white p-2 rounded-xl border border-cyan-400/40 shadow-xl flex items-center gap-2 backdrop-blur-md">
                  <Heart className="w-4 h-4 text-rose-500 fill-rose-500 animate-pulse" />
                  <div className="flex flex-col text-left">
                    <span className="text-[10px] text-cyan-300 font-semibold tracking-wider">PULSE</span>
                    <span className="text-xs font-black">72 BPM</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="absolute top-2 left-2 z-20 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl shadow-lg border border-slate-100 flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="w-6 h-6 rounded-full bg-cyan-100 text-cyan-600 flex items-center justify-center">
                <Heart className="w-3.5 h-3.5 fill-cyan-500 text-cyan-600" />
              </div>
              <div className="flex flex-col text-left leading-tight">
                <span className="text-[11px] font-bold text-slate-900">{t('feature.realTime', 'Real-Time')}</span>
                <span className="text-[9px] text-slate-400 font-semibold">{t('feature.healthMonitoring', 'Health Monitoring')}</span>
              </div>
            </div>

            <div className="absolute top-24 left-0 z-20 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl shadow-lg border border-slate-100 flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center">
                <Shield className="w-3.5 h-3.5 text-blue-600" />
              </div>
              <div className="flex flex-col text-left leading-tight">
                <span className="text-[11px] font-bold text-slate-900">{t('feature.emergency', 'Emergency')}</span>
                <span className="text-[9px] text-slate-400 font-semibold">{t('feature.alerts', 'Alerts')}</span>
              </div>
            </div>

            <div className="absolute bottom-16 left-2 z-20 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl shadow-lg border border-slate-100 flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="w-6 h-6 rounded-full bg-teal-100 text-teal-600 flex items-center justify-center">
                <Brain className="w-3.5 h-3.5 text-teal-600" />
              </div>
              <div className="flex flex-col text-left leading-tight">
                <span className="text-[11px] font-bold text-slate-900">{t('feature.aiPowered', 'AI-Powered')}</span>
                <span className="text-[9px] text-slate-400 font-semibold">{t('feature.insights', 'Insights')}</span>
              </div>
            </div>

            <div className="absolute bottom-2 right-4 z-20 bg-white/95 backdrop-blur-md px-3.5 py-2 rounded-2xl shadow-lg border border-slate-100 flex items-center gap-2 text-xs font-bold text-slate-800">
              <div className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center">
                <Globe className="w-3.5 h-3.5 text-indigo-600" />
              </div>
              <div className="flex flex-col text-left leading-tight">
                <span className="text-[11px] font-bold text-slate-900">{t('feature.multilingual', 'Multilingual')}</span>
                <span className="text-[9px] text-slate-400 font-semibold">{t('feature.support', 'Support')}</span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-200/60 flex items-center justify-between text-xs text-slate-400">
            <span>(c) 2026 PulseGuardian AI.</span>
            <div className="flex items-center gap-3">
              <span className="hover:text-slate-600 cursor-pointer">Privacy</span>
              <span>-</span>
              <span className="hover:text-slate-600 cursor-pointer">Terms</span>
              <span>-</span>
              <span className="hover:text-slate-600 cursor-pointer">Help</span>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: AUTHENTICATION FORM & ROLE SELECTION */}
        <div className="lg:col-span-6 p-6 sm:p-10 flex flex-col justify-between bg-white overflow-y-auto">
          <div className="flex justify-end items-center mb-2">
            <div className="relative">
              <select
                translate="no"
                value={language}
                onChange={(e) => setLanguage(e.target.value as SupportedLanguage)}
                className="notranslate appearance-none bg-slate-50 border border-slate-200 rounded-full py-1.5 pl-8 pr-8 text-xs font-medium text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-[#0284c7] cursor-pointer"
              >
                {languages.map((l) => (
                  <option key={l.code} value={l.code} translate="no" className="notranslate">
                    {l.code === 'en' ? 'English' : `${l.nativeName} (${l.name})`}
                  </option>
                ))}
              </select>
              <Globe className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          <div className="text-center my-2">
            <div className="inline-flex items-center justify-center p-2.5 rounded-2xl bg-cyan-50 mb-2 shadow-sm">
              <PulseGuardianLogo iconOnly size="md" className="shrink-0" />
            </div>
            <h2 className="text-2xl font-black text-slate-900 tracking-tight">PulseGuardian AI</h2>
            <p className="text-xs text-slate-500 mt-1 font-medium">{t('auth.loginToAccount', 'Login to your account')}</p>
          </div>

          {/* Role Pill Switcher */}
          <div className="bg-[#edf2f7] p-1 rounded-full flex max-w-md mx-auto w-full my-3">
            <button
              type="button"
              onClick={() => handleRoleSelect('patient')}
              className={`flex-1 py-2 rounded-full text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                selectedRole === 'patient'
                  ? 'bg-[#1864ab] text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              {t('role.patient', 'Patient')}
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('caregiver')}
              className={`flex-1 py-2 rounded-full text-xs font-bold flex items-center justify-center gap-2 transition-all cursor-pointer ${
                selectedRole === 'caregiver'
                  ? 'bg-[#1864ab] text-white shadow-md'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-3.5 h-3.5" />
              {t('role.caregiver', 'Caregiver')}
            </button>
          </div>

          {/* PATIENT-SPECIFIC SUB-OPTIONS */}
          {selectedRole === 'patient' && (
            <div className="max-w-md mx-auto w-full mb-3 flex items-center justify-center border-b border-slate-200 pb-2 gap-1 sm:gap-2">
              <button
                type="button"
                onClick={() => {
                  setPatientMode('login');
                  setRegSuccessData(null);
                  setErrorMessage(null);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  patientMode === 'login'
                    ? 'bg-sky-100 text-[#0284c7] font-bold border border-sky-300'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <LogIn className="w-3.5 h-3.5" />
                Existing Patient Login
              </button>
              <button
                type="button"
                onClick={() => {
                  setPatientMode('register');
                  setRegSuccessData(null);
                  setRegError(null);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  patientMode === 'register'
                    ? 'bg-sky-100 text-[#0284c7] font-bold border border-sky-300'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <UserPlus className="w-3.5 h-3.5" />
                Register as New Patient
              </button>
              <button
                type="button"
                onClick={() => {
                  setPatientMode('forgot_id');
                  setRegSuccessData(null);
                  setForgotError(null);
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
                  patientMode === 'forgot_id'
                    ? 'bg-sky-100 text-[#0284c7] font-bold border border-sky-300'
                    : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                <KeyRound className="w-3.5 h-3.5" />
                Forgot Patient ID
              </button>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="max-w-md mx-auto w-full mb-3 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* VIEW 1: REGISTRATION SUCCESS SCREEN */}
          {selectedRole === 'patient' && regSuccessData ? (
            <div className="max-w-md mx-auto w-full my-2 p-5 bg-gradient-to-br from-emerald-50 via-teal-50 to-white border border-emerald-200 rounded-2xl shadow-md text-center space-y-4">
              <div className="w-12 h-12 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-inner">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-lg font-black text-slate-900">Registration Successful!</h3>
                <p className="text-xs text-slate-600 mt-1">
                  Your permanent Unique Patient ID has been issued. Keep this ID safe for logging in and hospital visits.
                </p>
              </div>

              <div className="bg-white p-4 rounded-xl border-2 border-emerald-500/40 shadow-sm text-center">
                <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">Unique Patient ID</div>
                <div className="text-2xl font-black text-[#1864ab] tracking-wider my-1 font-mono">
                  {regSuccessData.patient_id}
                </div>
                <button
                  type="button"
                  onClick={() => handleCopyPatientId(regSuccessData.patient_id)}
                  className="mt-1 inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition-all cursor-pointer"
                >
                  <Copy className="w-3.5 h-3.5" />
                  {copiedSuccess ? 'Copied to Clipboard!' : 'Copy Patient ID'}
                </button>
              </div>

              <div className="text-left text-xs bg-slate-50/80 p-3 rounded-xl border border-slate-200/80 space-y-1.5 text-slate-700">
                <div className="flex justify-between">
                  <span className="text-slate-400">Patient Name:</span>
                  <span className="font-bold">{regSuccessData.patient_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Family Account:</span>
                  <span className="font-medium">{regSuccessData.family_email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Assigned Wearable:</span>
                  <span className="font-mono text-cyan-700 font-bold">DEV-WEAR-001</span>
                </div>
              </div>

              <button
                type="button"
                onClick={() => {
                  setPatientIdInput(regSuccessData.patient_id);
                  setEmail(regSuccessData.patient_id);
                  setPatientMode('login');
                  setRegSuccessData(null);
                }}
                className="w-full py-2.5 bg-gradient-to-r from-[#1864ab] to-[#0284c7] hover:from-[#155490] hover:to-[#0369a1] text-white text-xs font-bold rounded-xl shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
              >
                Proceed to Login with Patient ID
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          ) : selectedRole === 'patient' && patientMode === 'register' ? (
            /* VIEW 2: NEW PATIENT REGISTRATION FORM */
            <form onSubmit={(e) => handleRegisterSubmit(e, false)} className="space-y-3 my-2 max-w-md mx-auto w-full text-xs">
              {regError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{regError}</span>
                </div>
              )}

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Patient Full Name *</label>
                <div className="relative flex items-center">
                  <User className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  <input
                    type="text"
                    value={regFullName}
                    onChange={(e) => setRegFullName(e.target.value)}
                    placeholder="e.g. Ramesh Kumar"
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Date of Birth</label>
                  <div className="relative flex items-center">
                    <Calendar className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                    <input
                      type="date"
                      value={regDob}
                      onChange={(e) => setRegDob(e.target.value)}
                      className="w-full pl-9 pr-2 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none text-slate-700"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Gender</label>
                  <select
                    value={regGender}
                    onChange={(e) => setRegGender(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none text-slate-700"
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Contact Number *</label>
                  <div className="relative flex items-center">
                    <Phone className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                    <input
                      type="tel"
                      value={regContact}
                      onChange={(e) => setRegContact(e.target.value)}
                      placeholder="+91 9876543210"
                      className="w-full pl-9 pr-2 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Emergency Contact</label>
                  <input
                    type="tel"
                    value={regEmergencyContact}
                    onChange={(e) => setRegEmergencyContact(e.target.value)}
                    placeholder="Caregiver Phone"
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-slate-700 font-semibold">Family / Caretaker Email *</label>
                  <span className="text-[10px] text-sky-600 font-medium">Multiple patients under one family</span>
                </div>
                <div className="relative flex items-center">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  <input
                    type="email"
                    value={regFamilyEmail}
                    onChange={(e) => setRegFamilyEmail(e.target.value)}
                    placeholder="family.care@pulseguardian.ai"
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">
                  Individual Email ID <span className="text-slate-400 font-normal">(Optional)</span>
                </label>
                <input
                  type="email"
                  value={regIndividualEmail}
                  onChange={(e) => setRegIndividualEmail(e.target.value)}
                  placeholder="patient.personal@gmail.com (leave blank if none)"
                  className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-semibold mb-1">Residential Address</label>
                <div className="relative flex items-center">
                  <Home className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                  <input
                    type="text"
                    value={regAddress}
                    onChange={(e) => setRegAddress(e.target.value)}
                    placeholder="City, State, Zip"
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Password *</label>
                  <div className="relative flex items-center">
                    <Lock className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                    <input
                      type={showRegPassword ? 'text' : 'password'}
                      value={regPassword}
                      onChange={(e) => setRegPassword(e.target.value)}
                      placeholder="Min. 6 chars"
                      className="w-full pl-9 pr-8 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowRegPassword(!showRegPassword)}
                      className="absolute right-2 text-slate-400 hover:text-slate-600"
                    >
                      {showRegPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-slate-700 font-semibold mb-1">Confirm Password *</label>
                  <input
                    type={showRegPassword ? 'text' : 'password'}
                    value={regConfirmPassword}
                    onChange={(e) => setRegConfirmPassword(e.target.value)}
                    placeholder="Re-enter password"
                    className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={regLoading}
                className="w-full mt-2 py-3 px-4 bg-gradient-to-r from-[#1864ab] via-[#0284c7] to-[#10b981] hover:from-[#155490] hover:to-[#059669] text-white text-xs sm:text-sm font-bold rounded-xl shadow-lg transition-all cursor-pointer disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {regLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Generating Patient ID & Registering...</span>
                  </>
                ) : (
                  <>
                    <UserPlus className="w-4 h-4" />
                    <span>Complete Patient Registration</span>
                  </>
                )}
              </button>
            </form>
          ) : selectedRole === 'patient' && patientMode === 'forgot_id' ? (
            /* VIEW 3: FORGOT PATIENT ID RECOVERY */
            <div className="space-y-4 my-2 max-w-md mx-auto w-full text-xs">
              <div className="bg-sky-50 border border-sky-200 p-3.5 rounded-xl text-slate-700">
                <div className="font-bold text-sky-900 flex items-center gap-1.5 mb-1">
                  <KeyRound className="w-4 h-4 text-sky-600" />
                  Forgot Patient ID Recovery
                </div>
                <p className="text-[11px] text-slate-600">
                  Enter your registered family email or contact phone number. We will send an instant 6-digit OTP verification code to retrieve all Patient IDs linked to your family account.
                </p>
              </div>

              {forgotError && (
                <div className="p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{forgotError}</span>
                </div>
              )}

              {!forgotOtpSent ? (
                <form onSubmit={handleRequestForgotOtp} className="space-y-3">
                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Family Email or Registered Phone</label>
                    <div className="relative flex items-center">
                      <Mail className="w-4 h-4 text-slate-400 absolute left-3 pointer-events-none" />
                      <input
                        type="text"
                        value={forgotRecoveryContact}
                        onChange={(e) => setForgotRecoveryContact(e.target.value)}
                        placeholder="e.g. family.care@pulseguardian.ai or +91 9876543210"
                        className="w-full pl-9 pr-3 py-2.5 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none"
                        required
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={forgotLoading}
                    className="w-full py-2.5 bg-[#1864ab] hover:bg-[#155490] text-white font-bold rounded-xl shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
                  >
                    {forgotLoading ? 'Sending Verification Code...' : 'Send 6-Digit OTP Code'}
                  </button>
                </form>
              ) : forgotRecoveredPatients.length === 0 ? (
                <form onSubmit={handleVerifyForgotOtp} className="space-y-3">
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-[11px]">
                    Verification OTP code dispatched to <strong className="font-semibold">{forgotRecoveryContact}</strong>.
                    {forgotDemoOtp && (
                      <div className="mt-1 font-mono font-bold text-emerald-900">
                        Demo Instant OTP: {forgotDemoOtp}
                      </div>
                    )}
                  </div>

                  <div>
                    <label className="block text-slate-700 font-semibold mb-1">Enter 6-Digit OTP Code</label>
                    <input
                      type="text"
                      maxLength={6}
                      value={forgotOtpCode}
                      onChange={(e) => setForgotOtpCode(e.target.value)}
                      placeholder="Enter 6-digit OTP"
                      className="w-full px-3 py-2 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-[#0284c7] focus:outline-none text-center font-mono text-base tracking-widest font-bold"
                      required
                    />
                  </div>

                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => setForgotOtpSent(false)}
                      className="w-1/3 py-2 border border-slate-300 text-slate-600 rounded-xl font-semibold hover:bg-slate-50 cursor-pointer"
                    >
                      Back
                    </button>
                    <button
                      type="submit"
                      disabled={forgotLoading}
                      className="w-2/3 py-2 bg-[#0284c7] hover:bg-[#0369a1] text-white font-bold rounded-xl shadow-md transition-all cursor-pointer flex items-center justify-center gap-2"
                    >
                      {forgotLoading ? 'Verifying...' : 'Verify OTP & Show IDs'}
                    </button>
                  </div>
                </form>
              ) : (
                <div className="space-y-3">
                  <div className="text-xs font-bold text-slate-800">
                    Found {forgotRecoveredPatients.length} Patient Profile(s) under this family account:
                  </div>

                  <div className="text-[11px] text-slate-500 bg-sky-50 p-2.5 rounded-xl border border-sky-100">
                    <span className="font-semibold text-sky-800">Authorized Patient Selection: </span>
                    Showing only patient profiles you are authorized to manage under verified email <strong>{forgotRecoveryContact}</strong>. Distinguishing biographical details are shown below.
                  </div>

                  {forgotRecoveredPatients.map((pat) => (
                    <div
                      key={pat.patient_id}
                      className="p-3.5 bg-white border border-slate-200 rounded-2xl shadow-sm hover:border-sky-400 transition-all space-y-2"
                    >
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="text-sm font-bold text-slate-900 flex items-center gap-2">
                            {pat.patient_name}
                            {pat.relationship_role && (
                              <span className="text-[10px] font-medium bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                                {pat.relationship_role}
                              </span>
                            )}
                          </div>
                          <div className="text-xs font-mono font-bold text-sky-700">{pat.patient_id}</div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleSelectRecoveredPatient(pat.patient_id)}
                          className="px-3.5 py-1.5 bg-gradient-to-r from-sky-600 to-teal-600 hover:from-sky-700 hover:to-teal-700 text-white rounded-xl text-xs font-bold shadow-sm transition-all cursor-pointer flex items-center gap-1.5"
                        >
                          Select & Sign In
                        </button>
                      </div>

                      {/* Distinguishing Characteristics to Disambiguate Identical Names */}
                      <div className="grid grid-cols-2 gap-2 text-[10px] text-slate-500 bg-slate-50 p-2 rounded-xl border border-slate-100">
                        <div>
                          <span className="text-slate-400">Date of Birth: </span>
                          <strong className="text-slate-700">{pat.date_of_birth || 'Not recorded'}</strong>
                          {pat.age !== undefined && pat.age !== null && (
                            <span className="ml-1 text-slate-500">({pat.age} yrs)</span>
                          )}
                        </div>
                        <div>
                          <span className="text-slate-400">Gender / Blood: </span>
                          <strong className="text-slate-700">{pat.gender || 'N/A'}</strong>
                          {pat.blood_group && <span className="ml-1">| {pat.blood_group}</span>}
                        </div>
                        <div>
                          <span className="text-slate-400">Linked Phone: </span>
                          <span className="font-mono text-slate-700">{pat.masked_contact}</span>
                        </div>
                        <div>
                          <span className="text-slate-400">Wearable Device: </span>
                          <span className="font-mono text-slate-700">{pat.device_uuid || 'DEV-WEAR-001'}</span>
                        </div>
                      </div>
                    </div>
                  ))}

                  <button
                    type="button"
                    onClick={() => {
                      setPatientMode('login');
                      setForgotOtpSent(false);
                      setForgotRecoveredPatients([]);
                    }}
                    className="w-full py-2 text-slate-500 hover:text-slate-800 text-xs font-semibold cursor-pointer"
                  >
                    Return to Login
                  </button>
                </div>
              )}
            </div>
          ) : (
            /* VIEW 4: DEFAULT LOGIN FORM */
            <form onSubmit={handleLogin} className="space-y-4 my-2 max-w-md mx-auto w-full">
              <div>
                <label className="block text-slate-700 font-semibold text-xs mb-1">
                  {selectedRole === 'patient' ? 'Unique Patient ID or Email' : t('auth.emailAddress', 'Email Address')}
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                    {selectedRole === 'patient' ? <KeyRound className="w-4 h-4 text-cyan-600" /> : <Mail className="w-4 h-4" />}
                  </div>
                  <input
                    type="text"
                    value={selectedRole === 'patient' ? patientIdInput : email}
                    onChange={(e) => {
                      if (selectedRole === 'patient') {
                        setPatientIdInput(e.target.value);
                        setEmail(e.target.value);
                      } else {
                        setEmail(e.target.value);
                      }
                    }}
                    placeholder={selectedRole === 'patient' ? 'e.g. PT-2026-000001 or patient@pulseguardian.ai' : t('auth.emailAddress', 'Email Address')}
                    className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0284c7] focus:border-transparent transition-all"
                    required
                  />
                </div>
                {selectedRole === 'patient' && (
                  <p className="text-[10px] text-slate-400 mt-1">
                    Enter your permanent <strong className="text-slate-600 font-mono">PT-2026-XXXXXX</strong> ID or registered email.
                  </p>
                )}
              </div>

              <div>
                <label className="block text-slate-700 font-semibold text-xs mb-1">
                  {t('auth.password', 'Password')}
                </label>
                <div className="relative flex items-center">
                  <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                    <Lock className="w-4 h-4" />
                  </div>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={t('auth.password', 'Password')}
                    className="w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0284c7] focus:border-transparent transition-all"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 text-slate-400 hover:text-slate-600 focus:outline-none cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between text-xs pt-0.5">
                <label className="flex items-center gap-2 cursor-pointer select-none text-slate-600">
                  <input
                    type="checkbox"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                    className="w-4 h-4 rounded border-slate-300 text-[#0284c7] focus:ring-[#0284c7] cursor-pointer"
                  />
                  <span>{t('auth.rememberDevice', 'Remember this device')}</span>
                </label>
                <button
                  type="button"
                  onClick={() => {
                    if (selectedRole === 'patient') {
                      setPatientMode('forgot_id');
                    } else {
                      setShowForgotModal(true);
                    }
                  }}
                  className="text-xs text-slate-500 hover:text-[#0284c7] font-medium transition-colors"
                >
                  {selectedRole === 'patient' ? 'Forgot Patient ID?' : t('auth.forgotPassword', 'Forgot Password?')}
                </button>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3 px-4 bg-gradient-to-r from-[#1864ab] via-[#0284c7] to-[#10b981] hover:from-[#155490] hover:to-[#059669] text-white text-xs sm:text-sm font-bold rounded-xl shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] cursor-pointer disabled:opacity-50"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>{t('auth.signingIn', 'Signing In...')}</span>
                  </>
                ) : (
                  <>
                    <div className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                      <ArrowRight className="w-3 h-3 text-white" />
                    </div>
                    <span>{t('auth.login', 'Sign In')}</span>
                  </>
                )}
              </button>
            </form>
          )}

          {/* Social Login Separator */}
          <div className="relative my-4 max-w-md mx-auto w-full">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-white text-slate-400 font-medium">{t('auth.or', 'or')}</span>
            </div>
          </div>

          {/* Social Login Buttons */}
          <div className="space-y-2.5 max-w-md mx-auto w-full">
            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleOpenSocialModal('google')}
              className="w-full py-2.5 px-4 bg-white border border-slate-200 hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
              {t('auth.continueWithGoogle', 'Continue with Google')}
            </button>

            <button
              type="button"
              disabled={isLoading}
              onClick={() => handleOpenSocialModal('microsoft')}
              className="w-full py-2.5 px-4 bg-white border border-slate-200 hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <svg className="w-4 h-4" viewBox="0 0 23 23">
                <path fill="#f35325" d="M1 1h10v10H1z" />
                <path fill="#81bc06" d="M12 1h10v10H12z" />
                <path fill="#05a6f0" d="M1 12h10v10H1z" />
                <path fill="#ffba08" d="M12 12h10v10H1z" />
              </svg>
              {t('auth.continueWithMicrosoft', 'Continue with Microsoft')}
            </button>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-center space-y-1">
            <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-400 font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
              <span>{t('auth.encryptedNotice', 'Your data is protected with 256-bit encryption')}</span>
            </div>
            <p className="text-[10px] text-slate-400 leading-tight">
              {t('auth.medicalDisclaimer', 'Not a medical diagnosis. For assistive health monitoring only.')}
            </p>
          </div>
        </div>
      </div>

      {/* Duplicate Patient Detected Confirmation Modal */}
      {duplicateWarning.isOpen && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-amber-200 animate-in fade-in zoom-in-95">
            <div className="w-12 h-12 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900 text-center mb-1">
              Possible Existing Patient Detected
            </h3>
            <p className="text-xs text-slate-600 text-center mb-4">
              {duplicateWarning.message}
            </p>

            <div className="bg-amber-50 border border-amber-200 p-3 rounded-xl text-xs space-y-1 text-amber-900 mb-4">
              <div className="font-semibold">Matching Record Details:</div>
              <div>Name: <span className="font-bold">{duplicateWarning.matchedName}</span></div>
              <div>Patient ID: <span className="font-mono font-bold text-sky-700">{duplicateWarning.matchedId}</span></div>
            </div>

            <p className="text-[11px] text-slate-500 text-center mb-4">
              Is this the same patient returning, or a new family member with the same name?
            </p>

            <div className="space-y-2">
              <button
                type="button"
                onClick={() => {
                  if (duplicateWarning.matchedId) {
                    setPatientIdInput(duplicateWarning.matchedId);
                    setEmail(duplicateWarning.matchedId);
                  }
                  setDuplicateWarning({ isOpen: false, message: '' });
                  setPatientMode('login');
                }}
                className="w-full py-2.5 bg-[#1864ab] hover:bg-[#155490] text-white font-bold rounded-xl text-xs cursor-pointer shadow-md"
              >
                Log in as Existing Patient
              </button>
              <button
                type="button"
                onClick={(e) => handleRegisterSubmit(e, true)}
                className="w-full py-2 border border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold rounded-xl text-xs cursor-pointer"
              >
                Continue Registering as Separate New Patient
              </button>
              <button
                type="button"
                onClick={() => setDuplicateWarning({ isOpen: false, message: '' })}
                className="w-full py-1.5 text-slate-400 hover:text-slate-600 text-xs font-medium cursor-pointer"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Social Provider Account Chooser & Password Verification Modal */}
      {socialModalProvider && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2">
                {socialModalProvider === 'google' ? (
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" viewBox="0 0 23 23">
                    <path fill="#f35325" d="M1 1h10v10H1z" />
                    <path fill="#81bc06" d="M12 1h10v10H12z" />
                    <path fill="#05a6f0" d="M1 12h10v10H1z" />
                    <path fill="#ffba08" d="M12 12h10v10H1z" />
                  </svg>
                )}
                <span className="text-sm font-bold text-slate-800 capitalize">
                  {socialModalProvider} Sign-In
                </span>
              </div>
              <button
                type="button"
                onClick={() => setSocialModalProvider(null)}
                className="text-slate-400 hover:text-slate-600 rounded-lg p-1 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {socialPasswordError && (
              <div className="mb-3 p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
                <AlertCircle className="w-3.5 h-3.5 shrink-0" />
                <span>{socialPasswordError}</span>
              </div>
            )}

            {socialStep === 'choose_account' && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-slate-700">{t('auth.chooseAccount', 'Choose an account')}</p>
                <div className="space-y-2">
                  {[
                    {
                      email: selectedRole === 'patient' ? 'patient@pulseguardian.ai' : 'caregiver@pulseguardian.ai',
                      name: selectedRole === 'patient' ? 'Ramesh Kumar (Patient)' : 'Dr. Ananya Sharma (Caregiver)',
                    },
                    {
                      email: 'demo.user@gmail.com',
                      name: 'Demo Healthcare Profile',
                    },
                  ].map((acc) => (
                    <button
                      key={acc.email}
                      type="button"
                      onClick={() => handleSelectSocialAccount(acc)}
                      className="w-full p-3 rounded-xl border border-slate-200 hover:border-cyan-500 hover:bg-cyan-50/30 flex items-center gap-3 transition-all text-left cursor-pointer group"
                    >
                      <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-600 to-teal-500 text-white flex items-center justify-center font-bold text-xs uppercase shadow-sm">
                        {acc.name.charAt(0)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-xs font-bold text-slate-800 truncate group-hover:text-cyan-700">
                          {acc.name}
                        </div>
                        <div className="text-[11px] text-slate-400 truncate">{acc.email}</div>
                      </div>
                      <ArrowRight className="w-3.5 h-3.5 text-slate-300 group-hover:text-cyan-600 transition-colors" />
                    </button>
                  ))}

                  {!showCustomEmailInput ? (
                    <button
                      type="button"
                      onClick={() => setShowCustomEmailInput(true)}
                      className="w-full p-2.5 rounded-xl border border-dashed border-slate-300 hover:border-slate-400 text-slate-500 text-xs font-medium flex items-center justify-center gap-2 hover:bg-slate-50 transition-all cursor-pointer"
                    >
                      <Plus className="w-3.5 h-3.5" />
                      <span>{t('auth.useAnotherAccount', 'Use another account')}</span>
                    </button>
                  ) : (
                    <form onSubmit={handleConfirmCustomEmail} className="pt-2 space-y-2">
                      <label className="text-[11px] font-semibold text-slate-600">
                        {socialModalProvider === 'google' ? 'Google' : 'Microsoft'} {t('auth.emailAddress', 'Email Address')}:
                      </label>
                      <div className="flex gap-2">
                        <input
                          type="email"
                          value={customSocialEmail}
                          onChange={(e) => setCustomSocialEmail(e.target.value)}
                          placeholder="yourname@gmail.com"
                          className="flex-1 px-3 py-2 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                          autoFocus
                          required
                        />
                        <button
                          type="submit"
                          className="px-3 py-2 bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold rounded-xl cursor-pointer"
                        >
                          Next
                        </button>
                      </div>
                    </form>
                  )}
                </div>
              </div>
            )}

            {socialStep === 'enter_password' && selectedSocialAccount && (
              <form onSubmit={handleVerifyAndCompleteSocialLogin} className="space-y-4">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-7 h-7 rounded-full bg-cyan-600 text-white flex items-center justify-center font-bold text-xs uppercase">
                      {selectedSocialAccount.name.charAt(0)}
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-bold text-slate-800 truncate">{selectedSocialAccount.name}</div>
                      <div className="text-[10px] text-slate-400 truncate">{selectedSocialAccount.email}</div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSocialStep('choose_account');
                      setSocialPassword('');
                    }}
                    className="text-[11px] text-cyan-600 hover:text-cyan-800 font-semibold cursor-pointer"
                  >
                    {t('auth.change', 'Change')}
                  </button>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">
                    {t('auth.enterPasswordFor', 'Enter password for')} {selectedSocialAccount.email}
                  </label>
                  <div className="relative flex items-center">
                    <div className="absolute left-3 text-slate-400 pointer-events-none">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type="password"
                      value={socialPassword}
                      onChange={(e) => setSocialPassword(e.target.value)}
                      placeholder={t('auth.password', 'Password')}
                      className="w-full pl-9 pr-3.5 py-2.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      required
                      autoFocus
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Demo credentials: <strong className="text-slate-600">Patient@123</strong> ({t('role.patient', 'Patient')}) or <strong className="text-slate-600">Caregiver@123</strong> ({t('role.caregiver', 'Caregiver')})
                  </p>
                </div>

                <div className="flex items-center justify-between pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setSocialStep('choose_account');
                      setSocialPassword('');
                      setSocialPasswordError(null);
                    }}
                    className="text-xs text-slate-500 hover:text-slate-700 font-medium cursor-pointer"
                  >
                    {t('auth.back', 'Back')}
                  </button>
                  <button
                    type="submit"
                    disabled={isVerifyingSocial}
                    className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700 text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-md disabled:opacity-50 transition-all cursor-pointer"
                  >
                    {isVerifyingSocial ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        {t('auth.verifying', 'Verifying...')}
                      </>
                    ) : (
                      <>
                        {t('auth.verifyAndSignIn', 'Verify & Sign In')}
                        <ArrowRight className="w-3.5 h-3.5" />
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}

      {/* Forgot Password Modal */}
      {showForgotModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <h3 className="text-lg font-bold text-slate-900 mb-2">Reset Password</h3>
            <p className="text-xs text-slate-500 mb-4">
              Enter your account email. We will generate an instant temporary reset token for verification.
            </p>

            {forgotSuccess ? (
              <div className="bg-emerald-50 text-emerald-800 p-3 rounded-xl text-xs mb-4">
                {forgotSuccess}
              </div>
            ) : (
              <div className="space-y-3">
                <input
                  type="email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  placeholder="Enter your registered email"
                  className="w-full px-3.5 py-2.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-[#0284c7]"
                />
                <button
                  type="button"
                  onClick={() => {
                    setForgotSuccess('A password reset token has been dispatched. For local demo, use Patient@123 to sign in.');
                    setTimeout(() => {
                      setShowForgotModal(false);
                      setForgotSuccess(null);
                    }, 2500);
                  }}
                  className="w-full py-2.5 bg-[#1864ab] text-white rounded-xl text-xs font-bold hover:bg-[#155490] cursor-pointer"
                >
                  Send Reset Link
                </button>
              </div>
            )}

            <button
              type="button"
              onClick={() => setShowForgotModal(false)}
              className="mt-3 text-xs text-slate-400 hover:text-slate-600 block mx-auto font-medium cursor-pointer"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
