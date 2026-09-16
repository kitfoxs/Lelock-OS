# Quickstart

Complete the source/dependency and actual integration gates in the enclosing packet first. Commands here assume you are in `project/` and the generated `./lelock` launcher exists. Do not use a private Ada/Mempalace home as a test profile.

```sh
./lelock --home "$HOME/.local/share/lelock-os-alpha" init \
  --workspace "$HOME/LelockWorkspace" --name Samantha --person Kit \
  --relationship friendship --endpoint 'http://127.0.0.1:1234/v1' \
  --model 'REPLACE_WITH_ACTUAL_SELECTED_MODEL_ID' --retention explicit
./lelock --home "$HOME/.local/share/lelock-os-alpha" doctor
./lelock --home "$HOME/.local/share/lelock-os-alpha" chat
```
The endpoint/model above are an example shape, not a claim that this service is running. Remote endpoints require HTTPS and `LELOCK_MODEL_API_KEY` through approved environment secret handling; never put the key in a command history, README or datachip.

In chat, `/help` lists `/pending`, `/approve ID`, `/reject ID`, `/remember TEXT`, `/recall QUERY`, `/forget ID`, `/status`, and `/quit`. Human approval displays the stored payload and requires YES. The model cannot approve itself. Readable files must be inside the chosen workspace; writes are new files only.

Outside chat, all commands use global `--home PATH` **before** the subcommand:
```sh
./lelock --home "$HOME/.local/share/lelock-os-alpha" remember 'My synthetic practice project is Copper Meadow.'
./lelock --home "$HOME/.local/share/lelock-os-alpha" recall 'practice project'
./lelock --home "$HOME/.local/share/lelock-os-alpha" memory-list
./lelock --home "$HOME/.local/share/lelock-os-alpha" memory-flush
./lelock --home "$HOME/.local/share/lelock-os-alpha" new-session
./lelock --home "$HOME/.local/share/lelock-os-alpha" export ./selected-companion.json
./lelock inspect-datachip ./selected-companion.json
```
Export is plaintext and selected, not a full backup. Restore chooses a new home/workspace/endpoint:
```sh
./lelock --home "$HOME/.local/share/lelock-os-restored" restore ./selected-companion.json \
  --workspace "$HOME/LelockRestoredWorkspace" \
  --endpoint 'http://127.0.0.1:1234/v1' --model 'ACTUAL_MODEL_ID' --approve
```
Review a V2 JSON/PNG card using `card-review FILE`, then explicitly activate the returned review ID with `card-activate ID --approve`. Unsupported fields are ignored/reported, not executed. The old identity is backed up; permissions do not change.

`chat --temporary` does not recall the profile's Palace or allow commits/writes; selected workspace reading and provider processing remain possible. Explicit retention still preserves local session history. Journal retention is opt-in automatic direct transcript archival. Read the full privacy and recovery notes before promising deletion or using sensitive documents.
