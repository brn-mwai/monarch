import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  users: defineTable({
    clerkId: v.string(),
    email: v.string(),
    name: v.optional(v.string()),
    tier: v.union(v.literal("free"), v.literal("pro"), v.literal("research")),
    creditsUsed: v.number(),
    creditsMax: v.number(),
    createdAt: v.number(),
  }).index("by_clerk_id", ["clerkId"]),

  scans: defineTable({
    userId: v.id("users"),
    inputText: v.optional(v.string()),
    inputMediaUrl: v.optional(v.string()),
    inputModality: v.union(
      v.literal("text"),
      v.literal("audio"),
      v.literal("video"),
    ),
    status: v.union(
      v.literal("queued"),
      v.literal("processing"),
      v.literal("complete"),
      v.literal("failed"),
    ),
    naa: v.optional(
      v.object({
        value: v.number(),
        aAff: v.number(),
        aDel: v.number(),
        classification: v.union(
          v.literal("LOW"),
          v.literal("MOD"),
          v.literal("HIGH"),
        ),
      }),
    ),
    landau: v.optional(
      v.object({
        freeEnergyM: v.array(v.number()),
        freeEnergyF: v.array(v.number()),
        equilibriumM: v.number(),
        susceptibility: v.optional(v.number()),
        externalFieldH: v.number(),
        betaJ: v.number(),
        alphaHat: v.number(),
      }),
    ),
    roiBreakdown: v.optional(
      v.array(
        v.object({
          name: v.string(),
          activation: v.number(),
          system: v.string(),
          vertexCount: v.number(),
        }),
      ),
    ),
    nTrs: v.optional(v.number()),
    activationStorageId: v.optional(v.id("_storage")),
    timeSeriesStorageId: v.optional(v.id("_storage")),
    multimodal: v.optional(
      v.object({
        textStorageId: v.optional(v.id("_storage")),
        audioStorageId: v.optional(v.id("_storage")),
        videoStorageId: v.optional(v.id("_storage")),
      }),
    ),
    createdAt: v.number(),
    completedAt: v.optional(v.number()),
    processingTimeMs: v.optional(v.number()),
  })
    .index("by_user", ["userId"])
    .index("by_status", ["status"])
    .index("by_user_created", ["userId", "createdAt"]),

  comparisons: defineTable({
    userId: v.id("users"),
    scanIdA: v.id("scans"),
    scanIdB: v.id("scans"),
    naaDifference: v.optional(v.number()),
    createdAt: v.number(),
  }).index("by_user", ["userId"]),

  batchJobs: defineTable({
    userId: v.id("users"),
    name: v.string(),
    totalItems: v.number(),
    completedItems: v.number(),
    status: v.union(
      v.literal("queued"),
      v.literal("processing"),
      v.literal("complete"),
      v.literal("failed"),
    ),
    csvStorageId: v.optional(v.id("_storage")),
    scanIds: v.optional(v.array(v.id("scans"))),
    createdAt: v.number(),
    completedAt: v.optional(v.number()),
  }).index("by_user", ["userId"]),
});
