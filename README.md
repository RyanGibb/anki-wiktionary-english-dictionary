# Anki Wiktionary English Dictionary

Convert Wiktionary data to Anki flashcards for English vocabulary study. Generates 1.3M+ word entries.

**[Download from AnkiWeb](https://ankiweb.net/shared/info/)**

## Quick Start

1. Download English [dictionary data](https://kaikki.org/dictionary/English/) from [kaikki.org](https://kaikki.org)
2. Download frequency data: `curl -o wikipedia-frequency-2023.txt https://raw.githubusercontent.com/IlyaSemenov/wikipedia-word-frequency/refs/heads/master/results/enwiki-2023-04-13.txt`
3. Convert to CSV: `python wiktionary_to_anki.py kaikki.org-dictionary-English.jsonl`
4. Create Anki package: `python create_anki_package.py english.csv`
5. Import `english.apkg` into Anki

## Features

**Rich Content**: Definitions, pronunciation (IPA), etymology, word forms
**Audio Support**: Pronunciation audio when available
**Word Frequency Rankings**: from Wikipedia 2023 data

## Usage

### Convert JSONL to CSV
```bash
python wiktionary_to_anki.py input.jsonl -o output.csv
```

Options:
- `-l, --limit N` - Process only N entries (for testing)
- `--min-def-length N` - Minimum definition length (default: 10)

### Create Anki Package
```bash
python create_anki_package.py input.csv -o output.apkg
```

The package includes the custom note type and can be directly imported into Anki.

## Card Format

Each card contains:
- **Front**: Word
- **Back**: Definitions grouped by part of speech
- **Part of Speech**: noun, verb, adjective, etc.
- **IPA**: Pronunciation guide
- **Audio**: Pronunciation audio (when available)
- **Etymology**: Word origin and history
- **Forms**: Plural, past tense, etc.
- **Hyphenation**: Syllable breaks
- **Frequency**: Wikipedia ranking

## Requirements

- Python 3.6+
- Standard library only

## License

- **Code**: MIT License
- **Generated deck content**:
  - Wiktionary data: Dual-licensed under CC BY-SA 4.0 and GFDL
  - Wikipedia frequency data: MIT License

---

*Programmed with [Claude Code](https://claude.ai/code)*