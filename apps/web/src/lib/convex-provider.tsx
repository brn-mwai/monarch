'use client';

import { ConvexProviderWithClerk } from 'convex/react-clerk';
import { ConvexReactClient } from 'convex/react';
import { useAuth } from '@clerk/nextjs';
import { type ReactNode } from 'react';

// Only construct a Convex client when a real deployment URL is configured.
// With a placeholder/empty URL the client would spam websocket connection
// errors; the app uses no Convex hooks on the rendered paths, so we simply
// render children without the provider in that case.
const convexUrl = process.env.NEXT_PUBLIC_CONVEX_URL ?? '';
const isRealDeployment =
  /^https:\/\/[^/]+\.convex\.cloud/.test(convexUrl) &&
  !convexUrl.includes('placeholder');

const convex = isRealDeployment ? new ConvexReactClient(convexUrl) : null;

export function ConvexClientProvider({ children }: { children: ReactNode }) {
  if (!convex) return <>{children}</>;
  return (
    <ConvexProviderWithClerk client={convex} useAuth={useAuth}>
      {children}
    </ConvexProviderWithClerk>
  );
}
