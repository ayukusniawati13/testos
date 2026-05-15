/**
 * Single AudioEngine instance. Wraps a Web Audio AudioContext + AnalyserNode +
 * MediaElementAudioSource for the current track. Reusable for both preview
 * playback and export capture.
 */

export interface BeatState {
  /** 0..1 instantaneous beat pulse (1 = beat just hit). Decays toward 0. */
  pulse: number;
  /** Total bass energy this frame in 0..1. */
  bass: number;
  /** Total mid energy this frame in 0..1. */
  mid: number;
  /** Total treble energy this frame in 0..1. */
  treble: number;
  /** Detected BPM (rough). 0 if not yet detected. */
  bpm: number;
  /** Timestamp (audioCtx.currentTime) of last beat hit. */
  lastBeatAt: number;
  /** Monotonically increasing beat counter. */
  beatCount: number;
}

export interface AudioEngineSnapshot {
  freq: Uint8Array;
  time: Uint8Array;
  beat: BeatState;
  audioCtx: AudioContext;
  /** Current playback time (s) on the underlying media element */
  currentTime: number;
  /** Duration (s) or 0 if unknown */
  duration: number;
  playing: boolean;
}

export class AudioEngine {
  private static _instance: AudioEngine | null = null;
  static get(): AudioEngine {
    if (!this._instance) this._instance = new AudioEngine();
    return this._instance;
  }

  audio: HTMLAudioElement;
  ctx: AudioContext;
  analyser: AnalyserNode;
  source: MediaElementAudioSourceNode | null = null;
  gain: GainNode;
  freqArray: Uint8Array<ArrayBuffer>;
  timeArray: Uint8Array<ArrayBuffer>;
  beat: BeatState = {
    pulse: 0,
    bass: 0,
    mid: 0,
    treble: 0,
    bpm: 0,
    lastBeatAt: 0,
    beatCount: 0,
  };
  sensitivity = 0.55;

  // Beat detection state
  private bassHistory: number[] = [];
  private readonly historyLen = 43; // ~1s at 60fps
  private lastBeatTimes: number[] = [];

  private constructor() {
    this.audio = new Audio();
    this.audio.crossOrigin = "anonymous";
    this.audio.preload = "auto";
    const Ctx =
      window.AudioContext ||
      (window as unknown as { webkitAudioContext: typeof AudioContext })
        .webkitAudioContext;
    this.ctx = new Ctx();
    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 2048;
    this.analyser.smoothingTimeConstant = 0.78;
    this.gain = this.ctx.createGain();
    this.gain.gain.value = 1;
    this.analyser.connect(this.gain);
    this.gain.connect(this.ctx.destination);
    this.freqArray = new Uint8Array(new ArrayBuffer(this.analyser.frequencyBinCount));
    this.timeArray = new Uint8Array(new ArrayBuffer(this.analyser.fftSize));
  }

  setSrc(url: string) {
    if (this.audio.src === url) return;
    this.audio.src = url;
    this.audio.load();
    if (!this.source) {
      // First time: connect the audio element to the analyser
      this.source = this.ctx.createMediaElementSource(this.audio);
      this.source.connect(this.analyser);
    }
  }

  async play() {
    if (this.ctx.state === "suspended") await this.ctx.resume();
    await this.audio.play();
  }
  pause() {
    this.audio.pause();
  }
  toggle() {
    if (this.audio.paused) return this.play();
    this.pause();
    return Promise.resolve();
  }
  seek(t: number) {
    if (Number.isFinite(t)) this.audio.currentTime = Math.max(0, t);
  }
  setVolume(v: number) {
    this.gain.gain.value = v;
  }
  setSensitivity(v: number) {
    this.sensitivity = Math.max(0, Math.min(1, v));
  }

  /**
   * Analyse one frame. Returns a SHARED snapshot — do not store references
   * to the typed arrays across frames (they're reused).
   */
  tick(): AudioEngineSnapshot {
    this.analyser.getByteFrequencyData(this.freqArray);
    this.analyser.getByteTimeDomainData(this.timeArray);

    // Compute energy bands
    const bins = this.freqArray.length;
    // bass: ~0-200Hz, mid: ~200-2kHz, treble: 2kHz+
    // sampleRate / fftSize gives Hz per bin
    const hzPerBin = this.ctx.sampleRate / this.analyser.fftSize;
    const bassEnd = Math.max(1, Math.floor(200 / hzPerBin));
    const midEnd = Math.min(bins, Math.floor(2000 / hzPerBin));

    let bassSum = 0;
    let midSum = 0;
    let trebleSum = 0;
    for (let i = 0; i < bassEnd; i++) bassSum += this.freqArray[i];
    for (let i = bassEnd; i < midEnd; i++) midSum += this.freqArray[i];
    for (let i = midEnd; i < bins; i++) trebleSum += this.freqArray[i];

    const bass = bassSum / bassEnd / 255;
    const mid = midSum / Math.max(1, midEnd - bassEnd) / 255;
    const treble = trebleSum / Math.max(1, bins - midEnd) / 255;

    // Beat detection: energy-based with adaptive threshold
    this.bassHistory.push(bass);
    if (this.bassHistory.length > this.historyLen) this.bassHistory.shift();
    let avg = 0;
    for (const v of this.bassHistory) avg += v;
    avg /= Math.max(1, this.bassHistory.length);

    // Higher sensitivity -> lower threshold multiplier
    const thresholdMul = 1.65 - this.sensitivity * 0.85; // 0.8 .. 1.65
    const now = this.ctx.currentTime;
    const minInterval = 0.18; // 333 BPM upper cap
    const beatHit =
      bass > avg * thresholdMul &&
      bass > 0.18 &&
      now - this.beat.lastBeatAt > minInterval;

    if (beatHit) {
      this.beat.pulse = 1;
      this.beat.lastBeatAt = now;
      this.beat.beatCount += 1;
      this.lastBeatTimes.push(now);
      if (this.lastBeatTimes.length > 16) this.lastBeatTimes.shift();
      if (this.lastBeatTimes.length >= 4) {
        const diffs: number[] = [];
        for (let i = 1; i < this.lastBeatTimes.length; i++) {
          diffs.push(this.lastBeatTimes[i] - this.lastBeatTimes[i - 1]);
        }
        diffs.sort((a, b) => a - b);
        const median = diffs[Math.floor(diffs.length / 2)];
        if (median > 0) {
          let bpm = 60 / median;
          while (bpm < 70) bpm *= 2;
          while (bpm > 180) bpm /= 2;
          // smooth update
          this.beat.bpm = this.beat.bpm
            ? this.beat.bpm * 0.75 + bpm * 0.25
            : bpm;
        }
      }
    } else {
      // pulse decay
      this.beat.pulse = Math.max(0, this.beat.pulse - 0.06);
    }
    this.beat.bass = bass;
    this.beat.mid = mid;
    this.beat.treble = treble;

    return {
      freq: this.freqArray,
      time: this.timeArray,
      beat: this.beat,
      audioCtx: this.ctx,
      currentTime: this.audio.currentTime,
      duration: Number.isFinite(this.audio.duration) ? this.audio.duration : 0,
      playing: !this.audio.paused,
    };
  }

  /** Returns a MediaStream containing just the audio output (for export). */
  getOutputStream(): MediaStream {
    const dest = this.ctx.createMediaStreamDestination();
    this.gain.connect(dest);
    return dest.stream;
  }
}
