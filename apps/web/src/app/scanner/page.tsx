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
      <div className="mb-4 flex justify-end">
        <DemographicSelect />
      </div>
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
