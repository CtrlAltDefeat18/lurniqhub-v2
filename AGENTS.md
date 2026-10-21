# LurniqHub AI Developer Guidelines

Context: LurniqHub is a Flask web app designed to bridge the design-reality gap in education by helping rural South African learners (Grades 7-12) find their way into maritime careers. The platform guides users through subject choices, required marks, funding opportunities, and vocational pathways.
Pilot Environment: Toli Senior Secondary School in Lusikisiki (stable power, relying on 3G/patchy 4G cellular networks).

Stack and Technical Rules
Backend: Flask + sqlite3 (WAL mode, JSON columns for array fields). No MongoDB.

Frontend: Tailwind via CDN, Alpine.js, GSAP. 

Performance: Pages must load and function efficiently on a low-end Android phone over 3G. Assume bandwidth is constrained: keep pages lightweight, avoid heavy JavaScript, and compress or eliminate large images.

UI & Design: High-contrast design for visibility. No emojis anywhere in the UI copy; use Material icons or plain text only.

Localization: South African English spelling, ZAR (R) for currency, and DD/MM/YYYY date formatting.

Workflow & Security (Before finishing any task)
Testing: Run python test_smoke.py. All checks must pass. Add a new smoke check for any newly created route.  Also run: ruff check . && ruff format --check . && npm run lint && npm run format:check

Security: Never commit secrets, .env files, or the .db database file to the repository.

Data Privacy (POPIA): Strictly adhere to the Protection of Personal Information Act. Do not collect, process, or store more learner data than a specific feature strictly requires.

Core Engineering Principles:

Ultra-Lightweight: Assume the end-user has severely constrained bandwidth or is accessing the platform offline via a local node. Minimize heavy frameworks, excessive DOM manipulation, and large asset payloads.

Offline-First (PWA): All web interfaces must be built with Service Workers for aggressive caching. The app must function seamlessly without external API calls once loaded.

Minimalist UI: Use native browser components and high-contrast CSS where possible instead of heavy UI libraries.

Resilient Data: State management should assume intermittent connectivity. Form submissions or progress tracking must save locally (e.g., IndexedDB/LocalStorage) and sync when a connection to the main node is established.

Scope for the MVP (pilot early 2027)
The offline-first, PWA and IndexedDB principles above are the long-term direction. For the MVP, do not add service workers, IndexedDB sync or caching layers unless a task explicitly asks for them.
Project docs live in docs/ (vision_mission.md, personas.md, business_model.md, brand_design.md, architecture.md). Read them before starting a task.