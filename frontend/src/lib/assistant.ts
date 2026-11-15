import type { SiteConditions, SiteTimeline } from "../api/types";
import type { Screen } from "../components/AppShell";
import { formatValue } from "./format";

export interface AssistCtx {
  screen: Screen;
  cardCount: number;
  siteName: string | null;
  startUtc: string | null;
  conditions?: SiteConditions;
  timeline?: SiteTimeline;
  fixtures: boolean;
  tourActive: boolean;
}

export type Action =
  | { type: "go"; screen: Screen }
  | { type: "addDemo" }
  | { type: "tour" }
  | { type: "stopTour" }
  | { type: "skip" }
  | { type: "clear" };

export interface Reply {
  text: string;
  chips?: string[];
  action?: Action;
}

const SCREENS: { id: Screen; label: string; match: RegExp }[] = [
  { id: "timeline", label: "Timeline", match: /\btimeline\b/ },
  { id: "compare", label: "Compare", match: /\bcompar(e|ison)\b/ },
  { id: "sweep", label: "Date sweep", match: /\b(sweep|dates)\b/ },
  { id: "site", label: "Site view", match: /\bsite( view)?\b/ },
  { id: "builder", label: "Scenarios", match: /\b(scenarios?|builder|home)\b/ },
];

const matchScreen = (q: string) => SCREENS.find((s) => s.match.test(q));

export const PAGE_CHIPS: Record<Screen, string[]> = {
  builder: ["What is a scenario?", "/demo", "/tutorial"],
  site: ["What does the horizon show?", "What do the countdowns mean?", "/go timeline"],
  timeline: ["How do the bars work?", "What is the longest night?", "/go compare"],
  compare: ["How is best decided?", "What does Marginal mean?", "How do I export?"],
  sweep: ["How are the dates chosen?", "How do I export?", "/go scenarios"],
};

const PAGE_TEXT: Record<Screen, string> = {
  builder:
    "Scenarios: build up to 4 scenarios, each one a landing site on a landing date. Choose a site from the catalog or type coordinates, pick a date, and press “Add scenario”. Each card shows sunlight, Earth visibility and the longest night at a glance. “Open site view” takes you into one scenario.",
  site:
    "Site view: what the sky looks like from the landing site at landing time. The panorama is the local horizon (the terrain skyline) with the Sun and Earth. The tiles count down to the next Sun and Earth event and show the power numbers. Use the list on the left to switch scenario.",
  timeline:
    "Timeline: one full lunar day (about 29.5 days). Press Play or drag the slider and the Sun and Earth move across the horizon. The bars show when the Sun is up (yellow), Earth is visible (blue) and both (teal). Click or drag on the bars to jump in time.",
  compare:
    "Compare: your scenarios side by side. “Best” marks the best value in each row, the badge is the verdict with its reasons, and you can export the table with “Download CSV” or “Copy summary”. “Try other dates” opens a date sweep for that site.",
  sweep:
    "Date sweep: one site, 12 landing dates one lunar day apart. Switch the metric above the chart, click a bar to see that date, and use “Add as scenario” to bring it back to your list. “Download CSV” saves all 12 rows.",
};

export const pageReply = (ctx: AssistCtx): Reply => ({ text: PAGE_TEXT[ctx.screen], chips: PAGE_CHIPS[ctx.screen] });

const HELP =
  "Commands:\n" +
  "/tutorial  guided tour of every feature\n" +
  "/skip  skip the current tour step\n" +
  "/stop  leave the tour\n" +
  "/go <screen>  scenarios, site, timeline, compare, sweep\n" +
  "/demo  add the demo scenarios\n" +
  "/where  what this screen does\n" +
  "/status  your current scenario and its numbers\n" +
  "/glossary  the terms I can explain\n" +
  "/clear  clear this chat\n\n" +
  "You can also ask in plain words, for example “what is the longest night?” or “how do I export?”.";

const GLOSSARY =
  "I can explain: scenario, sunlight, longest night, Earth visibility, comms gap, power + comms, irradiance, horizon (terrain / smooth sphere), azimuth and elevation, countdowns, libration, lunar day, timeline bars, verdict, best, date sweep, export, fixture mode, accuracy. Just ask.";

