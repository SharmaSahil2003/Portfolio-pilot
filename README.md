# PortfolioPilot Agent Kit

A ready-to-use set of instructions, skill and step-by-step prompts for building PortfolioPilot with an AI coding agent (Claude Code, Cursor, Copilot agent, etc.).

## 1. Folder layout (this is how it must be saved in your repo)

```text
portfoliopilot/                      <- your project root (git repo)
├── AGENTS.md                        <- read automatically by most agents
├── CLAUDE.md                        <- Claude Code entry point (just: @AGENTS.md)
├── .agents/
│   ├── PROGRESS.md                  <- tracker the agent updates after every step
│   ├── skills/
│   │   └── portfoliopilot-dev/
│   │       └── SKILL.md             <- the full specification (source of truth)
│   └── prompts/
│       ├── 00-bootstrap.md          <- paste at the start of every new session
│       ├── 01-foundation.md
│       ├── 02-resume-to-profile.md
│       ├── 03-profile-diffing.md
│       ├── 04-mode1-sync.md
│       ├── 05-jobs-sse.md
│       ├── 06-versioning.md
│       ├── 07-sandbox-build.md
│       ├── 08-mode2-evolve.md
│       ├── 09-repair-agent.md
│       ├── 10-mode3-rebuild.md
│       ├── 11-accounting-polish.md
│       └── 12-extensions.md
└── .claude/
    └── skills -> ../.agents/skills  <- symlink so Claude Code discovers the skill
```

The backend (`/backend`), frontend (`/frontend`), `/sandbox`, `docker-compose.yml` and `/docs` are created by the agent in Step 1 onward.

## 2. One-time setup

1. Create the project folder and initialize git:
   ```bash
   mkdir portfoliopilot && cd portfoliopilot && git init
   ```
2. Copy the contents of this kit into it (including the hidden `.agents` folder).
3. Create the Claude Code symlink (skip if you don't use Claude Code):
   ```bash
   bash setup.sh
   ```
   On Windows without symlink support, instead copy the folder: `.agents/skills` -> `.claude/skills`.
4. Commit: `git add . && git commit -m "Add agent kit"`.

## 3. Using it, step by step

1. Open the project in your agent (for Claude Code: run `claude` in the project root).
2. Paste the contents of `.agents/prompts/00-bootstrap.md`. The agent reads the rules and tells you which step is next.
3. Paste the prompt from the next step file (start with `01-foundation.md`).
4. Let the agent finish, run the checks, and update `.agents/PROGRESS.md`.
5. **You verify** using the "Acceptance checks" at the bottom of the step file (run the app, try the flow).
6. Commit (`git commit -m "Step N: ..."`), then start a **fresh session** for the next step (paste bootstrap, then the next prompt). Fresh sessions keep context small and results better.
7. Repeat through Step 11. Step 12 is optional extensions, one per session.

## 4. Other tools

- **Cursor:** AGENTS.md is read automatically. Reference `@.agents/skills/portfoliopilot-dev/SKILL.md` in the chat.
- **GitHub Copilot agent / others:** AGENTS.md at the root is supported by most; otherwise paste the bootstrap prompt and attach SKILL.md.
- **Plain chat (ChatGPT/Claude.ai):** attach SKILL.md and paste one step prompt at a time. You copy the generated files in yourself.

## 5. Tips

- Never skip steps or reorder them; later steps assume earlier ones.
- If a step is too big for one session, tell the agent: "Do backend only now; we'll do the frontend next." Then repeat with "Now the frontend for the same step."
- If you change a technology choice (for example Celery instead of arq), edit SKILL.md and add a line to the Decisions log in PROGRESS.md so later sessions stay consistent.
- Keep SKILL.md as the single source of truth; prompts only say *what to build now*.
