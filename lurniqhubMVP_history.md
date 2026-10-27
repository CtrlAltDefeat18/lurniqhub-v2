# Historical archive

This file records an earlier MongoDB/Railway implementation phase. It is not
the current architecture or setup guide. For the implemented application, see
`README.md` and `docs/architecture.md`.

# Summary

LurniqHub purpose, target users, V2.0 stack, and current build state including the active MongoDB blocker

# Details
# Purpose and context

- LurniqHub is a maritime-themed EdTech platform for South African youth, particularly from rural and underserved communities
- Creates pathways from secondary school (Grades 9–12) into maritime careers
- Aligns with the South African CAPS curriculum
- Connects learners to industry opportunities, bursaries, and training programs
- Industry partners and reference points: SAMTRA, Transnet, Grindrod Shipping
- Success looks like a functional, deployed platform serving as a niche maritime career pipeline — distinct from generalist EdTech competitors — with sustainable engagement mechanics and eventually a viable revenue model beyond grants

# Constraint shaping the architecture

- Works exclusively on public machines with no ability to install local dependencies, so the stack must be web-deployable and dependency-light by design
V2.0 stack
- Backend/DB: Flask + PyMongo, MongoDB Atlas (free M0 cluster)
- Frontend: Tailwind CSS via CDN, GSAP for animations, Alpine.js for interactivity
- Deployment: Railway.app connected to GitHub
- V2.0 is a complete rebuild from an earlier Flask/SQLite prototype (v1) that ran locally

# Current state
# Mid-build on V2.0

- Nine files scaffolded and pushed to GitHub, with Railway deployment attempted
- Active blocker: MongoDB connection error at the register route
- Suspected causes of the connection error: malformed MONGODB_URI, unencoded special characters in the password, or a missing database name segment before the query string
- MongoDB Atlas network access is set to 0.0.0.0/0 and Railway environment variables were configured, but the root cause is not yet confirmed

# On the horizon

- Next step is resolving the MongoDB connection error and getting V2.0 fully deployed
- Deferred to Phase 2: photo upload for academic results verification, email system (password reset + verification), Robotics course content, Mathematics course content
- Potential partnership exploration with SkillCycle (met at Hult Prize nationals) — their decentralized peer-to-peer/torrenting-based platform and dual-mode AI system could be complementary
- Gaps to address from research: offline-first architecture, teacher integration tools, sustainable revenue model
- Moved app.py into a new src/ folder alongside templates (and static); wants initialisation in app.py updated to match that layout
- Adding a docs/ folder with vision_mission.md, personas.md, business_model.md, brand_design.md, architecture.md
- Wants strict Prettier/ESLint config and an unused-package check across package.json and requirements.txt
- Setting up GitHub Actions to test builds on every push to main
- Using OpenAI Codex (ChatGPT Plus free trial) and exploring Cursor to build the MVP; too broke for Claude Pro at the moment; aiming to put LurniqHub in front of learners at Toli by early 2027