function facts(ctx: AssistCtx): string | null {
  const m = ctx.conditions?.metrics ?? ctx.timeline?.metrics;
  if (!m || !ctx.siteName) return null;
  const when = ctx.startUtc ? ` landing ${ctx.startUtc.slice(0, 10)}` : "";
  return (
    `For ${ctx.siteName}${when}: sunlight ${formatValue(m.sunlight_pct, "%", 0)}, ` +
    `Earth visible ${formatValue(m.earth_visibility_pct, "%", 0)}, power + comms ${formatValue(m.power_and_comms_pct, "%", 0)}, ` +
    `longest night ${formatValue(m.longest_darkness_h, "h", 0)}, longest comms gap ${formatValue(m.longest_comms_gap_h, "h", 0)}.`
  );
}

function statusReply(ctx: AssistCtx): Reply {
  const f = facts(ctx);
  const head = `You have ${ctx.cardCount} scenario${ctx.cardCount === 1 ? "" : "s"}.`;
  if (ctx.cardCount === 0) return { text: `${head} Add one on the Scenarios screen, or type /demo.`, chips: ["/demo", "/tutorial"] };
  return { text: f ? `${head} ${f}` : `${head} The numbers for the selected scenario are still loading, or are not available.`, chips: PAGE_CHIPS[ctx.screen] };
}

interface Entry {
  test: RegExp;
  reply: (ctx: AssistCtx) => Reply;
}
const t = (text: string, chips?: string[]): Reply => ({ text, chips });
const withFacts = (ctx: AssistCtx, text: string, chips?: string[]): Reply => {
  const f = facts(ctx);
  return { text: f ? `${text}\n\n${f}` : text, chips: chips ?? PAGE_CHIPS[ctx.screen] };
};

