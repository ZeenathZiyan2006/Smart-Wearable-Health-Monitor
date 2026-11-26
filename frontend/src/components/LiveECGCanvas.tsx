import React, { useEffect, useRef, useState } from 'react';
import { Play, Pause, Maximize2, Info } from 'lucide-react';

interface LiveECGCanvasProps {
  heartRate?: number;
  className?: string;
}

export const LiveECGCanvas: React.FC<LiveECGCanvasProps> = ({ heartRate = 72, className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(true);
  const [fullscreen, setFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    let t = 0;
    const width = canvas.width;
    const height = canvas.height;
    const baselineY = height / 2;

    // ECG wave points buffer
    const points: number[] = new Array(width).fill(baselineY);

    const getEcgSample = (phase: number) => {
      // P wave: 0.12 - 0.22
      if (phase > 0.12 && phase < 0.22) {
        return Math.sin((phase - 0.12) / 0.1 * Math.PI) * 12;
      }
      // Q dip: 0.36 - 0.38
      if (phase >= 0.36 && phase < 0.38) {
        return -8;
      }
      // R peak: 0.38 - 0.42
      if (phase >= 0.38 && phase < 0.42) {
        return 55 * Math.sin((phase - 0.38) / 0.04 * Math.PI);
      }
      // S dip: 0.42 - 0.44
      if (phase >= 0.42 && phase < 0.44) {
        return -14;
      }
      // T wave: 0.60 - 0.78
      if (phase > 0.60 && phase < 0.78) {
        return Math.sin((phase - 0.60) / 0.18 * Math.PI) * 18;
      }
      return (Math.random() - 0.5) * 1.5; // baseline noise
    };

    const render = () => {
      if (isPlaying) {
        t += 1;
        const cycleFrames = Math.max(30, Math.round((60 * 60) / (heartRate || 72)));
        const phase = (t % cycleFrames) / cycleFrames;
        const val = baselineY - getEcgSample(phase);

        points.shift();
        points.push(val);
      }

      ctx.clearRect(0, 0, width, height);

      // Grid
      ctx.strokeStyle = 'rgba(0, 240, 255, 0.06)';
      ctx.lineWidth = 1;
      const gridSize = 16;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // ECG Glow effect
      ctx.shadowColor = '#00F0FF';
      ctx.shadowBlur = 8;
      ctx.strokeStyle = '#00F0FF';
      ctx.lineWidth = 2.2;
      ctx.beginPath();

      for (let i = 0; i < points.length; i++) {
        if (i === 0) {
          ctx.moveTo(i, points[i]);
        } else {
          ctx.lineTo(i, points[i]);
        }
      }
      ctx.stroke();

      // Sweeping scan head indicator
      ctx.shadowBlur = 12;
      ctx.shadowColor = '#00FFA3';
      ctx.fillStyle = '#00FFA3';
      ctx.beginPath();
      ctx.arc(width - 2, points[points.length - 1], 4, 0, Math.PI * 2);
      ctx.fill();

      ctx.shadowBlur = 0;

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [isPlaying, heartRate]);

  const toggleFullscreen = () => {
    if (!containerRef.current) return;
    if (!fullscreen) {
      if (containerRef.current.requestFullscreen) {
        containerRef.current.requestFullscreen();
      }
      setFullscreen(true);
    } else {
      if (document.exitFullscreen) {
        document.exitFullscreen();
      }
      setFullscreen(false);
    }
  };

  return (
    <div
      ref={containerRef}
      className={`relative bg-[#0d1527] rounded-2xl p-4 border border-cyan-500/20 shadow-xl overflow-hidden text-white ${className}`}
    >
      {/* Top Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          </div>
          <span className="text-sm font-semibold tracking-wide text-white">Live ECG Monitor</span>
          <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30" title="Simulated dynamic synthetic cardiac rhythm">
            Simulated DSP
          </span>
        </div>

        <div className="flex items-center space-x-3 text-xs text-slate-400 font-mono">
          <span>250 Hz</span>
          <span>•</span>
          <span>Lead I</span>
          <div className="flex items-center space-x-1 ml-2">
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="p-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
              title={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            </button>
            <button
              onClick={toggleFullscreen}
              className="p-1 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-300 transition-colors"
              title="Fullscreen"
            >
              <Maximize2 className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {/* Canvas */}
      <div className="relative w-full h-36 flex items-center justify-center bg-[#070d19]/80 rounded-xl overflow-hidden border border-cyan-500/10">
        <canvas
          ref={canvasRef}
          width={480}
          height={144}
          className="w-full h-full object-cover"
        />
      </div>

      {/* Bottom Telemetry Metrics with simulation disclaimer note */}
      <div className="flex items-center justify-between mt-3 px-2 text-[11px] font-mono text-slate-400">
        <div>
          PR <span className="text-white font-medium">98 ms</span>
        </div>
        <div>
          QRS <span className="text-white font-medium">82 ms</span>
        </div>
        <div>
          QT <span className="text-white font-medium">380 ms</span>
        </div>
        <div className="text-[9px] text-slate-500 italic">
          *Assistive simulation (Not a diagnostic ECG)
        </div>
      </div>
    </div>
  );
};
