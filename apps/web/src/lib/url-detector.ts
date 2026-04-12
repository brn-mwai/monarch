// ============================================================
// url-detector.ts - client-side platform detection from URLs
// ============================================================

export type PlatformType =
  | 'youtube'
  | 'youtube_shorts'
  | 'tiktok'
  | 'instagram'
  | 'facebook'
  | 'spotify'
  | 'soundcloud'
  | 'twitter'
  | 'vimeo'
  | 'reddit'
  | 'blog'
  | 'unknown';

export interface DetectedMedia {
  platform: PlatformType;
  url: string;
  mediaTypes: ('video' | 'audio' | 'image' | 'text')[];
  displayName: string;
  iconEmoji: string;
}

const PATTERNS: {
  pattern: RegExp;
  platform: PlatformType;
  media: ('video' | 'audio' | 'image' | 'text')[];
  name: string;
  icon: string;
}[] = [
  { pattern: /youtube\.com\/shorts\//i, platform: 'youtube_shorts', media: ['video', 'audio'], name: 'YouTube Shorts', icon: '▶' },
  { pattern: /(?:youtube\.com\/(?:watch|embed|v)|youtu\.be\/)/i, platform: 'youtube', media: ['video', 'audio'], name: 'YouTube', icon: '▶' },
  { pattern: /tiktok\.com\/@[^/]+\/video\//i, platform: 'tiktok', media: ['video', 'audio'], name: 'TikTok', icon: '♪' },
  { pattern: /instagram\.com\/(?:p|reel|tv)\//i, platform: 'instagram', media: ['video', 'image'], name: 'Instagram', icon: '◻' },
  { pattern: /facebook\.com\/(?:.*\/videos\/|watch)/i, platform: 'facebook', media: ['video', 'audio'], name: 'Facebook', icon: 'f' },
  { pattern: /open\.spotify\.com\/track\//i, platform: 'spotify', media: ['audio'], name: 'Spotify', icon: '♫' },
  { pattern: /soundcloud\.com\//i, platform: 'soundcloud', media: ['audio'], name: 'SoundCloud', icon: '♪' },
  { pattern: /(?:twitter\.com|x\.com)\/\w+\/status\//i, platform: 'twitter', media: ['video', 'text'], name: 'X / Twitter', icon: '𝕏' },
  { pattern: /vimeo\.com\/\d+/i, platform: 'vimeo', media: ['video', 'audio'], name: 'Vimeo', icon: '▶' },
  { pattern: /reddit\.com\/r\/\w+\/comments\//i, platform: 'reddit', media: ['text', 'video'], name: 'Reddit', icon: '⬆' },
];

export function detectPlatform(input: string): DetectedMedia | null {
  const trimmed = input.trim();
  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    return null;
  }
  for (const { pattern, platform, media, name, icon } of PATTERNS) {
    if (pattern.test(trimmed)) {
      return { platform, url: trimmed, mediaTypes: media, displayName: name, iconEmoji: icon };
    }
  }
  return {
    platform: 'blog',
    url: trimmed,
    mediaTypes: ['text'],
    displayName: 'Article',
    iconEmoji: '▤',
  };
}
