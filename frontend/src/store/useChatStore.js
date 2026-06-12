import { create } from "zustand";
import { persist } from "zustand/middleware";

const INITIAL_MESSAGES = [
  {
    role: "assistant",
    content: "Hello! I am SentinelX, your Autonomous Regulatory Intelligence & Compliance Operating System. I am ready to answer complex compliance queries based on the active document.",
    sources: null,
    debug: null
  }
];

export const useChatStore = create(
  persist(
    (set, get) => ({
      // Messages per document
      messagesByDoc: {},

      // Active request tracking
      activeRequests: {},

      // Active payloads per document (for refresh recovery)
      activePayloads: {},

      // Pending graph query
      pendingGraphQuery: null,

      // Add message
      addMessage: (docId, message) =>
        set((state) => ({
          messagesByDoc: {
            ...state.messagesByDoc,
            [docId]: [
              ...(state.messagesByDoc[docId] || INITIAL_MESSAGES),
              message
            ]
          }
        })),

      // Update last message
      updateLastMessage: (docId, content, extra = {}) =>
        set((state) => {
          const msgs = [...(state.messagesByDoc[docId] || INITIAL_MESSAGES)];
          if (msgs.length > 0) {
            msgs[msgs.length - 1] = {
              ...msgs[msgs.length - 1],
              content,
              isStreaming: false,
              ...extra
            };
          }
          return {
            messagesByDoc: {
              ...state.messagesByDoc,
              [docId]: msgs
            }
          };
        }),

      // Get messages for doc
      getMessages: (docId) => get().messagesByDoc[docId] || INITIAL_MESSAGES,

      // Clear doc messages (only on new upload)
      clearDoc: (docId) =>
        set((state) => {
          const m = { ...state.messagesByDoc };
          delete m[docId];
          return { messagesByDoc: m };
        }),

      // Pending graph query
      setPendingGraphQuery: (query) => set({ pendingGraphQuery: query }),

      clearPendingGraphQuery: () => set({ pendingGraphQuery: null }),

      // Active request status
      setRequestStatus: (docId, status) =>
        set((state) => ({
          activeRequests: {
            ...state.activeRequests,
            [docId]: status
            // status: 'pending' | 'processing' | 'complete' | 'error'
          }
        })),

      getRequestStatus: (docId) => get().activeRequests[docId] || "idle",

      // Active payloads for recovery
      setPayload: (docId, payload) =>
        set((state) => ({
          activePayloads: {
            ...state.activePayloads,
            [docId]: payload
          }
        })),

      clearPayload: (docId) =>
        set((state) => {
          const p = { ...state.activePayloads };
          delete p[docId];
          return { activePayloads: p };
        })
    }),
    {
      name: "sentinelx-chat-store",
      // sessionStorage use karo — tab close pe clear ho jaaye
      storage: {
        getItem: (key) => sessionStorage.getItem(key),
        setItem: (key, val) => sessionStorage.setItem(key, val),
        removeItem: (key) => sessionStorage.removeItem(key)
      },
      // Persist messages, graph queries, status, and recovery payloads
      partialize: (state) => ({
        messagesByDoc: state.messagesByDoc,
        pendingGraphQuery: state.pendingGraphQuery,
        activeRequests: state.activeRequests,
        activePayloads: state.activePayloads
      })
    }
  )
);
