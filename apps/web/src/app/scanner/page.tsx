'use client';

import { useState } from 'react';

import { BatchTab } from '@/components/scanner-tabs/BatchTab';
import { CompareTab } from '@/components/scanner-tabs/CompareTab';
import { MultimodalTab } from '@/components/scanner-tabs/MultimodalTab';
import { ScanTab } from '@/components/scanner-tabs/ScanTab';
import { TabNav, type Tab } from '@/components/TabNav';

const TABS: Tab[] = [
  { id: 'scan', label: 'Scan Content' },
  { id: 'compare', label: 'Compare A / B' },
  { id: 'batch', label: 'Batch Audit' },
  { id: 'multimodal', label: 'Multimodal' },
];

export default function ScannerPage() {
  const [activeTab, setActiveTab] = useState<string>('scan');

  return (
    <div>
      <TabNav tabs={TABS} active={activeTab} onChange={setActiveTab} />
      <div className="mt-5">
        {activeTab === 'scan' && <ScanTab />}
        {activeTab === 'compare' && <CompareTab />}
        {activeTab === 'batch' && <BatchTab />}
        {activeTab === 'multimodal' && <MultimodalTab />}
      </div>
    </div>
  );
}
