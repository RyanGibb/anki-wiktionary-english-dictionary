# Anki Wiktionary English Dictionary

Comprehensive English vocabulary flashcards generated from Wiktionary data, taking the top 100k words according to Wikipedia frequency data.

**[Download from AnkiWeb](https://ankiweb.net/shared/info/1033970499)**

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

### Add Individual Words
```bash
# View word info
python add_word.py "serendipity"

# Save single word as CSV for Anki import
python add_word.py "serendipity" -o serendipity.csv

# Add multiple words to one CSV file
python add_word.py "serendipity" "ephemeral" "ubiquitous" -o new-words.csv
```

Extract any words from Wiktionary data as Anki cards.

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

## Limitations

The Wikipedia frequency list is case-insensitive, so "IN" (Indiana) ranks the same as "in".
The [Google Books Ngram Viewer Exports](https://storage.googleapis.com/books/ngrams/books/datasetsv3.html) would provide a better case-sensitive ranking, but hyphens are treated as non-word characters so to support words like self-control we'd need to download the whole dataset, which I don't have the bandwidth for at the moment.

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