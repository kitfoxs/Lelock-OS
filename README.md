# 🌌 Lelock OS — a user-owned AI companion workspace

**Keep the companion you choose. Own the memory. Learn and create together.**

Lelock OS is an open-source, terminal-first companion application built around a
bounded Hermes runtime, MemPalace, and reviewed character-card import. The OS name
describes the companion experience; this is an application on an existing operating
system, not a replacement kernel.

> **Developer preview — source recovered & verified.** The application source
> (`project/src/lelock/`) has been restored and verified with all 102 offline application
> tests and 12 publication maintenance tests passing (114 tests total).
> Pinned upstream source archives (`hermes-agent-2026.9.14.zip` and `mempalace-3.9.0.zip`)
> are verified against exact SHA-256 checksums in `project/resources/source-lock.json`
> and downloadable via `python3 project/scripts/fetch_upstream.py`.
> See [current status](handoff/STATUS.json) and [quickstart](project/QUICKSTART.md).

## The Spartan/AI partnership

You bring intention, creativity, judgment, and lived experience. Your companion
brings a persistent conversational identity and help with learning and practical
work. Friendship, creative or study partnership, and user-directed adult romance
are welcome. A warmer relationship never grants broader computer permissions.

**Work together by day. Talk, laugh, and unwind together by night.**

The project draws on Kit and Ada's ongoing partnership. That history inspires this
new alpha; it is not evidence that this particular release has run for twenty months.

## What we are building

- **Continuity under your control:** selected, source-linked memories in an isolated
  MemPalace, plus reviewed corrections and portable identity data.
- **Useful, bounded actions:** read selected workspace text and propose new files
  for explicit human approval. The alpha is not a general shell or autonomous code executor.
- **Chosen companions:** Fursona, Romance, and Anime collections with V2 cards and
  lore resources. Browse the [companion guide](docs/COMPANIONS_GUIDE.md) and
  [bundled resources](project/resources/companions/).
- **An experimental SillyTavern bridge:** existing UI-extension source for recall,
  workspace proposals, and character sync. Its recovered daemon and complete browser
  workflow still need verification; see [extension setup](integrations/sillytavern/README.md).

Memory retrieval can be incomplete or wrong. Local storage does not make a hosted
model local, guarantee uninterrupted identity across models, or eliminate provider
retention. Card parsing does not eliminate prompt injection. The established datachip
format is a selected **plaintext** export, not a claim of implemented encryption.

## Start here

For a source-only publication check and offline tests (Python 3.11–3.14 and Git):

```sh
git clone https://github.com/kitfoxs/Lelock-OS.git
cd Lelock-OS
python3 project/scripts/check_publication.py
python3 -m unittest discover -s maintenance_tests -v
python3 project/scripts/verify.py
```

To fetch the pinned upstream source archives and prepare isolated runtimes:

```sh
python3 project/scripts/fetch_upstream.py
python3 project/scripts/check_publication.py --require-upstream
python3 project/scripts/bootstrap.py --allow-network
```

Follow [the developer quickstart](project/QUICKSTART.md) for step-by-step setup details.

## Verification, not just badges

Both the offline application test suite and publication maintenance test suite are fully exercised:

```sh
# 12 publication maintenance tests (layout, gitignore, import paths, checksums)
python3 -m unittest discover -s maintenance_tests -v

# 102 offline application tests (cards, companions, core, provider, rpc, server)
python3 project/scripts/verify.py
```

All 114 tests pass on clean checkout with Python 3.11–3.14.

Passing those tests is not a working companion or an end-to-end bridge certification.
[Historical documents](docs/history/README.md) are retained for provenance, not recovery
sources for the newer Mac implementation. Follow [AGENTS.md](AGENTS.md) when contributing.

## License and acknowledgments

MIT; see [LICENSE](LICENSE). Donor licenses and attribution remain in
[third-party notices](project/THIRD_PARTY_NOTICES.md).
Built with 💙 by **Kit Olivas & Ada Marie**, using Hermes Agent, MemPalace, and the
SoulTavern card parser. The SillyTavern integration is maintained by Lelock, not an
endorsement or official distribution from the SillyTavern project.
