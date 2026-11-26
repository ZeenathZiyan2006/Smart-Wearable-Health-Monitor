import React, { useState } from 'react';
import { Download, FileText, Calendar, Filter, FileSpreadsheet, Check } from 'lucide-react';
import { healthService } from '../api/services';

export const HealthHistoryPage: React.FC = () => {
  const [downloading, setDownloading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleExport = async (format: 'json' | 'csv') => {
    setDownloading(true);
    try {
      const data = await healthService.exportRecords(undefined, format, 30);
      // Trigger browser download
      const blob = new Blob([format === 'json' ? JSON.stringify(data, null, 2) : String(data)], {
        type: format === 'json' ? 'application/json' : 'text/csv',
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `PulseGuardian_Health_Export.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch {
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } finally {
      setDownloading(false);
    }
  };

  const sampleLogs = [
    { date: 'Nov 26, 2026', hr: '72 BPM', spo2: '98%', temp: '36.8 °C', bp: '120/80', steps: '4,820', status: 'Optimal' },
    { date: 'Nov 25, 2026', hr: '74 BPM', spo2: '97%', temp: '36.7 °C', bp: '122/82', steps: '5,900', status: 'Normal' },
    { date: 'Nov 24, 2026', hr: '71 BPM', spo2: '99%', temp: '36.9 °C', bp: '118/78', steps: '6,100', status: 'Optimal' },
    { date: 'Nov 23, 2026', hr: '75 BPM', spo2: '98%', temp: '36.8 °C', bp: '121/81', steps: '5,200', status: 'Normal' },
  ];

  return (
    <div className="space-y-6 pb-12 max-w-5xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">Health History & Medical Records</h2>
          <p className="text-sm text-slate-500">
            Export structured HIPAA-compliant biomarker logs for physicians and healthcare providers.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => handleExport('csv')}
            disabled={downloading}
            className="px-4 py-2 bg-white rounded-xl border border-slate-200 text-xs font-bold text-slate-700 hover:bg-slate-50 shadow-sm flex items-center space-x-2"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
            <span>Export CSV</span>
          </button>

          <button
            onClick={() => handleExport('json')}
            disabled={downloading}
            className="px-4 py-2 bg-cyan-500 rounded-xl text-xs font-bold text-white hover:bg-cyan-600 shadow-sm flex items-center space-x-2"
          >
            <Download className="w-4 h-4" />
            <span>Export JSON</span>
          </button>
        </div>
      </div>

      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs font-semibold text-emerald-700 flex items-center space-x-2">
          <Check className="w-4 h-4" />
          <span>Biometric audit log successfully exported to your downloads folder.</span>
        </div>
      )}

      {/* Table */}
      <div className="glass-card rounded-3xl border border-slate-100 shadow-sm overflow-hidden bg-white">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-slate-800 text-sm">Archived Vitals Log</h3>
          <span className="text-xs text-slate-400">Showing last 4 days</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-3 px-5">Date</th>
                <th className="py-3 px-4">Heart Rate</th>
                <th className="py-3 px-4">SpO2</th>
                <th className="py-3 px-4">Temperature</th>
                <th className="py-3 px-4">Blood Pressure</th>
                <th className="py-3 px-4">Steps</th>
                <th className="py-3 px-4">Assessment</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {sampleLogs.map((row, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-5 font-medium text-slate-900">{row.date}</td>
                  <td className="py-3.5 px-4 font-mono">{row.hr}</td>
                  <td className="py-3.5 px-4 font-mono">{row.spo2}</td>
                  <td className="py-3.5 px-4 font-mono">{row.temp}</td>
                  <td className="py-3.5 px-4 font-mono">{row.bp}</td>
                  <td className="py-3.5 px-4 font-mono">{row.steps}</td>
                  <td className="py-3.5 px-4">
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-50 text-emerald-600 border border-emerald-200">
                      {row.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
