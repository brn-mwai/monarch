'use client';

import {
  SignedIn,
  SignedOut,
  SignInButton,
  UserButton,
} from '@clerk/nextjs';
import { ArrowUpRight } from '@phosphor-icons/react/dist/ssr';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

interface NavItem {
  label: string;
  href: string;
  external?: boolean;
  /** When true, only visible to authenticated users. */
  protected?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Scanner', href: '/scanner', protected: true },
  { label: 'Report', href: '/report', protected: true },
  { label: 'Batch', href: '/batch', protected: true },
  { label: 'Research', href: 'https://cuea.edu', external: true },
  { label: 'AMD', href: 'https://www.amd.com/en/developer.html', external: true },
];

/**
 * Fixed top header bar on every page.
 *
 * Public visitors see: logo + Research + AMD + Sign In.
 * Authenticated users see: logo + Scanner + Report + Batch + Research + AMD + UserButton.
 */
export function Header() {
  const pathname = usePathname() ?? '/';

  const renderNavItem = (item: NavItem) => {
    const isActive =
      !item.external &&
      (pathname === item.href || pathname.startsWith(`${item.href}/`));
    const cls = `inline-flex items-center gap-1 text-sm transition-colors ${
      isActive ? 'text-white' : 'text-white/60 hover:text-white'
    }`;
    if (item.external) {
      return (
        <a
          key={item.label}
          href={item.href}
          target="_blank"
          rel="noopener noreferrer"
          className={cls}
        >
          {item.label}
          <ArrowUpRight size={11} weight="bold" className="opacity-60" />
        </a>
      );
    }
    return (
      <Link key={item.label} href={item.href} className={cls}>
        {item.label}
      </Link>
    );
  };

  const publicLinks = NAV_ITEMS.filter((i) => !i.protected);
  const protectedLinks = NAV_ITEMS.filter((i) => i.protected);

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center border-b border-white/10 bg-black px-10">
      {/* Left: build tag */}
      <Link
        href="/"
        className="font-mono text-xs uppercase tracking-[0.25em] text-white/55 transition-colors hover:text-white"
      >
        M-V1
      </Link>

      {/* Center: logo */}
      <Link
        href="/"
        className="group absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2"
      >
        <Image
          src="/monarch-logo.svg"
          alt="Monarch"
          width={160}
          height={39}
          priority
          className="h-9 w-auto opacity-90 transition-opacity group-hover:opacity-100"
        />
      </Link>

      {/* Right: Nav + Auth */}
      <div className="ml-auto flex items-center gap-6">
        <nav className="flex items-center gap-6">
          {/* Protected routes: only visible when signed in */}
          <SignedIn>
            {protectedLinks.map(renderNavItem)}
          </SignedIn>

          {/* Public links: always visible */}
          {publicLinks.map(renderNavItem)}
        </nav>

        <SignedIn>
          <UserButton
            appearance={{
              elements: { avatarBox: 'h-7 w-7' },
            }}
          />
        </SignedIn>
        <SignedOut>
          <SignInButton mode="modal">
            <button
              type="button"
              className="rounded-full border border-white/20 px-4 py-1.5 text-xs text-white/70 transition-colors hover:border-white/50 hover:text-white"
            >
              Sign In
            </button>
          </SignInButton>
        </SignedOut>
      </div>
    </header>
  );
}
