import { create } from "zustand";

export const useStore = create((set, get) => ({
  // Auth state
  token: localStorage.getItem("token") || null,
  user: JSON.parse(localStorage.getItem("user") || "null"),
  
  // Document state
  documents: [],
  selectedDocId: localStorage.getItem("document_id") || "",
  
  // Alerts / notifications
  notifications: [],
  
  // Toasts state
  toasts: [],
  
  // Actions
  setAuth: (token, user) => {
    if (token) localStorage.setItem("token", token);
    else localStorage.removeItem("token");
    
    if (user) localStorage.setItem("user", JSON.stringify(user));
    else localStorage.removeItem("user");
    
    set({ token, user });
  },
  
  logout: () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    localStorage.removeItem("document_id");
    set({ token: null, user: null, selectedDocId: "" });
  },
  
  setDocuments: (documents) => {
    set({ documents });
    // If there is no active doc selected, default to the first one in the list
    const currentSelected = get().selectedDocId;
    if (documents.length > 0 && (!currentSelected || !documents.some(d => d.id === currentSelected))) {
      const defaultId = documents[0].id;
      get().setSelectedDocId(defaultId);
    }
  },
  
  setSelectedDocId: (selectedDocId) => {
    if (selectedDocId) {
      localStorage.setItem("document_id", selectedDocId);
    } else {
      localStorage.removeItem("document_id");
    }
    set({ selectedDocId });
    // Dispatch storage event to keep other hooks in sync if they rely on it
    window.dispatchEvent(new Event("storage"));
  },
  
  pushToast: (message, type = "info") => {
    const id = crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 9);
    set((state) => ({
      toasts: [...state.toasts, { id, message, type }]
    }));
    setTimeout(() => {
      get().removeToast(id);
    }, 2800);
  },
  
  removeToast: (id) => {
    set((state) => ({
      toasts: state.toasts.filter((t) => t.id !== id)
    }));
  },
  
  addNotification: (notification) => {
    set((state) => ({
      notifications: [notification, ...state.notifications].slice(0, 50)
    }));
  }
}));
