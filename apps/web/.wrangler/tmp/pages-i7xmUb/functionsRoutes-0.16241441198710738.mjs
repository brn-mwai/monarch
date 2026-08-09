import { onRequestPost as __api_chat_ts_onRequestPost } from "C:\\Users\\Windows\\Downloads\\monarch\\apps\\web\\functions\\api\\chat.ts"

export const routes = [
    {
      routePath: "/api/chat",
      mountPath: "/api",
      method: "POST",
      middlewares: [],
      modules: [__api_chat_ts_onRequestPost],
    },
  ]