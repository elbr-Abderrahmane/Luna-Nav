import type { Screen } from "../components/AppShell";

export interface TourState {
  screen: Screen;
  cardCount: number;
  sliderHours: number;
  exported: boolean;
}

export interface TourStep {
  id: string;
  title: string;
  ask: string;
  chips: string[];
  /** true once the user has done what the step asks */
  done: (s: TourState) => boolean;
  /** shown when the step is finished */
  ack: string;
}

export const TOUR: TourStep[] = [
  {
    id: "pick",
    title: "Pick landing sites",
    ask: "Go to Scenarios, choose a site and a landing date, then press “Add scenario”. Add at least 2 (up to 4) so we can compare them. In a hurry? Type /demo and I will add a set for you.",
    chips: ["/demo", "/go scenarios", "/skip"],
    done: (s) => s.cardCount >= 2,
    ack: "You have scenarios to work with.",
  },
  {
    id: "site",
    title: "Open a site view",
    ask: "Press “Open site view” on a scenario card (or use the › arrow at the top). You will see the sky from the landing site: the horizon, the Sun and Earth, countdowns to sunset and earthrise, and the power numbers.",
    chips: ["/go site", "/skip"],
    done: (s) => s.screen === "site",
    ack: "That is the site view.",
  },
  {
    id: "timeline",
    title: "Run the timeline",
    ask: "Open the Timeline (“Open the timeline” button), then press Play or drag the slider through the lunar day. Watch the Sun and Earth move, and the bars below show when you have sunlight, a line of sight to Earth, and both.",
    chips: ["/go timeline", "/skip"],
    done: (s) => s.screen === "timeline" && s.sliderHours > 0,
    ack: "Nice, that is one full lunar day in motion.",
  },
  {
    id: "compare",
    title: "Compare your scenarios",
    ask: "Open Compare (top bar or the › arrow). Each column is one scenario; “best” marks the best value in each row, and the badge is the verdict with its reasons.",
    chips: ["/go compare", "/skip"],
    done: (s) => s.screen === "compare",
    ack: "That is the comparison table.",
  },
  {
    id: "export",
    title: "Export your result",
    ask: "Press “Download CSV” (a table you can open in Excel) or “Copy summary” (a short text for a message or report) above the table.",
    chips: ["How do I export?", "/skip"],
    done: (s) => s.exported,
    ack: "Exported.",
  },
  {
    id: "sweep",
    title: "Find the best date",
    ask: "Open Date sweep. It keeps one site and tries 12 landing dates, one lunar day apart. Click a bar to see that date, then “Add as scenario” to bring it back to your list.",
    chips: ["/go sweep", "/skip"],
    done: (s) => s.screen === "sweep",
    ack: "That is the date sweep.",
  },
];

export const TOUR_INTRO =
  "Let's take the tour. I will ask you to do something on each screen and move on when you have done it. Type /skip to skip a step, /stop to leave.";

export const TOUR_OUTRO =
  "That is every feature: scenarios, site view, timeline, compare, export and date sweep. Ask me anything on any screen, or type /help for the commands.";

export const stepText = (i: number): string => `Step ${i + 1} of ${TOUR.length} · ${TOUR[i].title}\n${TOUR[i].ask}`;

/** First step at or after `from` that the user has not done yet. TOUR.length = all done. */
export function nextOpenStep(from: number, s: TourState): number {
  let i = from;
  while (i < TOUR.length && TOUR[i].done(s)) i++;
  return i;
}
