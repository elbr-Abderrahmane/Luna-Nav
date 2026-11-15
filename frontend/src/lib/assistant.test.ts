import { describe, expect, it } from "vitest";
import { respond, type AssistCtx } from "./assistant";
import { nextOpenStep, TOUR } from "./tour";

const ctx = (over: Partial<AssistCtx> = {}): AssistCtx => ({
  screen: "builder",
  cardCount: 0,
  siteName: null,
  startUtc: null,
  fixtures: true,
  tourActive: false,
  ...over,
});

describe("assistant commands", () => {
  it("starts and stops the tour", () => {
    expect(respond("/tutorial", ctx()).action).toEqual({ type: "tour" });
    expect(respond("/stop", ctx()).action).toEqual({ type: "stopTour" });
    expect(respond("guide me", ctx()).action).toEqual({ type: "tour" });
  });
  it("navigates with /go and in plain words", () => {
    expect(respond("/go compare", ctx()).action).toEqual({ type: "go", screen: "compare" });
    expect(respond("/go date sweep", ctx()).action).toEqual({ type: "go", screen: "sweep" });
    expect(respond("take me to the timeline", ctx()).action).toEqual({ type: "go", screen: "timeline" });
    expect(respond("/go nowhere", ctx()).action).toBeUndefined();
  });
  it("only adds the demo set when there are no scenarios", () => {
    expect(respond("/demo", ctx()).action).toEqual({ type: "addDemo" });
    expect(respond("/demo", ctx({ cardCount: 2 })).action).toBeUndefined();
  });
  it("skips only while a tour is running", () => {
    expect(respond("/skip", ctx()).action).toBeUndefined();
    expect(respond("/skip", ctx({ tourActive: true })).action).toEqual({ type: "skip" });
  });
  it("answers an unknown command without crashing", () => {
    expect(respond("/banana", ctx()).text).toContain("/help");
  });
});

describe("assistant answers", () => {
  it("explains the main metrics", () => {
    expect(respond("what is the longest night?", ctx()).text).toMatch(/Sun below the horizon/);
    expect(respond("what does power and comms mean", ctx()).text).toMatch(/both above the horizon/);
    expect(respond("How do I export?", ctx()).text).toMatch(/Download CSV/);
  });
  it("says it does not know instead of inventing", () => {
    expect(respond("what is the weather in Paris", ctx()).text).toMatch(/not sure/);
  });
  it("is aware of fixture mode", () => {
    expect(respond("why does the date not change", ctx({ fixtures: true })).text).toMatch(/fixture mode/);
    expect(respond("why does the date not change", ctx({ fixtures: false })).text).not.toMatch(/fixture mode/);
  });
});

describe("tour", () => {
  const s = { screen: "builder" as const, cardCount: 0, sliderHours: 0, exported: false };
  it("starts at the first step and skips what is already done", () => {
    expect(nextOpenStep(0, s)).toBe(0);
    expect(nextOpenStep(0, { ...s, cardCount: 2 })).toBe(1);
    expect(nextOpenStep(0, { ...s, cardCount: 2, screen: "site" })).toBe(2);
  });
  it("finishes when everything is done", () => {
    expect(nextOpenStep(TOUR.length, s)).toBe(TOUR.length);
    expect(nextOpenStep(TOUR.length - 1, { ...s, screen: "sweep" })).toBe(TOUR.length);
  });
});
