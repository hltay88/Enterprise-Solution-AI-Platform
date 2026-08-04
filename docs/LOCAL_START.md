# Local start on Mac (Docker)

One-command / one-click start/stop for Project Atlas using Docker Compose.

## One-time setup

1. Install **Docker Desktop** for Mac and open it once.
2. Docker Desktop → **Settings → General** → enable **Start Docker Desktop when you log in**.
3. Pull the latest repo on your Mac:

```bash
cd "/path/to/Enterprise Solution AI Platform"
git pull origin main
chmod +x start-atlas.sh stop-atlas.sh "Start Atlas.command" "Stop Atlas.command"
```

## One-click start / stop (Finder or Dock)

These are **not** set up automatically by git alone — after you pull, do this once on your Mac:

1. In **Finder**, open your repo folder.
2. Double-click **`Start Atlas.command`** to start (or **`Stop Atlas.command`** to stop).
   - If macOS says it can’t be opened: Right-click → **Open** → **Open**.
3. Optional Dock pins:
   - Drag **`Start Atlas.command`** to the Dock.
   - Drag **`Stop Atlas.command`** to the Dock.
4. Optional Login Item (auto-start after login):
   - System Settings → General → **Login Items** → add **`Start Atlas.command`**.
   - Keep Docker Desktop set to start at login first.

After that: **one Dock click = start** or **stop**.

## Terminal (same actions)

```bash
./start-atlas.sh
./stop-atlas.sh
```

`start-atlas.sh` will:

- create `.env` from `env.example.md` if missing
- start Postgres + backend + frontend
- wait until healthy
- open http://localhost:3000 (set `SKIP_BROWSER=1` to skip)

Login: `demo@example.com` / `changeme`

Wipe local DB volume (destructive):

```bash
./stop-atlas.sh --wipe
```

## Notes

- One-click was **not** fully finished before — shell scripts existed; Finder/Dock `.command` launchers are what make true double-click / Dock start-stop work.
- `http://localhost:3000` only works while the stack is running.
- After a Mac reboot: wait for Docker Desktop, then click **Start Atlas** (or wait for Login Item).
- AI keys are optional; without them the backend uses the local analysis fallback.
