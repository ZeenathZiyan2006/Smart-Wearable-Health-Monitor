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
  const [selectedSocialAccount, setSelectedSocialAccount] = useState<{ email: string; name: string; avatar?: string } | null>(null);
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

  const handleSelectSocialAccount = (acc: { email: string; name: string; avatar?: string }) => {
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
    const name = customSocialEmail.split('@')[0].replace('.', ' ');
    const formattedName = name.charAt(0).toUpperCase() + name.slice(1);
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
          selectedSocialAccount.name
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
              <div className="w-7 h-7 rounded-full bg-sky-100 flex items-center justify-center text-sky-600">
                <Globe className="w-4 h-4 text-sky-600" />
              </div>
              <div className="text-left">
                <p className="text-[11px] font-bold text-slate-800 leading-tight">Multilingual</p>
                <p className="text-[10px] text-slate-500">Support</p>
              </div>
            </div>
          </div>

          {/* Bottom Curved Wave Ribbon: "Healthier Lives. A Safer Community." */}
          <div className="mt-6 -mx-6 -mb-6 sm:-mx-10 sm:-mb-10 lg:-mx-12 lg:-mb-12 bg-gradient-to-r from-[#02495d] via-[#04617b] to-[#0c3756] py-3.5 px-6 sm:px-10 flex items-center justify-between text-white shadow-inner">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-white/10 flex items-center justify-center border border-white/20">
                <ShieldCheck className="w-4 h-4 text-cyan-300" />
              </div>
              <div className="text-left">
                <p className="text-xs font-bold tracking-wide">Healthier Lives.</p>
                <p className="text-[11px] text-cyan-100/80">A Safer Community.</p>
              </div>
            </div>
            {/* Decorative Heartbeat ECG vector line */}
            <div className="hidden sm:flex items-center opacity-40">
              <svg width="120" height="24" viewBox="0 0 120 24" fill="none">
                <path d="M0 12H30L35 3L45 21L52 9L58 15L64 12H120" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </div>
        </div>

        {/* ======================================================== */}
        {/* RIGHT COLUMN: The Clean, High-Conversion Login Form Card */}
        {/* ======================================================== */}
        <div className="lg:w-1/2 p-6 sm:p-10 lg:p-14 flex flex-col justify-between bg-white">
          
          {/* Top Row: Language Picker Dropdown */}
          <div className="flex justify-end">
            <div className="relative inline-block text-left">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-slate-200 text-xs font-semibold text-slate-700 bg-slate-50/80 hover:bg-slate-100 transition-colors cursor-pointer">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={language}
                  onChange={(e) => setLanguage(e.target.value)}
                  className="bg-transparent border-none text-xs font-semibold focus:outline-none cursor-pointer pr-1"
                >
                  <option value="English">English</option>
                  <option value="Kannada">ಕನ್ನಡ (Kannada)</option>
                  <option value="Hindi">हिन्दी (Hindi)</option>
                  <option value="Malayalam">മലയാളം (Malayalam)</option>
                  <option value="Tamil">தமிழ் (Tamil)</option>
                  <option value="Telugu">తెలుగు (Telugu)</option>
                </select>
              </div>
            </div>
          </div>

          {/* Centered Brand Title & Subtitle */}
          <div className="text-center my-4">
            <div className="inline-flex items-center justify-center mb-2">
              <PulseGuardianLogo size="lg" showTagline={false} />
            </div>
            <p className="text-slate-500 text-sm font-medium mt-1">
              Login to your account
            </p>
          </div>

          {/* Role Switcher Tab: [ Patient | Caregiver ] */}
          <div className="bg-slate-100 p-1.5 rounded-full border border-slate-200/80 flex items-center max-w-md mx-auto w-full my-3">
            <button
              type="button"
              onClick={() => handleRoleSelect('patient')}
              className={`flex-1 py-2 px-4 rounded-full text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
                selectedRole === 'patient'
                  ? 'bg-[#1864ab] text-white shadow-md shadow-blue-900/20'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <User className="w-4 h-4" />
              Patient
            </button>
            <button
              type="button"
              onClick={() => handleRoleSelect('caregiver')}
              className={`flex-1 py-2 px-4 rounded-full text-xs sm:text-sm font-bold flex items-center justify-center gap-2 transition-all ${
                selectedRole === 'caregiver'
                  ? 'bg-[#1864ab] text-white shadow-md shadow-blue-900/20'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Users className="w-4 h-4" />
              Caregiver
            </button>
          </div>

          {/* Error Message Alert */}
          {errorMessage && (
            <div className="bg-rose-50 border border-rose-200 text-rose-700 px-4 py-2.5 rounded-xl text-xs flex items-center gap-2 my-2">
              <AlertCircle className="w-4 h-4 flex-shrink-0 text-rose-500" />
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
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Email Address"
                  className="w-full pl-10 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0284c7]/30 focus:border-[#0284c7] transition-all shadow-sm"
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
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  className="w-full pl-10 pr-11 py-3 bg-white border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0284c7]/30 focus:border-[#0284c7] transition-all shadow-sm"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 text-slate-400 hover:text-slate-600 focus:outline-none"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Remember Me & Forgot Password Row */}
            <div className="flex items-center justify-between text-xs pt-1">
              <label className="flex items-center gap-2 cursor-pointer text-slate-600 font-medium select-none">
                <div
                  onClick={() => setRememberMe(!rememberMe)}
                  className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${
                    rememberMe ? 'bg-[#1864ab] border-[#1864ab] text-white' : 'border-slate-300 bg-white'
                  }`}
                >
                  {rememberMe && <Check className="w-3 h-3 stroke-[3]" />}
                </div>
                Remember this device
              </label>

              <button
                type="button"
                onClick={() => setShowForgotModal(true)}
                className="text-[#1864ab] hover:text-[#0284c7] font-semibold transition-colors"
              >
                Forgot Password?
              </button>
            </div>

            {/* Submit Gradient Button: [ ➔ Sign In ] */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 px-6 rounded-xl font-bold text-white text-sm bg-gradient-to-r from-[#1864ab] via-[#0284c7] to-[#10b981] hover:opacity-95 shadow-lg shadow-blue-500/25 flex items-center justify-center gap-2 transition-all transform active:scale-[0.99] disabled:opacity-60 cursor-pointer"
            >
              {isLoading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <>
                  <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center">
                    <ArrowRight className="w-3.5 h-3.5 text-white" />
                  </div>
                  Sign In
                </>
              )}
            </button>
          </form>

          {/* Social Divider: "or" */}
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
              disabled={socialLoading !== null || isLoading}
              onClick={() => handleOpenSocialModal('google')}
              className="w-full py-2.5 px-4 bg-white border border-slate-200 hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {socialLoading === 'google' ? (
                <div className="w-4 h-4 border-2 border-slate-300 border-t-cyan-600 rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                </svg>
              )}
              {socialLoading === 'google' ? 'Connecting to Google...' : 'Continue with Google'}
            </button>

            {/* Microsoft */}
            <button
              type="button"
              disabled={socialLoading !== null || isLoading}
              onClick={() => handleOpenSocialModal('microsoft')}
              className="w-full py-2.5 px-4 bg-white border border-slate-200 hover:bg-slate-50 active:bg-slate-100 text-slate-700 text-xs font-semibold rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-sm cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {socialLoading === 'microsoft' ? (
                <div className="w-4 h-4 border-2 border-slate-300 border-t-cyan-600 rounded-full animate-spin" />
              ) : (
                <svg className="w-4 h-4" viewBox="0 0 23 23">
                  <path fill="#f35325" d="M1 1h10v10H1z" />
                  <path fill="#81bc06" d="M12 1h10v10H12z" />
                  <path fill="#05a6f0" d="M1 12h10v10H1z" />
                  <path fill="#ffba08" d="M12 12h10v10H12z" />
                </svg>
              )}
              {socialLoading === 'microsoft' ? 'Connecting to Microsoft...' : 'Continue with Microsoft'}
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
                  className="w-full py-2.5 bg-[#1864ab] text-white rounded-xl text-xs font-bold hover:bg-[#155490]"
                >
                  Send Reset Link
                </button>
              </div>
            )}

            <button
              type="button"
              onClick={() => setShowForgotModal(false)}
              className="mt-3 text-xs text-slate-400 hover:text-slate-600 block mx-auto font-medium"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