// Order matters: more specific entries first.
const KB: Entry[] = [
  {
    test: /\b(who|what) are you\b|\bwhat can you do\b|\bare you (an? )?(ai|bot|llm)\b/,
    reply: () =>
      t("I am LunaNav's built-in guide. I answer from this app's own documentation and the numbers on your screen. I am not a live AI model, so I only know about LunaNav. Type /help for commands or /tutorial for a guided tour.", ["/tutorial", "/help", "/where"]),
  },
  { test: /^(hi|hello|hey|yo|good (morning|afternoon|evening))\b/, reply: () => t("Hello! Type /tutorial for a guided tour, or ask me anything about this screen.", ["/tutorial", "/where", "/help"]) },
  { test: /^(thanks|thank you|thx|ok|okay|great|nice|cool)\b/, reply: (c) => t("Glad to help. Ask me anything else, or try one of these.", PAGE_CHIPS[c.screen]) },
  {
    test: /\bpower (and|\+|&|plus) comms?\b|\bpower and communications?\b|\bboth\b.*\b(sun|earth)\b/,
    reply: (c) =>
      withFacts(c, "Power + comms is the share of the window when the Sun AND Earth are both above the horizon: sunlight for power and a line of sight to Earth at the same time. It is the headline number for a site."),
  },
  {
    test: /\blongest (night|darkness|dark)\b|\bdarkness\b|\bnight\b/,
    reply: (c) =>
      withFacts(c, "The longest night is the longest continuous stretch with the Sun below the horizon. A lander has to get through it on stored energy or heaters, so shorter is better."),
  },
  {
    test: /\bcomms? gap\b|\bcommunication gap\b|\bno (contact|signal)\b|\blongest.*earth\b/,
    reply: (c) => withFacts(c, "The longest comms gap is the longest continuous time with no line of sight to Earth. Shorter is better."),
  },
  {
    test: /\bearth (visib|view|line of sight)|\bearth visibility\b|\bearth visible\b|\bsee earth\b|\bline of sight\b/,
    reply: (c) =>
      withFacts(c, "Earth visibility is the share of the window when Earth is above the local horizon, terrain included. It is geometric line of sight only; it is not a radio link budget."),
  },
  {
    test: /\bsunlight\b|\bsunlit\b|\bsun (hours|share|time)\b/,
    reply: (c) =>
      withFacts(c, "Sunlight is the share of the window (one lunar day, about 29.5 days) when the Sun is above the local horizon, so solar panels can produce power. The terrain skyline is included where we have it."),
  },
  {
    test: /\birradiance\b|\bw\/m|\bpanel\b|\bsolar power\b|\bpower\b/,
    reply: (c) =>
      withFacts(c, "Irradiance is the sunlight power reaching a surface, in W/m². These values are geometry only: the Sun's angle, with no panel efficiency, temperature or dust. “Vertical panel” is a panel standing upright, which works well at the poles where the Sun stays low."),
  },
  {
    test: /\bterrain\b|\bdem\b|\blola\b|\bsmooth.?sphere\b|\bhorizon (mask|method)\b|\bskyline\b|\bwhat does the horizon\b|\bhorizon\b/,
    reply: (c) => {
      const method = c.conditions?.method;
      const extra = method ? `\n\nThis scenario uses: ${method === "horizon_mask" ? "terrain horizon (LOLA elevation data)" : "smooth sphere (no terrain data)"}.` : "";
      return t(
        "The horizon is the skyline seen from the landing site. Between 80° and 90° S it comes from terrain (LOLA elevation data), so hills block the Sun and Earth. Outside that area there is no terrain data, so the horizon is a smooth sphere, which is less accurate." + extra,
        PAGE_CHIPS[c.screen],
      );
    },
  },
  { test: /\bazimuth\b|\belevation\b|\bcompass\b|\bdegrees?\b/, reply: (c) => t("Azimuth is the compass direction measured clockwise from north (0° north, 90° east, 180° south). Elevation is the angle above the horizon; below 0° the object is hidden.", PAGE_CHIPS[c.screen]) },
  {
    test: /\bcountdown|\bearthrise|\bearthset|\bsunrise|\bsunset|\bnext event\b/,
    reply: (c) => {
      const cd = c.conditions?.countdown;
      const extra = cd ? `\n\nAt landing: Sun — ${cd.sun.summary}. Earth — ${cd.earth.summary}.` : "";
      return t(
        "The tiles count down to the next Sun event (sunset or sunrise) and the next Earth event (earthrise or earthset). On the Timeline they follow the slider. Near the poles the Sun skims the horizon and Earth wobbles, so events can come often or be far apart." + extra,
        PAGE_CHIPS[c.screen],
      );
    },
  },
  { test: /\blibration\b|\bwobble\b/, reply: (c) => t("Libration is the slow wobble of the Moon as seen from Earth. Near the poles it moves Earth up and down across the horizon, which is why Earth can rise and set several times in one lunar day.", PAGE_CHIPS[c.screen]) },
  { test: /\blunar day\b|\b29\.5\b|\b708\b|\bsynodic\b|\bhow long\b.*\b(window|mission)\b|\bmission duration\b/, reply: (c) => t("A lunar day (one Sun cycle) lasts 29.53 Earth days, about 708.7 hours. Every scenario covers one lunar day unless you choose a shorter mission (14 or 7 days).", PAGE_CHIPS[c.screen]) },
  { test: /\bslider\b|\bplay\b|\bbars?\b|\bwindow bars\b|\bwhat do the (colou?rs|bars)\b/, reply: (c) => t("On the Timeline, drag the slider or press Play to move through the lunar day. In the bars, yellow means the Sun is up, blue means Earth is visible, and teal means both. Click or drag on the bars to jump to a moment.", ["/go timeline", ...PAGE_CHIPS[c.screen].slice(0, 2)]) },
  { test: /\bmarginal\b|\bnot viable\b|\bviable\b|\bverdict\b|\bbadge\b|\bthreshold/, reply: (c) => t("The verdict badge (Viable, Marginal, Not viable) comes from a rule applied to the metrics, for example the longest night or the sunlight share. The reasons under the badge say which threshold applied. In fixture mode the verdict is a labelled placeholder until the API provides the real rule.", PAGE_CHIPS[c.screen]) },
  { test: /\bbest\b.*\b(decided|chosen|work|mean|marked|highlight)|\bhow is best\b|\bwhat does best\b|\bwhich (site|date|scenario).*\bbest\b|\bwhich is best\b/, reply: (c) => t("“Best” marks the best value in each row among your scenarios: higher is better for sunlight, Earth visibility, power + comms and panel energy; lower is better for the longest night and comms gap. It does not pick a winner for you. Read the verdict and the reasons too.", ["/go compare", ...PAGE_CHIPS[c.screen].slice(0, 2)]) },
  { test: /\bexport|\bdownload\b|\bcsv\b|\bsave\b|\bcopy summary\b|\bshare\b/, reply: () => t("On Compare, “Download CSV” saves the table (it opens in Excel) and “Copy summary” puts a short text summary on your clipboard. Date sweep has “Download CSV” for its 12 rows.", ["/go compare", "/go sweep"]) },
  { test: /\bdate sweep\b|\bsweep\b|\b12 (dates|lunar)\b|\bhow are the dates\b|\bother dates\b/, reply: (c) => t("The date sweep keeps one site and tries 12 landing dates, one lunar day (29.5 days) apart, starting from your scenario's date. Pick a bar to see that date, then “Add as scenario” to compare it with the others. It needs a catalog site.", ["/go sweep", ...PAGE_CHIPS[c.screen].slice(0, 2)]) },
  { test: /\bcompare\b|\bcomparison\b|\bside by side\b/, reply: () => t("Compare needs at least 2 scenarios (up to 4). Add them on the Scenarios screen, then open Compare: each column is one scenario, with a verdict, the metrics, the horizon method and any warnings.", ["/go compare", "/demo"]) },
  { test: /\bscenario\b|\badd (a )?(site|scenario|card)\b|\bremove\b|\bhow many\b|\bcards?\b/, reply: () => t("A scenario is one site on one landing date (and a mission length). Add 2 to 4 of them, then compare. Use “Remove” on a card to drop it. The numbers on each card update when you change its date.", ["/demo", "/tutorial", "/go compare"]) },
  { test: /\bcoordinates?\b|\blat(itude)?\b|\blon(gitude)?\b|\bcustom (site|location)\b|\bmy own site\b/, reply: (c) => t("Choose “Type coordinates” on the Scenarios screen and enter latitude and longitude in degrees (south pole is −90, east longitude is positive). Typed coordinates cannot be used in a date sweep. North of 80° S there is no terrain data, so the horizon is a smooth sphere.", PAGE_CHIPS[c.screen]) },
  { test: /\blanding date\b|\bchange the date\b|\bdate (doesn.t|does not|didn.t|not) change\b|\bwhy (is|are) the numbers\b.*\bsame\b/, reply: (c) => t(c.fixtures ? "You are in fixture mode: the app shows saved example runs made for 2027-01-10, so changing the date does not change the numbers. With the live API every date is calculated." : "Each scenario has its own landing date. Change it on the card and its numbers are recalculated.", PAGE_CHIPS[c.screen]) },
  { test: /\bfixture|\bsaved example|\bmock\b|\bdemo data\b|\bno data\b|\bno fixture\b|\bwhy (is there )?an? error\b|\bcould not load\b|\bfixture_missing\b/, reply: (c) => t(c.fixtures ? "Fixture mode means the app is showing saved example runs instead of calling the API. Only a few sites have saved data, which is why some sites show “No fixture”. Press Hide on the yellow banner to dismiss it; setting VITE_USE_FIXTURES=false in .env switches to the live API." : "The app is using the live API. If something fails to load, check that the API is running and press “Try again”.", PAGE_CHIPS[c.screen]) },
  { test: /\bapi\b|\blive mode\b|\bbackend\b|\bserver\b/, reply: (c) => t(c.fixtures ? "Right now the app reads saved example runs. To use the live API, set VITE_USE_FIXTURES=false and VITE_API_URL in .env, then restart the dev server." : "The app is talking to the live API.", PAGE_CHIPS[c.screen]) },
  { test: /\baccura|\btrust\b|\breliable\b|\blimit(s|ation)?\b|\bhow (are|is) (these|this|the) (numbers|calculated)\b|\bhow does it work\b|\bephemeris\b/, reply: (c) => t("The numbers come from astronomical geometry (where the Sun and Earth are) plus a terrain skyline where terrain data exists. They tell you when the Sun and Earth are above the horizon; they are not a full power system or radio link analysis. Open “How these numbers are made” on the Site view for the details and limits.", PAGE_CHIPS[c.screen]) },
  { test: /\bwhere am i\b|\bthis (page|screen)\b|\bwhat (is|can i do) (here|this)\b|\bwhat do i do\b|\bhelp me\b/, reply: (c) => pageReply(c) },
  { test: /\bhelp\b|\bcommands?\b|\bwhat can i (ask|type)\b/, reply: () => t(HELP, ["/tutorial", "/where", "/glossary"]) },
];

