import { create } from "zustand";

export interface Msg {
  id: number;
  from: "bot" | "user";
  text: string;
  chips?: string[];
}

interface AssistantState {
  open: boolean;
  messages: Msg[];
  tour: number | null; // index of the current tour step, null = no tour running
  exported: boolean; // set when the user exports (the tour waits for it)
  unread: number;
  typing: boolean;
  setOpen: (open: boolean) => void;
  push: (from: Msg["from"], text: string, chips?: string[]) => void;
  clear: () => void;
  setTour: (tour: number | null) => void;
  setTyping: (typing: boolean) => void;
  noteExport: () => void;
}

let counter = 0;

// Not persisted on purpose: a fresh page starts with a fresh greeting.
export const useAssistantStore = create<AssistantState>()((set, get) => ({
  open: false,
  messages: [],
  tour: null,
  exported: false,
  unread: 0,
  typing: false,
  setOpen: (open) => set({ open, unread: open ? 0 : get().unread }),
  push: (from, text, chips) =>
    set({
      messages: [...get().messages, { id: ++counter, from, text, chips }],
      unread: from === "bot" && !get().open ? get().unread + 1 : get().unread,
    }),
  clear: () => set({ messages: [] }),
  setTour: (tour) => set({ tour }),
  setTyping: (typing) => set({ typing }),
  noteExport: () => set({ exported: true }),
}));
