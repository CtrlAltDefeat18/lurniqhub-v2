# Brand and Design

Status: Draft v0.1, 21/10/2026. The current palette is a working set. A fuller redesign comes after the MVP works and has been tested with learners.

## Brand in one line

Working tagline: "Navigate your future." Tone: calm, direct, credible. The nautical theme is a framing device, not a costume.

## Voice

- Plain language. Short sentences. Written for a Grade 9 reader.
- South African English spelling (organise, colour, programme). Dates as DD/MM/YYYY. Money in rand (R).
- No emojis, anywhere in the interface or in documents.
- Say what a thing is and what to do next. Avoid hype, slang for its own sake, and childish phrasing.
- Be exact about requirements, deadlines and amounts, and show where the information came from.

## Colour (working palette)

| Token | Hex | Use |
|---|---|---|
| primary | #1976D2 | Main actions, links |
| secondary | #0097A7 | Secondary accents |
| ocean | #006994 | Headers, gradients |
| deep-sea | #003D5C | Dark surfaces, text on light |
| wave | #4ECDC4 | Highlights only |

Rules:
- Text and interactive elements must meet WCAG AA contrast (4.5:1 for body text). White text on `wave` does not pass, so use dark text on it.
- Do not rely on colour alone to carry meaning. Pair it with a label or icon.
- Define colours once as tokens in the Tailwind config. Do not scatter hex values through templates.

## Typography

- Headings: Space Grotesk. Body: Inter. Both with a system-font fallback stack.
- Consider self-hosting fonts later to save data and avoid third-party requests.
- Body text 16px minimum.

## Iconography and imagery

- One icon set (Material Icons, rounded). Consider inline SVG or a subset later, since the full icon font is heavy on slow connections.
- Photographs only with explicit consent. No identifiable images of learners without parent or guardian consent.
- Prefer real places and real people from the region over generic stock images.

## Motion

- Use GSAP sparingly: page entrance and feedback, not decoration.
- Respect `prefers-reduced-motion` and turn animation off when it is set.
- Animation must never block content from appearing.

## Layout and components

- Mobile first. Design at about 360px wide, then scale up.
- Touch targets at least 44px.
- One primary action per screen.
- Standard components: button, card, form field, alert, progress bar, modal. Build each once and reuse it.
- Forms: visible labels, clear error messages, and no more fields than needed.

## Performance budget (targets)

- Initial page weight kept small enough to load on 3G in a few seconds. Set a number once measured on a real device.
- No large images without compression and explicit dimensions.
- No render-blocking third-party scripts beyond what is essential.

## Gamification

Ranks, points and badges are deferred until the pathway guide and lessons are working. When reintroduced, they must be understated and tied to real learning, not login counts.

## Accessibility checklist

- Semantic HTML and one `h1` per page
- Keyboard-reachable controls with visible focus
- Alt text on meaningful images
- Language attribute set on the page
- Tested with a screen reader at least once before the pilot

## Later

Logo, final palette and a design system are to be developed after user feedback. Until then, keep the working palette and avoid new one-off styles.
