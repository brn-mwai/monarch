'use client';

import { useSignIn } from '@clerk/nextjs';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function SignInPage() {
  const { isLoaded, signIn, setActive } = useSignIn();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded) return;
    setError('');
    setLoading(true);

    try {
      const result = await signIn.create({
        identifier: email,
        password,
      });

      if (result.status === 'complete' && result.createdSessionId) {
        await setActive({ session: result.createdSessionId });
        router.push('/scanner');
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : (err as { errors?: { message: string }[] })?.errors?.[0]?.message ??
            'Sign in failed. Check your credentials.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center bg-black px-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Image
            src="/monarch-logo.svg"
            alt="Monarch"
            width={140}
            height={34}
            className="mx-auto h-8 w-auto opacity-90"
          />
          <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.25em] text-white/40">
            Sign in to the scanner
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50"
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              className="w-full rounded-lg border border-white/15 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-white/25 focus:border-white/40"
              placeholder="you@example.com"
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50"
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="w-full rounded-lg border border-white/15 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-white/25 focus:border-white/40"
              placeholder="Your password"
            />
          </div>

          {error && (
            <p className="rounded-lg border border-red-500/20 bg-red-500/5 px-3 py-2 text-xs text-red-400">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading || !isLoaded}
            className="w-full rounded-lg bg-white py-3 font-mono text-sm font-semibold uppercase tracking-wider text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <p className="mt-6 text-center text-xs text-white/40">
          No account?{' '}
          <Link href="/sign-up" className="text-white/70 hover:text-white">
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
