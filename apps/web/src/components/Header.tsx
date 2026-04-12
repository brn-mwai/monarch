'use client';

import {
  Show,
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
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Scanner', href: '/scanner' },
  { label: 'Report', href: '/report' },
  { label: 'Batch', href: '/batch' },
  { label: 'Research', href: 'https://cuea.edu', external: true },
  { label: 'AMD', href: 'https://www.amd.com/en/developer.html', external: true },
];

/**
 * Fixed top header bar shared by every page.
 *
 * 48px tall, full width, pure black background, 1px subtle bottom
 * border. Mirrors the TRIBE v2 demo header layout: brand block on the
 * left, primary nav + external research links on the right.
 *
 * Active page link is rendered in pure white; others sit at white/60.
 */
export function Header() {
  const pathname = usePathname() ?? '/';

  return (
    <header className="fixed inset-x-0 top-0 z-50 flex h-16 items-center border-b border-white/10 bg-black px-10">
      {/* Left: build tag */}
      <Link
        href="/"
        className="font-mono text-xs uppercase tracking-[0.25em] text-white/55 transition-colors hover:text-white"
      >
        M-V1
      </Link>

      {/* Center: logo (absolutely centered so the left/right widths
          do not affect its alignment) */}
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
        {NAV_ITEMS.map((item) => {
          const isActive =
            !item.external &&
            (pathname === item.href || pathname.startsWith(`${item.href}/`));
          const className = `inline-flex items-center gap-1 text-sm transition-colors ${
            isActive ? 'text-white' : 'text-white/60 hover:text-white'
          }`;
          if (item.external) {
            return (
              <a
                key={item.label}
                href={item.href}
                target="_blank"
                rel="noopener noreferrer"
                className={className}
              >
                {item.label}
                <ArrowUpRight size={11} weight="bold" className="opacity-60" />
              </a>
            );
          }
          return (
            <Link key={item.label} href={item.href} className={className}>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <Show when="signed-in">
        <UserButton
          appearance={{
            elements: { avatarBox: 'h-7 w-7' },
          }}
        />
      </Show>
      <Show when="signed-out">
        <SignInButton mode="modal">
          <button
            type="button"
            className="rounded-full border border-white/20 px-4 py-1.5 text-xs text-white/70 transition-colors hover:border-white/50 hover:text-white"
          >
            Sign In
          </button>
        </SignInButton>
      </Show>
      </div>
    </header>
  );
}
