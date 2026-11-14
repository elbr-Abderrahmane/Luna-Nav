# Agent brief — P1 Frontend & Visualization (LunaNav)

You are the coding agent for **P1, Frontend & Visualization** on LunaNav, a 5-person NASA challenge team
building a lunar South Pole landing-site selection app. Before writing any code, **read `README.md` at the
repo root completely**. It is the source of truth for contracts, conventions and folder ownership. If this
brief and the README disagree, the README wins.

## Your scope
- You own **`frontend/`** only. Do not edit files outside it (except proposing changes, see "Contracts").
- Stack: Vite, React 18, TypeScript (strict), three, @react-three/fiber, @react-three/drei, zustand,
  @tanstack/react-query, recharts, openapi-typescript, vitest.
- The frontend never computes science (scores, slopes, illumination). It displays what the API returns and only
  converts coordinates for rendering.

## What to build, per layer
**App shell (all layers):** starfield background, space theme, layer stepper (1–4) with back navigation,
`InfoCard` (floating, anchored to a 3D object), `CollapsiblePanel`, loading/error states, `CameraRig` for smooth
animated transitions (ease-in-out, ~1.5–2.5 s).

**L1 Mission (`layers/L1Mission`, `scenes/EarthMoonScene.tsx`)**
- Earth-centred scene, `1 unit = 1000 km`, true-scale positions, visually enlarged bodies (`BODY_VISUAL_SCALE`).
- Arrival date/time picker (UTC) → `POST /api/v1/mission/plan`.
- Animate Moon along `moon_track`, draw `trajectory` as a line, mark interception window, light the scene from `sun_direction_eci`.
- Collapsible mission panel: launch, arrival, Earth–Moon distance, transfer duration, interception window, every row in `parameters`.
- Confirm button → store `missionPlan`, go to L2.

**L2 Regions (`layers/L2Regions`, `scenes/MoonScene.tsx`)**
- Earth fades out, camera flies to the South Pole. Moon-centred scene, `1 unit = 1 km`.
- `GET /regions?arrival_utc=` → draw each polygon boundary draped on the surface (lift slightly above terrain to avoid z-fighting).
- Hover highlights, click opens InfoCard: name, center, elevation, mean slope, surface description, illumination, suitability label.
- Select a region → camera zooms in; load `GET /terrain/heightmap?area_id=REG-xx` and build a displaced terrain mesh.

**L3 Zones (`layers/L3Zones`)**
- `GET /regions/{id}/zones?arrival_utc=` → zone polygons on the terrain mesh, hover/click InfoCard with all `terrain` and `illumination` fields.
- Selection UI enforcing **exactly 3** (4th click is refused with a hint; deselect by clicking again).
- "Compare" → `POST /evaluate/zones` → comparison view: score bars, radar chart of `normalized` criteria, table of raw values with units, disqualifiers in red, sensitivity note, `explanation.summary` + bullets. Highlight `recommended_id`.
- "Continue" → camera transitions to the winning zone.

**L4 Points (`layers/L4Points`)**
- `GET /zones/{id}/points?arrival_utc=` → markers; optimal (`evaluation.recommended_id`) highlighted.
- Click marker → InfoCard with lat/lon, elevation, slope, roughness, hazard distances, illumination, Earth visibility, score.
- Allow orbiting around the selected point to inspect terrain.
- **Generate Report**: capture canvas screenshots (`gl.domElement.toDataURL`), send `ReportRequest` to `POST /report`, download the PDF.

## Conventions you must apply (summary, full text in README §6)
- Field names carry units (`_m`, `_km`, `_deg`, `_pct`, `_h`, `_utc`). Show units in the UI from the suffix/`unit` field, never guess.
- Lat/lon degrees, longitude east-positive −180…180. **GeoJSON coordinates are `[lon, lat]`.**
- Physical → three.js axes: `three.x = X`, `three.y = Z`, `three.z = −Y`.
- Surface point: `r = (1737400 + elevation_m × VERTICAL_EXAGGERATION) / 1000` km; `X = r cosφ cosλ`, `Y = r cosφ sinλ`, `Z = r sinφ`.
- Heightmap: polar stereographic (README §6.2), `float32_base64`, row 0 = ymax. Convert each vertex x_m,y_m → lat/lon (inverse formula) → 3D on the sphere.
- Implement all of this once in `src/lib/coords.ts`, and test it in vitest against `contracts/coord_test_vectors.json`.
- Constants mirrored in `src/lib/constants.ts` (README §6.6).

## State (README §8)
Use one zustand store `state/missionStore.ts` with exactly the `MissionState` fields from the README.
Back navigation never clears state; an upstream change clears only dependents; persist to `sessionStorage`.

## API integration
- Types are **generated**, never handwritten: `npm run gen:api` → `openapi-typescript ../contracts/openapi.json -o src/api/types.gen.ts`.
- `src/api/client.ts` wraps fetch with base URL from `VITE_API_URL`, maps the error shape `{error:{code,message}}`.
- `VITE_USE_FIXTURES=true` makes the client read JSON from `../mock_data/` directly, so you can work even when the backend is down.
- Use TanStack Query; query keys include `arrival_utc`.

## Order of work
1. Vite app, folder layout from README §5, store, constants, `coords.ts` + tests, generated types, fixture client.
2. L1 scene + panel on fixtures. 3. L2 globe + region overlays. 4. Heightmap mesh. 5. L3 polygons, 3-selection, comparison charts. 6. L4 markers + report button. 7. Transitions and polish (M4).
Reach the **M1 walking skeleton** (click L1 → L4 on fixtures) before polishing anything.

## Definition of done for each feature
Typecheck clean, vitest green, works with both `VITE_USE_FIXTURES=true` and the live API, no console errors,
usable at 1280×720, reasonable frame rate (keep meshes ≤ 512×512 vertices, dispose geometries on unmount).

## Contracts
If you need a field the API does not provide, **do not invent it in the frontend and do not edit schemas**.
Write the proposed change (field, type, unit, which endpoint, why) and stop so P1 can raise a `contract` PR with P5.
