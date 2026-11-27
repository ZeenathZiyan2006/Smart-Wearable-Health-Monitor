import { apiClient } from './client';
import type {
  AuthResponse,
  DashboardSummary,
  Device,
  DigitalTwinBaseline,
  EmergencyAlert,
  InAppNotification,
  TelemetryReading,
  User,
  VoiceMessage,
  DigitalDocument,
  EmergencyQRProfile,
  EmergencyQRPublicView,
} from './types';

// ==========================================
// 1. Authentication & Profile APIs
// ==========================================
export const authApi = {
  login: async (credentials: { email: string; password: string }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/login', credentials);
    return res.data;
  },

  socialLogin: async (payload: { provider: 'google' | 'microsoft'; role?: string; email?: string; password?: string; full_name?: string }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/auth/social-login', payload);
    return res.data;
  },

  register: async (payload: any): Promise<User> => {
    const res = await apiClient.post<User>('/auth/register', payload);
    return res.data;
  },

  getMe: async (): Promise<User> => {
    const res = await apiClient.get<User>('/auth/me');
    return res.data;
  },

  updateMe: async (updates: { full_name?: string; phone_number?: string; preferred_language?: string }): Promise<User> => {
    const res = await apiClient.put<User>('/auth/me', updates);
    return res.data;
  },

  changePassword: async (passwords: { old_password: string; new_password: string }): Promise<{ message: string }> => {
    const res = await apiClient.post<{ message: string }>('/auth/change-password', passwords);
    return res.data;
  },

  logout: async (): Promise<{ message: string }> => {
    const res = await apiClient.post<{ message: string }>('/auth/logout');
    return res.data;
  },

  forgotPassword: async (email: string): Promise<{ message: string; reset_token?: string }> => {
    const res = await apiClient.post('/auth/forgot-password', { email });
    return res.data;
  },

  resetPassword: async (token: string, new_password: string): Promise<{ message: string }> => {
    const res = await apiClient.post('/auth/reset-password', { token, new_password });
    return res.data;
  },
};

// ==========================================
// 2. Health & Telemetry APIs
// ==========================================
export const healthApi = {
  getDashboard: async (patientId?: number): Promise<DashboardSummary> => {
    const url = patientId ? `/health/patients/${patientId}/dashboard` : '/health/dashboard';
    const res = await apiClient.get<DashboardSummary>(url);
    return res.data;
  },

  getLatest: async (patientId?: number): Promise<TelemetryReading> => {
    const url = patientId ? `/health/patients/${patientId}/latest` : '/health/latest';
    const res = await apiClient.get<TelemetryReading>(url);
    return res.data;
  },

  getHistory: async (patientId?: number, limit = 50): Promise<TelemetryReading[]> => {
    const url = patientId ? `/health/patients/${patientId}/history` : '/health/history';
    const res = await apiClient.get<TelemetryReading[]>(url, { params: { limit } });
    return res.data;
  },

  getDailyReport: async (patientId?: number, date?: string): Promise<any> => {
    const url = patientId ? `/health/patients/${patientId}/reports/daily` : '/health/reports/daily';
    const res = await apiClient.get(url, { params: { date } });
    return res.data;
  },

  getWeeklyReport: async (patientId?: number): Promise<any> => {
    const url = patientId ? `/health/patients/${patientId}/reports/weekly` : '/health/reports/weekly';
    const res = await apiClient.get(url);
    return res.data;
  },

  getDeviceStatus: async (patientId?: number): Promise<any> => {
    const res = await apiClient.get('/health/device-status', { params: { patient_id: patientId } });
    return res.data;
  },

  ingestTelemetry: async (telemetry: Partial<TelemetryReading>): Promise<TelemetryReading> => {
    const res = await apiClient.post<TelemetryReading>('/health/telemetry', telemetry);
    return res.data;
  },

  exportRecords: async (patientId?: number, format = 'csv', days = 30): Promise<Blob | any> => {
    const url = patientId ? `/health/patients/${patientId}/reports/export` : '/health/reports/export';
    const res = await apiClient.get(url, {
      params: { format, days },
      responseType: format === 'csv' ? 'blob' : 'json',
    });
    return res.data;
  },

  checkGeofence: async (params: { latitude: number; longitude: number; center_latitude?: number; center_longitude?: number; radius_meters?: number }): Promise<any> => {
    const res = await apiClient.post('/health/geofence/check', params);
    return res.data;
  },
};

