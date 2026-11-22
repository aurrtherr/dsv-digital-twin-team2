# Slide Design System

A reusable design guide based on the Team 2 DSV Digital Twin deck. It covers the look (colours, type, spacing), the building blocks (nav, cards, pills, bars, quote panels) and the writing style, so a new deck can look and read the same way.

---

## 1. Look and feel

- **Clean and calm.** The background is warm off-white, there is one strong brand blue, and yellow is the only highlight.
- **Big, bold headlines; plain body text.** Headings use a rounded geometric sans (Lexend 800). Body text uses a friendly grotesque (DM Sans).
- **Rounded everything.** Cards have 12–20 px corners, and pills and tags are fully rounded.
- **One idea per slide.** The headline states the point and the body proves it with real numbers.
- **Colour has meaning.** Blue is for structure, yellow means "look here / current", rust-orange means a problem or risk, and green means OK.

---

## 2. Canvas and grid

| Item | Value |
|---|---|
| Slide size | **1920 × 1080 px** (16:9) |
| Outer padding | **128 px left/right**, **128 px top**, **160 px bottom** |
| Safe content bottom | keep content above **y = 920 px**; the footer line sits at `bottom: 64px` |
| Content width | 1664 px (1920 − 2 × 128) |
| Vertical rhythm | 24 px between the title block and the body; 12–20 px inside cards |
| Columns | 2-up (`gap: 40px`), 3-up or 4-up (`gap: 14–20px`); use flex or CSS grid with `1fr` columns |

Every slide is a flex column: **nav (absolute, top right) → title block → body (`flex: 1`) → optional footer note (absolute, bottom)**.

---

## 3. Colour tokens

### Core palette

| Token | Hex | Use |
|---|---|---|
| `--blue` (brand) | `#004AAD` | Headlines, nav bar, number labels, primary panels, key bars |
| `--blue-mid` | `#3F6FC0` | Secondary bars, rule tags, second-level accents |
| `--blue-light` | `#A9C3EC` | Timelines, dividers, soft fills, "low" level |
| `--blue-tint` | `#DCE6F7` | Inactive nav text on blue, subtle text on dark panels |
| `--gold` (highlight) | `#FFD23F` | The ONE highlight: active nav item, current step, quote marks, key callouts |
| `--rust` (alert) | `#C25A3A` | Problems, risks, "high" level, late or bad numbers |
| `--green` (ok) | `#22774A` | Good or confirmed states, used sparingly |
| `--amber-text` | `#9A6400` | Warning text on light backgrounds |
| `--navy` (ink) | `#27364C` | Main text colour, dark pills, icons |
| `--body` | `#4A5568` | Sub-titles and body copy |
| `--mute` | `#6A7179` | Labels, captions, footers, inactive steps |

### Surfaces

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#FBFBF8` | Slide background (warm off-white) |
| `--card` | `#FFFFFF` | Cards |
| `--panel` | `#EEF2F8` | Chips inside cards, soft panels |
| `--panel-2` | `#F7F9FC` | Table rows, zebra stripes |
| `--track` | `#E3E8F0` | Empty bar tracks, inactive pills |
| `--line` | `#DCE3EE` | 2 px card borders |
| `--grey` | `#C9D3E3` | Neutral bars, disabled |
| `--rust-tint` | `#F3D6CC` | Background for problem callouts |
| `--gold-tint` | `#FFF6D6` | Background for highlight callouts |
| `--screen` | `#0B1220` | Dark frames around app screenshots |

### Colour rules

1. **Gold appears once or twice per slide at most.** It marks "where we are" or "the number to remember".
2. **Rust is only for bad news:** problems, risks, late, missing.
3. **Blue does the structure:** titles, numbers, panels, nav.
4. **Text on blue** is white or `#DCE6F7`; **text on gold** is navy.
5. **Levels** (e.g. likelihood): High = rust with white text, Medium = gold with navy text, Low = light blue with navy text.

---

## 4. Typography

