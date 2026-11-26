import React, { useEffect, useState } from 'react';
import { Moon, Footprints, Flame, Award, RefreshCw } from 'lucide-react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { healthService } from '../api/services';

export const SleepActivityPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [weeklySteps, setWeeklySteps] = useState([
    { day: 'Mon', steps: 5200, cal: 240 },
    { day: 'Tue', steps: 6100, cal: 290 },
    { day: 'Wed', steps: 4800, cal: 210 },
    { day: 'Thu', steps: 7300, cal: 340 },
    { day: 'Fri', steps: 5900, cal: 270 },
    { day: 'Sat', steps: 4200, cal: 190 },
    { day: 'Sun', steps: 4820, cal: 220 },
  ]);
  const [todaySteps, setTodaySteps] = useState(4820);
  const [calories, setCalories] = useState(220);
  const [distanceKm, setDistanceKm] = useState('2.4');
  const [sleepDurationStr, setSleepDurationStr] = useState('7h 20m');

  const fetchLiveActivity = async () => {
    setLoading(true);
    try {
      const data = await healthService.getDashboard();
      if (data && data.summary_24h) {
        if (data.summary_24h.total_steps) {
          setTodaySteps(data.summary_24h.total_steps);
          setDistanceKm((data.summary_24h.total_steps * 0.00075).toFixed(1));
        }
        if (data.summary_24h.total_calories) {
          setCalories(Math.round(data.summary_24h.total_calories));
        }
      }

      // Fetch weekly report for graph
      const weekly = await healthService.getWeeklyReport();
      if (weekly && weekly.daily_summaries && weekly.daily_summaries.length > 0) {
        const mapped = weekly.daily_summaries.map((item: any) => {
          const dateObj = new Date(item.date);
          const dayName = dateObj.toLocaleDateString(undefined, { weekday: 'short' });
          return {
            day: dayName,
            steps: item.steps || 0,
            cal: Math.round((item.steps || 0) * 0.045),
          };
        });
        setWeeklySteps(mapped);
      }
    } catch {
      // Retain baseline initialized values
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLiveActivity();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-slate-800">Sleep & Physical Activity</h2>
          <p className="text-sm text-slate-500">
            Track sleep architecture, circadian rhythm alignment, and daily active energy expenditure.
          </p>
        </div>

        <button
          onClick={fetchLiveActivity}
          className="p-2 bg-white rounded-xl border border-slate-200 text-slate-600 hover:text-cyan-600 shadow-sm"
          title="Refresh Activity Data"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Hero Sleep Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 rounded-3xl p-6 bg-gradient-to-br from-indigo-900 via-indigo-950 to-slate-900 text-white shadow-xl flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-2.5 rounded-2xl bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                <Moon className="w-5 h-5 fill-indigo-400" />
              </div>
              <span className="text-sm font-bold tracking-wide">Last Night's Sleep Analysis</span>
            </div>
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
              88% Quality Score
            </span>
          </div>

          <div className="my-6 flex flex-col sm:flex-row items-center justify-between gap-6">
            <div className="text-center sm:text-left">
              <div className="text-4xl font-black tracking-tight text-white">{sleepDurationStr}</div>
              <p className="text-xs text-indigo-300 mt-1">Total restorative sleep duration</p>
            </div>

            {/* Stages Bar */}
            <div className="w-full sm:w-64 space-y-2">
              <div className="flex justify-between text-xs text-slate-300 font-medium">
                <span>Deep: 2h 10m (30%)</span>
                <span>REM: 1h 45m (24%)</span>
              </div>
              <div className="h-3 w-full bg-slate-800 rounded-full flex overflow-hidden p-0.5">
                <div className="bg-indigo-600 h-full rounded-l-full w-[30%]" title="Deep" />
                <div className="bg-cyan-400 h-full w-[24%]" title="REM" />
                <div className="bg-blue-400 h-full w-[36%]" title="Light" />
                <div className="bg-amber-400 h-full rounded-r-full w-[10%]" title="Awake" />
              </div>
              <div className="flex justify-between text-[10px] text-slate-400">
                <span>Light: 2h 40m</span>
                <span>Awake: 45m</span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 pt-4 border-t border-indigo-800/60 text-center text-xs">
            <div>
              <div className="text-slate-400">Fell Asleep</div>
              <div className="font-bold text-white mt-0.5">10:45 PM</div>
            </div>
            <div>
              <div className="text-slate-400">Woke Up</div>
              <div className="font-bold text-white mt-0.5">06:05 AM</div>
            </div>
            <div>
              <div className="text-slate-400">Efficiency</div>
              <div className="font-bold text-emerald-400 mt-0.5">91%</div>
            </div>
          </div>
        </div>

        {/* Activity Summary Right */}
        <div className="lg:col-span-5 glass-card rounded-3xl p-6 border border-slate-100 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="p-2.5 rounded-2xl bg-cyan-50 text-cyan-600">
                <Footprints className="w-5 h-5" />
              </div>
              <span className="text-sm font-bold text-slate-800">Daily Activity Goal</span>
            </div>
            <span className="text-xs font-semibold text-slate-500">Goal: 6,000 steps</span>
          </div>

          <div className="my-4 text-center">
            <div className="text-4xl font-extrabold text-slate-800">{todaySteps.toLocaleString()}</div>
            <p className="text-xs text-slate-500 mt-0.5">
              {Math.min(100, Math.round((todaySteps / 6000) * 100))}% of daily target reached
            </p>
            <div className="w-full bg-slate-100 rounded-full h-2.5 mt-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-cyan-400 to-blue-600 h-2.5 rounded-full"
                style={{ width: `${Math.min(100, Math.round((todaySteps / 6000) * 100))}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 pt-3 border-t border-slate-100 text-center">
            <div className="p-3 bg-amber-50/60 rounded-2xl">
              <div className="flex items-center justify-center space-x-1 text-amber-600 text-xs font-semibold">
                <Flame className="w-4 h-4" />
                <span>Burned</span>
              </div>
              <div className="text-xl font-bold text-slate-800 mt-1">{calories} kcal</div>
            </div>
            <div className="p-3 bg-blue-50/60 rounded-2xl">
              <div className="flex items-center justify-center space-x-1 text-blue-600 text-xs font-semibold">
                <Award className="w-4 h-4" />
                <span>Distance</span>
              </div>
              <div className="text-xl font-bold text-slate-800 mt-1">{distanceKm} km</div>
            </div>
          </div>
        </div>
      </div>

      {/* Weekly Steps Chart */}
      <div className="glass-card rounded-2xl p-6 border border-slate-100 shadow-sm">
        <h3 className="text-base font-bold text-slate-800 mb-4">Weekly Step History</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weeklySteps}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
              <XAxis dataKey="day" tick={{ fontSize: 12, fill: '#64748b' }} />
              <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
              <Tooltip />
              <Bar dataKey="steps" fill="#06b6d4" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
