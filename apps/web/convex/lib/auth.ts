import type { MutationCtx, QueryCtx } from "../_generated/server";
import type { Id } from "../_generated/dataModel";

/**
 * Verify the authenticated user owns the requested resource.
 * Throws if the resource belongs to a different user.
 */
export async function assertOwnership(
  ctx: QueryCtx | MutationCtx,
  resourceUserId: Id<"users">,
  clerkId: string,
): Promise<void> {
  const user = await ctx.db
    .query("users")
    .withIndex("by_clerk_id", (q) => q.eq("clerkId", clerkId))
    .unique();

  if (!user || user._id !== resourceUserId) {
    throw new Error("Unauthorized: you do not own this resource");
  }
}

/**
 * Get the authenticated user or throw.
 */
export async function requireUser(
  ctx: QueryCtx | MutationCtx,
  clerkId: string,
) {
  const user = await ctx.db
    .query("users")
    .withIndex("by_clerk_id", (q) => q.eq("clerkId", clerkId))
    .unique();

  if (!user) {
    throw new Error("Unauthorized: user not found");
  }

  return user;
}
