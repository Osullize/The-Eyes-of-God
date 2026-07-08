---
name: "Heat Pump Lead Console"
description: "An executive-grade command console for overseas heat-pump lead discovery, crawling, and AI profiling."
colors:
  ink-950: "#07111f"
  ink-900: "#0c1726"
  ink-800: "#132338"
  steel-700: "#304155"
  steel-500: "#64748b"
  steel-300: "#cbd5e1"
  steel-200: "#e2e8f0"
  paper-50: "#f7f8f5"
  paper-100: "#eef2ec"
  surface: "#ffffff"
  accent-teal: "#0f766e"
  accent-teal-soft: "#dff7f2"
  accent-amber: "#b7791f"
  accent-rose: "#be123c"
  nav-teal-glow: "#8bd8cf"
  success-bg: "#dcfce7"
  warning-bg: "#fef3c7"
  danger-bg: "#fee2e2"
typography:
  display:
    fontFamily: "Geist, Cabinet Grotesk, Avenir Next, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "clamp(30px, 3.2vw, 46px)"
    fontWeight: 700
    lineHeight: 1.02
    letterSpacing: "0"
  headline:
    fontFamily: "Geist, Cabinet Grotesk, Avenir Next, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "21px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0"
  title:
    fontFamily: "Geist, Cabinet Grotesk, Avenir Next, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "14px"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "0"
  body:
    fontFamily: "Geist, Cabinet Grotesk, Avenir Next, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "13px"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "0"
  label:
    fontFamily: "Geist, Cabinet Grotesk, Avenir Next, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "12px"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "0"
rounded:
  sm: "4px"
  md: "8px"
  pill: "999px"
spacing:
  xs: "5px"
  sm: "8px"
  md: "14px"
  lg: "18px"
  xl: "24px"
  xxl: "30px"
components:
  button-primary:
    backgroundColor: "{colors.accent-teal}"
    textColor: "{colors.surface}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "38px"
  button-default:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-900}"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "38px"
  button-danger:
    backgroundColor: "#fff1f3"
    textColor: "#9f1239"
    rounded: "{rounded.md}"
    padding: "0 12px"
    height: "38px"
  input-field:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-900}"
    rounded: "{rounded.md}"
    padding: "7px 9px"
    height: "36px"
  panel:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink-900}"
    rounded: "{rounded.md}"
    padding: "18px"
---

# Design System: Heat Pump Lead Console

## 1. Overview

**Creative North Star: "The Market Intelligence Command Deck"**

This design system serves a task-heavy internal platform for overseas heat-pump lead generation. It should feel like an executive-grade command console: calm enough for long operating sessions, technical enough to communicate durable infrastructure, and forceful enough to support high-stakes market decisions.

The visual system uses a deep ink command rail against a light data workspace. The product personality is professional, calm, and aggressively capable. The interface rejects generic SaaS landing-page gestures, toy-like consumer styling, and decorative effects that distract from task execution, table scanning, or evidence review.

**Key Characteristics:**
- Dense but readable operational surfaces.
- Deep navigation shell with restrained teal command accents.
- Light work surfaces with clear borders, tonal separation, and modest state motion.
- Tables, task progress, candidate groups, and AI dossiers treated as auditable evidence.
- Chinese UI labels sized for dashboard density.

## 2. Colors

The palette is a restrained technical neutral system with one primary teal accent, one amber warning accent, and one rose danger accent.

### Primary

