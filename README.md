# Anki Wiktionary English Dictionary

Comprehensive English vocabulary flashcards containing definitions, pronunciation (IPA), etymology, word forms, and pronunciation audio from Wiktionary.
Google Books Ngram frequency data is used to rank words and select the top `n`.

**[Download from AnkiWeb](https://ankiweb.net/shared/info/1140417632)**

## Quick Start

1. Download English [dictionary data](https://kaikki.org/dictionary/English/) from [kaikki.org](https://kaikki.org)
2. Download frequency data from [hackerb9/gwordlist](https://github.com/hackerb9/gwordlist):
   `curl -o frequency-all.txt.gz https://raw.githubusercontent.com/hackerb9/gwordlist/master/frequency-all.txt.gz && gunzip frequency-all.txt.gz`
3. Convert to CSV: `python wiktionary_to_anki.py kaikki.org-dictionary-Chinese.jsonl`
4. Create Anki package: `python create_anki_package.py english.csv`
5. Import `english.apkg` into Anki

## Usage

```bash
python wiktionary_to_anki.py input.jsonl
python create_anki_package.py input.csv
```

The package `english.apkg` can then be imported into Anki.
Select `Import any learning progress` to start all cards suspended, and unsuspend them as you want to learn them.

## Create cards for individual words

```bash
python add_word.py "serendipity" "ephemeral" "ubiquitous" -o words.csv
```

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
- **Frequency**: Google Books Ngram ranking

## Requirements

- Python 3.6+

## License

- **Code**: MIT License
- **Generated deck content**:
  - Wiktionary data: Dual-licensed under CC BY-SA 4.0 and GFDL
  - Google Books Ngram frequency data: CC BY 3.0

---

*Programmed with [Claude Code](https://claude.ai/code)*