// ==========================================
// 3. Wearable Device Management APIs
// ==========================================
export const deviceApi = {
  pairDevice: async (deviceData: { device_uuid: string; device_name?: string; model_type?: string; is_simulator?: boolean; patient_id?: number }): Promise<Device> => {
    const res = await apiClient.post<Device>('/devices/pair', deviceData);
    return res.data;
  },

  listDevices: async (): Promise<Device[]> => {
    const res = await apiClient.get<Device[]>('/devices');
    return res.data;
  },

  getDevice: async (deviceId: number): Promise<Device> => {
    const res = await apiClient.get<Device>(`/devices/${deviceId}`);
    return res.data;
  },

  updateConfig: async (deviceId: number, config: any): Promise<Device> => {
    const res = await apiClient.put<Device>(`/devices/${deviceId}/config`, config);
    return res.data;
  },

  syncDevice: async (deviceId: number): Promise<Device> => {
    const res = await apiClient.post<Device>(`/devices/${deviceId}/sync`);
    return res.data;
  },

  disconnectDevice: async (deviceId: number): Promise<Device> => {
    const res = await apiClient.post<Device>(`/devices/${deviceId}/disconnect`);
    return res.data;
  },

  getHistory: async (deviceId: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>(`/devices/${deviceId}/history`);
    return res.data;
  },

  simulateReading: async (deviceId: number, data: any): Promise<any> => {
    const res = await apiClient.post(`/devices/${deviceId}/simulate`, data);
    return res.data;
  },
};

// ==========================================
// 4. Emergency SOS & Escalation APIs
// ==========================================
export const emergencyApi = {
  triggerSOS: async (alertData: { alert_type?: string; severity?: string; latitude?: number; longitude?: number; assistance_message?: string; trigger_source?: string; description?: string }): Promise<EmergencyAlert> => {
    const res = await apiClient.post<EmergencyAlert>('/emergency/sos', {
      alert_type: alertData.alert_type || 'manual_sos',
      severity: alertData.severity || 'critical',
      latitude: alertData.latitude,
      longitude: alertData.longitude,
      assistance_message: alertData.assistance_message || alertData.description,
    });
    return res.data;
  },

  requestAssistance: async (message?: string): Promise<EmergencyAlert> => {
    const res = await apiClient.post<EmergencyAlert>('/emergency/assistance', { message });
    return res.data;
  },

  listAlerts: async (): Promise<EmergencyAlert[]> => {
    const res = await apiClient.get<EmergencyAlert[]>('/emergency/alerts');
    return res.data;
  },

  acknowledgeAlert: async (alertId: number, notes?: string): Promise<EmergencyAlert> => {
    const res = await apiClient.post<EmergencyAlert>(`/emergency/${alertId}/acknowledge`, { acknowledgment_notes: notes });
    return res.data;
  },

  rejectAlert: async (alertId: number, reason: string): Promise<EmergencyAlert> => {
    const res = await apiClient.post<EmergencyAlert>(`/emergency/${alertId}/reject`, { rejection_reason: reason });
    return res.data;
  },
};

