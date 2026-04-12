import type { ReactNode } from 'react';

import { SplitLayout } from '@/components/SplitLayout';

export default function ScannerLayout({ children }: { children: ReactNode }) {
  return <SplitLayout>{children}</SplitLayout>;
}
