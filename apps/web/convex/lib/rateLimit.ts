import type { MutationCtx } from "../_generated/server";
import type { Id } from "../_generated/dataModel";

interface RateLimitConfig {
  maxRequests: number;
  windowMs: number;
}

const RATE_LIMITS: Record<string, RateLimitConfig> = {
  scan: { maxRequests: 10, windowMs: 60 * 1000 },
  compare: { maxRequests: 5, windowMs: 60 * 1000 },
  batch: { maxRequests: 2, windowMs: 5 * 60 * 1000 },
  upload: { maxRequests: 10, windowMs: 60 * 1000 },
};

/**
 * Check rate limit for a user action. Throws if exceeded.
 */
export async function checkRateLimit(
  ctx: MutationCtx,
  userId: Id<"users">,
  action: keyof typeof RATE_LIMITS,
): Promise<void> {
  const config = RATE_LIMITS[action];
  if (!config) return;

  const windowStart = Date.now() - config.windowMs;

  const recentScans = await ctx.db
    .query("scans")
    .withIndex("by_user_created", (q) =>
      q.eq("userId", userId).gte("createdAt", windowStart),
    )
    .collect();

  if (recentScans.length >= config.maxRequests) {
    const retryAfterMs =
      config.windowMs - (Date.now() - recentScans[0].createdAt);
    throw new Error(
      `Rate limit exceeded: max ${config.maxRequests} ${action}(s) per ${config.windowMs / 1000}s. ` +
        `Retry after ${Math.ceil(retryAfterMs / 1000)}s.`,
    );
  }
}
