# Anki Wiktionary Dictionary

Comprehensive English and Chinese vocabulary flashcards containing definitions, pronunciation (IPA), etymology, word forms, and pronunciation audio from Wiktionary.
Google Books Ngram frequency data is used to rank words and select the top `n`.

**English deck: [download from AnkiWeb](https://ankiweb.net/shared/info/1140417632).**

## Quick Start

Download the frequency data both languages rank by:

```bash
curl -o frequency-all.txt.gz https://raw.githubusercontent.com/hackerb9/gwordlist/master/frequency-all.txt.gz && gunzip frequency-all.txt.gz
```

### English

1. Download the [English dictionary data](https://kaikki.org/dictionary/English/) from
   [kaikki.org](https://kaikki.org)
2. Build it:

   ```bash
   python wiktionary_to_anki.py kaikki.org-dictionary-English.jsonl --language english -o english.csv
   python create_anki_package.py english.csv -o english.apkg --language english
   ```

3. Import `english.apkg` into Anki

### Chinese

1. Download the [Chinese dictionary data](https://kaikki.org/dictionary/Chinese/) from
   [kaikki.org](https://kaikki.org)
2. Clone what the cards draw on, beside this script:

   ```bash
   git clone --depth 1 https://github.com/skishore/makemeahanzi
   git clone --depth 1 --filter=blob:none --sparse https://github.com/hugolpz/audio-cmn
   git -C audio-cmn sparse-checkout set 96k/hsk 64k/syllabs
   curl -o cedict.u8.gz https://www.mdbg.net/chinese/export/cedict/cedict_1_0_ts_utf-8_mdbg.txt.gz && gunzip cedict.u8.gz
   ```

3. Build it:

   ```bash
   CEDICT=cedict.u8 python wiktionary_to_anki.py kaikki.org-dictionary-Chinese.jsonl --language chinese -o chinese.csv
   CEDICT=cedict.u8 python create_anki_package.py chinese.csv -o chinese.apkg --language chinese
   ```

4. Import `chinese.apkg` into Anki

Without those checkouts the deck still builds, with no stroke diagrams and no audio.

## Usage

```bash
python wiktionary_to_anki.py input.jsonl --language english|chinese
python create_anki_package.py input.csv --language english|chinese
```

`--language` picks which Wiktionary language to read and which columns to write, and
has to agree across the two: the CSV's columns are the notetype's fields. It selects
the notetype too, whose id is pinned so that re-importing a rebuilt deck updates the
existing notes rather than adding a second copy. `DECK` names the deck to build into,
by default `Chinese Dictionary` or `English Dictionary`.

Chinese also reads, if set:

| variable | supplies |
|---|---|
| `MAKEMEAHANZI` | [skishore/makemeahanzi](https://github.com/skishore/makemeahanzi), stroke-order diagrams |
| `AUDIO_CMN` | [hugolpz/audio-cmn](https://github.com/hugolpz/audio-cmn), the recordings |
| `CEDICT` | CC-CEDICT, for the simplified forms kaikki no longer gives |
| `SWAC_INDEX` | what each recording says, so audio is matched by reading rather than spelling |

The first three default to a checkout of that name beside the script; `SWAC_INDEX` to
the `swac-index.csv` in this repo.

The package can then be imported into Anki.
Select `Import any learning progress` to start all cards suspended, and unsuspend them as you want to learn them.

## Create cards for individual words

```bash
python add_word.py "serendipity" "ephemeral" "ubiquitous" -o words.csv
```

## Card Format

Each English card contains:
- **Front**: Word
- **Back**: Definitions grouped by part of speech
- **Part of Speech**: noun, verb, adjective, etc.
- **IPA**: Pronunciation guide
- **Audio**: Pronunciation audio (when available)
- **Etymology**: Word origin and history
- **Forms**: Plural, past tense, etc.
- **Hyphenation**: Syllable breaks
- **Frequency**: Google Books Ngram ranking

Chinese cards carry **Simplified**, **Traditional**, **Pinyin**, **Stroke Order** and
**Glyph Origin** — the per-character 六書 analysis, since Wiktionary writes a word
etymology for only a twentieth of compounds.

## Requirements

- Python 3.6+

## License

- **Code**: MIT License
- **Generated deck content**:
  - Wiktionary data: Dual-licensed under CC BY-SA 4.0 and GFDL
  - Google Books Ngram frequency data: CC BY 3.0

---

*Programmed with [Claude Code](https://claude.ai/code)*