// ==========================================
// 5. In-App Notifications APIs
// ==========================================
export const notificationApi = {
  list: async (unreadOnly = false): Promise<InAppNotification[]> => {
    const res = await apiClient.get<InAppNotification[]>('/notifications', { params: { unread_only: unreadOnly } });
    return res.data;
  },

  getAll: async (): Promise<InAppNotification[]> => {
    const res = await apiClient.get<InAppNotification[]>('/notifications');
    return res.data;
  },

  getUnreadCount: async (): Promise<{ unread_count: number }> => {
    const res = await apiClient.get<{ unread_count: number }>('/notifications/unread-count');
    return res.data;
  },

  markAsRead: async (id: number | string): Promise<InAppNotification> => {
    const res = await apiClient.patch<InAppNotification>(`/notifications/${id}/read`);
    return res.data;
  },

  markAllAsRead: async (): Promise<{ marked_read_count: number }> => {
    const res = await apiClient.post<{ marked_read_count: number }>('/notifications/read-all');
    return res.data;
  },

  deleteNotification: async (id: number | string): Promise<void> => {
    await apiClient.delete(`/notifications/${id}`);
  },
};

// ==========================================
// 6. Voice Assistant & Messaging APIs
// ==========================================
export const voiceApi = {
  getSupportedLanguages: async (): Promise<any[]> => {
    const res = await apiClient.get('/voice/languages');
    return res.data.languages || [];
  },

  transcribeText: async (promptText: string, lang = 'en'): Promise<any> => {
    const res = await apiClient.post('/voice/transcribe-text', {
      text: promptText,
      language: lang,
    });
    return res.data;
  },

  transcribeAudio: async (audioBase64: string, format = 'audio/wav', lang = 'en'): Promise<any> => {
    const res = await apiClient.post('/voice/transcribe', {
      audio_base64: audioBase64,
      audio_format: format,
      language_hint: lang,
      consent_confirmed: true,
    });
    return res.data;
  },

  translateText: async (data: { text: string; target_language: string; source_language?: string }): Promise<any> => {
    const res = await apiClient.post('/voice/translate', {
      text: data.text,
      target_language: data.target_language,
      source_language: data.source_language || 'en',
    });
    return res.data;
  },

  synthesizeSpeech: async (text: string, lang = 'en'): Promise<any> => {
    const res = await apiClient.post('/voice/synthesize', {
      text,
      language: lang,
    });
    return res.data;
  },

  getConversations: async (): Promise<any[]> => {
    const res = await apiClient.get('/voice/conversations');
    return res.data;
  },

  getMessages: async (partnerId: number): Promise<VoiceMessage[]> => {
    const res = await apiClient.get(`/voice/conversations/${partnerId}`);
    return res.data.messages || [];
  },

  sendMessage: async (messageData: { recipient_id: number; text: string; source_language?: string; target_language?: string }): Promise<VoiceMessage> => {
    const res = await apiClient.post<VoiceMessage>('/voice/messages', messageData);
    return res.data;
  },

  markConversationRead: async (partnerId: number): Promise<any> => {
    const res = await apiClient.post(`/voice/conversations/${partnerId}/read-all`);
    return res.data;
  },
};

// ==========================================
// 7. AI & Digital Twin APIs
// ==========================================
export const aiApi = {
  getDigitalTwinBaseline: async (patientId?: number): Promise<DigitalTwinBaseline> => {
    const res = await apiClient.get<DigitalTwinBaseline>('/ai/digital-twin/baseline', { params: { patient_id: patientId } });
    return res.data;
  },

  getHealthDriftSummary: async (patientId?: number, windowDays = 7): Promise<any> => {
    const res = await apiClient.get('/ai/health-drift/summary', { params: { patient_id: patientId, window_days: windowDays } });
    return res.data;
  },

  getAIHealthStatus: async (patientId?: number): Promise<any> => {
    const res = await apiClient.get('/ai/health-status', { params: { patient_id: patientId } });
    return res.data;
  },
};

