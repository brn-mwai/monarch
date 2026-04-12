import type { ReactNode } from 'react';

import { SplitLayout } from '@/components/SplitLayout';

export default function BatchLayout({ children }: { children: ReactNode }) {
  return <SplitLayout>{children}</SplitLayout>;
}
