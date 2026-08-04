# Local start on Mac (Docker)

One-command start/stop for Project Atlas using Docker Compose.

## One-time setup

1. Install **Docker Desktop** for Mac and open it once.
2. Docker Desktop → **Settings → General** → enable **Start Docker Desktop when you log in**.
3. Clone/pull this repo and open a Terminal in the repo root.
4. Make scripts executable (once):

```bash
chmod +x start-atlas.sh stop-atlas.sh
```

### Optional: open Atlas at login

- System Settings → General → **Login Items** → add `start-atlas.sh`, **or**
- Create an Automator/Shortcuts app that runs `./start-atlas.sh` and put that in Login Items / Dock.

## Daily use

```bash
./start-atlas.sh
```

This will:

- create `.env` from `env.example.md` if missing
- start Postgres + backend + frontend
- wait until healthy
- open http://localhost:3000 (set `SKIP_BROWSER=1` to skip)

Login: `demo@example.com` / `changeme`

Stop (keeps database data):

```bash
./stop-atlas.sh
```

Stop and wipe local DB volume:

```bash
./stop-atlas.sh --wipe
```

## Notes

- `http://localhost:3000` only works while the stack is running (or while Docker Desktop is up with containers set to restart).
- After a Mac reboot: wait for Docker Desktop, then run `./start-atlas.sh` (or rely on Login Items).
- AI keys are optional; without them the backend uses the local analysis fallback.