// Unified aliases
export const authService = {
  ...authApi,
  updateProfile: authApi.updateMe,
};
export const healthService = {
  ...healthApi,
  exportData: healthApi.exportRecords,
};
export const deviceService = {
  ...deviceApi,
  getAll: deviceApi.listDevices,
};
export const emergencyService = emergencyApi;
export const notificationService = notificationApi;
export const voiceService = voiceApi;
export const aiService = aiApi;

// ==========================================
// 8. Patient Identity, Registration & Reports APIs
// ==========================================
export const patientAuthApi = {
  checkDuplicate: async (payload: { full_name: string; family_email: string; date_of_birth?: string }): Promise<any> => {
    const res = await apiClient.post('/patient/check-duplicate', payload);
    return res.data;
  },

  register: async (payload: any): Promise<any> => {
    const res = await apiClient.post('/patient/register', payload);
    return res.data;
  },

  login: async (credentials: { patient_id: string; password: string }): Promise<AuthResponse> => {
    const res = await apiClient.post<AuthResponse>('/patient/login', credentials);
    return res.data;
  },

  requestForgotIdOtp: async (emailOrPhone: string): Promise<{ message: string; otp_demo?: string; expires_in_minutes: number }> => {
    const res = await apiClient.post('/patient/forgot-id/request-otp', { email_or_phone: emailOrPhone });
    return res.data;
  },

  verifyForgotIdOtp: async (emailOrPhone: string, otpCode: string): Promise<{ status: string; message: string; patients: any[] }> => {
    const res = await apiClient.post('/patient/forgot-id/verify-otp', { email_or_phone: emailOrPhone, otp_code: otpCode });
    return res.data;
  },

  confirmPatientIdSelection: async (email: string, patientId: string): Promise<any> => {
    const res = await apiClient.post('/patient/forgot-id/confirm-selection', { email, patient_id: patientId });
    return res.data;
  },

  getFamilyPatients: async (): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/family/patients');
    return res.data;
  },

  getMedicalReports: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/reports', { params: { patient_id: patientId } });
    return res.data;
  },
};
export const patientAuthService = patientAuthApi;


