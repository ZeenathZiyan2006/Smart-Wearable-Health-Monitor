import io
import logging
import struct
import wave
from typing import Optional

logger = logging.getLogger("pulseguardian.voice.validator")


def parse_webm_duration(data: bytes) -> Optional[float]:
    """
    Parses audio duration from in-memory WebM / Matroska EBML container.
    Inspects EBML header magic (0x1A45DFA3), locates Segment Info Duration (0x4489),
    and adjusts for TimecodeScale (0x2AD7B1, default 1ms = 1,000,000ns).
    Returns duration in seconds, or None if unparseable/missing.
    """
    if len(data) < 12:
        return None

    # Check EBML header magic
    if not data.startswith(b"\x1a\x45\xdf\xa3"):
        return None

    dur_idx = data.find(b"\x44\x89")
    if dur_idx == -1:
        return None

    offset = dur_idx + 2
    if offset >= len(data):
        return None

    len_byte = data[offset]
    mask = 0x80
    vlen = 1
    while mask > 0 and not (len_byte & mask):
        mask >>= 1
        vlen += 1

    if vlen > 8 or offset + vlen > len(data):
        return None

    size = len_byte & (mask - 1)
    for i in range(1, vlen):
        size = (size << 8) | data[offset + i]

    val_offset = offset + vlen
    if val_offset + size > len(data) or size not in (4, 8):
        return None

    raw_val = data[val_offset : val_offset + size]
    if size == 4:
        raw_dur = struct.unpack(">f", raw_val)[0]
    else:
        raw_dur = struct.unpack(">d", raw_val)[0]

    # Look for TimecodeScale (0x2A 0xD7 0xB1)
    scale_idx = data.find(b"\x2a\xd7\xb1")
    timecode_scale = 1_000_000  # Default 1,000,000 ns = 1 ms
    if scale_idx != -1 and scale_idx < dur_idx:
        s_off = scale_idx + 3
        if s_off < len(data):
            s_len_byte = data[s_off]
            s_mask = 0x80
            s_vlen = 1
            while s_mask > 0 and not (s_len_byte & s_mask):
                s_mask >>= 1
                s_vlen += 1
            s_size = s_len_byte & (s_mask - 1)
            for i in range(1, s_vlen):
                s_size = (s_size << 8) | data[s_off + i]
            s_val_off = s_off + s_vlen
            if s_val_off + s_size <= len(data) and 1 <= s_size <= 8:
                scale_val = 0
                for b in data[s_val_off : s_val_off + s_size]:
                    scale_val = (scale_val << 8) | b
                if scale_val > 0:
                    timecode_scale = scale_val

    duration_seconds = (raw_dur * timecode_scale) / 1_000_000_000.0
    return duration_seconds if duration_seconds > 0 else None


def parse_m4a_mvhd_duration(data: bytes) -> Optional[float]:
    """
    Parses audio duration from in-memory MP4/M4A moov->mvhd header atom.
    Extracts timescale and duration fields for version 0 and version 1 atoms.
    Returns duration in seconds, or None if unparseable/missing.
    """
    mvhd_idx = data.find(b"mvhd")
    if mvhd_idx == -1:
        return None

    ver_offset = mvhd_idx + 4
    if ver_offset >= len(data):
        return None

    version = data[ver_offset]
    if version == 0:
        if ver_offset + 20 > len(data):
            return None
        timescale, duration = struct.unpack(">II", data[ver_offset + 12 : ver_offset + 20])
    elif version == 1:
        if ver_offset + 32 > len(data):
            return None
        timescale, duration = struct.unpack(">IQ", data[ver_offset + 20 : ver_offset + 32])
    else:
        return None

    if timescale == 0 or duration == 0:
        return None

    return duration / float(timescale)


