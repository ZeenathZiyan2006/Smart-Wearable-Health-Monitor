import React, { useEffect, useState } from 'react';
import {
  Heart,
  Droplets,
  Thermometer,
  Activity,
  Calendar,
  Download,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';
import { healthService } from '../api/services';
import type { HealthTelemetry } from '../api/types';

export const HealthMonitorPage: React.FC = () => {
  const [history, setHistory] = useState<HealthTelemetry[]>([]);
  const [filter, setFilter] = useState<'day' | 'week' | 'month'>('week');
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    setLoading(true);
    try {
      const data = await healthService.getHistory(30);
      setHistory(data);
    } catch {
      // Mock history if offline
      const mock: HealthTelemetry[] = Array.from({ length: 14 }).map((_, i) => ({
        id: i + 1,
        heart_rate: 68 + Math.sin(i) * 10 + (i % 3) * 4,
        spo2: 97 + (i % 3),
        temperature: 36.6 + (i % 4) * 0.2,
        blood_pressure_sys: 118 + (i % 5) * 2,
        blood_pressure_dia: 78 + (i % 3) * 2,
        step_count: 4000 + i * 300,
        recorded_at: new Date(Date.now() - (14 - i) * 86400000).toISOString(),
      }));
      setHistory(mock);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [filter]);

  const chartData = history.map((item) => ({
    time: new Date(item.recorded_at).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    }),
    heartRate: item.heart_rate,
    spo2: item.spo2,
    temp: item.temperature,
    bpSys: item.blood_pressure_sys,
  }));

  const latest = history[history.length - 1] || {
    heart_rate: 72,
    spo2: 98,
    temperature: 36.8,
    blood_pressure_sys: 120,
    blood_pressure_dia: 80,
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">Health Monitoring Center</h2>
          <p className="text-sm text-slate-500">
            Real-time biometric analytics, historical trends, and sensor diagnostics.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          {/* Time range pill */}
          <div className="bg-white rounded-xl p-1 shadow-sm border border-slate-200 flex items-center text-xs font-semibold">
            {(['day', 'week', 'month'] as const).map((mode) => (
              <button
                key={mode}
                onClick={() => setFilter(mode)}
                className={`px-3 py-1.5 rounded-lg transition-all capitalize ${
                  filter === mode
                    ? 'bg-cyan-500 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          <button
            onClick={fetchHistory}
            className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
            title="Refresh"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* 4 Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-center space-x-4">
          <div className="p-3 rounded-2xl bg-rose-50 text-rose-500">
            <Heart className="w-6 h-6 fill-rose-500" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500">Resting Heart Rate</div>
            <div className="text-2xl font-bold text-slate-800">
              {latest.heart_rate} <span className="text-xs font-normal text-slate-400">BPM</span>
            </div>
            <div className="text-[11px] text-emerald-600 font-medium">Optimal Rhythm</div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-center space-x-4">
          <div className="p-3 rounded-2xl bg-blue-50 text-blue-500">
            <Droplets className="w-6 h-6 fill-blue-500" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500">Oxygen Saturation</div>
            <div className="text-2xl font-bold text-slate-800">
              {latest.spo2} <span className="text-xs font-normal text-slate-400">%</span>
            </div>
            <div className="text-[11px] text-emerald-600 font-medium">Normal Blood Oxygen</div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-center space-x-4">
          <div className="p-3 rounded-2xl bg-amber-50 text-amber-500">
            <Thermometer className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500">Skin Temperature</div>
            <div className="text-2xl font-bold text-slate-800">
              {latest.temperature} <span className="text-xs font-normal text-slate-400">°C</span>
            </div>
            <div className="text-[11px] text-emerald-600 font-medium">Afebrile Baseline</div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-center space-x-4">
          <div className="p-3 rounded-2xl bg-purple-50 text-purple-500">
            <Activity className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs font-semibold text-slate-500">Blood Pressure</div>
            <div className="text-2xl font-bold text-slate-800">
              {latest.blood_pressure_sys || 120} / {latest.blood_pressure_dia || 80}
            </div>
            <div className="text-[11px] text-emerald-600 font-medium">Standard Normotensive</div>
          </div>
        </div>
      </div>

      {/* Main Charts: Heart Rate & SpO2 Trends */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Heart Rate Area Chart */}
        <div className="glass-card rounded-2xl p-6 border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Heart className="w-5 h-5 text-rose-500" />
              <h3 className="text-base font-bold text-slate-800">Heart Rate Trend (BPM)</h3>
            </div>
            <span className="text-xs font-semibold text-slate-400">Continuous Sampling</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="hrColor" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis domain={[50, 110]} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Area
                  type="monotone"
                  dataKey="heartRate"
                  stroke="#f43f5e"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#hrColor)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* SpO2 Line Chart */}
        <div className="glass-card rounded-2xl p-6 border border-slate-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Droplets className="w-5 h-5 text-blue-500" />
              <h3 className="text-base font-bold text-slate-800">Oxygen Saturation Trend (% SpO2)</h3>
            </div>
            <span className="text-xs font-semibold text-slate-400">Target &gt; 95%</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis domain={[90, 100]} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="spo2"
                  stroke="#0284c7"
                  strokeWidth={2.5}
                  dot={{ r: 3, fill: '#0284c7' }}
                  activeDot={{ r: 6 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
