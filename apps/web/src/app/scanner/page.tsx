'use client';

import { BatchTab } from '@/components/scanner-tabs/BatchTab';
import { CompareTab } from '@/components/scanner-tabs/CompareTab';
import { MultimodalTab } from '@/components/scanner-tabs/MultimodalTab';
import { ScanTab } from '@/components/scanner-tabs/ScanTab';
import { DemographicSelect } from '@/components/scanner/DemographicSelect';
import { TabNav, type Tab } from '@/components/TabNav';
import { useScanState } from '@/lib/scan-store';

const TABS: Tab[] = [
  { id: 'scan', label: 'Scan Content' },
  { id: 'compare', label: 'Compare A / B' },
  { id: 'batch', label: 'Batch Audit' },
  { id: 'multimodal', label: 'Multimodal' },
];

export default function ScannerPage() {
  const { state, dispatch } = useScanState();
  const activeTab = state.activeTab;

  return (
    <div>
      <header className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="font-mono text-xl font-light tracking-wider text-white">
            Neural scanner
          </h1>
          <p className="mt-1 font-mono text-[11px] uppercase tracking-wider text-white/40">
            Predict how media engages emotion versus reasoning
          </p>
        </div>
        <DemographicSelect />
      </header>
      <TabNav
        tabs={TABS}
        active={activeTab}
        onChange={(tab) => dispatch({ type: 'SET_TAB', tab })}
      />
      <div className="mt-5">
        {activeTab === 'scan' && <ScanTab />}
        {activeTab === 'compare' && <CompareTab />}
        {activeTab === 'batch' && <BatchTab />}
        {activeTab === 'multimodal' && <MultimodalTab />}
      </div>
    </div>
  );
}