def inspect_audio_duration(audio_bytes: bytes, mime_type: str) -> float:
    """
    Inspects audio duration in seconds from an in-memory byte buffer without writing to disk.
    Supports WAV, MP3, OGG, FLAC, M4A, and WebM using TinyTag, standard wave, Mutagen,
    and direct container header parsing.
    Raises ValueError if the audio is corrupted, truncated, unparseable, or missing duration.
    """
    if not audio_bytes or len(audio_bytes) == 0:
        raise ValueError("Audio payload cannot be empty.")

    norm_mime = (mime_type or "").lower().strip()

    # 1. WAV / X-WAV
    if norm_mime in ("audio/wav", "audio/x-wav"):
        # First attempt: standard library wave module
        try:
            with wave.open(io.BytesIO(audio_bytes), "rb") as wav:
                frames = wav.getnframes()
                rate = wav.getframerate()
                if rate > 0 and frames >= 0:
                    return frames / float(rate)
        except Exception:
            pass

        # Second attempt: TinyTag
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_obj=io.BytesIO(audio_bytes), filename="audio.wav")
            if tag.duration is not None and tag.duration > 0:
                return float(tag.duration)
        except Exception:
            pass

        raise ValueError("Invalid, corrupted, or unparseable WAV audio stream.")

    # 2. MP3 / MPEG
    elif norm_mime in ("audio/mpeg", "audio/mp3"):
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_obj=io.BytesIO(audio_bytes), filename="audio.mp3")
            if tag.duration is not None and tag.duration > 0:
                return float(tag.duration)
        except Exception:
            pass

        try:
            import mutagen
            mut = mutagen.File(io.BytesIO(audio_bytes))
            if mut and mut.info and getattr(mut.info, "length", None) and mut.info.length > 0:
                return float(mut.info.length)
        except Exception:
            pass

        raise ValueError("Invalid, corrupted, or unparseable MP3 audio stream.")

    # 3. OGG
    elif norm_mime == "audio/ogg":
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_obj=io.BytesIO(audio_bytes), filename="audio.ogg")
            if tag.duration is not None and tag.duration > 0:
                return float(tag.duration)
        except Exception:
            pass

        try:
            import mutagen
            mut = mutagen.File(io.BytesIO(audio_bytes))
            if mut and mut.info and getattr(mut.info, "length", None) and mut.info.length > 0:
                return float(mut.info.length)
        except Exception:
            pass

        raise ValueError("Invalid, corrupted, or unparseable OGG audio stream.")

    # 4. FLAC
    elif norm_mime == "audio/flac":
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_obj=io.BytesIO(audio_bytes), filename="audio.flac")
            if tag.duration is not None and tag.duration > 0:
                return float(tag.duration)
        except Exception:
            pass

        try:
            import mutagen
            mut = mutagen.File(io.BytesIO(audio_bytes))
            if mut and mut.info and getattr(mut.info, "length", None) and mut.info.length > 0:
                return float(mut.info.length)
        except Exception:
            pass

        raise ValueError("Invalid, corrupted, or unparseable FLAC audio stream.")

    # 5. M4A
    elif norm_mime == "audio/x-m4a":
        try:
            from tinytag import TinyTag
            tag = TinyTag.get(file_obj=io.BytesIO(audio_bytes), filename="audio.m4a")
            if tag.duration is not None and tag.duration > 0:
                return float(tag.duration)
        except Exception:
            pass

        try:
            import mutagen
            mut = mutagen.File(io.BytesIO(audio_bytes))
            if mut and mut.info and getattr(mut.info, "length", None) and mut.info.length > 0:
                return float(mut.info.length)
        except Exception:
            pass

        dur = parse_m4a_mvhd_duration(audio_bytes)
        if dur is not None and dur > 0:
            return float(dur)

        raise ValueError("Invalid, corrupted, or unparseable M4A audio stream.")

    # 6. WebM
    elif norm_mime == "audio/webm":
        dur = parse_webm_duration(audio_bytes)
        if dur is not None and dur > 0:
            return float(dur)
        raise ValueError("Invalid, corrupted, or unparseable WebM audio stream.")

    else:
        raise ValueError(f"Unsupported audio MIME type '{mime_type}' for duration validation.")
