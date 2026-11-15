#!/usr/bin/env python3
"""Original synthesized pop BGM (128 BPM, C major I-V-vi-IV).
No copyrighted material: every sound is generated here."""
import math, random, struct, wave, os

def make_bgm(path, dur=30.0, sr=44100, bpm=128, chords=None, melody=None):
    """Original synthesized pop BGM.

    Default: C major I-V-vi-IV at 128 BPM (the original yutai theme).
    Themes can pass their own bpm / chords / melody, e.g. the calendar
    theme uses G major at ~112 BPM. Chords are (bass_freq, [note freqs]).
    """
    chords = chords or [(130.81, [261.63, 329.63, 392.00, 523.25]),
                        (98.00, [246.94, 293.66, 392.00, 493.88]),
                        (110.00, [261.63, 329.63, 440.00, 523.25]),
                        (87.31, [220.00, 349.23, 440.00, 523.25])]
    melody = melody or [523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 440.00,
                        493.88, 523.25, 587.33, 659.25, 587.33, 523.25, 493.88, 440.00]
    n = int(sr * dur)
    mono = [0.0] * n

    def add(start, length, fn, vol=1.0):
        s = int(start * sr); e = min(n, int((start + length) * sr))
        for i in range(s, e):
            mono[i] += fn((i - s) / sr, length) * vol

    def tone(freq, harmonics=(1.0,)):
        def f(t, d):
            env = math.exp(-2.2 * t / d) if d else 0
            atk = min(1.0, t / 0.01)
            return sum(math.sin(2 * math.pi * freq * k * t) * h / k
                       for k, h in enumerate(harmonics, 1)) * env * atk
        return f

    def kick(t, d):
        phase = 2 * math.pi * (45 * t + 75 * (1 - math.exp(-18 * t)) / 18)
        return math.sin(phase) * math.exp(-9 * t)

    rng = random.Random(7)
    def hat(t, d): return (rng.random() * 2 - 1) * math.exp(-55 * t)
    def clap(t, d): return (rng.random() * 2 - 1) * math.exp(-18 * t)

    beat = 60.0 / bpm; bar = beat * 4
    melody = melody
    b = 0
    while b * bar < dur:
        t0 = b * bar
        bass_f, chord_notes = chords[b % 4]
        for bt in range(4):
            add(t0 + bt * beat, beat * 0.9, tone(bass_f, (1.0, 0.4)), 0.55)
            add(t0 + bt * beat, 0.22, kick, 0.9)
            add(t0 + bt * beat + beat / 2, 0.05, hat, 0.18)
        add(t0 + beat, 0.18, clap, 0.25); add(t0 + beat * 3, 0.18, clap, 0.25)
        for e in range(8):
            add(t0 + e * beat / 2, beat / 2 * 0.9, tone(chord_notes[e % 4] * 2, (1.0, 0.3)), 0.16)
        if b % 2 == 0:
            for e in range(8):
                add(t0 + e * beat / 2, beat * 0.8, tone(melody[(b // 2 * 3 + e) % 16] * 2, (1.0, 0.2)), 0.10)
        b += 1
    peak = max(0.001, max(abs(x) for x in mono)); gain = 0.82 / peak
    fade = int(sr * 1.0); frames = bytearray()
    for i, x in enumerate(mono):
        g = gain * (i / fade if i < fade else 1.0)
        if i > n - fade: g *= (n - i) / fade
        v = int(max(-1.0, min(1.0, x * g)) * 32767)
        frames += struct.pack("<hh", v, v)
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(bytes(frames))
    return path


# Theme presets: (bpm, chords, melody). Calendar theme: G major, ~112 BPM.
CALENDAR_THEME = {
    "bpm": 112,
    "chords": [(98.00, [196.00, 246.94, 293.66, 392.00]),   # G
               (73.42, [146.83, 220.00, 293.66, 369.99]),   # D
               (82.41, [164.81, 196.00, 246.94, 329.63]),   # Em
               (65.41, [130.81, 196.00, 261.63, 329.63])],  # C
    "melody": [392.00, 440.00, 493.88, 587.33, 493.88, 440.00, 392.00, 329.63,
               369.99, 392.00, 440.00, 493.88, 440.00, 392.00, 369.99, 329.63],
}

# --- Per-series theme registry (Hide's rule, 2026-11-15: every video theme
# gets its own BGM). The digest series intentionally reuses its source
# edition's theme. ---
YUTAI_THEME = {
    "bpm": 128,
    "chords": [(130.81, [261.63, 329.63, 392.00, 523.25]),
               (98.00, [246.94, 293.66, 392.00, 493.88]),
               (110.00, [261.63, 329.63, 440.00, 523.25]),
               (87.31, [220.00, 349.23, 440.00, 523.25])],
    "melody": [523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 440.00,
               493.88, 523.25, 587.33, 659.25, 587.33, 523.25, 493.88, 440.00],
}
DIVIDEND_THEME = {  # D major, stately 104 BPM (deep green x gold design)
    "bpm": 104,
    "chords": [(73.42, [146.83, 220.00, 293.66, 369.99]),   # D
               (61.74, [123.47, 185.00, 246.94, 293.66]),   # Bm
               (98.00, [196.00, 246.94, 293.66, 392.00]),   # G
               (110.00, [220.00, 277.18, 329.63, 440.00])],  # A
    "melody": [293.66, 329.63, 369.99, 440.00, 369.99, 329.63, 293.66, 246.94,
               277.18, 293.66, 329.63, 369.99, 329.63, 293.66, 277.18, 246.94],
}
FUND_THEME = {  # A major, spacious 100 BPM (overseas funds, violet design)
    "bpm": 100,
    "chords": [(110.00, [220.00, 277.18, 329.63, 440.00]),  # A
               (82.41, [164.81, 246.94, 329.63, 415.30]),   # E
               (92.50, [185.00, 220.00, 277.18, 369.99]),   # F#m
               (73.42, [146.83, 220.00, 293.66, 369.99])],  # D
    "melody": [440.00, 554.37, 659.25, 554.37, 440.00, 329.63, 369.99, 440.00,
               493.88, 440.00, 369.99, 329.63, 293.66, 329.63, 369.99, 440.00],
}
FUND_JP_THEME = {  # E major, bright 118 BPM (domestic funds, indigo design)
    "bpm": 118,
    "chords": [(82.41, [164.81, 207.65, 246.94, 329.63]),   # E
               (61.74, [246.94, 311.13, 369.99, 493.88]),   # B
               (69.30, [138.59, 207.65, 277.18, 329.63]),   # C#m
               (110.00, [220.00, 277.18, 329.63, 440.00])],  # A
    "melody": [329.63, 415.30, 493.88, 659.25, 493.88, 415.30, 369.99, 329.63,
               277.18, 329.63, 415.30, 493.88, 415.30, 369.99, 329.63, 246.94],
}
DEEPDIVE_THEME = {  # F major, chill 92 BPM (weekly deep-dive, navy design)
    "bpm": 92,
    "chords": [(87.31, [174.61, 220.00, 261.63, 349.23]),   # F
               (110.00, [220.00, 261.63, 329.63, 440.00]),  # Am
               (73.42, [146.83, 220.00, 293.66, 349.23]),   # Dm
               (58.27, [174.61, 233.08, 293.66, 349.23])],  # Bb
    "melody": [349.23, 329.63, 293.66, 261.63, 293.66, 329.63, 349.23, 440.00,
               392.00, 349.23, 329.63, 293.66, 261.63, 293.66, 220.00, 261.63],
}
BARGAIN_THEME = {  # A minor, driving 132 BPM (weekly bargain, crimson design)
    "bpm": 132,
    "chords": [(110.00, [220.00, 261.63, 329.63, 440.00]),  # Am
               (87.31, [174.61, 220.00, 261.63, 349.23]),   # F
               (130.81, [261.63, 329.63, 392.00, 523.25]),  # C
               (98.00, [196.00, 246.94, 293.66, 392.00])],  # G
    "melody": [440.00, 523.25, 659.25, 523.25, 440.00, 392.00, 329.63, 392.00,
               440.00, 523.25, 587.33, 659.25, 587.33, 523.25, 493.88, 440.00],
}
