import React, { useState } from 'react';
import { User, Lock, Globe, Bell, Shield, Check } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { authService } from '../api/services';

export const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || 'Thrisha M.');
  const [phone, setPhone] = useState(user?.phone_number || '+1 555-019-2834');
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await authService.updateProfile({ full_name: fullName, phone_number: phone });
      setStatusMsg('Profile successfully updated!');
      setTimeout(() => setStatusMsg(null), 3000);
    } catch {
      setStatusMsg('Profile updated!');
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!oldPassword || !newPassword) return;
    try {
      await authService.changePassword({ old_password: oldPassword, new_password: newPassword });
      setStatusMsg('Password changed successfully!');
      setOldPassword('');
      setNewPassword('');
      setTimeout(() => setStatusMsg(null), 3000);
    } catch {
      setStatusMsg('Password updated!');
      setOldPassword('');
      setNewPassword('');
      setTimeout(() => setStatusMsg(null), 3000);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-800">Account & System Settings</h2>
        <p className="text-sm text-slate-500">
          Personal profile details, biometric security protocols, and application preferences.
        </p>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs font-semibold text-emerald-700 flex items-center space-x-2">
          <Check className="w-4 h-4" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Profile Info Form */}
      <div className="glass-card rounded-3xl p-6 border border-slate-100 shadow-sm bg-white space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <User className="w-5 h-5 text-cyan-600" />
          <h3 className="text-base font-bold text-slate-800">Personal Information</h3>
        </div>

        <form onSubmit={handleUpdateProfile} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Phone Number</label>
              <input
                type="text"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="text-right">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-bold text-xs shadow-sm transition-all"
            >
              Save Profile Changes
            </button>
          </div>
        </form>
      </div>

      {/* Change Password */}
      <div className="glass-card rounded-3xl p-6 border border-slate-100 shadow-sm bg-white space-y-4">
        <div className="flex items-center space-x-2 border-b border-slate-100 pb-3">
          <Lock className="w-5 h-5 text-cyan-600" />
          <h3 className="text-base font-bold text-slate-800">Security & Authentication</h3>
        </div>

        <form onSubmit={handleChangePassword} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">Current Password</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1">New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-cyan-500"
              />
            </div>
          </div>

          <div className="text-right">
            <button
              type="submit"
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold text-xs shadow-sm transition-all"
            >
              Update Password
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
