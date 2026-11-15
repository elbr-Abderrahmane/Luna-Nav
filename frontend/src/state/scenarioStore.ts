import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";
import type { SiteInput } from "../api/types";
import { MAX_CARDS, MIN_CARDS, WINDOW_HOURS } from "../lib/constants";

// README 7. Card ids are frontend-only ("card-1"...). The API identifies a scenario by its label.
export interface ScenarioCard {
  id: string;
  site: SiteInput; // catalog id or { lat_deg, lon_deg, name? }
  startUtc: string;
  windowDays?: number; // mission duration, default one lunar day
  label?: string;
}

interface ScenarioData {
  cards: ScenarioCard[]; // 2..4 for compare
  activeCardId: string | null; // the card shown in site view and timeline
  sliderHours: number; // 0 .. 708.7, position on the timeline
  sweepSiteId: string | null; // site of the open date sweep
}

interface ScenarioActions {
  /** Returns the new id, or null when MAX_CARDS is reached (show a hint). */
  addCard: (card: Omit<ScenarioCard, "id">) => string | null;
  removeCard: (id: string) => void;
  updateCard: (id: string, patch: Partial<Omit<ScenarioCard, "id">>) => void;
  setActiveCard: (id: string | null) => void;
  setSliderHours: (h: number) => void;
  setSweepSiteId: (id: string | null) => void;
  reset: () => void;
}

const initial: ScenarioData = { cards: [], activeCardId: null, sliderHours: 0, sweepSiteId: null };

const nextId = (cards: ScenarioCard[]) =>
  `card-${cards.reduce((max, c) => Math.max(max, Number(c.id.replace("card-", "")) || 0), 0) + 1}`;

export const useScenarioStore = create<ScenarioData & ScenarioActions>()(
  persist(
    (set, get) => ({
      ...initial,
      addCard: (card) => {
        const cards = get().cards;
        if (cards.length >= MAX_CARDS) return null;
        const id = nextId(cards);
        set({ cards: [...cards, { ...card, id }], activeCardId: get().activeCardId ?? id });
        return id;
      },
      removeCard: (id) => {
        const cards = get().cards.filter((c) => c.id !== id);
        const active = get().activeCardId === id ? (cards[0]?.id ?? null) : get().activeCardId;
        set({ cards, activeCardId: active, sliderHours: active === get().activeCardId ? get().sliderHours : 0 });
      },
      // Only this card's results are refetched (query keys include site + startUtc).
      updateCard: (id, patch) => set({ cards: get().cards.map((c) => (c.id === id ? { ...c, ...patch } : c)) }),
      setActiveCard: (id) => set({ activeCardId: id, sliderHours: 0 }),
      setSliderHours: (h) => set({ sliderHours: Math.min(WINDOW_HOURS, Math.max(0, h)) }),
      setSweepSiteId: (id) => set({ sweepSiteId: id }),
      reset: () => set({ ...initial }),
    }),
    {
      name: "lunanav-scenarios",
      // sessionStorage so a refresh keeps the cards. If it is unavailable the state stays in memory.
      storage: createJSONStorage(() => sessionStorage),
    },
  ),
);

export const canCompare = (cards: ScenarioCard[]) => cards.length >= MIN_CARDS;
