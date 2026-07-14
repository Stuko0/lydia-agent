# Lydia Desktop ☤

<p align="center">
  <a href="https://10.1.200.116:3000/arquant-admin/NewLydia/releases"><img src="https://img.shields.io/badge/Download-macOS%20%C2%B7%20Windows%20%C2%B7%20Linux-FFD700?style=for-the-badge" alt="Download"></a>
  <a href="https://lydia-agent.nousresearch.com/docs/"><img src="https://img.shields.io/badge/Docs-lydia--agent.nousresearch.com-FFD700?style=for-the-badge" alt="Documentation"></a>
  <a href="https://discord.gg/NousResearch"><img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord"></a>
  <a href="https://10.1.200.116:3000/arquant-admin/NewLydia/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License: MIT"></a>
</p>

**The native desktop app for [Lydia Agent](../../README.md) — the self-improving AI agent from [Nous Research](https://nousresearch.com).** Same agent, same skills, same memory as the CLI and gateway, in a polished native window — chat with streaming tool output, side-by-side previews, a file browser, voice, and settings, no terminal required. Available for **macOS, Windows, and Linux**.

<table>
<tr><td><b>Chat with the full agent</b></td><td>Streaming responses, live tool activity, structured tool summaries, and the same conversation history as every other Lydia surface.</td></tr>
<tr><td><b>Side-by-side previews</b></td><td>Render web pages, files, and tool outputs in a right-hand pane while you keep chatting.</td></tr>
<tr><td><b>File browser</b></td><td>Explore and preview the working directory without leaving the app.</td></tr>
<tr><td><b>Voice</b></td><td>Talk to Lydia and hear it back.</td></tr>
<tr><td><b>Settings & onboarding</b></td><td>Manage providers, models, tools, and credentials from a real UI. First-run setup gets you to your first message in seconds.</td></tr>
<tr><td><b>Stays current</b></td><td>Built-in updates pull the latest agent and rebuild the app in place.</td></tr>
</table>

---

## Install

### Install with Lydia (recommended)

Already have the Lydia CLI? Just run:

```bash
lydia desktop
```

It builds and launches the GUI against your existing install — same config, keys, sessions, and skills. On first launch Lydia walks you through picking a provider and model; nothing else to configure.

### Prebuilt installers

Prebuilt installers are built and distributed via [the Lydia Desktop website.](https://lydia-agent.nousresearch.com/).

---

## Updating

The app checks for updates in the background and offers a one-click update when one is ready. You can also update any time from the CLI:

```bash
lydia update
```

---

## Requirements

The installer handles everything for you (Python 3.11+, a portable Git, ripgrep).

---

## Development

Want to hack on the app itself? Install workspace deps from the repo root once, then run the dev server from this directory:

```bash
npm install          # from repo root — links apps/desktop, web, apps/shared
cd apps/desktop
npm run dev          # Vite renderer + Electron, which boots the Python backend
```

Point the app at a specific source checkout, or sandbox it away from your real config:

```bash
LYDIA_DESKTOP_LYDIA_ROOT=/path/to/clone npm run dev
LYDIA_HOME=/tmp/throwaway npm run dev
npm run dev:fake-boot   # exercise the startup overlay with deterministic delays
```

### Building installers

```bash
npm run dist:mac     # DMG + zip
npm run dist:win     # NSIS + MSI
npm run dist:linux   # AppImage + deb + rpm
npm run pack         # unpacked app under release/ (no installer)
```

Installers are built and uploaded to GitHub Releases manually. macOS/Windows signing & notarization happen automatically when the relevant credentials are present in the environment (`CSC_LINK` / `CSC_KEY_PASSWORD` / `APPLE_*` for macOS, `WIN_CSC_*` for Windows).

### How it works

The packaged app ships the Electron shell and a native React chat surface. On first launch it can install the Lydia Agent runtime into `LYDIA_HOME` (`~/.lydia`, or `%LOCALAPPDATA%\lydia` on Windows) — the **same layout a CLI install uses**, so the two are interchangeable. Backend resolution first honours `LYDIA_DESKTOP_LYDIA_ROOT`, then a completed managed install, then a probed `lydia` on `PATH` (unless `LYDIA_DESKTOP_IGNORE_EXISTING=1` is set), and finally an explicit `LYDIA_DESKTOP_LYDIA` command override for packagers/troubleshooting. The renderer (React, in `src/`) talks to a headless backend the app launches for you — a `lydia serve` process that serves the `tui_gateway` JSON-RPC/WebSocket API — through the framework-agnostic client in [`apps/shared`](../shared/) (the same client the web dashboard consumes), and reuses the agent runtime rather than embedding `lydia --tui`. The app is **self-contained**: it runs its own `lydia serve` backend and never opens or requires the web dashboard UI. (For backward compatibility, a runtime that predates the `serve` command automatically falls back to a headless `dashboard --no-open` — see `electron/backend-command.cjs` — so mid-upgrade installs never break.) The install, backend-resolution, and self-update logic all live in `electron/main.cjs`.

### Verification

Run before opening a PR (lint may surface pre-existing warnings but must exit cleanly):

```bash
npm run fix
npm run typecheck
npm run lint
npm run test:desktop:all
```

### Troubleshooting

Boot logs land in `LYDIA_HOME/logs/desktop.log` (includes backend output and recent Python tracebacks) — check it first if the app reports a boot failure.

**macOS / Linux:**

```bash
# Force a clean first-launch setup
rm "$HOME/.lydia/lydia-agent/.lydia-bootstrap-complete"
# Rebuild a broken Python venv
rm -rf "$HOME/.lydia/lydia-agent/venv"
# Reset a stuck macOS microphone prompt (macOS only)
tccutil reset Microphone com.nousresearch.lydia
```

**Windows (PowerShell):**

```powershell
# Force a clean first-launch setup
Remove-Item "$env:LOCALAPPDATA\lydia\lydia-agent\.lydia-bootstrap-complete"
# Rebuild a broken Python venv
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\lydia\lydia-agent\venv"
```

> The default Lydia home on Windows is `%LOCALAPPDATA%\lydia`. Set the `LYDIA_HOME` env var if you've relocated it.

---

## Community

- 💬 [Discord](https://discord.gg/NousResearch)
- 📖 [Documentation](https://lydia-agent.nousresearch.com/docs/)
- 🐛 [Issues](https://10.1.200.116:3000/arquant-admin/NewLydia/issues)

---

## License

MIT — see [LICENSE](../../LICENSE).

Built by [Nous Research](https://nousresearch.com).
