// ============================================================
// echarts-theme.ts -- shared monochrome theme for Monarch
// ============================================================
//
// Black background, white text, hot/fire accent colors. Every chart
// in the app should pull from these constants so the visual language
// stays consistent and a single change here cascades everywhere.
// ============================================================

/** Base ECharts option fragment that any chart can spread into its config. */
export const monarchTheme = {
  backgroundColor: 'transparent',
  textStyle: {
    color: '#FFFFFF',
    fontFamily: 'var(--font-geist-mono), ui-monospace, SFMono-Regular, monospace',
  },
  title: {
    textStyle: {
      color: '#FFFFFF',
      fontSize: 13,
      fontWeight: 400,
    },
    left: 'center',
    top: 0,
  },
  legend: {
    textStyle: { color: 'rgba(255,255,255,0.7)' },
    icon: 'roundRect',
    itemWidth: 10,
    itemHeight: 10,
  },
  grid: {
    top: 36,
    right: 24,
    bottom: 30,
    left: 48,
    containLabel: true,
  },
  xAxis: {
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
    axisTick: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
    axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    nameTextStyle: { color: 'rgba(255,255,255,0.6)' },
  },
  yAxis: {
    axisLine: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
    axisTick: { lineStyle: { color: 'rgba(255,255,255,0.2)' } },
    axisLabel: { color: 'rgba(255,255,255,0.6)', fontSize: 10 },
    splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
    nameTextStyle: { color: 'rgba(255,255,255,0.6)' },
  },
  tooltip: {
    backgroundColor: 'rgba(0,0,0,0.92)',
    borderColor: 'rgba(255,255,255,0.2)',
    borderWidth: 1,
    textStyle: { color: '#FFFFFF', fontSize: 11 },
    extraCssText: 'backdrop-filter: blur(8px); border-radius: 6px;',
  },
};

/** Hot/fire color stops -- mirror the brain renderer's COLORMAP_CSS_GRADIENT. */
export const FIRE_COLORS = [
  '#000000',
  '#1E0000',
  '#500000',
  '#8C0000',
  '#BE0000',
  '#DC1900',
  '#F54100',
  '#FF6E00',
  '#FFA500',
  '#FFD70A',
  '#FFF050',
  '#FFFCB4',
  '#FFFFFF',
];

/** NAA classification accent colors (used sparingly, only for HIGH/MOD/LOW labels). */
export const NAA_COLORS = {
  LOW: '#9CDCB6',
  MOD: '#FFD60A',
  HIGH: '#FF6E00',
} as const;

/** RGB modality channel colors -- match ActivationMapper R=video G=text B=audio. */
export const MULTIMODAL_COLORS = {
  text: '#FF4444',
  audio: '#44FF66',
  video: '#4488FF',
} as const;

/** Standard chart container className for consistent spacing. */
export const CHART_CARD_CLASS =
  'rounded-lg border border-white/10 bg-white/[0.02] p-4';