**Fonts**
- **Display:** `'Lexend', Arial, sans-serif`, weight **800**
- **Body:** `'DM Sans', Arial, sans-serif`, weights 400 and 700
- **Code / IDs (optional):** `'Courier New', monospace`

```html
<link href="https://fonts.googleapis.com/css2?family=Lexend:wght@800&family=DM+Sans:ital,wght@0,400;0,700;1,700&display=swap" rel="stylesheet">
```

**Type scale**

| Role | Font | Size | Weight | Line height | Colour | Notes |
|---|---|---|---|---|---|---|
| Slide title | Lexend | **72 px** | 800 | 1.1 | `--blue` | `letter-spacing: -2px`; max 2 lines |
| Subtitle | DM Sans | **28 px** | 400 | 1.3 | `--body` | One sentence under the title |
| Big number / index | Lexend | **44–64 px** | 800 | 1.0–1.1 | `--blue` (or rust for bad) | e.g. "01", "1,460" |
| Card title | Lexend | **30 px** | 800 | 1.15 | `--navy` | |
| Body / labels | DM Sans | **24 px** | 400/700 | 1.3 | `--navy` / `--body` | **Minimum size on any slide** |
| Small print / footers | DM Sans | **22–24 px** | 400 | 1.3 | `--mute` | |
| Quote | DM Sans | **52 px** | 700 italic | 1.35 | white on blue | |
| Section label | DM Sans | **24 px** | 700 | 1.3 | `--mute` | UPPERCASE, `letter-spacing: 1px` |

Rule: nothing smaller than **22–24 px**, because slides must read from the back of a room.

---

## 5. Shape and depth

| Element | Radius |
|---|---|
| Pills, tags, nav bar | `999px` (fully round) |
| Chips inside cards | `10px` |
| Cards | `14–16px` |
| Feature panels, images, quote panels | `20px` |
| Bars | `6px` |
| Small swatches | `4–8px` |

- **Borders:** `2px solid #DCE3EE` on white cards, or a **6 px coloured top border** (`border-top: 6px solid #004AAD`) to mark a category.
- **Shadows:** none. Depth comes from the white cards sitting on the off-white background.

---

## 6. Components

### 6.1 Section nav (top right)
A rounded blue bar listing the deck's sections. The current one is gold and bold.
```html
<div style="position:absolute;top:40px;right:128px;display:flex;gap:28px;align-items:center;background:#004AAD;border-radius:999px;padding:8px 32px">
  <p style="font-size:24px;color:#DCE6F7">Intro</p>
  <p style="font-size:24px;color:#FFD23F;font-weight:700">Background</p>
  <p style="font-size:24px;color:#DCE6F7">Scope</p>
  …
</div>
```

### 6.2 Step tracker (top left, optional)
Shows the steps inside a section: a navy label pill, then the step pills. The current step is gold and the rest are grey.
```html
<div style="position:absolute;top:44px;left:128px;display:flex;gap:8px;align-items:center">
  <p class="pill" style="background:#27364C;color:#fff">DATA</p>
  <p class="pill" style="background:#E3E8F0;color:#6A7179">① Scan &amp; clean</p>
  <p class="pill" style="background:#FFD23F;color:#27364C">② Analyse</p>
</div>
```

### 6.3 Title block
```html
<div style="display:flex;flex-direction:column;gap:12px">
  <h2 style="font-family:'Lexend',Arial,sans-serif;font-size:72px;font-weight:800;line-height:1.1;letter-spacing:-2px;color:#004AAD">The headline states the point</h2>
  <p style="font-size:28px;line-height:1.3;color:#4A5568">One sentence of context.</p>
</div>
```

### 6.4 Pill / tag
```html
<p style="font-size:24px;line-height:1.3;font-weight:700;color:#27364C;background:#EEF2F8;padding:1px 12px;border-radius:999px;white-space:nowrap">Label</p>
```
Variants: gold (current or highlight), navy with white text (category), rust with white text (risk), light blue (low or neutral).