function command(q: string, ctx: AssistCtx): Reply {
  const [cmd, ...rest] = q.slice(1).split(" ");
  const arg = rest.join(" ").trim();
  switch (cmd) {
    case "help":
    case "?":
    case "commands":
      return t(HELP, ["/tutorial", "/where", "/glossary"]);
    case "tutorial":
    case "tour":
    case "start":
      return { text: "Starting the guided tour.", action: { type: "tour" } };
    case "stop":
    case "exit":
    case "quit":
      return { text: "Tour stopped. Type /tutorial to start it again.", action: { type: "stopTour" }, chips: ["/tutorial", "/where"] };
    case "skip":
      return ctx.tourActive ? { text: "Skipping this step.", action: { type: "skip" } } : t("No tour is running. Type /tutorial to start one.", ["/tutorial"]);
    case "go": {
      const s = matchScreen(arg);
      return s
        ? { text: `Opening ${s.label}.`, action: { type: "go", screen: s.id } }
        : t("Which screen? Try /go scenarios, /go site, /go timeline, /go compare or /go sweep.", ["/go scenarios", "/go compare", "/go sweep"]);
    }
    case "demo":
      return ctx.cardCount > 0
        ? t(`You already have ${ctx.cardCount} scenario${ctx.cardCount === 1 ? "" : "s"}. Remove them on the Scenarios screen if you want the demo set, or add more yourself (4 at most).`, ["/go scenarios", "/where"])
        : { text: "Adding the demo scenarios.", action: { type: "addDemo" } };
    case "clear":
      return { text: "", action: { type: "clear" } };
    case "where":
    case "page":
    case "here":
      return pageReply(ctx);
    case "status":
      return statusReply(ctx);
    case "glossary":
    case "terms":
      return t(GLOSSARY, PAGE_CHIPS[ctx.screen]);
    case "export":
      return t("On Compare, “Download CSV” saves the table and “Copy summary” copies a short text. Date sweep has “Download CSV”.", ["/go compare", "/go sweep"]);
    default:
      return t(`I do not know the command /${cmd}. Type /help to see them.`, ["/help", "/tutorial"]);
  }
}

