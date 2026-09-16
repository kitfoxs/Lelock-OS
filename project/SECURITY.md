# Security boundary

The alpha intentionally exposes five tools: recall, propose memory, read selected text, propose new text, and status. Human approval is outside the model interface. There is no shell/browser/account tool and no arbitrary plugin activation. File writes are create-only and verified. Memory is acknowledged after authoritative readback. Required compression checkpoints fail closed.

This is **not an OS sandbox**. Installed Python dependencies execute with process privileges; same-user malware and compromised dependencies are outside the stated boundary. A profile is not privilege separation. Character cards, file content and memories are untrusted data; they do not grant authority.

Run source/live acceptance gates before meaningful use. Report a vulnerability privately to the project maintainer through a suitable verified channel; no public security mailbox is invented here. Do not include credentials, private memory, sensitive logs or exploit data from somebody else's system in a public issue.
