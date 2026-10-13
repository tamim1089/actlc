# ACTLC design rules (minimalist, Apple-derived)

Sources: Apple Human Interface Guidelines (Typography, Layout, Color, Accessibility, Writing,
Buttons, Motion, Branding; read from developer.apple.com, Oct 2026) and Dieter Rams, *Ten
principles for good design* (vitsoe.com). Each rule is checked by `tools/check_pages.py` where
a command can decide it.

| # | Rule | Source | How we apply it |
|---|------|--------|-----------------|
| 1 | Content first; chrome and brand defer to it. | HIG Branding; Rams "unobtrusive" | No decorative video, orbs, gradients, accent bars. |
| 2 | One primary action per view, in the prominent style. | HIG Buttons | One filled button per section at most; the rest are text links. |
| 3 | Order by importance, top to bottom. | HIG Layout | When, where and Register before detail. |
| 4 | One typeface. | HIG Typography | Inter everywhere (checked on every text node). |
| 5 | One type scale that grows as a whole. | HIG Typography (text styles, Dynamic Type) | Apple ratios on one base size: 17px phone to 20px at 1920. |
| 6 | Readable sizes; no thin weights for small text. | HIG Typography | Body >= 17px; nothing under 13px. |
| 7 | Hierarchy through size, weight and colour, not boxes. | HIG Typography | Headings and spacing carry structure. |
| 8 | Align to one grid with consistent margins. | HIG Layout | 1140px column; shared left edge. |
| 9 | Group with space first; lines only when space is not enough. | HIG Layout | Hairlines instead of bordered cards. |
| 10 | Progressive disclosure. | HIG Layout | Track topics and programme days open on demand. |
| 11 | Accent colour only for actions and status; one meaning per colour. | HIG Branding, Color | Teal = links/buttons/current; red = ended. Times and labels are ink. |
| 12 | WCAG contrast; never colour alone. | HIG Accessibility, Color | Alpha-aware contrast check on every text node. |
| 13 | Targets >= 44pt, with space between. | HIG Accessibility | Checked on buttons, tabs, links in bars. |
| 14 | Every control shows press, focus and hover; hover is never required. | HIG Buttons | :active scale, :focus-visible ring, hover only for mouse. |
| 15 | Short, verb-first labels in sentence case that say what happens. | HIG Writing | "Register", "Email your proposal", "Opens your email app". |
| 16 | Honest: no fake controls, fake status or invented numbers. | Rams "honest" | No fake "sent"; facts only (2 days, 4 tracks). |
| 17 | Motion only with purpose; brief; optional. | HIG Motion | <= 0.5s, opacity/transform, off for reduced motion. |
| 18 | Familiar components in expected places. | HIG Branding | Sticky section bar, segmented control, disclosure. |
| 19 | Recompose per size class; never shrink. | HIG Layout (size classes) | Separate phone layout; text never below 13px. |
| 20 | As little design as possible. | Rams "less, but better" | Remove a box, colour or label unless it carries information. |