// ==========================================
// 9. Patient Dashboard Modules API
// ==========================================
export const patientDashboardApi = {
  // Medicines
  getMedicines: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/dashboard/medicines', { params: { patient_id: patientId } });
    return res.data;
  },

  addMedicine: async (payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.post('/patient/dashboard/medicines', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  updateMedicine: async (medicineId: number, payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.put(`/patient/dashboard/medicines/${medicineId}`, payload, { params: { patient_id: patientId } });
    return res.data;
  },

  recordMedicineAction: async (medicineId: number, action: { status: 'taken' | 'skipped' | 'missed'; notes?: string }, patientId?: number): Promise<any> => {
    const res = await apiClient.post(`/patient/dashboard/medicines/${medicineId}/action`, action, { params: { patient_id: patientId } });
    return res.data;
  },

  deleteMedicine: async (medicineId: number, patientId?: number): Promise<any> => {
    const res = await apiClient.delete(`/patient/dashboard/medicines/${medicineId}`, { params: { patient_id: patientId } });
    return res.data;
  },

  // Reminders
  getReminders: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/dashboard/reminders', { params: { patient_id: patientId } });
    return res.data;
  },

  createReminder: async (payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.post('/patient/dashboard/reminders', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  updateReminder: async (reminderId: number, payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.put(`/patient/dashboard/reminders/${reminderId}`, payload, { params: { patient_id: patientId } });
    return res.data;
  },

  deleteReminder: async (reminderId: number, patientId?: number): Promise<any> => {
    const res = await apiClient.delete(`/patient/dashboard/reminders/${reminderId}`, { params: { patient_id: patientId } });
    return res.data;
  },

  // Appointments
  getAppointments: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/dashboard/appointments', { params: { patient_id: patientId } });
    return res.data;
  },

  createAppointment: async (payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.post('/patient/dashboard/appointments', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  updateAppointment: async (appointmentId: number, payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.put(`/patient/dashboard/appointments/${appointmentId}`, payload, { params: { patient_id: patientId } });
    return res.data;
  },

  // Conditions & Allergies
  getConditions: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/dashboard/conditions', { params: { patient_id: patientId } });
    return res.data;
  },

  addCondition: async (payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.post('/patient/dashboard/conditions', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  getAllergies: async (patientId?: number): Promise<any[]> => {
    const res = await apiClient.get<any[]>('/patient/dashboard/allergies', { params: { patient_id: patientId } });
    return res.data;
  },

  addAllergy: async (payload: any, patientId?: number): Promise<any> => {
    const res = await apiClient.post('/patient/dashboard/allergies', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  // Hydration
  getHydration: async (patientId?: number): Promise<{ total_intake_ml: number; target_intake_ml: number; percentage: number; logs_count: number }> => {
    const res = await apiClient.get('/patient/dashboard/hydration', { params: { patient_id: patientId } });
    return res.data;
  },

  logHydration: async (intakeMl: number, patientId?: number): Promise<{ total_intake_ml: number; target_intake_ml: number; percentage: number; logs_count: number }> => {
    const res = await apiClient.post('/patient/dashboard/hydration', { intake_ml: intakeMl }, { params: { patient_id: patientId } });
    return res.data;
  },

  // Digital Medical Documents & AI Clinical Analysis
  getDigitalDocuments: async (patientId?: number): Promise<DigitalDocument[]> => {
    const res = await apiClient.get<DigitalDocument[]>('/patient/dashboard/documents', { params: { patient_id: patientId } });
    return res.data;
  },

  uploadDigitalDocument: async (payload: { document_name: string; document_type: string; file_url?: string; file_text_content?: string }, patientId?: number): Promise<DigitalDocument> => {
    const res = await apiClient.post<DigitalDocument>('/patient/dashboard/documents', payload, { params: { patient_id: patientId } });
    return res.data;
  },

  analyzeDigitalDocument: async (documentId: number, patientId?: number): Promise<DigitalDocument> => {
    const res = await apiClient.post<DigitalDocument>(`/patient/dashboard/documents/${documentId}/ai-analyze`, {}, { params: { patient_id: patientId } });
    return res.data;
  },

  deleteDigitalDocument: async (documentId: number, patientId?: number): Promise<void> => {
    await apiClient.delete(`/patient/dashboard/documents/${documentId}`, { params: { patient_id: patientId } });
  },

  getEmergencyQRProfile: async (patientId?: number): Promise<EmergencyQRProfile> => {
    const res = await apiClient.get<EmergencyQRProfile>('/patient/dashboard/emergency-qr', { params: { patient_id: patientId } });
    return res.data;
  },

  getPublicEmergencyQRProfile: async (qrToken: string): Promise<EmergencyQRPublicView> => {
    const res = await apiClient.get<EmergencyQRPublicView>(`/patient/dashboard/emergency-qr/public/${qrToken}`);
    return res.data;
  },
};
export const patientDashboardService = patientDashboardApi;

export const locationApi = {
  trackLocation: async (payload: {
    latitude?: number;
    longitude?: number;
    altitude?: number;
    accuracy?: number;
    speed?: number;
    is_gps_available?: boolean;
    device_battery?: number;
    device_uuid?: string;
    patient_id?: number;
  }): Promise<any> => {
    const res = await apiClient.post('/location/track', payload);
    return res.data;
  },

  getLatest: async (patientId?: number): Promise<any> => {
    const url = patientId ? `/location/latest/${patientId}` : '/location/latest';
    const res = await apiClient.get(url);
    return res.data;
  },

  getHistory: async (patientId?: number, hours = 24): Promise<any[]> => {
    const url = patientId ? `/location/patients/${patientId}/history` : '/location/history';
    const res = await apiClient.get(url, { params: { hours } });
    return res.data;
  },
};
export const locationService = locationApi;
