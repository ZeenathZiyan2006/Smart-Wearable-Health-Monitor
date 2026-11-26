import React from 'react';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showTagline?: boolean;
  tagline?: string;
  lightText?: boolean;
  iconOnly?: boolean;
}

export const PulseGuardianLogo: React.FC<LogoProps> = ({
  className = '',
  size = 'md',
  showTagline = true,
  tagline = 'Care. Protect. Live Better.',
  lightText = false,
  iconOnly = false,
}) => {
  const iconSizes = {
    sm: 'w-7 h-7',
    md: 'w-9 h-9',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16',
  };

  const titleSizes = {
    sm: 'text-base',
    md: 'text-xl',
    lg: 'text-2xl',
    xl: 'text-3xl',
  };

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      {/* PulseGuardian Heart + Person Icon */}
      <div className={`relative ${iconSizes[size]} flex-shrink-0 flex items-center justify-center`}>
        <svg viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-full drop-shadow-md">
          <defs>
            <linearGradient id="pgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#06b6d4" />
              <stop offset="50%" stopColor="#0284c7" />
              <stop offset="100%" stopColor="#1e40af" />
            </linearGradient>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>
          {/* Heart outline / body */}
          <path
            d="M50 88C50 88 15 62 15 36C15 22 26 12 40 12C46 12 50 16 50 16C50 16 54 12 60 12C74 12 85 22 85 36C85 62 50 88 50 88Z"
            stroke="url(#pgGradient)"
            strokeWidth="10"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
          {/* Inner person head */}
          <circle cx="50" cy="38" r="8" fill="url(#pgGradient)" />
          {/* Inner person body / arms hugging */}
          <path
            d="M36 60C36 50 42 46 50 46C58 46 64 50 64 60C64 65 58 70 50 72C42 70 36 65 36 60Z"
            fill="url(#pgGradient)"
          />
        </svg>
      </div>

      {/* Brand Name & Tagline */}
      {!iconOnly && (
        <div className="flex flex-col">
          <div className="flex items-center gap-1 font-extrabold tracking-tight leading-none">
            <span className={`${titleSizes[size]} ${lightText ? 'text-white' : 'text-slate-900'} font-['Outfit']`}>
              PulseGuardian
            </span>
            <span className={`${titleSizes[size]} text-cyan-500 font-['Outfit']`}>AI</span>
          </div>
          {showTagline && (
            <span className={`text-[11px] font-medium tracking-wide mt-1 ${lightText ? 'text-slate-300' : 'text-slate-500'}`}>
              {tagline}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
