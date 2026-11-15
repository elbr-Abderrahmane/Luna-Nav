import { useEffect, useRef, useState } from "react";
import { USE_FIXTURES } from "../api/client";
import { useSites } from "../api/queries";
import { PAGE_CHIPS, respond, type Action, type AssistCtx } from "../lib/assistant";
import { addDemoScenarios } from "../lib/demo";
import { nextOpenStep, stepText, TOUR, TOUR_INTRO, TOUR_OUTRO, type TourState } from "../lib/tour";
import { useAssistantStore } from "../state/assistantStore";
import { useScenarioStore } from "../state/scenarioStore";
import { useActive } from "../state/useActive";
import type { Screen } from "./AppShell";

const SEEN_KEY = "lunanav.guideSeen";

export function Assistant({ screen, onNavigate }: { screen: Screen; onNavigate: (s: Screen) => void }) {
  const open = useAssistantStore((s) => s.open);
  const messages = useAssistantStore((s) => s.messages);
  const tour = useAssistantStore((s) => s.tour);
  const exported = useAssistantStore((s) => s.exported);
  const unread = useAssistantStore((s) => s.unread);
  const typing = useAssistantStore((s) => s.typing);
  const cards = useScenarioStore((s) => s.cards);
  const addCard = useScenarioStore((s) => s.addCard);
  const sliderHours = useScenarioStore((s) => s.sliderHours);
  const { card, conditions, timeline } = useActive();
  const catalog = useSites().data?.sites;

  const siteName = conditions.data?.site.name ?? timeline.data?.site.name ?? null;
  const ctx: AssistCtx = {
    screen,
    cardCount: cards.length,
    siteName,
    startUtc: card?.startUtc ?? null,
    conditions: conditions.data,
    timeline: timeline.data,
    fixtures: USE_FIXTURES,
    tourActive: tour !== null,
  };
  const tourState: TourState = { screen, cardCount: cards.length, sliderHours, exported };
  // always the latest values inside timeouts
  const live = useRef({ ctx, tourState, catalog });
  live.current = { ctx, tourState, catalog };

  const [text, setText] = useState("");
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const store = useAssistantStore.getState;

  // greeting; opens by itself the first time this browser sees the app
  useEffect(() => {
    const st = store();
    if (st.messages.length > 0) return;
    st.push("bot", "Hi, I am the LunaNav guide. I can walk you through every feature, or answer questions about whatever screen you are on.\n\nType /tutorial to start the tour, or /help for commands.", ["/tutorial", "What can you do?", "/where"]);
    let first = true;
    try {
      first = localStorage.getItem(SEEN_KEY) !== "1";
      localStorage.setItem(SEEN_KEY, "1");
    } catch {
      /* storage can be blocked: just open */
    }
    if (first) st.setOpen(true);
  }, [store]);

  // the tour moves on by itself when the user has done what the step asks
  useEffect(() => {
    const st = store();
    if (st.tour === null) return;
    const idx = nextOpenStep(st.tour, live.current.tourState);
    if (idx === st.tour) return;
    const ack = `✓ ${TOUR[st.tour].ack}`;
    if (idx >= TOUR.length) {
      st.push("bot", `${ack}\n\n${TOUR_OUTRO}`, ["/where", "/glossary", "How do I export?"]);
      st.setTour(null);
    } else {
      st.push("bot", `${ack}\n\n${stepText(idx)}`, TOUR[idx].chips);
      st.setTour(idx);
    }
  }, [tour, screen, cards.length, sliderHours, exported, store]);

  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages.length, typing, open]);

  useEffect(() => {
    if (open) inputRef.current?.focus();
  }, [open]);

  const startTour = () => {
    const st = store();
    st.setOpen(true);
    const idx = nextOpenStep(0, live.current.tourState);
    if (idx >= TOUR.length) {
      st.push("bot", "You have already done everything the tour covers. Ask me anything, or type /help.", ["/where", "/glossary"]);
      return;
    }
    st.setTour(idx);
    st.push("bot", `${TOUR_INTRO}\n\n${stepText(idx)}`, TOUR[idx].chips);
  };

  const skipStep = () => {
    const st = store();
    if (st.tour === null) return;
    const idx = nextOpenStep(st.tour + 1, live.current.tourState);
    if (idx >= TOUR.length) {
      st.push("bot", TOUR_OUTRO, ["/where", "/glossary"]);
      st.setTour(null);
    } else {
      st.push("bot", stepText(idx), TOUR[idx].chips);
      st.setTour(idx);
    }
  };

  const run = (a: Action | undefined) => {
    if (!a) return;
    const st = store();
    switch (a.type) {
      case "go":
        onNavigate(a.screen);
        break;
      case "addDemo": {
        const n = addDemoScenarios(live.current.catalog, addCard);
        st.push("bot", n > 0 ? `Added ${n} demo scenarios. Open one with “Open site view”, or use the › arrow.` : "I could not add the demo set: the site catalog has not loaded yet. Try again in a moment.", ["/go site", "/go compare"]);
        break;
      }
      case "tour":
        startTour();
        break;
      case "stopTour":
        st.setTour(null);
        break;
      case "skip":
        skipStep();
        break;
      case "clear":
        st.clear();
        break;
    }
  };

  const send = (raw: string) => {
    const input = raw.trim();
    if (!input) return;
    const st = store();
    st.push("user", input);
    st.setTyping(true);
    window.setTimeout(() => {
      const r = respond(input, live.current.ctx);
      const s2 = store();
      s2.setTyping(false);
      if (r.text) s2.push("bot", r.text, r.chips);
      run(r.action);
    }, 220);
  };

  const last = messages[messages.length - 1];
  const chips = last && last.from === "bot" && last.chips?.length ? last.chips : PAGE_CHIPS[screen];

  return (
    <div className="assistant">
      {open && (
        <section
          className="chat"
          role="dialog"
          aria-label="LunaNav guide"
          onKeyDown={(e) => {
            if (e.key === "Escape") store().setOpen(false);
          }}
        >
          <header className="chat-head">
            <div>
              <strong>Luna guide</strong>
            </div>
            <div className="row" style={{ gap: 6 }}>
              {tour !== null && <span className="badge ok">Tour {tour + 1}/{TOUR.length}</span>}
              <button className="btn small" onClick={() => send("/tutorial")} title="Start or restart the guided tour">
                Tour
              </button>
              <button className="btn small" onClick={() => store().setOpen(false)} aria-label="Close the guide">
                ×
              </button>
            </div>
          </header>
          <div className="chat-log" ref={listRef} role="log" aria-live="polite">
            {messages.map((m) => (
              <div key={m.id} className={`msg msg-${m.from}`}>
                {m.text}
              </div>
            ))}
            {typing && <div className="msg msg-bot typing" aria-label="Typing">…</div>}
          </div>
          <div className="chips chat-chips">
            {chips.map((c) => (
              <button key={c} className="chip" onClick={() => send(c)}>
                {c}
              </button>
            ))}
          </div>
          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
              setText("");
            }}
          >
            <input ref={inputRef} type="text" value={text} onChange={(e) => setText(e.target.value)} placeholder="Ask a question or type /help" aria-label="Message to the guide" />
            <button className="btn primary small" type="submit" disabled={!text.trim()}>
              Send
            </button>
          </form>
        </section>
      )}
      <button className="chat-launch" onClick={() => store().setOpen(!open)} aria-expanded={open} aria-label={open ? "Close the guide" : "Open the guide"}>
        <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20 14.5A8.5 8.5 0 0 1 9.5 4a8.5 8.5 0 1 0 10.5 10.5z" fill="currentColor" />
        </svg>
        <span>Guide</span>
        {!open && unread > 0 && <span className="chat-dot" aria-label={`${unread} new messages`}>{unread}</span>}
      </button>
    </div>
  );
}
