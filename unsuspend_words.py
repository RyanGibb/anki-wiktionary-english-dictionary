#!/usr/bin/env python3

import sqlite3
import sys
import re
import time
from pathlib import Path


def get_english_deck_id(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM decks WHERE name LIKE '%English%'")
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        print("English deck not found!")
        return None

def find_and_update_cards(conn, word_to_source, english_deck_id):
    cursor = conn.cursor()

    cursor.execute("""
        SELECT c.id, c.nid, c.queue, n.flds
        FROM cards c
        JOIN notes n ON c.nid = n.id
        WHERE c.did = ?
    """, (english_deck_id,))

    cards = cursor.fetchall()
    print(f"Found {len(cards)} cards in English deck")

    updated_count = 0
    found_words = set()

    for card_id, note_id, queue, fields in cards:
        field_list = fields.split('\x1f')

        if len(field_list) == 0:
            continue

        word = field_list[0].strip()
        word_clean = re.sub(r'<[^>]+>', '', word).strip()

        if word_clean in word_to_source:
            found_words.add(word_clean)
            source = word_to_source[word_clean]

            if queue == -1:
                cursor.execute("UPDATE cards SET queue = 0 WHERE id = ?", (card_id,))
                print(f"Unsuspended card for word: {word_clean}")

            if source and len(field_list) > 1:
                field_list[-1] = source
                updated_fields = '\x1f'.join(field_list)
                cursor.execute("UPDATE notes SET flds = ?, mod = ? WHERE id = ?",
                             (updated_fields, int(time.time()), note_id))
                print(f"Updated source for word: {word_clean} -> {source}")
                updated_count += 1

    not_found = set(word_to_source.keys()) - found_words
    if not_found:
        print(f"\nWords not found in deck ({len(not_found)}):")
        for word in sorted(not_found):
            print(f"  - {word}")

    conn.commit()
    return updated_count

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 unsuspend_words.py <word1> [word2] [word3] ...")
        print("   or: python3 unsuspend_words.py --source 'source_name' <word1> [word2] ...")
        sys.exit(1)

    anki_db_path = Path.home() / ".local/share/Anki2/User 1/collection.anki2"

    if not anki_db_path.exists():
        print(f"Anki database not found: {anki_db_path}")
        sys.exit(1)

    word_to_source = {}
    args = sys.argv[1:]

    if args[0] == '--source':
        if len(args) < 3:
            print("Error: --source requires a source name and at least one word")
            sys.exit(1)
        source = args[1]
        words = args[2:]
        for word in words:
            word_to_source[word.strip()] = source
    else:
        for word in args:
            word_to_source[word.strip()] = None

    print(f"Processing {len(word_to_source)} words")

    print("Connecting to Anki database...")
    conn = sqlite3.connect(str(anki_db_path))

    try:
        english_deck_id = get_english_deck_id(conn)
        if not english_deck_id:
            sys.exit(1)

        print(f"English deck ID: {english_deck_id}")

        updated_count = find_and_update_cards(conn, word_to_source, english_deck_id)
        print(f"Updated {updated_count} cards")

    finally:
        conn.close()

if __name__ == "__main__":
    main()