### 6.5 Numbered card (overview / parts)
White card with a 2 px border. Inside, from top to bottom: a big blue number and an icon on one row, the card title, a one-line description, a spacer, then stacked chips.
```html
<div style="flex:1;display:flex;flex-direction:column;gap:12px;background:#fff;border-radius:16px;padding:22px;border:2px solid #DCE3EE">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <p style="font-family:Lexend;font-size:56px;font-weight:800;line-height:1;color:#004AAD">01</p>
    <!-- icon 36px, colour #004AAD -->
  </div>
  <p style="font-family:Lexend;font-size:30px;font-weight:800;line-height:1.15;color:#27364C">Card title</p>
  <p style="font-size:24px;line-height:1.3;color:#4A5568">One-line description</p>
  <div style="flex:1"></div>
  <p style="font-size:24px;font-weight:700;color:#27364C;background:#EEF2F8;border-radius:10px;padding:4px 12px">Sub-item</p>
</div>
```

### 6.6 Category card (top-border)
White card with a **6 px blue top border**, a big ID ("A1"), a bold title and a muted description. Works well in a 4-column grid (index or appendix pages).

### 6.7 Quote panel
A blue panel (radius 20, padding 56/64) with a large gold Lexend quote mark (160 px), a white italic quote (52 px), and an attribution line made of a 48 × 4 px gold rule plus gold italic text. Pair it with a full-height photo (640 px wide, radius 20, `object-fit: cover`).

### 6.8 Progress / comparison bar
A grey track with a coloured fill, 26 px high and 6 px radius.
```html
<div style="width:300px;height:26px;background:#E3E8F0;border-radius:6px;display:flex">
  <div style="width:180px;height:26px;background:#004AAD;border-radius:6px"></div>
</div>
```
Fill colour follows meaning: blue = neutral, rust = bad, gold = highlight, light blue = comparison.

### 6.9 Timeline divider
A section label on the left, a 4 px light-blue line (`flex:1`) and a label on the right:
`BRIEF ──────────── FINAL · 20 DEC` in 24 px bold uppercase muted text.

### 6.10 Callout box
- **Problem:** `background:#F3D6CC`, left border or text in `#C25A3A`.
- **Highlight:** `background:#FFF6D6`, with a gold accent.
- **Neutral note:** `background:#EEF2F8`.

### 6.11 Tables
White background, a header row in navy or bold 24 px text, zebra rows in `#F7F9FC`, cell padding of about 8–12 px, numbers right-aligned. Status shown as pills rather than plain text.

### 6.12 Screenshot frame
App screenshots sit on a dark `#0B1220` rounded frame (radius 16–20) or on a white card with a 2 px border. Labels around them use numbered gold dots.

### 6.13 Footer note
For a source or a caveat:
```html
<p style="position:absolute;left:128px;bottom:64px;width:1664px;font-size:24px;color:#6A7179">Source: … · Figures checked on the full files.</p>
```

### 6.14 Speaker notes
Put the script in `<aside>` inside each slide, written as it would be spoken.

---

## 7. Icons, images and charts

- **Icons:** simple line icons (Lucide or Feather style), 36 px, in `--blue` or `--navy`. Use the same family across the deck.
- **Photos:** real, relevant photography with rounded 20 px corners, cropped with `object-fit: cover`. Use one per slide at most, and always add alt text.
- **Simple SVG figures:** flat shapes in navy, blue and gold only (e.g. a navy person with a gold badge).
- **Charts:**
  - Use the bar colours from §3; there are no gridline borders, just light `#E3E8F0` guides.
  - Label values directly on the bars instead of relying on a legend.
  - Highlight only the bar that matters (gold or rust) and grey the rest.
  - Bar charts start at zero.

---

## 8. Slide types (templates)

