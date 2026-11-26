import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import { LoginPage } from './pages/LoginPage';
import { DashboardLayout } from './layouts/DashboardLayout';

// Lazy load route pages for performance & code-splitting
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const HealthMonitorPage = lazy(() => import('./pages/HealthMonitorPage').then(m => ({ default: m.HealthMonitorPage })));
const ECGMonitorPage = lazy(() => import('./pages/ECGMonitorPage').then(m => ({ default: m.ECGMonitorPage })));
const SleepActivityPage = lazy(() => import('./pages/SleepActivityPage').then(m => ({ default: m.SleepActivityPage })));
const AIInsightsPage = lazy(() => import('./pages/AIInsightsPage').then(m => ({ default: m.AIInsightsPage })));
const GPSTrackingPage = lazy(() => import('./pages/GPSTrackingPage').then(m => ({ default: m.GPSTrackingPage })));
const EmergencySOSPage = lazy(() => import('./pages/EmergencySOSPage').then(m => ({ default: m.EmergencySOSPage })));
const NotificationsPage = lazy(() => import('./pages/NotificationsPage').then(m => ({ default: m.NotificationsPage })));
const CommunicationPage = lazy(() => import('./pages/CommunicationPage').then(m => ({ default: m.CommunicationPage })));
const HealthHistoryPage = lazy(() => import('./pages/HealthHistoryPage').then(m => ({ default: m.HealthHistoryPage })));
const DevicesPage = lazy(() => import('./pages/DevicesPage').then(m => ({ default: m.DevicesPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));

// Page Loading Fallback Spinner
const PageFallback: React.FC = () => (
  <div className="min-h-[50vh] flex items-center justify-center">
    <div className="flex flex-col items-center space-y-2">
      <div className="w-8 h-8 border-3 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-xs text-slate-500 font-medium">Loading view...</span>
    </div>
  </div>
);

// Protected Route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactElement }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#F0F5FA] flex items-center justify-center">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-10 h-10 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs font-semibold text-slate-500">Authenticating PulseGuardian AI...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <BrowserRouter>
          <Suspense fallback={<PageFallback />}>
            <Routes>
              {/* Public Authentication Route */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected Application Routes */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="health" element={<HealthMonitorPage />} />
                <Route path="ecg" element={<ECGMonitorPage />} />
                <Route path="sleep-activity" element={<SleepActivityPage />} />
                <Route path="ai-insights" element={<AIInsightsPage />} />
                <Route path="gps" element={<GPSTrackingPage />} />
                <Route path="emergency" element={<EmergencySOSPage />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="communication" element={<CommunicationPage />} />
                <Route path="history" element={<HealthHistoryPage />} />
                <Route path="devices" element={<DevicesPage />} />
                <Route path="settings" element={<SettingsPage />} />
              </Route>

              {/* Catch-all */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </WebSocketProvider>
    </AuthProvider>
  );
};

export default App;
