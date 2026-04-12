'use client';

import { useSignUp } from '@clerk/nextjs';
import Image from 'next/image';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';

export default function SignUpPage() {
  const { isLoaded, signUp, setActive } = useSignUp();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [pendingVerification, setPendingVerification] = useState(false);

  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded) return;
    setError('');
    setLoading(true);

    try {
      await signUp.create({ emailAddress: email, password });
      await signUp.prepareEmailAddressVerification({ strategy: 'email_code' });
      setPendingVerification(true);
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : (err as { errors?: { message: string }[] })?.errors?.[0]?.message ??
            'Sign up failed.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!isLoaded) return;
    setError('');
    setLoading(true);

    try {
      const result = await signUp.attemptEmailAddressVerification({ code });
      if (result.status === 'complete' && result.createdSessionId) {
        await setActive({ session: result.createdSessionId });
        router.push('/scanner');
      }
    } catch (err: unknown) {
      const msg =
        err instanceof Error
          ? err.message
          : (err as { errors?: { message: string }[] })?.errors?.[0]?.message ??
            'Verification failed.';
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
            {pendingVerification ? 'Check your email' : 'Create your account'}
          </p>
        </div>

        {!pendingVerification ? (
          <form onSubmit={handleSignUp} className="space-y-4">
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
                minLength={8}
                autoComplete="new-password"
                className="w-full rounded-lg border border-white/15 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none transition-colors placeholder:text-white/25 focus:border-white/40"
                placeholder="Min 8 characters"
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
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
        ) : (
          <form onSubmit={handleVerify} className="space-y-4">
            <p className="text-sm text-white/60">
              We sent a verification code to{' '}
              <span className="font-semibold text-white">{email}</span>.
            </p>
            <div>
              <label
                htmlFor="code"
                className="mb-1.5 block font-mono text-[10px] uppercase tracking-wider text-white/50"
              >
                Verification code
              </label>
              <input
                id="code"
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                required
                autoComplete="one-time-code"
                className="w-full rounded-lg border border-white/15 bg-white/[0.03] px-4 py-3 text-center font-mono text-lg tracking-[0.5em] text-white outline-none transition-colors placeholder:text-white/25 focus:border-white/40"
                placeholder="------"
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
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>
        )}

        <p className="mt-6 text-center text-xs text-white/40">
          Already have an account?{' '}
          <Link href="/sign-in" className="text-white/70 hover:text-white">
            Sign in
          </Link>
        </p>

        <p className="mt-8 text-center text-[10px] leading-relaxed text-white/25">
          By creating an account you agree that Monarch scan results are
          predicted population-level estimates, not individual neural
          measurements.
        </p>
      </div>
    </div>
  );
}
