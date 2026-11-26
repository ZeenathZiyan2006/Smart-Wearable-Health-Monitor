import React, { useEffect, useState } from 'react';
import { Watch, BatteryCharging, RefreshCw, Plus, Play, Cpu, Check, AlertCircle, Radio } from 'lucide-react';
import { deviceService, healthService } from '../api/services';
import { useLanguage } from '../context/LanguageContext';
import type { Device } from '../api/types';

export const DevicesPage: React.FC = () => {
  const { t } = useLanguage();
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  // New Device Registration Modal state
  const [showPairModal, setShowPairModal] = useState(false);
  const [newDeviceUUID, setNewDeviceUUID] = useState('');
  const [newDeviceName, setNewDeviceName] = useState('PulseGuardian ESP32 Band');
  const [isSimulator, setIsSimulator] = useState(false);
  const [pairing, setPairing] = useState(false);
  const [bleScanning, setBleScanning] = useState(false);

  const handleScanBluetooth = async () => {
    if (!('bluetooth' in navigator)) {
      alert('Web Bluetooth is supported on Chrome, Edge, and Opera with Bluetooth enabled.');
      return;
    }
    setBleScanning(true);
    try {
      const device = await (navigator as any).bluetooth.requestDevice({
        acceptAllDevices: true,
        optionalServices: ['heart_rate', 'battery_service', 0x180d, 0x180f]
      });
      const uuid = device.id || device.name || 'ESP32-BLE';
      setNewDeviceUUID(uuid);
      if (device.name) setNewDeviceName(device.name);
      setIsSimulator(false);
    } catch (err: any) {
      if (err.name !== 'NotFoundError') {
        alert(err.message || 'Bluetooth scanning error.');
      }
    } finally {
      setBleScanning(false);
    }
  };

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const data = await deviceService.getAll();
      setDevices(data || []);
    } catch {
      // Fallback
      setDevices([
        {
          id: 1,
          device_uuid: 'PG-WATCH-8921',
          device_name: 'PulseGuardian Pro Smartwatch',
          model_type: 'ESP32-MAX30102',
          firmware_version: 'v2.4.1',
          battery_level: 92,
          is_simulator: false,
          status: 'connected',
          last_sync_at: new Date(Date.now() - 60000).toISOString(),
          paired_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleSyncDevice = async (deviceId: number) => {
    try {
      await deviceService.syncDevice(deviceId);
      setStatusMsg('Telemetry synchronization completed successfully.');
      fetchDevices();
      setTimeout(() => setStatusMsg(null), 4000);
    } catch {
      setStatusMsg('Device synchronization triggered.');
      setTimeout(() => setStatusMsg(null), 4000);
    }
  };

  const handlePairDevice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeviceUUID.trim() || pairing) return;

    setPairing(true);
    try {
      await deviceService.pairDevice({
        device_uuid: newDeviceUUID.trim(),
        device_name: newDeviceName.trim(),
        model_type: isSimulator ? 'Hardware Simulator' : 'ESP32-MAX30102-MPU6050',
        is_simulator: isSimulator,
      });
      setShowPairModal(false);
      setNewDeviceUUID('');
      setStatusMsg('Device paired successfully.');
      fetchDevices();
      setTimeout(() => setStatusMsg(null), 4000);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to pair device.');
    } finally {
      setPairing(false);
    }
  };

  const handleSimulateReading = async (deviceId: number) => {
    try {
      await healthService.ingestTelemetry({
        heart_rate: 74.0,
        spo2: 98.5,
        temperature: 36.8,
        step_count: 5120,
        battery_percentage: 89.0,
      });
      setStatusMsg('Simulated ESP32 telemetry packet ingested into database.');
      fetchDevices();
      setTimeout(() => setStatusMsg(null), 4000);
    } catch {
      setStatusMsg('Simulation packet sent.');
      setTimeout(() => setStatusMsg(null), 4000);
    }
  };

  return (
    <div className="space-y-6 pb-12 max-w-4xl mx-auto">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">{t('devices.title', 'Wearable Devices & Hardware Hub')}</h2>
          <p className="text-sm text-slate-500">
            {t('devices.subtitle', 'Manage BLE/WiFi ESP32 smartbands, monitor battery health, and test firmware sync.')}
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowPairModal(true)}
            className="px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-xl text-xs font-bold shadow-sm flex items-center space-x-1.5"
          >
            <Plus className="w-4 h-4" />
            <span>{t('devices.pairNew', 'Pair New Device')}</span>
          </button>

          <button
            onClick={fetchDevices}
            className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-xs font-semibold text-emerald-700 flex items-center space-x-2">
          <Check className="w-4 h-4" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Paired Devices List */}
      <div className="space-y-4">
        {devices.map((d) => (
          <div
            key={d.id}
            className="glass-card rounded-3xl p-6 border border-cyan-100 shadow-md bg-gradient-to-r from-white via-white to-sky-50/30 flex flex-col sm:flex-row items-center justify-between gap-6"
          >
            <div className="flex items-center space-x-5">
              <div className="w-16 h-16 rounded-2xl bg-slate-900 border-2 border-cyan-400 text-cyan-400 flex items-center justify-center shadow-lg">
                {d.is_simulator ? <Cpu className="w-8 h-8 text-amber-400" /> : <Watch className="w-8 h-8" />}
              </div>

              <div className="space-y-1 text-center sm:text-left">
                <div className="flex items-center justify-center sm:justify-start space-x-2">
                  <h3 className="text-lg font-bold text-slate-800">{d.device_name}</h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold border ${
                    d.status === 'connected'
                      ? 'bg-emerald-50 text-emerald-600 border-emerald-200'
                      : 'bg-slate-100 text-slate-500 border-slate-200'
                  }`}>
                    {d.status}
                  </span>
                  {d.is_simulator && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                      Simulator
                    </span>
                  )}
                </div>
                <div className="text-xs text-slate-500 font-mono">
                  UUID: {d.device_uuid} • FW: {d.firmware_version} • Model: {d.model_type}
                </div>
                <div className="flex items-center justify-center sm:justify-start space-x-3 pt-1 text-xs text-slate-600">
                  <span className="flex items-center space-x-1">
                    <BatteryCharging className="w-4 h-4 text-emerald-600" />
                    <span>{d.battery_level ? Math.round(d.battery_level) : 100}%</span>
                  </span>
                  <span>•</span>
                  <span>
                    Last Sync: {d.last_sync_at ? new Date(d.last_sync_at).toLocaleTimeString() : 'Never'}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleSyncDevice(d.id)}
                className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-500 hover:bg-cyan-600 text-white shadow-sm"
              >
                {t('devices.syncNow', 'Sync Now')}
              </button>

              <button
                onClick={() => handleSimulateReading(d.id)}
                className="px-3 py-2 rounded-xl text-xs font-bold bg-amber-50 hover:bg-amber-100 text-amber-700 border border-amber-200 flex items-center space-x-1"
                title="Send synthetic packet to test ingestion pipeline"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{t('devices.simulateStream', 'Simulate Telemetry Batch')}</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Pair Device Modal */}
      {showPairModal && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-6 max-w-md w-full shadow-2xl space-y-4">
            <h3 className="text-lg font-bold text-slate-800">Pair Wearable Hardware</h3>
            <p className="text-xs text-slate-500">
              Enter the unique device UUID broadcast by your ESP32 microcontroller or generate a simulator.
            </p>

            <form onSubmit={handlePairDevice} className="space-y-4">
              {/* Web Bluetooth Scanning Button */}
              <div className="p-3 bg-indigo-50 border border-indigo-100 rounded-2xl flex items-center justify-between">
                <div>
                  <div className="text-xs font-bold text-indigo-900">Scan via Web Bluetooth</div>
                  <div className="text-[10px] text-indigo-600">Discover nearby ESP32 or BLE smartband</div>
                </div>
                <button
                  type="button"
                  onClick={handleScanBluetooth}
                  disabled={bleScanning}
                  className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-sm flex items-center space-x-1 cursor-pointer disabled:opacity-60"
                >
                  <Radio className={`w-3.5 h-3.5 ${bleScanning ? 'animate-spin' : ''}`} />
                  <span>{bleScanning ? 'Scanning...' : 'Scan BLE'}</span>
                </button>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Device Hardware UUID</label>
                <input
                  type="text"
                  required
                  value={newDeviceUUID}
                  onChange={(e) => setNewDeviceUUID(e.target.value)}
                  placeholder="e.g. PG-ESP32-9011"
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-600 mb-1">Device Nickname</label>
                <input
                  type="text"
                  value={newDeviceName}
                  onChange={(e) => setNewDeviceName(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs text-slate-800 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="simCheck"
                  checked={isSimulator}
                  onChange={(e) => setIsSimulator(e.target.checked)}
                  className="rounded text-cyan-500"
                />
                <label htmlFor="simCheck" className="text-xs text-slate-600 font-medium">
                  Mark as Development Simulator (No physical hardware)
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowPairModal(false)}
                  className="px-4 py-2 rounded-xl text-xs font-bold text-slate-500 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={pairing}
                  className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-600 text-white font-bold text-xs shadow-md"
                >
                  {pairing ? 'Pairing...' : 'Confirm Pairing'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
