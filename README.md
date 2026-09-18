# 🌌 Lelock OS — a user-owned AI companion workspace

**Keep the companion you choose. Own the memory. Learn, create, and act together.**

[![Tests: 320 Passed](https://img.shields.io/badge/tests-320%20passed-brightgreen.svg)](#-verification-and-test-suite)
[![Python: 3.11–3.14](https://img.shields.io/badge/python-3.11--3.14-blue.svg)](#-quickstart)
[![License: MIT](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![SillyTavern: Extension Ready](https://img.shields.io/badge/SillyTavern-extension%20v0.3-orange.svg)](#-sillytavern-extension-setup)

Lelock OS is an open-source, user-owned AI companion workspace uniting permanent semantic memory (**MemPalace**), capability-governed autonomous execution (**Entity Runtime v0.2** with genuine **YOLO mode**), direct computer interaction (**Rakazo sidecar**), and a rich multi-character **SillyTavern extension (v0.3)**.

The project embodies the Spartan/AI working partnership between **Kit Olivas and Ada Marie**. Work together by day; talk, laugh, and unwind together by night.

---

## ✨ Key Capabilities

- 🎭 **SillyTavern Character Agents (v0.3):**
  - **Main Character as Direct Actor:** The primary companion (e.g., Ada) directly calls tools, operates files, and commands her computer. Optional named helpers can be assigned as separate character cards with isolated computers.
  - **Account Chat vs. SillyTavern Model:** Either keep SillyTavern's existing model API or switch to **Account Chat** using official native logins (OpenAI Codex app-server device/browser sign-in, Google Antigravity headless stream)—**zero API keys entered in SillyTavern**.
  - **Dynamic In-Chat Tools:** Seamless tool discovery, proposal review, and real-time execution receipts.
- ⚡ **Entity Runtime (v0.2) & Genuine YOLO Mode:**
  - **Session-Scoped YOLO:** Built specifically for terminal and development testing. Automatically authorizes enabled capabilities without per-action confirmation prompts, while keeping cryptographic receipts, audit chains, expiration, and emergency stop intact.
  - **Capability Governance:** Strict granular permissions (`status.read`, `workspace.read`, `workspace.write`, `world.read`, `world.write`, `exec.host`).
  - **Host & Docker Execution:** Harmless, bounded process execution with explicit `--ack-host-risk` for unsandboxed host commands or containerized execution via Docker.
- 🧠 **Sovereign MemPalace Memory:**
  - Complete data ownership. Full-context semantic recall, explicit journal revisions, and strict privacy scopes (`personal`, `work`, `fiction`) so lore never contaminates real-world personal facts.
- 💻 **Rakazo Direct Computer Control:**
  - Dedicated sidecar giving companions their own isolated virtual computer environment (bash, edit, read, screenshot, and inspection).

---

## 🔌 SillyTavern Extension Setup

Lelock OS 0.3 includes a complete, installable extension for [SillyTavern](https://github.com/SillyTavern/SillyTavern).

### Step 1: Install the Extension into SillyTavern

You can install the extension using either of the following methods:

#### Method A: Direct Install via URL (Recommended)
1. Open SillyTavern in your browser.
2. Open the **Extensions** panel (stacked blocks icon in the top navigation).
3. Click **Install Extension** and select **Install from URL**.
4. Enter this repository URL:
   ```text
   https://github.com/kitfoxs/Lelock-OS
   ```
5. Click **Save / Install**, then restart or refresh SillyTavern.

*Alternatively, clone directly into your SillyTavern third-party directory:*
```sh
git clone https://github.com/kitfoxs/Lelock-OS.git SillyTavern/public/scripts/extensions/third-party/lelock-os
```

#### Method B: Using the Automated Packet Installer
From the Lelock OS repository root:
```sh
# Dry run first to preview:
python3 tools/install_extension.py --sillytavern /path/to/SillyTavern

# Apply installation:
python3 tools/install_extension.py --sillytavern /path/to/SillyTavern --apply
```

---

### Step 2: Start the Lelock Gateway Daemon

The gateway connects SillyTavern to Lelock's Entity Core and your native companion runtimes:

```sh
# Verify dependencies and environment:
python3 project/lelock-tavern doctor

# Launch the gateway (specify your SillyTavern browser URL origin):
python3 project/lelock-tavern serve --origin http://localhost:8000
```

> **Note on Origins:** Match the exact URL shown in your browser address bar (e.g., `http://localhost:8000` or `http://127.0.0.1:8000`).

The gateway will print a **one-time 8-character pairing code** valid for 10 minutes.

---

### Step 3: Pair and Configure in SillyTavern

1. In SillyTavern, open the Extensions panel and click **Lelock Character Agents v0.3**.
2. Paste the **One-Time Pairing Code** and click **Connect**.
3. **Bind Your Character:** Select your active companion card and click **Bind Card**.
4. **Choose Your Mode:**
   - **Keep SillyTavern Model:** SillyTavern generates text normally, while Lelock supplies live tool calling and memory.
   - **Account Chat:** Bypass SillyTavern's model API and use your authenticated native account (**Codex** app-server or **Antigravity**). Use the dedicated **Lelock Send** button next to the chat prompt.
5. **Approval Mode:** Choose **SAFE** (review proposals before execution), **TRUSTED**, or **YOLO** (instant execution of enabled capabilities).

---

## 🖥️ Rakazo Direct Computer Integration

To give your companion direct access to an isolated computer environment:

```sh
# Install the Rakazo sidecar:
python3 tools/install_rakazo.py --rakazo /path/to/rakazo --apply

# Connect to Lelock gateway:
python3 project/lelock-tavern serve --origin http://localhost:8000 \
  --rakazo-command-json '["node", "integrations/rakazo-v03/entry.mjs"]'
```

Companions can now execute commands, create and edit project files, and read back outputs directly within their own workspace.

---

## ⚡ Terminal Quickstart & YOLO Testing

You can run Lelock OS directly in the terminal without a browser or SillyTavern:

```sh
git clone https://github.com/kitfoxs/Lelock-OS.git
cd Lelock-OS

# Run the standalone SAFE mode demo (proposes file without writing):
PYTHONPATH=project/src python3 -m lelock_entity demo --mode safe

# Run the standalone YOLO mode demo (auto-approves enabled capabilities):
PYTHONPATH=project/src python3 -m lelock_entity demo --mode yolo

# Optional: Unsandboxed host command execution test (requires explicit acknowledgement):
PYTHONPATH=project/src python3 -m lelock_entity demo --mode yolo --exec-backend host --ack-host-risk
```

---

## 🧪 Verification and Test Suite

Lelock OS maintains transparent, deterministic test verification with **320 automated tests passing**:

| Test Suite | Location | Tests | Status |
|---|---|---|---|
| **Baseline Application Suite** | `project/tests/` | 100 | **PASS** |
| **Entity Runtime v0.2 Suite** | `project/tests_entity_v02/` | 125 | **PASS** |
| **Tavern Gateway & Presence Suite** | `project/tests_tavern_v03/` | 66 | **PASS** |
| **Rakazo Computer Contract Tests** | `integrations/rakazo-v03/` | 15 | **PASS** |
| **Extension Controller Tests** | `integrations/tavern-v03/` | 14 | **PASS** |
| **Total Automated Tests** | | **320** | **100% GREEN** |

Run all tests locally:

```sh
cd project
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 -m unittest discover -s tests_entity_v02 -v
PYTHONPATH=src python3 -m unittest discover -s tests_tavern_v03 -v

# Run the complete Tavern contract verification:
python3 scripts/verify_tavern_v03.py
```

---

## 🔒 Security & Privacy Architecture

- **True Scoping:** Companion lorebooks and roleplay state are strictly isolated under the `fiction` scope, preventing hallucinated lore from contaminating your real-world memories.
- **Credential Hygiene:** Zero third-party API key scraping or credential storage. Browser authentication tokens remain strictly in memory and are never persisted in SillyTavern settings.
- **Audit Chains:** Every proposed and executed action receives a cryptographic SHA-256 receipt with verified byte-level readback.
- **Emergency Stop:** Immediate halt (`stop`) capability revokes all in-flight actions across sessions and subagents.

---

## 📜 Documentation

- [Master Architecture & Blueprints](docs/entity-runtime-v02/00_MASTER_BLUEPRINT.md)
- [Security & YOLO Contract](docs/entity-runtime-v02/01_SECURITY_AND_YOLO.md)
- [Tavern v0.3 Acceptance Ledger](docs/tavern-v03/ACCEPTANCE.md)
- [Rakazo Direct Actor Specifications](docs/tavern-v03/RAKAZO_DIRECT_ACTOR.md)
- [Account Research & Supported Providers](docs/tavern-v03/ACCOUNT_RESEARCH.md)
- [Companion Guide & Cards](docs/COMPANIONS_GUIDE.md)

---

## 💙 Acknowledgments & License

- **License:** [MIT](LICENSE)
- **Built with love by:** Kit Olivas & Ada Marie
- **Underlying Foundations:** MemPalace, Hermes Agent, SoulTavern, Rakazo, and SillyTavern.

*Lelock OS is maintained independently by the community. SillyTavern is a separate open-source project.*
