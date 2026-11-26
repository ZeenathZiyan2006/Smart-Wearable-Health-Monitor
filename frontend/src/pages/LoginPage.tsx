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
  Info,
  Check,
  User,
  Users,
  AlertCircle,
  X,
  Plus
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { PulseGuardianLogo } from '../components/PulseGuardianLogo';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login, socialLogin, selectedRole, setSelectedRole } = useAuth();

  const [email, setEmail] = useState('patient@pulseguardian.ai');
  const [password, setPassword] = useState('Patient@123');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [language, setLanguage] = useState('English');
  const [isLoading, setIsLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState<'google' | 'microsoft' | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Social account chooser modal state
  const [socialModalProvider, setSocialModalProvider] = useState<'google' | 'microsoft' | null>(null);
  const [socialStep, setSocialStep] = useState<'choose_account' | 'enter_password'>('choose_account');
  const [selectedSocialAccount, setSelectedSocialAccount] = useState<{ email: string; name: string } | null>(null);
  const [socialPassword, setSocialPassword] = useState('');
  const [socialPasswordError, setSocialPasswordError] = useState<string | null>(null);
  const [isVerifyingSocial, setIsVerifyingSocial] = useState(false);
  const [customSocialEmail, setCustomSocialEmail] = useState('');
  const [showCustomEmailInput, setShowCustomEmailInput] = useState(false);

  // Forgot password modal state
  const [showForgotModal, setShowForgotModal] = useState(false);
  const [forgotEmail, setForgotEmail] = useState('');
  const [forgotSuccess, setForgotSuccess] = useState<string | null>(null);

  // Switch quick credentials based on role
  const handleRoleSelect = (role: 'patient' | 'caregiver') => {
    setSelectedRole(role);
    setErrorMessage(null);
    if (role === 'patient') {
      setEmail('patient@pulseguardian.ai');
      setPassword('Patient@123');
    } else {
      setEmail('caregiver@pulseguardian.ai');
      setPassword('Caregiver@123');
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    if (!email || !password) {
      setErrorMessage('Please provide both email and password.');
      return;
    }

    setIsLoading(true);
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      const detail = err.response?.data?.detail || 'Authentication failed. Please verify your credentials.';
      setErrorMessage(detail);
    } finally {
      setIsLoading(false);
    }
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
      const detail = err.response?.data?.detail || 'Authentication verification failed. Please try again.';
      setSocialPasswordError(detail);
    } finally {
      setIsVerifyingSocial(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#edf3f8] flex items-center justify-center p-3 sm:p-6 lg:p-10 font-sans">
      {/* Outer Card Container directly matching the supplied Login design */}
      <div className="bg-white rounded-[2rem] sm:rounded-[2.5rem] shadow-2xl border border-white/80 overflow-hidden flex flex-col lg:flex-row max-w-6xl w-full transition-all">
        
        {/* ======================================================== */}
        {/* LEFT COLUMN: Visual Brand Hero & Floating Feature Badges */}
        {/* ======================================================== */}
        <div className="lg:w-1/2 relative bg-gradient-to-b from-[#f2f7fa] via-[#e8f2f5] to-[#def0f5] p-6 sm:p-10 lg:p-12 flex flex-col justify-between overflow-hidden">
          {/* Top Logo */}
          <div className="z-10">
            <PulseGuardianLogo size="md" tagline="Smart Care. Safer Tomorrow." />
          </div>

          {/* Hero Typography */}
          <div className="my-6 z-10">
            <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-black tracking-tight leading-[1.15]">
              <span className="text-[#0f2942]">Your Health.</span>
              <br />
              <span className="text-[#0284c7]">Our Priority.</span>
            </h1>
            <p className="mt-3 text-slate-600 text-sm sm:text-base max-w-md font-medium leading-relaxed">
              Advanced wearable monitoring for a healthier, happier and safer life.
            </p>
          </div>

          {/* Hero Graphic: Indian Grandmother Patient and Doctor with Smart Watch */}
          <div className="relative w-full my-auto flex items-center justify-center min-h-[300px] sm:min-h-[360px]">
            {/* Background glowing circular spotlight */}
            <div className="absolute w-72 h-72 sm:w-88 sm:h-88 rounded-full bg-cyan-400/15 blur-3xl -z-0 pointer-events-none" />

            {/* Stylized Realistic Visual Mockup */}
            <div className="relative z-10 w-full max-w-md rounded-2xl overflow-hidden shadow-lg border border-white/60 bg-white/40 backdrop-blur-sm">
              <div className="relative aspect-[4/3] w-full bg-gradient-to-tr from-cyan-900/10 to-teal-500/10 flex items-center justify-center overflow-hidden">
                <img
                  src="/doctor-patient-hero.jpg"
                  alt="Confident smiling doctor and happy elderly patient wearing health monitoring smartwatch"
                  className="w-full h-full object-cover object-center filter brightness-[1.02]"
                />
                
                {/* Overlay Smart Watch Simulation on Patient's wrist */}
                <div className="absolute bottom-6 left-12 bg-black/85 text-white p-2 rounded-xl border border-cyan-400/40 shadow-xl flex items-center gap-2 backdrop-blur-md">
                  <Heart className="w-4 h-4 text-rose-500 fill-rose-500 animate-pulse" />
                  <div className="flex flex-col text-left">
                    <span className="text-[10px] text-cyan-300 font-semibold tracking-wider">PULSE</span>
                    <span className="text-xs font-black">72 BPM</span>
                  </div>
                </div>
              </div>
            </div>

            {/* 4 Floating Feature Pills Matching Image Reference */}
            {/* 1. Real-Time Health Monitoring */}
            <div className="absolute -top-1 left-2 sm:left-4 z-20 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-full shadow-lg border border-white/80 flex items-center gap-2.5 transform hover:-translate-y-0.5 transition-all">
              <div className="w-7 h-7 rounded-full bg-cyan-100 flex items-center justify-center text-cyan-600">
                <Heart className="w-4 h-4 fill-cyan-600" />
              </div>
              <div className="text-left">
                <p className="text-[11px] font-bold text-slate-800 leading-tight">Real-Time</p>
                <p className="text-[10px] text-slate-500">Health Monitoring</p>
              </div>
            </div>

            {/* 2. Emergency Alerts */}
            <div className="absolute top-20 left-0 sm:left-2 z-20 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-full shadow-lg border border-white/80 flex items-center gap-2.5 transform hover:-translate-y-0.5 transition-all">
              <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-blue-600">
                <Shield className="w-4 h-4 fill-blue-600" />
              </div>
              <div className="text-left">
                <p className="text-[11px] font-bold text-slate-800 leading-tight">Emergency</p>
                <p className="text-[10px] text-slate-500">Alerts</p>
              </div>
            </div>

            {/* 3. AI-Powered Insights */}
            <div className="absolute bottom-12 left-2 sm:left-4 z-20 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-full shadow-lg border border-white/80 flex items-center gap-2.5 transform hover:-translate-y-0.5 transition-all">
              <div className="w-7 h-7 rounded-full bg-teal-100 flex items-center justify-center text-teal-600">
                <Brain className="w-4 h-4 text-teal-600" />
              </div>
              <div className="text-left">
                <p className="text-[11px] font-bold text-slate-800 leading-tight">AI-Powered</p>
                <p className="text-[10px] text-slate-500">Insights</p>
              </div>
            </div>

            {/* 4. Multilingual Support */}
            <div className="absolute -bottom-2 right-4 sm:right-8 z-20 bg-white/90 backdrop-blur-md px-3.5 py-2 rounded-full shadow-lg border border-white/80 flex items-center gap-2.5 transform hover:-translate-y-0.5 transition-all">
              <div className="w-7 h-7 rounded-full bg-cyan-100 flex items-center justify-center text-cyan-600">
                <Globe className="w-4 h-4 text-cyan-600" />
              </div>
              <div className="text-left">
                <p className="text-[11px] font-bold text-slate-800 leading-tight">Multilingual</p>
                <p className="text-[10px] text-slate-500">Support</p>
              </div>
            </div>
          </div>

          {/* Bottom Trust Badge */}
          <div className="mt-6 pt-4 border-t border-cyan-800/10 flex items-center gap-3 z-10">
            <div className="w-8 h-8 rounded-full bg-cyan-600/10 flex items-center justify-center text-[#0284c7]">
              <ShieldCheck className="w-5 h-5 text-[#0284c7]" />
            </div>
            <div>
              <p className="text-xs font-bold text-[#0f2942]">Healthier Lives.</p>
              <p className="text-[11px] text-slate-500">A Safer Community.</p>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT COLUMN: Clean Login Authentication Form            */}
        {/* ======================================================== */}
        <div className="lg:w-1/2 p-6 sm:p-10 lg:p-12 flex flex-col justify-between bg-white">
          {/* Top Right Language Selector */}
          <div className="flex justify-end items-center gap-1.5">
            <div className="relative inline-block text-left">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200 text-xs font-medium text-slate-600 hover:bg-slate-50 cursor-pointer">
                <Globe className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-transparent border-none text-xs focus:outline-none cursor-pointer pr-1"
                >
                  <option value="English">English</option>
                  <option value="Tamil">தமிழ் (Tamil)</option>
                  <option value="Hindi">हिंदी (Hindi)</option>
                  <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Brand Header */}
          <div className="text-center my-4">
            <div className="flex justify-center mb-2">
              <PulseGuardianLogo size="md" showTagline={false} />
            </div>
            <p className="text-xs text-slate-500 mt-1 font-medium">Login to your account</p>
          </div>

          {/* Patient vs Caregiver Role Switcher Tabs */}
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
              Patient
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
              Caregiver
            </button>
          </div>

          {/* Error Banner */}
          {errorMessage && (
            <div className="max-w-md mx-auto w-full mb-3 p-3 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-rose-700 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* The Login Form */}
          <form onSubmit={handleLogin} className="space-y-4 my-2 max-w-md mx-auto w-full">
            {/* Email Input */}
            <div>
              <div className="relative flex items-center">
                <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                  <Mail className="w-4 h-4" />
                </div>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email Address"
                  className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0284c7] focus:border-transparent transition-all"
                  required
                />
              </div>
            </div>

            {/* Password Input */}
            <div>
              <div className="relative flex items-center">
                <div className="absolute left-3.5 text-slate-400 pointer-events-none">
                  <Lock className="w-4 h-4" />
                </div>
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
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

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between text-xs pt-0.5">
              <label className="flex items-center gap-2 cursor-pointer select-none text-slate-600">
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  className="w-4 h-4 rounded border-slate-300 text-[#0284c7] focus:ring-[#0284c7] cursor-pointer"
                />
                <span>Remember this device</span>
              </label>
              <button
                type="button"
                onClick={() => setShowForgotModal(true)}
                className="text-xs text-slate-500 hover:text-[#0284c7] font-medium transition-colors"
              >
                Forgot Password?
              </button>
            </div>

            {/* Main Sign In Button Matching Gradient in Design */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3 px-4 bg-gradient-to-r from-[#1864ab] via-[#0284c7] to-[#10b981] hover:from-[#155490] hover:to-[#059669] text-white text-xs sm:text-sm font-bold rounded-xl shadow-lg shadow-cyan-500/20 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] cursor-pointer disabled:opacity-50"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <div className="w-4 h-4 rounded-full bg-white/20 flex items-center justify-center">
                    <ArrowRight className="w-3 h-3 text-white" />
                  </div>
                  <span>Sign In</span>
                </>
              )}
            </button>
          </form>

          {/* Social Login Separator */}
          <div className="relative my-4 max-w-md mx-auto w-full">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-slate-200" />
            </div>
            <div className="relative flex justify-center text-xs">
              <span className="px-3 bg-white text-slate-400 font-medium">or</span>
            </div>
          </div>

          {/* Social Login Buttons Matching Reference */}
          <div className="space-y-2.5 max-w-md mx-auto w-full">
            {/* Google */}
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
              Continue with Google
            </button>

            {/* Microsoft */}
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
              Continue with Microsoft
            </button>
          </div>

          {/* Footer Encryption & Medical Disclaimers */}
          <div className="mt-6 pt-4 text-center border-t border-slate-100">
            <div className="flex items-center justify-center gap-1.5 text-[11px] font-semibold text-slate-600 mb-1">
              <ShieldCheck className="w-3.5 h-3.5 text-[#0284c7]" />
              Your data is protected with 256-bit encryption
            </div>
            <p className="text-[10px] text-slate-400 flex items-center justify-center gap-1">
              Not a medical diagnosis. For assistive health monitoring only.
              <Info className="w-3 h-3 text-slate-400 cursor-pointer" />
            </p>
          </div>
        </div>

      </div>

      {/* Interactive Google & Microsoft OAuth Account & Password Verification Dialog */}
      {socialModalProvider && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 relative animate-in zoom-in-95 duration-200">
            {/* Header with Provider Logo */}
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-4">
              <div className="flex items-center gap-2.5">
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
                <div>
                  <h3 className="text-sm font-bold text-slate-800">
                    Sign in with {socialModalProvider === 'google' ? 'Google' : 'Microsoft'}
                  </h3>
                  <p className="text-[11px] text-slate-400">to continue to PulseGuardian AI</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSocialModalProvider(null)}
                className="w-7 h-7 rounded-full text-slate-400 hover:text-slate-600 hover:bg-slate-100 flex items-center justify-center transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Error Message */}
            {socialPasswordError && (
              <div className="mb-4 p-2.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2 text-rose-700 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{socialPasswordError}</span>
              </div>
            )}

            {/* STEP 1: CHOOSE AN ACCOUNT */}
            {socialStep === 'choose_account' && (
              <div className="space-y-3">
                <p className="text-xs font-semibold text-slate-700">Choose an account</p>

                {/* Account 1: Ramesh Kumar (Patient) */}
                <button
                  type="button"
                  onClick={() => handleSelectSocialAccount({
                    email: 'patient@pulseguardian.ai',
                    name: 'Ramesh Kumar',
                  })}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:border-cyan-500 hover:bg-cyan-50/40 text-left transition-all group cursor-pointer"
                >
                  <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-cyan-600 to-teal-500 text-white font-bold text-xs flex items-center justify-center shadow-sm">
                    RK
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-800 group-hover:text-cyan-700 truncate">Ramesh Kumar</p>
                    <p className="text-[11px] text-slate-500 truncate">patient@pulseguardian.ai</p>
                  </div>
                  <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-medium">Patient</span>
                </button>

                {/* Account 2: Dr. Sunita Rao (Caregiver) */}
                <button
                  type="button"
                  onClick={() => handleSelectSocialAccount({
                    email: 'caregiver@pulseguardian.ai',
                    name: 'Dr. Sunita Rao',
                  })}
                  className="w-full flex items-center gap-3 p-3 rounded-xl border border-slate-200 hover:border-cyan-500 hover:bg-cyan-50/40 text-left transition-all group cursor-pointer"
                >
                  <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-500 text-white font-bold text-xs flex items-center justify-center shadow-sm">
                    SR
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-800 group-hover:text-cyan-700 truncate">Dr. Sunita Rao</p>
                    <p className="text-[11px] text-slate-500 truncate">caregiver@pulseguardian.ai</p>
                  </div>
                  <span className="text-[10px] bg-blue-50 text-blue-700 px-2 py-0.5 rounded font-medium">Caregiver</span>
                </button>

                {/* Custom Email Input Toggle */}
                {!showCustomEmailInput ? (
                  <button
                    type="button"
                    onClick={() => setShowCustomEmailInput(true)}
                    className="w-full flex items-center gap-3 p-3 rounded-xl border border-dashed border-slate-200 hover:border-slate-300 hover:bg-slate-50 text-left text-xs font-semibold text-slate-600 transition-colors cursor-pointer"
                  >
                    <div className="w-9 h-9 rounded-full bg-slate-100 text-slate-500 flex items-center justify-center">
                      <Plus className="w-4 h-4" />
                    </div>
                    <span>Use another {socialModalProvider === 'google' ? 'Google' : 'Microsoft'} account</span>
                  </button>
                ) : (
                  <form onSubmit={handleConfirmCustomEmail} className="space-y-2 p-3 bg-slate-50 rounded-xl border border-slate-200">
                    <label className="text-[11px] font-semibold text-slate-700 block">
                      Enter {socialModalProvider === 'google' ? 'Google' : 'Microsoft'} Email:
                    </label>
                    <input
                      type="email"
                      value={customSocialEmail}
                      onChange={(e) => setCustomSocialEmail(e.target.value)}
                      placeholder={socialModalProvider === 'google' ? 'user@gmail.com' : 'user@outlook.com'}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      required
                    />
                    <div className="flex justify-end gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => setShowCustomEmailInput(false)}
                        className="px-3 py-1.5 text-xs text-slate-500 hover:text-slate-700 cursor-pointer"
                      >
                        Cancel
                      </button>
                      <button
                        type="submit"
                        className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-700 text-white font-semibold text-xs rounded-lg cursor-pointer"
                      >
                        Next
                      </button>
                    </div>
                  </form>
                )}
              </div>
            )}

            {/* STEP 2: VERIFY PASSWORD */}
            {socialStep === 'enter_password' && selectedSocialAccount && (
              <form onSubmit={handleVerifyAndCompleteSocialLogin} className="space-y-4">
                {/* Selected Account Info */}
                <div className="flex items-center gap-3 p-2.5 bg-slate-50 rounded-xl border border-slate-200">
                  <div className="w-8 h-8 rounded-full bg-cyan-600 text-white font-bold text-xs flex items-center justify-center">
                    {selectedSocialAccount.name.slice(0, 2).toUpperCase()}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-bold text-slate-800 truncate">{selectedSocialAccount.name}</p>
                    <p className="text-[11px] text-slate-500 truncate">{selectedSocialAccount.email}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSocialStep('choose_account');
                      setSocialPassword('');
                      setSocialPasswordError(null);
                    }}
                    className="text-[11px] text-cyan-600 hover:underline font-semibold cursor-pointer"
                  >
                    Change
                  </button>
                </div>

                <div>
                  <label className="text-xs font-semibold text-slate-700 block mb-1.5">
                    Enter password for {selectedSocialAccount.email}
                  </label>
                  <div className="relative flex items-center">
                    <div className="absolute left-3 text-slate-400 pointer-events-none">
                      <Lock className="w-4 h-4" />
                    </div>
                    <input
                      type="password"
                      value={socialPassword}
                      onChange={(e) => setSocialPassword(e.target.value)}
                      placeholder="Account password (e.g. Patient@123)"
                      className="w-full pl-9 pr-3.5 py-2.5 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-cyan-500"
                      required
                      autoFocus
                    />
                  </div>
                  <p className="text-[10px] text-slate-400 mt-1">
                    Demo credentials: <strong className="text-slate-600">Patient@123</strong> (Patient) or <strong className="text-slate-600">Caregiver@123</strong> (Caregiver)
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
                    Back
                  </button>
                  <button
                    type="submit"
                    disabled={isVerifyingSocial}
                    className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700 text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-md disabled:opacity-50 transition-all cursor-pointer"
                  >
                    {isVerifyingSocial ? (
                      <>
                        <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        Verifying...
                      </>
                    ) : (
                      <>
                        Verify & Sign In
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