export function respond(raw: string, ctx: AssistCtx): Reply {
  const q = raw.trim().toLowerCase().replace(/[?!.,;:]+/g, " ").replace(/\s+/g, " ").trim();
  if (!q) return t("Type a question or a command. /help lists them.", ["/help", "/tutorial"]);
  if (raw.trim().startsWith("/")) return command(raw.trim().toLowerCase().replace(/\s+/g, " "), ctx);

  if (/\b(tutorial|tour|walk ?through|get started|show me around|guide me)\b|\bhow do i start\b|\bi('m| am) new\b/.test(q)) {
    return { text: "Starting the guided tour.", action: { type: "tour" } };
  }
  const go = q.match(/^(go|take me|open|show( me)?|switch)( to)?( the)? ([a-z ]{3,14})$/);
  if (go) {
    const s = matchScreen(go[5]);
    if (s) return { text: `Opening ${s.label}.`, action: { type: "go", screen: s.id } };
  }
  if (/^(add|load|use) (the )?(demo|example|sample)\b|\bdemo (set|scenarios?)\b/.test(q)) return command("/demo", ctx);
  if (/^(status|summary|my scenarios?)$|\bhow (is|does) (my|this|the) (scenario|site) (look|do)\b|\bhow much\b|\bhow (many|long)\b.*\b(sunlight|night|dark|earth)\b|\bwhat('s| is) the\b.*\b(sunlight|night|earth)\b.*\b(here|this|now)\b/.test(q)) {
    const f = facts(ctx);
    if (f) return { text: f, chips: PAGE_CHIPS[ctx.screen] };
  }
  for (const e of KB) if (e.test.test(q)) return e.reply(ctx);

  return t(
    "I am not sure about that one. I can explain sunlight, the longest night, Earth visibility, power + comms, the verdict, the horizon, countdowns, the date sweep, exporting and fixture mode. Type /help for commands, or try one of these.",
    PAGE_CHIPS[ctx.screen],
  );
}
