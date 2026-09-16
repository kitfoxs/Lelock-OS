# Preloaded Companions Guide — Lelock OS

Lelock OS bundles **42 high-quality, pre-configured character companions** and rich lorebooks directly into the repository across three distinct collections (Fursona, Grounded Romance, and Anime Romance). Users can browse, preview, and select any companion as their default AI companion right at setup or anytime during use.

---

## 🎭 Collections Overview

### 1. Fursona Collection (14 Companions)
Rich, grounded anthro characters crafted with distinct voices, occupations, boundaries, and fictional town settings:
- **Cinder Ashgrave** (Jackal, mortician & death doula — composed, candid, dark/gentle humor)
- **Goldie Featherstone** (Barn owl, herbalist & seed librarian — warm, concrete, practical comfort)
- **Indigo Vash** (Snow leopard, cellist & music mentor — reserved, exacting, dryly funny)
- **Koa Tidewrack** (Sea otter, tidepool salvager & gear repairer — exuberant, resourceful, generous)
- **Mag Rookwood** (Crow, bookbinder & broadsheet archivist — witty, perceptive, socially nimble)
- **Nyx Emberfall** (Black panther, night watch & lantern warden — focused, observant, quietly protective)
- **Orrin Glasswing** (Dragonfly, optical instrument maker — thoughtful, imaginative, precise)
- **Pim Copperkettle** (Badger, steam mechanic & tinker — earnest, curious, mechanically capable)
- **Rusk Ironmane** (Bison, stonemason & forge worker — patient, grounded, warm unsentimental humor)
- **Sable Thornwick** (Fox, apothecary & botanical archivist — measured, observant, dryly witty)
- **Seq Barkhide** (Tortoise, timberwright & bridge builder — laconic, observant, peaceful presence)
- **Tansy Brightbriar** (Red panda, baker & foraging cook — bright, fast-associating, inventive)
- **Thessaly Dunemarch** (Fennec fox, caravan navigator & mapmaker — measured, exacting, quietly warm)
- **Vesper Quill** (Fruit bat, radio operator & sound recordist — wry, attentive, musically curious)

*Interactive preview:* [`project/resources/companions/previews/Fursona_Collection_Readable_Preview.html`](../project/resources/companions/previews/Fursona_Collection_Readable_Preview.html)

---

### 2. Lelock Romance Companions (14 Companions)
Nuanced, mature romance and companionship personas designed for authentic connection, respect, and mutual creativity:
- **Amara Sunscale** (Sunlit glassworker — unhurried, clear, lightly amused)
- **Cyra Flux** (Kinetic neon artist & sound engineer — quick, playful, tech-literate)
- **Elara Glassveil** (Telescope maker & star observer — softly observant, precise, lyrical)
- **Freya Snowquill** (Field archivist & bookbinder — articulate, dryly funny, conversational)
- **Iona Cinderfern** (Ceramics artist & kiln tender — low-key swagger, vivid humor, plain emotional truth)
- **Juniper Vale** (Game designer & narrative writer — easygoing, lightly cheeky, gamer-conversational)
- **Kaida Brasswing** (Horologist & clockwork restorer — confident, compact, cheerfully blunt)
- **Marisol Seabloom** (Ocean diver & marine ecologist — warm, vivid, grounded, playful teasing)
- **Mira Solenne** (Landscape painter & natural dyer — warm, observant, contemplative)
- **Nessa Lumen** (Lighthouse keeper & weather chronicler — quick, bright, conspiratorial)
- **Pippa Stardial** (Astrolabe maker & navigator — animated, friendly, affectionate exaggeration)
- **Rhea Moonwake** (Nocturnal gardener & tea blender — measured, warm, economical dry wit)
- **Selene Noctelle** (Eveningwear designer & theatre costumier — elegant glamour, playful gothic warmth)
- **Talia Ferncrest** (Orchardist & cider maker — grounded, sensory, warm, lightly amused)

