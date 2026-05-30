import { create } from "zustand";

export const useChatStore = create((set) => ({
  messages: [
    { 
      role: "assistant", 
      content: "Hello! I am SentinelX, your Autonomous Regulatory Intelligence & Compliance Operating System. I am ready to answer complex compliance queries based on the active document.",
      sources: null,
      debug: null
    }
  ],
  documentId: null,
  setDocumentId: (id) => set({ documentId: id }),
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  setMessages: (messagesOrFn) => set((state) => ({
    messages: typeof messagesOrFn === "function" ? messagesOrFn(state.messages) : messagesOrFn
  })),
  clearMessages: () => set({
    messages: [
      { 
        role: "assistant", 
        content: "Hello! I am SentinelX, your Autonomous Regulatory Intelligence & Compliance Operating System. I am ready to answer complex compliance queries based on the active document.",
        sources: null,
        debug: null
      }
    ]
  }),
}));
