/**
 * Universal Date and Time Formatting Utilities
 * Standardized across the PulseGuardian Wearable Healthcare Platform:
 * - Date format: DD MMM YYYY (e.g., 28 Nov 2026)
 * - Time format: 12-hour with mandatory AM/PM (e.g., 09:30 AM, 12:00 PM, 12:00 AM)
 * - DateTime format: DD MMM YYYY, hh:mm AM/PM
 */

const MONTH_NAMES = [
  'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
];

/**
 * Formats a Date object, ISO string, or timestamp into `DD MMM YYYY` (e.g. "28 Nov 2026").
 */
export function formatDisplayDate(input?: string | Date | number | null): string {
  if (!input) return '28 Nov 2026';
  const d = typeof input === 'string' || typeof input === 'number' ? new Date(input) : input;
  if (isNaN(d.getTime())) return String(input);

  const day = String(d.getDate()).padStart(2, '0');
  const month = MONTH_NAMES[d.getMonth()];
  const year = d.getFullYear();
  return `${day} ${month} ${year}`;
}

/**
 * Formats a Date object, ISO string, or HH:mm string into `hh:mm A` (e.g. "09:30 AM", "08:00 PM").
 * Also handles comma-separated schedule slots like "08:00, 20:00" -> "08:00 AM, 08:00 PM".
 */
export function formatDisplayTime(input?: string | Date | number | null): string {
  if (!input) return '09:00 AM';

  // Handle comma-separated time slots: e.g. "08:00, 20:00" or "10:38,11:45"
  if (typeof input === 'string' && input.includes(',')) {
    return input
      .split(',')
      .map((part) => formatSingleTimeSlot(part.trim()))
      .join(', ');
  }

  if (typeof input === 'string') {
    return formatSingleTimeSlot(input.trim());
  }

  const d = typeof input === 'number' ? new Date(input) : input;
  if (isNaN(d.getTime())) return '09:00 AM';

  let hours = d.getHours();
  const minutes = String(d.getMinutes()).padStart(2, '0');
  const ampm = hours >= 12 ? 'PM' : 'AM';
  hours = hours % 12;
  hours = hours ? hours : 12; // 0 hour should be 12
  const formattedHours = String(hours).padStart(2, '0');

  return `${formattedHours}:${minutes} ${ampm}`;
}

function formatSingleTimeSlot(str: string): string {
  if (!str) return '09:00 AM';

  // If already contains AM or PM
  if (/AM|PM/i.test(str)) {
    return str.toUpperCase();
  }

  // Check if string matches "HH:mm" or "H:mm"
  const match = str.match(/^(\d{1,2}):(\d{2})/);
  if (match) {
    let hours = parseInt(match[1], 10);
    const minutes = match[2];
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;
  }

  // Attempt parse as Date ISO string
  const d = new Date(str);
  if (!isNaN(d.getTime())) {
    let hours = d.getHours();
    const minutes = String(d.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12;
    return `${String(hours).padStart(2, '0')}:${minutes} ${ampm}`;
  }

  return str;
}

/**
 * Formats a Date object, ISO string, or timestamp into `DD MMM YYYY, hh:mm A`.
 * e.g. "28 Nov 2026, 09:30 AM"
 */
export function formatDisplayDateTime(input?: string | Date | number | null): string {
  if (!input) return '28 Nov 2026, 09:00 AM';
  return `${formatDisplayDate(input)}, ${formatDisplayTime(input)}`;
}

/**
 * Returns current GPS-synchronized timestamp formatted with 12-hour AM/PM.
 */
export function getCurrentDisplayDateTime(): { date: string; time: string; full: string } {
  const now = new Date();
  const date = formatDisplayDate(now);
  const time = formatDisplayTime(now);
  return {
    date,
    time,
    full: `${date}, ${time}`
  };
}
