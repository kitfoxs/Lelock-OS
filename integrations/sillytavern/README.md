# Lelock OS — SillyTavern Agent Harness & MemPalace Extension

> **Transform your favorite SillyTavern companion into an active pair-programmer and autonomous agent with permanent, hallucination-resistant memory.**

This extension bridges [SillyTavern](https://github.com/SillyTavern/SillyTavern) with [Lelock OS](https://github.com/kitfoxs/lelock-os), bringing:
1. 🧠 **Autonomous MemPalace Memory:** Context-aware episodic & semantic memory recall that survives across weeks and months without context rot.
2. 🛠️ **Native Workspace Tools:** Your companion can inspect directories and read UTF-8 files in your authorized project directory.
3. 🛡️ **Human-in-the-Loop Safe Approvals:** When your companion writes code or creates a file, an interactive **Diff & Approval Widget** appears directly in your chat stream. Nothing touches your disk until you click **Approve & Write**.
4. 🎴 **1-Click Card & Lorebook Sync:** Ingest any SillyTavern Character Card V2 and automatically seed its full world lorebook into your local MemPalace.

---

## ⚡ Installation (Under 1 Minute)

### Option 1: Direct Link in SillyTavern UI
1. In SillyTavern, open the top navigation bar and click the **Extensions** (cubes icon) drawer.
2. Click **Install extension** (or **Import Extension From Git Repo**).
3. Paste the extension repository URL:
   ```
   https://github.com/kitfoxs/lelock-os.git
   ```
4. Reload SillyTavern.

### Option 2: Symlink or Copy (Local)
From your terminal, link this folder directly into your SillyTavern extensions directory:
```bash
# Assuming SillyTavern is in ~/SillyTavern and Lelock OS is in ~/lelock-os:
mkdir -p ~/SillyTavern/public/scripts/extensions/third-party/
ln -s ~/lelock-os/integrations/sillytavern ~/SillyTavern/public/scripts/extensions/third-party/lelock-os
```

---

## 🚀 Quickstart

### 1. Start the Lelock OS Bridge Daemon
From your Lelock OS directory:
```bash
./project/lelock serve
```
You will see:
```text
Lelock OS Bridge Daemon running on http://127.0.0.1:8780
Companion: Samantha | Scope: personal | Workspace: /Users/kit/workspace
Connected to MemPalace wing: lelock-default
Press Ctrl+C to stop.
```

### 2. Open SillyTavern & Verify Connection
1. Open SillyTavern in your browser (`http://127.0.0.1:8000`).
2. Open the **Extensions** drawer.
3. Scroll down to **Lelock OS — Agent Harness & MemPalace**.
4. You will see a green badge: **Connected (`<Companion Name>`)**.

### 3. Sync Your Character & Lorebook
1. Select your favorite character card in SillyTavern.
2. In the Lelock OS extension panel, click **Sync Active Character to Lelock OS**.
3. Your card's persona and all 8 lorebook entries are immediately indexed into your local MemPalace!

---

## 🛡️ Interactive In-Chat Approvals

When your companion uses `lelock_write_text` to write code or modify files in your workspace, SillyTavern renders a rich, interactive card right in the chat:

```text
┌────────────────────────────────────────────────────────────┐
│ 📝 Workspace Proposal: src/main.py                         │
│ Toggle Content Preview (482 chars)                         │
│                                                            │
│   [✅ Approve & Write]          [❌ Reject]               │
└────────────────────────────────────────────────────────────┘
```

* Clicking **[Approve & Write]** safely commits the file to your workspace and turns the badge green (**APPROVED & WRITTEN**).
* Clicking **[Reject]** discards the proposal without touching your disk.

---

## ⌨️ Slash Commands

| Command | Description |
|---|---|
| `/lelock-status` | Print active connection status, companion identity, workspace path, and MemPalace wing. |
| `/lelock-recall <query>` | Manually query MemPalace for past conversations, facts, or lore. |
| `/lelock-remember <text>` | Permanently save a fact or preference into your local MemPalace. |
| `/lelock-sync` | Sync the currently active SillyTavern character card and lorebook to Lelock OS. |

---

## 🔒 Security & Privacy Notice
* **Loopback Only:** The bridge daemon binds strictly to `127.0.0.1:8780`. It never opens external ports.
* **No Blind Shells:** Companions cannot execute raw bash commands. Only bounded, descriptor-relative file operations and MemPalace queries are permitted.
* **Zero Direct Overwrites:** All writes require human operator approval.
