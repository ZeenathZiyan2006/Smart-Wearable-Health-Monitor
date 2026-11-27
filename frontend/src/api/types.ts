export type UserRole = 'patient' | 'caregiver' | 'admin';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  phone_number?: string;
  preferred_language: string;
  is_active: boolean;
  created_at: string;
  patient_profile?: PatientProfile;
  caregiver_profile?: CaregiverProfile;
}

export interface PatientProfile {
  id: number;
  user_id: number;
  patient_id?: string;
  uuid?: string;
  family_email?: string;
  contact_number?: string;
  address?: string;
  date_of_birth?: string;
  gender?: string;
  blood_group?: string;
  medical_history?: string;
  emergency_contact_phone?: string;
  device_uuid?: string;
  device_status: string;
  last_sync_at?: string;
}

export interface CaregiverProfile {
  id: number;
  user_id: number;
  relationship_type: string;
  organization?: string;
  notification_preference: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user_id: number;
  email: string;
  role: UserRole;
  full_name: string;
}

export interface TelemetryReading {
  id?: number;
  patient_id?: number;
  device_uuid?: string;
  heart_rate: number | null;
  spo2: number | null;
  temperature: number | null;
  temperature_unit?: string;
  blood_pressure_sys?: number | null;
  blood_pressure_dia?: number | null;
  respiratory_rate?: number | null;
  step_count?: number;
  activity_type?: string;
  calories_burned?: number | null;
  sleep_stage?: string | null;
  sleep_duration_minutes?: number | null;
  fall_detected?: boolean;
  battery_percentage?: number | null;
  is_anomalous?: boolean;
  anomaly_reason?: string | null;
  recorded_at: string;
}

export interface DashboardSummary {
  patient_id: number;
  patient_name: string;
  device_status: {
    patient_id: number;
    device_uuid?: string;
    device_status: string;
    battery_percentage?: number;
    is_online: boolean;
    is_stale: boolean;
    last_sync_at?: string;
    last_recorded_at?: string;
    sensor_status?: Record<string, string>;
  };
  latest_vitals: {
    heart_rate: number | null;
    spo2: number | null;
    temperature: number | null;
    temperature_unit: string;
    blood_pressure_sys?: number | null;
    blood_pressure_dia?: number | null;
    respiratory_rate?: number | null;
    activity_type: string;
    battery_percentage?: number | null;
    fall_detected: boolean;
    recorded_at: string | null;
  };
  summary_24h: {
    avg_heart_rate: number | null;
    min_heart_rate: number | null;
    max_heart_rate: number | null;
    avg_spo2: number | null;
    min_spo2: number | null;
    avg_temperature: number | null;
    total_steps: number;
    total_calories: number;
    anomalies_detected: number;
    falls_detected: number;
    readings_count: number;
  };
  disclaimer: string;
}

export interface Device {
  id: number;
  device_uuid: string;
  device_name: string;
  model_type: string;
  firmware_version: string;
  patient_id?: number;
  status: string;
  battery_level?: number;
  is_simulator: boolean;
  config_json?: string;
  last_sync_at?: string;
  paired_at: string;
}

export interface EmergencyAlert {
  id: number;
  patient_id: number;
  device_uuid?: string;
  alert_type: string;
  severity: string;
  status: string;
  current_escalation_tier: number;
  latitude?: number;
  longitude?: number;
  location_accuracy?: number;
  assistance_message?: string;
  voice_transcript?: string;
  detected_language?: string;
  translated_summary?: string;
  created_at: string;
  acknowledged_at?: string;
  resolved_at?: string;
}

export interface InAppNotification {
  id: number;
  user_id: number;
  title: string;
  body: string;
  notification_type: string;
  severity: string;
  data_json?: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
}

export interface VoiceMessage {
  id: number;
  sender_id: number;
  recipient_id: number;
  source_language: string;
  target_language: string;
  original_text: string;
  translated_text?: string;
  is_read: boolean;
  delivery_status: string;
  created_at: string;
}

export interface DigitalTwinBaseline {
  id: number;
  patient_id: number;
  baseline_resting_hr: number;
  hr_min_normal: number;
  hr_max_normal: number;
  baseline_spo2: number;
  spo2_min_normal: number;
  baseline_temperature: number;
  samples_count: number;
  last_calculated_at: string;
}

export type HealthTelemetry = TelemetryReading;
export type NotificationItem = InAppNotification;

// Patient Identity & Management Types
export interface PatientRegisterPayload {
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  contact_number: string;
  individual_email?: string;
  family_email: string;
  address?: string;
  emergency_contact?: string;
  password: string;
  confirm_password: string;
  force_duplicate?: boolean;
}

export interface PatientRegisterResponse {
  status: string;
  message: string;
  patient_id: string;
  patient_name: string;
  registration_date: string;
  family_email: string;
  uuid: string;
  access_token?: string;
  refresh_token?: string;
  token_type?: string;
  user_id?: number;
}