- **Command Teal** (#0f766e): Use for primary actions, active focus rings, selected rows, task progress, and evidence-positive states.
- **Soft Teal Wash** (#dff7f2): Use for selected rows, recommendation panels, and progress backgrounds when the surface needs emphasis without saturation.
- **Navigation Glow Teal** (#8bd8cf): Use sparingly inside the dark command rail for active navigation and brand signal.

### Secondary

- **Signal Amber** (#b7791f): Use for caution, secondary progress accents, and mixed-quality status signals.

### Tertiary

- **Risk Rose** (#be123c): Use for destructive actions, risk flags, and failure emphasis.

### Neutral

- **Command Ink 950** (#07111f): Primary dark navigation and highest-emphasis text.
- **Command Ink 900** (#0c1726): Primary body text and dark active controls.
- **Command Ink 800** (#132338): Section headings and supporting dark surfaces.
- **Steel 700** (#304155): Table headers and important secondary text.
- **Steel 500** (#64748b): Notes, descriptions, timestamps, and metadata.
- **Steel 300** (#cbd5e1): Form borders and panel outlines.
- **Steel 200** (#e2e8f0): Dividers and table row borders.
- **Cool Paper 50** (#f7f8f5): Main app background.
- **Cool Paper 100** (#eef2ec): Subtle toolbar and fieldset background.
- **Surface White** (#ffffff): Primary cards, tables, inputs, and reader pages.

### Named Rules

**The Accent Budget Rule.** Command Teal should mark action, selection, or progress. It should not become decorative wallpaper.

**The Evidence Surface Rule.** Tables, raw records, task items, and AI results stay on light surfaces so leadership can scan and compare data quickly.

**The Operator-Facing Data Rule.** Business review surfaces must not expose implementation provenance such as CSV filenames, crawl/import source labels, internal table names, or raw pipeline fields. Contact rows, AI profile previews, customer details, and exported reports show business values only; developer-facing provenance belongs only in explicit audit/debug views.

## 3. Typography

**Display Font:** Geist with Cabinet Grotesk and Avenir Next fallback.
**Body Font:** Geist with Cabinet Grotesk and system fallback.
**Label/Mono Font:** No separate mono family is defined yet.

**Character:** The type system is a tight product UI sans stack. It should feel precise and operational, not editorial or promotional.

### Hierarchy

- **Display** (700, `clamp(30px, 3.2vw, 46px)`, 1.02): Current module title in the top command header. Use only for the active module title, not inside panels or tables.
- **Headline** (700, 21px, 1.2): Panel titles, library titles, and AI profile headings.
- **Title** (700, 14px, 1.2): Section labels, item titles, and compact task headings.
- **Body** (400, 13px, 1.45): Table cells, helper text, metadata, descriptions, and profile summaries. Keep long prose around 65-75ch where possible.
- **Label** (700, 12px, 1.3): Form labels, metric labels, chips, status text, and compact metadata.

### Named Rules

**The Dashboard Scale Rule.** Do not use hero-sized typography inside operational panels. The interface is for repeated work and review, so hierarchy should come from placement, weight, and state, not shouting.

**The Chinese Density Rule.** Chinese labels must remain legible at 12-14px. Avoid squeezing long labels into narrow controls without wrapping or responsive fallback.

## 4. Elevation

The system uses a hybrid of tonal layering, borders, and modest shadows. Most depth should come from background layers and clear borders. Shadows are reserved for main shell surfaces, active controls, and hover feedback, never for decorative ghost-card effects.

### Shadow Vocabulary

- **Command Rail Shadow** (`26px 0 60px rgba(7, 17, 31, 0.18)`): The left navigation shell only.
- **Header Lift** (`0 24px 70px rgba(7, 17, 31, 0.1)`): The top module command header.
- **Metric Lift** (`0 14px 36px rgba(7, 17, 31, 0.075)`): Metric cards at rest.
- **Metric Hover Lift** (`0 22px 48px rgba(7, 17, 31, 0.12)`): Metric cards on hover.
- **Panel Lift** (`0 18px 50px rgba(7, 17, 31, 0.08)`): Main panels, list panes, detail panes, and AI reader pages.
- **Primary Button Lift** (`0 12px 28px rgba(15, 118, 110, 0.26)`): Primary task execution buttons.
- **Focus Ring** (`0 0 0 3px rgba(15, 118, 110, 0.12)`): Form, select, textarea, and search focus.

### Named Rules

**The Structure Before Shadow Rule.** Use borders and tonal layers first. Add shadow only when it clarifies a surface's role or state.

## 5. Components

### Buttons

- **Shape:** Rounded rectangle with 8px radius.
- **Primary:** Command Teal gradient with white text, 38px minimum height, 12px horizontal padding, medium elevation.
- **Hover / Focus:** 160-180ms state transition. Hover may translate up by 1px. Focus uses the teal focus ring.
- **Default:** White surface, ink text, steel border, subtle shadow.
- **Danger:** Soft rose background, rose text, rose border tint. Use for cancellation and deletion only.

### Chips

- **Style:** Pill shape using 999px radius, light neutral surface, steel border, and 12px bold label text.
- **State:** Status chips must include text, not color alone. Running uses teal-tinted backgrounds; success/warning/error use semantic fills.

### Cards / Containers

- **Corner Style:** 8px radius.
- **Background:** Surface White for primary containers; Cool Paper 100 for toolbars and fieldsets.
- **Shadow Strategy:** Panel Lift for major surfaces; no nested card shadows.
- **Border:** Steel 300 / Steel 200 tinted borders for auditable edges.
- **Internal Padding:** 18px default for panels, 24-26px for top command header, 14px for table cells and compact groups.

### Inputs / Fields

- **Style:** White background, 8px radius, steel border, 36-38px minimum height.
- **Focus:** Teal border shift plus 3px soft focus ring.
- **Disabled:** Muted steel text, pale background, no hover lift.
- **Error:** Use rose text and rose-tinted borders, with explicit error copy.

### Navigation

- **Style:** Dark command rail at 292px desktop width. Navigation items are 68px tall with icon, title, and short description.
- **Default State:** Low-contrast translucent surface on dark ink.
- **Hover State:** Slight upward motion, stronger border, brighter translucent surface.
- **Active State:** Teal-tinted dark fill, bright text, left active indicator, and nav glow teal accent.
- **Mobile Treatment:** Sidebar becomes a top block and nav items collapse into responsive columns, then a single column on small screens.

### Tables

- **Style:** Sticky table headers, separate border model, light surface, subtle row dividers.
- **Rows:** Hover uses Soft Teal Wash at low opacity; selected rows use the full Soft Teal Wash.
- **Density:** Default table cells use 11px vertical and 14px horizontal padding. Raw database tables can be wider and horizontally scrollable.

### Task Progress

- **Style:** Soft teal evidence surface with a 3px top progress accent that moves from teal to amber.
- **Progress Bar:** Rounded pill bar using teal-to-cyan fill.
- **Items:** Compact bordered rows with key, status chip, and detail text.

### AI Profile Reader

- **Style:** One result per page with a 4px top signal bar using teal, amber, and rose.
- **Score Strip:** Compact score panel with priority badge, total score, and model metadata.
- **Sections:** Light sub-panels for summary, business type, market role, product fit, score breakdown, evidence, risk flags, and recommended action.

## 6. Do's and Don'ts

### Do:

- **Do** keep the product register: task execution, database review, and AI evidence inspection come before visual showmanship.
- **Do** use Command Teal (#0f766e) for action, selection, progress, and focus only.
- **Do** preserve auditable surfaces for raw tables, candidate groups, task runs, and AI results.
- **Do** keep panel radius at 8px unless a control is intentionally pill-shaped.
- **Do** make every status understandable from text, not color alone.
- **Do** respect reduced motion. Hover transitions should remain 150-250ms and never block task work.

### Don't:

- **Don't** make this look like a generic SaaS landing page.
- **Don't** use playful, toy-like, consumer-app styling.
- **Don't** bury workflows inside decorative cards or marketing copy.
- **Don't** use visual effects that distract from task execution, table scanning, or evidence review.
- **Don't** make the system feel like a one-off script wrapper; it should feel like a durable internal platform.
- **Don't** use gradient text, oversized hero typography, or ornamental badges.
- **Don't** add colored side-stripe borders greater than 1px to cards, callouts, or list rows.
- **Don't** create nested cards or repeated identical icon-card grids for operational content.
- **Don't** introduce decorative grid or stripe backgrounds into new surfaces; technical feeling should come from structure, not wallpaper.
