import { mutation, query } from "./_generated/server";
import { v } from "convex/values";
import { assertOwnership, requireUser } from "./lib/auth";
import { checkRateLimit } from "./lib/rateLimit";

// === Queries ===

export const getUserScans = query({
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
      .take(50);
  },
});

export const getScan = query({
  args: { scanId: v.id("scans"), clerkId: v.string() },
  handler: async (ctx, args) => {
    const scan = await ctx.db.get(args.scanId);
    if (!scan) throw new Error("Scan not found");
    await assertOwnership(ctx, scan.userId, args.clerkId);
    return scan;
  },
});

export const getActivationUrl = query({
  args: { scanId: v.id("scans"), clerkId: v.string() },
  handler: async (ctx, args) => {
    const scan = await ctx.db.get(args.scanId);
    if (!scan) throw new Error("Scan not found");
    await assertOwnership(ctx, scan.userId, args.clerkId);
    if (!scan.activationStorageId) return null;
    return await ctx.storage.getUrl(scan.activationStorageId);
  },
});

// === Mutations ===

export const createScan = mutation({
  args: {
    clerkId: v.string(),
    inputText: v.optional(v.string()),
    inputMediaUrl: v.optional(v.string()),
    inputModality: v.union(
      v.literal("text"),
      v.literal("audio"),
      v.literal("video"),
    ),
  },
  handler: async (ctx, args) => {
    if (!/^user_[a-zA-Z0-9]+$/.test(args.clerkId)) {
      throw new Error("Invalid user identifier");
    }
    if (args.inputText) {
      if (args.inputText.length > 10000) {
        throw new Error("Text input exceeds maximum length");
      }
      if (args.inputText.length < 10) {
        throw new Error("Text input is too short");
      }
      if (args.inputText.includes("\0")) {
        throw new Error("Input contains invalid characters");
      }
    }

    let user = await ctx.db
      .query("users")
      .withIndex("by_clerk_id", (q) => q.eq("clerkId", args.clerkId))
      .unique();

    if (!user) {
      const userId = await ctx.db.insert("users", {
        clerkId: args.clerkId,
        email: "",
        tier: "free",
        creditsUsed: 0,
        creditsMax: 3,
        createdAt: Date.now(),
      });
      user = (await ctx.db.get(userId))!;
    }

    await checkRateLimit(ctx, user._id, "scan");

    if (user.creditsUsed >= user.creditsMax) {
      throw new Error("No scan credits remaining");
    }

    const scanId = await ctx.db.insert("scans", {
      userId: user._id,
      inputText: args.inputText,
      inputMediaUrl: args.inputMediaUrl,
      inputModality: args.inputModality,
      status: "queued",
      createdAt: Date.now(),
    });

    await ctx.db.patch(user._id, {
      creditsUsed: user.creditsUsed + 1,
    });

    return scanId;
  },
});

export const updateScanStatus = mutation({
  args: {
    scanId: v.id("scans"),
    status: v.union(
      v.literal("queued"),
      v.literal("processing"),
      v.literal("complete"),
      v.literal("failed"),
    ),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.scanId, { status: args.status });
  },
});

export const updateScanResults = mutation({
  args: {
    scanId: v.id("scans"),
    naa: v.object({
      value: v.number(),
      aAff: v.number(),
      aDel: v.number(),
      classification: v.union(
        v.literal("LOW"),
        v.literal("MOD"),
        v.literal("HIGH"),
      ),
    }),
    landau: v.object({
      freeEnergyM: v.array(v.number()),
      freeEnergyF: v.array(v.number()),
      equilibriumM: v.number(),
      susceptibility: v.optional(v.number()),
      externalFieldH: v.number(),
      betaJ: v.number(),
      alphaHat: v.number(),
    }),
    roiBreakdown: v.array(
      v.object({
        name: v.string(),
        activation: v.number(),
        system: v.string(),
        vertexCount: v.number(),
      }),
    ),
    nTrs: v.number(),
    activationStorageId: v.id("_storage"),
    timeSeriesStorageId: v.optional(v.id("_storage")),
    multimodal: v.optional(
      v.object({
        textStorageId: v.optional(v.id("_storage")),
        audioStorageId: v.optional(v.id("_storage")),
        videoStorageId: v.optional(v.id("_storage")),
      }),
    ),
    processingTimeMs: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.scanId, {
      status: "complete",
      naa: args.naa,
      landau: args.landau,
      roiBreakdown: args.roiBreakdown,
      nTrs: args.nTrs,
      activationStorageId: args.activationStorageId,
      timeSeriesStorageId: args.timeSeriesStorageId,
      multimodal: args.multimodal,
      completedAt: Date.now(),
      processingTimeMs: args.processingTimeMs,
    });
  },
});