export interface DuplicateCheckPayload {
  full_name: string;
  family_email: string;
  date_of_birth?: string;
}

export interface DuplicateCheckResponse {
  has_duplicate: boolean;
  message: string;
  matched_name?: string;
  matched_patient_id?: string;
}

export interface RecoveredPatientProfile {
  patient_id: string;
  patient_name: string;
  gender?: string;
  date_of_birth?: string;
  masked_contact: string;
  device_uuid?: string;
  age?: number;
  blood_group?: string;
  relationship_role?: string;
  authorized_for_recovery?: boolean;
}

export interface PatientIdConfirmationResponse {
  status: string;
  message: string;
  patient_id: string;
  patient_name: string;
  confirmation_timestamp: string;
}

export interface PatientForgotIdResponse {
  status: string;
  message: string;
  patients: RecoveredPatientProfile[];
}

export interface FamilyPatient {
  patient_id: string;
  profile_id: number;
  user_id: number;
  full_name: string;
  date_of_birth?: string;
  gender?: string;
  device_uuid?: string;
  device_status?: string;
  family_email?: string;
  contact_number?: string;
  last_sync_at?: string;
}

export interface MedicalReport {
  id: number;
  patient_id: number;
  doctor_name: string;
  report_type: string;
  title: string;
  summary: string;
  observations?: string;
  recommendations?: string;
  report_date: string;
  created_at: string;
}



// Patient Dashboard Module Types
export interface PatientMedicine {
  id: number;
  patient_id: number;
  medicine_name: string;
  dosage: string;
  frequency: string;
  scheduled_times: string;
  start_date: string;
  end_date?: string;
  expiry_date?: string;
  total_quantity: number;
  remaining_quantity: number;
  medicine_status: string;
  consumed_quantity: number;
  is_low_stock: boolean;
  is_expired: boolean;
  notes?: string;
  created_at: string;
}

export interface PatientReminder {
  id: number;
  patient_id: number;
  title: string;
  reminder_type: 'medicine' | 'sleep' | 'hydration' | 'appointment';
  reminder_time: string;
  is_enabled: boolean;
  recurring_days: string;
  alarm_tone: string;
  volume: number;
  vibration_enabled: boolean;
  snooze_interval_minutes: number;
  created_at: string;
}

export interface DoctorAppointment {
  id: number;
  patient_id: number;
  doctor_name: string;
  specialization: string;
  hospital_name: string;
  phone_number?: string;
  appointment_date: string;
  status: 'confirmed' | 'completed' | 'rescheduled' | 'cancelled';
  reason?: string;
  notes?: string;
  created_at: string;
}

export interface MedicalCondition {
  id: number;
  patient_id: number;
  condition_name: string;
  diagnosed_date?: string;
  severity: string;
  status: string;
  notes?: string;
  created_at: string;
}

export interface PatientAllergy {
  id: number;
  patient_id: number;
  allergen: string;
  reaction?: string;
  severity: string;
  created_at: string;
}

export interface HydrationSummary {
  total_intake_ml: number;
  target_intake_ml: number;
  percentage: number;
  logs_count: number;
}

export interface DigitalDocument {
  id: number;
  patient_id: number;
  document_name: string;
  document_type: string;
  file_url?: string;
  file_text_content?: string;
  uploaded_at: string;
  ai_analysis_status: string;
  ai_summary?: string;
  ai_detected_conditions?: string;
  ai_key_biomarkers?: string;
  ai_clinical_suggestions?: string;
  ai_confidence_score: number;
}

export interface EmergencyQRProfile {
  id: number;
  patient_id: number;
  qr_token: string;
  qr_code_url: string;
  is_active: boolean;
  blood_group: string;
  display_blood_group: boolean;
  display_allergies: boolean;
  display_conditions: boolean;
  display_medicines: boolean;
  display_emergency_contacts: boolean;
  emergency_instructions?: string;
  doctor_contact_details?: string;
  regenerated_at: string;
  created_at: string;
}

export interface EmergencyQRPublicView {
  patient_name: string;
  patient_id_readable: string;
  blood_group?: string;
  allergies: string[];
  medical_conditions: string[];
  active_medicines: string[];
  emergency_contacts: Array<{ name: string; relation: string; phone: string }>;
  emergency_instructions?: string;
  doctor_contact?: string;
  uploaded_documents: Array<{
    id: number;
    document_name: string;
    document_type: string;
    file_url?: string;
    file_text_content?: string;
    uploaded_at: string;
    ai_summary: string;
    ai_detected_conditions: string;
    ai_key_biomarkers: string;
    ai_clinical_suggestions: string;
    ai_confidence_score: number;
  }>;
  is_verified: boolean;
  notice: string;
}
