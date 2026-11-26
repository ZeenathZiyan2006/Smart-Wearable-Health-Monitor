import React, { useState } from 'react';
import { Activity, ShieldCheck, Heart, Radio, Play, Pause, AlertCircle } from 'lucide-react';
import { LiveECGCanvas } from '../components/LiveECGCanvas';

export const ECGMonitorPage: React.FC = () => {
  const [lead, setLead] = useState<'Lead I' | 'Lead II' | 'Lead III'>('Lead I');
  const [filterType, setFilterType] = useState('0.05-150Hz');

  return (
    <div className="space-y-6 pb-12">
      <div>
        <h2 className="text-2xl font-extrabold text-slate-800">Live ECG & Cardiac Telemetry</h2>
        <p className="text-sm text-slate-500">
          Assistive continuous cardiac waveform monitoring (Simulated DSP Demonstration).
        </p>
      </div>

      {/* Medical Safety Disclaimer Alert */}
      <div className="p-4 rounded-2xl bg-amber-50/80 border border-amber-200 text-xs text-amber-900 flex items-start space-x-3">
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <span className="font-bold">Medical Safety & Hardware Notice: </span>
          The MAX30102 sensor provides optical photoplethysmography (PPG) pulse volume data. Real electrophysiological ECG monitoring requires dedicated analog front-end biopotential hardware (e.g. AD8232 or ADS1292R with dry/AgCl chest electrodes). The waveform displayed below is a synthetic DSP simulation for demonstration purposes and is not intended for clinical cardiac diagnosis.
        </div>
      </div>

      {/* Main Big ECG Waveform Monitor */}
      <div className="bg-[#0b1324] rounded-3xl p-6 border border-cyan-500/30 shadow-2xl">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4 pb-4 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <span className="w-3 h-3 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="text-lg font-bold text-white tracking-wide">Continuous ECG Rhythm Strip</span>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
              Simulated DSP Feed
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs text-slate-300">
            <div className="flex items-center space-x-1 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-700">
              <span>Bandpass:</span>
              <span className="font-mono text-cyan-400">{filterType}</span>
            </div>
            <div className="flex items-center space-x-1 bg-slate-900 px-3 py-1.5 rounded-xl border border-slate-700">
              <span>Speed:</span>
              <span className="font-mono text-cyan-400">25 mm/s</span>
            </div>
          </div>
        </div>

        {/* Oscilloscope Canvas Component */}
        <div className="my-2">
          <LiveECGCanvas heartRate={72} className="!border-0 !p-0 !bg-transparent" />
        </div>

        {/* Cardiac Interval Metrics */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-slate-800 text-center font-mono">
          <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="text-xs text-slate-400">Heart Rate</div>
            <div className="text-xl font-bold text-rose-400">72 BPM</div>
            <div className="text-[10px] text-slate-500">Regular Sinus</div>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="text-xs text-slate-400">PR Interval</div>
            <div className="text-xl font-bold text-cyan-400">98 ms</div>
            <div className="text-[10px] text-slate-500">Normal (80-120)</div>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="text-xs text-slate-400">QRS Duration</div>
            <div className="text-xl font-bold text-cyan-400">82 ms</div>
            <div className="text-[10px] text-slate-500">Narrow Complex</div>
          </div>
          <div className="bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="text-xs text-slate-400">QT / QTc Interval</div>
            <div className="text-xl font-bold text-emerald-400">380 ms</div>
            <div className="text-[10px] text-slate-500">Normofrequent</div>
          </div>
        </div>
      </div>

      {/* Rhythm Analysis and Safety Banner */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-start space-x-3">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-2xl">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Sinus Rhythm Verified</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Automated DSP filtering confirms consistent P waves, regular R-R intervals, and absence of ectopic beats or atrial fibrillation.
            </p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-start space-x-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Wearable Electrode Quality</h4>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">
              Optical photoplethysmography (PPG) and dry electrode skin contact impedance are optimal (&lt; 50 kΩ). Baseline drift filter active.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
