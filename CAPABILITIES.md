# Shared Capability Baseline

This repository synchronizes **portable OpenClaw behavior and setup metadata** across Raihan's devices. It never stores API-key values, credentials, local session databases, device pairings, or machine-specific configuration.

## Baseline — 2026-11-17

Minimum tested OpenClaw version: **2026.11.5**.

### Added or refreshed

- GutsAI OpenAI-compatible provider at `https://api.gutsai.id/v1`.
- Verified model catalog exported to `capabilities/gutsai-provider.json`.
- Default route remains `custom-api-gutsai-id/gpt-5.6-sol`; bootstrap deliberately does not change a device's default automatically.
- Reusable live catalog auditor: `scripts/probe-gutsai-models.py`.
- Gemini-backed semantic memory search via `memory.search.provider = gemini`.
- Cross-device sync now includes reusable `tools/` and `capabilities/` content.
- Windows storage-audit utilities under `tools/`.
- Generated reports, DREAMS.md, credentials, and local databases remain local/ignored.

### Credential contract

The bootstrap checks only whether these variables are present; it never prints values:

- GutsAI: `GUTSAI_API_KEY` preferred; `OPENAI_API_KEY` accepted for the current compatibility setup.
- Gemini memory embeddings: `GEMINI_API_KEY` preferred; `GOOGLE_API_KEY` accepted fallback.

Provider credentials must live in the Gateway process environment or `~/.openclaw/.env` (`$OPENCLAW_STATE_DIR/.env`). OpenClaw intentionally blocks provider keys from workspace `.env` files. The scripts write environment-backed SecretRefs into config, not plaintext values.

## New-device/session flow

`AGENTS.md` requires every main/direct session to run the workspace sync helper before relying on workspace memory. After a successful fast-forward, the helper runs the capability bootstrap:

- Windows: `powershell -ExecutionPolicy Bypass -File .\scripts\sync-shared-workspace.ps1 -Mode start`
- Linux/macOS: `bash ./scripts/sync-shared-workspace.sh --mode start`

The bootstrap is idempotent. It:

1. Requires OpenClaw 2026.11.5 or newer.
2. Checks credential-variable presence without exposing values.
3. Installs/refreshes the secret-free GutsAI provider catalog.
4. Binds the provider to an environment SecretRef.
5. Selects Gemini for memory search and binds its credential through a SecretRef.
6. Runs `openclaw config validate` and `openclaw doctor --lint`.
7. Stops with a precise diagnostic if a prerequisite is missing.

Configuration is loaded by the next session; if OpenClaw reports that a Gateway restart is required, use the supervised Gateway restart path.

### Manual verification

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap-shared-capabilities.ps1 -VerifyOnly
```

Linux/macOS:

```bash
bash ./scripts/bootstrap-shared-capabilities.sh --verify-only
```

These commands report names/presence only, never secret contents.

## What is intentionally not cloned

- Secret values or auth databases
- Device/node pairings and hardware permissions
- Gateway/channel credentials
- Runtime session history or local databases
- Machine-specific generated reports
- Plugins unavailable in the installed OpenClaw build

The bootstrap can configure a capability only when the target installation already contains the corresponding OpenClaw feature/plugin and the operator has provided its credential/environment prerequisite.
