# 🌌 Lelock OS — a user-owned AI companion workspace

**Keep the companion you choose. Own the memory. Learn and create together.**

Lelock OS is an open-source, terminal-first companion application built around a
bounded Hermes runtime, MemPalace, and reviewed character-card import. The OS name
describes the companion experience; this is an application on an existing operating
system, not a replacement kernel.

> **Developer preview — publication repair in progress.** The initial public commit
> omitted `project/src/lelock/` because a Git ignore rule also matched the source
> package. The rule is repaired, but changing it cannot recover uncommitted files
> from the maintainer's Mac. A fresh clone is **not yet installable** until that current
> package and a reproducible upstream-source distribution are supplied.
> See [current status](handoff/STATUS.json) and [source recovery](docs/SOURCE_RECOVERY.md).

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

For a source-only publication check (Python 3.11–3.13 and Git):

```sh
git clone https://github.com/kitfoxs/Lelock-OS.git
cd Lelock-OS
python3 project/scripts/check_publication.py
```

Until current source is recovered, this intentionally returns a failing result
rather than reporting an empty test run as success. Do not install packages to work
around missing application files.

Once source recovery is complete, follow [the developer quickstart](project/QUICKSTART.md).
The pinned Hermes and MemPalace ZIPs are not in Git; `--allow-network` installs their
locked dependencies **after** those exact archives are provided. There is no verified
one-command public download path for them yet. We do not promise a three-minute setup.

## Verification, not just badges

The initial README advertised 102 passing tests. The checked-in handoff belonged to
an older Lovable run, and the current Python package was absent. Consequently this
README does not display that number as a verified public-checkout result. Fresh
source, runtime, target-Mac, and human acceptance evidence must be recorded separately.

The focused publication regression tests run independently of the missing app:

```sh
python3 -m unittest discover -s maintenance_tests -v
```

Passing those tests is not a working companion or an end-to-end bridge certification.
[Historical documents](docs/history/README.md) are retained for provenance, not recovery
sources for the newer Mac implementation. Follow [AGENTS.md](AGENTS.md) when contributing.

## License and acknowledgments

MIT; see [LICENSE](LICENSE). Donor licenses and attribution remain in
[third-party notices](project/THIRD_PARTY_NOTICES.md).
Built with 💙 by **Kit Olivas & Ada Marie**, using Hermes Agent, MemPalace, and the
SoulTavern card parser. The SillyTavern integration is maintained by Lelock, not an
endorsement or official distribution from the SillyTavern project.