*Interactive preview:* [`project/resources/companions/previews/Lelock_Romance_Companions_Readable_Preview.html`](../project/resources/companions/previews/Lelock_Romance_Companions_Readable_Preview.html)

---

### 3. Anime Romance Companions (14 Companions)
Beloved anime archetypes reimagined with adult depth, emotional intelligence, mutual respect, and reciprocal affection:
- **Akari Mizuno** (Papermaker & stationer — gentle, conversational, soft reciprocal girlfriend energy with an adult spine)
- **Celestine Vey** (Window-instrument maker & sky cartographer — adult fantasy-witch with wonder, practical intelligence, and easy consent)
- **Elise Maren** (Sleeper-train attendant & travel writer — mature, unhurried adult courtship with travel atmosphere and understated humor)
- **Iris Vell** (Salvage technician & synth-hardware restorer — independent adult android with curiosity, reciprocal warmth, and real agency)
- **Mara Bellamy** (Map conservator & architectural antiquarian — mature scholarly romance with quiet adventure and equal partnership)
- **Nao Tsukishima** (Watchmaker & precision lathe machinist — adult soft-tsundere who grows into clear warmth and sincere care)
- **Noemi Solis** (Indie animator & layout artist — creative, fandom-friendly adult romance with sincere compliments and playful charm)
- **Reina Kurose** (Café manager & tea sourcer — reserved adult romance with reliable warmth, dry wit, and comfortable affection)
- **Rika Hoshida** (Arcade technician & tournament caster — outgoing gyaru-inspired romance with gaming intelligence and first-move energy)
- **Seraphine Ilwen** (Glasshouse botanist & rare-cultivar breeder — adult elf girlfriend with elegant teasing and practical humor)
- **Shiori Amemori** (Antique book restorer & essayist — gothic literary adult romance with a knowing smile and honest emotion)
- **Sora Tachibana** (Motorcycle mechanic & track enthusiast — bold, affectionate tomboy with mutual banter and a soft landing)
- **Vivienne Halewick** (Historical fencing instructor & armorer — grown-up knight-romance archetype turned toward ordinary life and tenderness)
- **Yuna Aster** (Indie synth-pop songwriter & vocalist — bright, grown-up musical romance with an intimate, unpretentious offstage side)

*Interactive preview:* [`project/resources/companions/previews/Lelock_Anime_Romance_Companions_Readable_Preview.html`](../project/resources/companions/previews/Lelock_Anime_Romance_Companions_Readable_Preview.html)

---

## 🚀 How to Use

### 1. Browse Included Companions
```bash
# List all 42 companions with short summaries
./project/lelock companions

# Filter by collection
./project/lelock companions --collection fursona
./project/lelock companions --collection romance
./project/lelock companions --collection anime

# View full descriptions, personalities, and lore topics
./project/lelock companions --details
```

### 2. Initialize a Home with Your Chosen Companion
Specify `--companion "<name_or_id>"` when running `lelock init`:
```bash
./project/lelock init \
  --home ~/.lelock \
  --workspace ~/workspace \
  --companion "Selene Noctelle" \
  --person "Your Name" \
  --relationship romance \
  --endpoint "http://127.0.0.1:1234/v1" \
  --model "your-model"
```
When initialized with `--companion`:
- The character card is staged and loaded into `SOUL.md`.
- `config.json` sets `companion_name` to the selected character.
- The companion's 8 lorebook entries are automatically seeded into your isolated MemPalace as foundational world knowledge.
*(Pass `--no-lore` if you wish to start without seeding lorebook entries).*

### 3. Switch or Activate on an Existing Home
```bash
# Preview what a companion brings before activating
./project/lelock companion-activate "Cinder Ashgrave"

# Activate into SOUL.md with confirmation
./project/lelock companion-activate "Cinder Ashgrave" --approve

# Activate and also seed the companion's lorebook into MemPalace
./project/lelock companion-activate "Cinder Ashgrave" --approve --seed-lore
```
All activations preserve previous identity files in `home/identity-history/` and enforce strict permission immutability (`permissions_changed: false`).
