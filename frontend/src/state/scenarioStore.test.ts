import { beforeEach, describe, expect, it } from "vitest";
import { WINDOW_HOURS } from "../lib/constants";
import { canCompare, useScenarioStore as store } from "./scenarioStore";

const card = (site: string) => ({ site, startUtc: "2027-01-10T00:00:00Z" });

describe("scenarioStore", () => {
  beforeEach(() => store.getState().reset());

  it("allows at most 4 cards and returns null for the 5th", () => {
    for (const s of ["a", "b", "c", "d"]) expect(store.getState().addCard(card(s))).not.toBeNull();
    expect(store.getState().addCard(card("e"))).toBeNull();
    expect(store.getState().cards).toHaveLength(4);
  });
  it("first card becomes active; compare needs 2 cards", () => {
    store.getState().addCard(card("a"));
    expect(store.getState().activeCardId).toBe("card-1");
    expect(canCompare(store.getState().cards)).toBe(false);
    store.getState().addCard(card("b"));
    expect(canCompare(store.getState().cards)).toBe(true);
  });
  it("ids stay unique after removing a card", () => {
    store.getState().addCard(card("a"));
    store.getState().addCard(card("b"));
    store.getState().removeCard("card-1");
    expect(store.getState().addCard(card("c"))).toBe("card-3");
    expect(store.getState().activeCardId).toBe("card-2");
  });
  it("clamps the slider to one lunar day", () => {
    store.getState().setSliderHours(-5);
    expect(store.getState().sliderHours).toBe(0);
    store.getState().setSliderHours(99999);
    expect(store.getState().sliderHours).toBeCloseTo(WINDOW_HOURS);
  });
  it("updating a card changes only that card", () => {
    store.getState().addCard(card("a"));
    store.getState().addCard(card("b"));
    store.getState().updateCard("card-2", { startUtc: "2027-02-08T00:00:00Z" });
    expect(store.getState().cards[0].startUtc).toBe("2027-01-10T00:00:00Z");
    expect(store.getState().cards[1].startUtc).toBe("2027-02-08T00:00:00Z");
  });
});
