#!/usr/bin/env python3
"""Original synthesized pop BGM (128 BPM, C major I-V-vi-IV).
No copyrighted material: every sound is generated here."""
import math, random, struct, wave, os

def make_bgm(path, dur=30.0, sr=44100):
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

    beat = 60.0 / 128; bar = beat * 4
    chords = [(130.81, [261.63, 329.63, 392.00, 523.25]),
              (98.00, [246.94, 293.66, 392.00, 493.88]),
              (110.00, [261.63, 329.63, 440.00, 523.25]),
              (87.31, [220.00, 349.23, 440.00, 523.25])]
    melody = [523.25, 587.33, 659.25, 783.99, 659.25, 587.33, 523.25, 440.00,
              493.88, 523.25, 587.33, 659.25, 587.33, 523.25, 493.88, 440.00]
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
