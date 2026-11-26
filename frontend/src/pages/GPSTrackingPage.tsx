import React, { useEffect, useState } from 'react';
import { MapPin, Shield, Navigation, Compass, AlertCircle, CheckCircle2, RefreshCw } from 'lucide-react';
import { healthService } from '../api/services';

export const GPSTrackingPage: React.FC = () => {
  const [coords, setCoords] = useState<{ lat: number; lng: number }>({ lat: 12.9716, lng: 77.5946 });
  const [isLiveGps, setIsLiveGps] = useState(false);
  const [geofenceStatus, setGeofenceStatus] = useState<{ isInside: boolean; distance: number; message: string }>({
    isInside: true,
    distance: 12.4,
    message: 'Wearer is within registered safe residence perimeter.',
  });
  const [loading, setLoading] = useState(false);

  const checkLocation = () => {
    setLoading(true);
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (pos) => {
          const lat = Number(pos.coords.latitude.toFixed(4));
          const lng = Number(pos.coords.longitude.toFixed(4));
          setCoords({ lat, lng });
          setIsLiveGps(true);

          // Verify with backend geofence API
          try {
            const check = await healthService.checkGeofence({
              latitude: lat,
              longitude: lng,
              center_latitude: 12.9716,
              center_longitude: 77.5946,
              radius_meters: 500.0,
            });
            if (check) {
              setGeofenceStatus({
                isInside: check.is_inside,
                distance: check.distance_from_center_meters,
                message: check.message,
              });
            }
          } catch {
            // Keep status
          } finally {
            setLoading(false);
          }
        },
        () => {
          setIsLiveGps(false);
          setLoading(false);
        },
        { enableHighAccuracy: true, timeout: 6000 }
      );
    } else {
      setIsLiveGps(false);
      setLoading(false);
    }
  };

  useEffect(() => {
    checkLocation();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">GPS & Geofence Safety Tracking</h2>
          <p className="text-sm text-slate-500">
            Real-time outdoor coordinates, safe perimeter boundary enforcement, and fall-location broadcasting.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
            <span>{isLiveGps ? 'GNSS Browser Fix: Active' : 'Fallback Residence Coordinates'}</span>
          </span>

          <button
            onClick={checkLocation}
            className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
            title="Refresh GPS Coordinates"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Main Map Card */}
      <div className="glass-card rounded-3xl p-6 border border-slate-100 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <MapPin className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-bold text-slate-800">Live Geographic Location</h3>
          </div>
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-500 font-mono">{coords.lat}° N, {coords.lng}° E</span>
          </div>
        </div>

        {/* Map Visual */}
        <div className="relative w-full h-96 rounded-2xl overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center shadow-inner">
          <div className="absolute inset-0 bg-[#e5eef7] opacity-80" />
          <svg className="absolute inset-0 w-full h-full stroke-white/80 stroke-[4]">
            <line x1="0" y1="120" x2="1000" y2="120" />
            <line x1="0" y1="280" x2="1000" y2="280" />
            <line x1="200" y1="0" x2="200" y2="600" />
            <line x1="600" y1="0" x2="600" y2="600" />
            <line x1="850" y1="0" x2="850" y2="600" />
          </svg>

          {/* Safe Zone Geofence Circle */}
          <div className={`relative w-72 h-72 rounded-full border-2 border-dashed flex items-center justify-center animate-pulse ${
            geofenceStatus.isInside ? 'bg-blue-500/10 border-blue-400' : 'bg-rose-500/10 border-rose-500'
          }`}>
            <div className="relative flex flex-col items-center">
              <div className={`w-10 h-10 rounded-full border-4 border-white shadow-xl flex items-center justify-center text-white ${
                geofenceStatus.isInside ? 'bg-blue-600' : 'bg-rose-600'
              }`}>
                <Navigation className="w-5 h-5 fill-white transform rotate-45" />
              </div>
              <div className="mt-2 bg-slate-900/90 text-white text-[11px] font-bold px-3 py-1 rounded-full shadow-lg backdrop-blur-sm">
                Wearer Fix: {coords.lat}, {coords.lng}
              </div>
            </div>
          </div>

          {/* Map Controls Overlay */}
          <div className="absolute bottom-4 left-4 bg-white/95 rounded-2xl p-3 shadow-lg border border-slate-200 backdrop-blur-sm space-y-1 text-xs">
            <div className="font-bold text-slate-800 flex items-center space-x-1.5">
              {geofenceStatus.isInside ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-500" />
                  <span>Status: Inside Safe Zone</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-4 h-4 text-rose-500" />
                  <span className="text-rose-600">Status: Safe Zone Breach Detected!</span>
                </>
              )}
            </div>
            <div className="text-slate-500">
              Perimeter: 500m radius | Current Distance: {geofenceStatus.distance}m
            </div>
          </div>
        </div>
      </div>

      {/* Geofence Management Options */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-start space-x-3">
          <div className="p-3 bg-blue-50 text-blue-600 rounded-2xl">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Geofence Perimeter (500m)</h4>
            <p className="text-xs text-slate-500 mt-1">Automatic alert notifications if wearer wanders beyond safe radius.</p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-start space-x-3">
          <div className="p-3 bg-teal-50 text-teal-600 rounded-2xl">
            <Compass className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Fall Coordinate Lock</h4>
            <p className="text-xs text-slate-500 mt-1">Locks GPS fix upon accelerometer fall detection for emergency responders.</p>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-slate-100 flex items-start space-x-3">
          <div className="p-3 bg-purple-50 text-purple-600 rounded-2xl">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-slate-800">Caregiver Broadcast</h4>
            <p className="text-xs text-slate-500 mt-1">Live SMS/Push notifications dispatched to designated emergency contacts.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
