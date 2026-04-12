import { query } from "./_generated/server";
import { v } from "convex/values";

export const getCredits = query({
  args: { clerkId: v.optional(v.string()) },
  handler: async (ctx, args) => {
    if (!args.clerkId) return { remaining: 0, max: 0 };
    const user = await ctx.db
      .query("users")
      .withIndex("by_clerk_id", (q) => q.eq("clerkId", args.clerkId))
      .unique();
    if (!user) return { remaining: 0, max: 0 };
    return {
      remaining: Math.max(0, user.creditsMax - user.creditsUsed),
      max: user.creditsMax,
    };
  },
});

export const getScanHistory = query({
  args: { clerkId: v.string() },
  handler: async (ctx, args) => {
    const user = await ctx.db
      .query("users")
      .withIndex("by_clerk_id", (q) => q.eq("clerkId", args.clerkId))
      .unique();
    if (!user) return [];
    return await ctx.db
      .query("scans")
      .withIndex("by_user_created", (q) => q.eq("userId", user._id))
      .order("desc")
      .take(20);
  },
});