| Type | Layout |
|---|---|
| **Overview / agenda** | Title, timeline divider, 4–5 numbered cards in a row |
| **Quote / hook** | Title, quote panel (flex 1) and photo (640 px) side by side |
| **Big number** | Title, one huge Lexend number (rust or blue), 2–3 supporting bars |
| **Comparison** | Two cards (`gap: 40px`), each with a coloured top border, the "bad" side in rust and the "fix" side in blue |
| **Process / flow** | A row of step cards joined by arrows; the current step is gold |
| **Table / log** | Title, full-width table with status pills, footer note |
| **Screens / demo** | Title, a large screenshot in a dark frame, 3–5 numbered callouts on the side |
| **Index / appendix** | Title, a 4-column grid of top-border category cards |
| **Risks** | Title, rows of icon + risk + impact + level pill + mitigation |

---

## 9. Writing style

- **Headline = the takeaway**, written as a sentence ("DSV has data everywhere, but too little insight"), not a topic label ("Background").
- **Plain words.** Short sentences, no jargon or buzzwords; explain a term the first time it appears.
- **Real numbers only**, with their unit and timeframe ("1,460 orders past their planned day, 21 Aug"). Round sensibly and give ranges for estimates ("29 people, range 27–32").
- **Honest labels.** Say "projection", "our assumption" or "prototype" where that is true, and never overclaim (avoid calling things "AI-powered" or "live" unless they are).
- **Label the source** of every key fact in the footer.
- **About 40 words of body text per slide;** move detail to the speaker notes or the appendix.

---

## 10. Do and don't

| Do | Don't |
|---|---|
| Use one gold highlight per slide | Use gold as a general decoration |
| Keep body text at 24 px or more | Shrink text to fit; cut words instead |
| Keep content above y = 920 | Let cards run into the footer |
| Show meaning with colour (rust = bad) | Use rust or green just for variety |
| Give every slide a nav with the current section | Change the nav position between slides |
| Use white cards on the off-white background | Add drop shadows or gradients |

---

## 11. Copy-paste tokens (CSS)

```css
:root{
  /* brand */
  --blue:#004AAD; --blue-mid:#3F6FC0; --blue-light:#A9C3EC; --blue-tint:#DCE6F7;
  --gold:#FFD23F; --rust:#C25A3A; --green:#22774A; --amber-text:#9A6400;
  /* text */
  --navy:#27364C; --body:#4A5568; --mute:#6A7179;
  /* surfaces */
  --bg:#FBFBF8; --card:#FFFFFF; --panel:#EEF2F8; --panel-2:#F7F9FC;
  --track:#E3E8F0; --line:#DCE3EE; --grey:#C9D3E3;
  --rust-tint:#F3D6CC; --gold-tint:#FFF6D6; --screen:#0B1220;
  /* type */
  --font-display:'Lexend', Arial, sans-serif;
  --font-body:'DM Sans', Arial, sans-serif;
  --fs-title:72px; --fs-sub:28px; --fs-card:30px; --fs-body:24px; --fs-small:22px;
  /* shape */
  --r-pill:999px; --r-chip:10px; --r-card:16px; --r-panel:20px; --r-bar:6px;
  /* layout */
  --pad-x:128px; --pad-top:128px; --pad-bottom:160px; --gap:24px;
}
```

## 12. Slide skeleton

```html
<section style="width:1920px;height:1080px;position:relative;background:var(--bg);color:var(--navy);
  font-family:var(--font-body);padding:128px 128px 160px;display:flex;flex-direction:column;gap:24px;box-sizing:border-box">

  <!-- nav (6.1) -->
  <!-- optional step tracker (6.2) -->

  <div style="display:flex;flex-direction:column;gap:12px">
    <h2 style="font-family:var(--font-display);font-size:72px;font-weight:800;line-height:1.1;letter-spacing:-2px;color:var(--blue)">Headline that states the point</h2>
    <p style="font-size:28px;line-height:1.3;color:var(--body)">One sentence of context.</p>
  </div>

  <div style="flex:1;display:flex;gap:40px;min-height:0">
    <!-- body: cards, bars, image, table -->
  </div>

  <p style="position:absolute;left:128px;bottom:64px;width:1664px;font-size:24px;color:var(--mute)">Source / caveat</p>
  <aside>Speaker notes, as you would say them.</aside>
</section>
```
