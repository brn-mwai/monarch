let context: AudioContext | null = null;
let noise: AudioBuffer | null = null;

function audio() {
  if (typeof window === 'undefined') return null;
  if (!context) {
    const Constructor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Constructor) return null;
    context = new Constructor();
  }
  if (context.state === 'suspended') void context.resume();
  return context;
}

function noiseBuffer(ctx: AudioContext) {
  if (noise) return noise;
  const length = Math.floor(ctx.sampleRate * 0.6);
  noise = ctx.createBuffer(1, length, ctx.sampleRate);
  const data = noise.getChannelData(0);
  let brown = 0;
  for (let index = 0; index < length; index += 1) {
    const white = Math.random() * 2 - 1;
    brown = (brown + 0.04 * white) / 1.04;
    data[index] = white * 0.55 + brown * 3.2;
  }
  return noise;
}

export function playFlip(fast: boolean) {
  const ctx = audio();
  if (!ctx) return;
  const now = ctx.currentTime;
  const duration = fast ? 0.18 : 0.42;
  const volume = fast ? 0.12 : 0.26;

  const source = ctx.createBufferSource();
  source.buffer = noiseBuffer(ctx);
  source.playbackRate.value = 0.9 + Math.random() * 0.25;

  const band = ctx.createBiquadFilter();
  band.type = 'bandpass';
  band.Q.value = 0.7;
  band.frequency.setValueAtTime(3200, now);
  band.frequency.exponentialRampToValueAtTime(900, now + duration);

  const gain = ctx.createGain();
  gain.gain.setValueAtTime(0.0001, now);
  gain.gain.exponentialRampToValueAtTime(volume, now + duration * 0.18);
  gain.gain.exponentialRampToValueAtTime(volume * 0.45, now + duration * 0.55);
  gain.gain.exponentialRampToValueAtTime(0.0001, now + duration);

  source.connect(band).connect(gain).connect(ctx.destination);
  source.start(now);
  source.stop(now + duration + 0.05);

  const thump = ctx.createOscillator();
  thump.type = 'sine';
  thump.frequency.setValueAtTime(140, now + duration * 0.85);
  thump.frequency.exponentialRampToValueAtTime(60, now + duration + 0.08);
  const thumpGain = ctx.createGain();
  thumpGain.gain.setValueAtTime(0.0001, now + duration * 0.85);
  thumpGain.gain.exponentialRampToValueAtTime(fast ? 0.03 : 0.07, now + duration * 0.9);
  thumpGain.gain.exponentialRampToValueAtTime(0.0001, now + duration + 0.1);
  thump.connect(thumpGain).connect(ctx.destination);
  thump.start(now + duration * 0.85);
  thump.stop(now + duration + 0.12);
}
