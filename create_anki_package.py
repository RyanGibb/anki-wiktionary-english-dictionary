#!/usr/bin/env python3

import json
import sqlite3
import zipfile
import tempfile
import os
from pathlib import Path
import time
import re

def generate_stroke_order(word):
    """Generate stroke order HTML with SVG images for each Chinese character"""
    if not word:
        return ""

    # Filter to only Chinese characters (CJK unified ideographs)
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', word)

    if not chinese_chars:
        return ""

    img_tags = []
    for char in chinese_chars:
        img_tags.append(f'<img width="640" src="{char}.svg">')

    return ''.join(img_tags)

def create_anki_package(csv_file, output_file="chinese.apkg"):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        db_path = temp_path / "collection.anki2"
        create_anki_database(db_path, csv_file)

        media_path = temp_path / "media"
        media_path.write_text("{}")

        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as apkg:
            apkg.write(db_path, "collection.anki2")
            apkg.write(media_path, "media")

    print(f"Created Anki package: {output_file}")

def create_anki_database(db_path, csv_file):

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    create_anki_schema(cursor)

    note_type_id = insert_note_type(cursor)

    deck_id = insert_deck(cursor)

    insert_cards_from_csv(cursor, csv_file, note_type_id, deck_id)

    conn.commit()
    conn.close()

def create_anki_schema(cursor):

    cursor.execute('''
        CREATE TABLE col (
            id INTEGER PRIMARY KEY,
            crt INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            scm INTEGER NOT NULL,
            ver INTEGER NOT NULL,
            dty INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            ls INTEGER NOT NULL,
            conf TEXT NOT NULL,
            models TEXT NOT NULL,
            decks TEXT NOT NULL,
            dconf TEXT NOT NULL,
            tags TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            guid TEXT NOT NULL,
            mid INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            tags TEXT NOT NULL,
            flds TEXT NOT NULL,
            sfld TEXT NOT NULL,
            csum INTEGER NOT NULL,
            flags INTEGER NOT NULL,
            data TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE cards (
            id INTEGER PRIMARY KEY,
            nid INTEGER NOT NULL,
            did INTEGER NOT NULL,
            ord INTEGER NOT NULL,
            mod INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            type INTEGER NOT NULL,
            queue INTEGER NOT NULL,
            due INTEGER NOT NULL,
            ivl INTEGER NOT NULL,
            factor INTEGER NOT NULL,
            reps INTEGER NOT NULL,
            lapses INTEGER NOT NULL,
            left INTEGER NOT NULL,
            odue INTEGER NOT NULL,
            odid INTEGER NOT NULL,
            flags INTEGER NOT NULL,
            data TEXT NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE graves (
            usn INTEGER NOT NULL,
            oid INTEGER NOT NULL,
            type INTEGER NOT NULL
        )
    ''')

    cursor.execute('''
        CREATE TABLE revlog (
            id INTEGER PRIMARY KEY,
            cid INTEGER NOT NULL,
            usn INTEGER NOT NULL,
            ease INTEGER NOT NULL,
            ivl INTEGER NOT NULL,
            lastIvl INTEGER NOT NULL,
            factor INTEGER NOT NULL,
            time INTEGER NOT NULL,
            type INTEGER NOT NULL
        )
    ''')

    cursor.execute('CREATE INDEX ix_notes_usn ON notes (usn)')
    cursor.execute('CREATE INDEX ix_cards_usn ON cards (usn)')
    cursor.execute('CREATE INDEX ix_notes_csum ON notes (csum)')
    cursor.execute('CREATE UNIQUE INDEX ix_notes_guid ON notes (guid)')
    cursor.execute('CREATE INDEX ix_cards_nid ON cards (nid)')
    cursor.execute('CREATE INDEX ix_cards_sched ON cards (did, queue, due)')
    cursor.execute('CREATE INDEX ix_revlog_usn ON revlog (usn)')
    cursor.execute('CREATE INDEX ix_revlog_cid ON revlog (cid)')

def insert_note_type(cursor):

    note_type_id = int(time.time() * 1000)

    note_type = {
        str(note_type_id): {
            "id": note_type_id,
            "vers": [],
            "name": "Chinese",
            "tags": [],
            "did": 1,
            "usn": -1,
            "req": [[0, "any", [0]]],
            "type": 0,
            "flds": [
                {"name": "Front", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Back", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Part of Speech", "ord": 2, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "IPA", "ord": 3, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Audio", "ord": 4, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Etymology", "ord": 5, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Forms", "ord": 6, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Hyphenation", "ord": 7, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Stroke Order", "ord": 8, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Tags", "ord": 9, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Frequency", "ord": 10, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False}
            ],
            "sortf": 10,
            "tmpls": [
                {
                    "name": "Card 1",
                    "ord": 0,
                    "qfmt": '''<div class="word-front">
  <a class="word" href="https://en.wiktionary.org/wiki/{{Front}}#Chinese">{{Front}}</a>
  {{#IPA}}<div class="ipa">{{IPA}}</div>{{/IPA}}
  {{#Audio}}<div class="audio">{{Audio}}</div>{{/Audio}}
  {{#Hyphenation}}<div class="hyphenation">{{Hyphenation}}</div>{{/Hyphenation}}
  {{#Stroke Order}}<div class="stroke-order">{{Stroke Order}}</div>{{/Stroke Order}}
</div>''',
                    "afmt": '''{{FrontSide}}

<hr id="answer">

<div class="word-back">
  <div class="definitions">{{Back}}</div>
  {{#Part of Speech}}<div class="pos"><strong>Part of Speech:</strong> {{Part of Speech}}</div>{{/Part of Speech}}
  {{#Etymology}}<div class="etymology"><strong>Etymology:</strong> {{Etymology}}</div>{{/Etymology}}
  {{#Forms}}<div class="forms"><strong>Forms:</strong> {{Forms}}</div>{{/Forms}}
  {{#Frequency}}<div class="frequency"><strong>Frequency:</strong> {{Frequency}}</div>{{/Frequency}}
</div>''',
                    "bqfmt": "{{Front}}",
                    "bafmt": "{{Back}}",
                    "did": None,
                    "bfont": "",
                    "bsize": 0
                }
            ],
            "mod": int(time.time()),
            "css": '''.card {
  text-align: left;
}

.word-front {
  text-align: center;
}

.word {
  font-size: 2em;
  font-weight: bold;
}

.ipa {
  opacity: 0.8;
}

.hyphenation {
  font-size: 1em;
  font-style: italic;
  opacity: 0.7;
}

.pos, .etymology, .forms, .frequency {
  margin: 8px 0;
  font-size: 0.9em;
  opacity: 0.85;
}

hr {
  border: none;
  border-top: 1px solid;
  margin: 15px 0;
  opacity: 0.3;
}'''
        }
    }

    conf = {
        "nextPos": 1,
        "estTimes": True,
        "activeDecks": [1],
        "sortType": "noteFld",
        "timeLim": 0,
        "sortBackwards": False,
        "addToCur": True,
        "curDeck": 1,
        "newBury": True,
        "newSpread": 0,
        "dueCounts": True,
        "curModel": str(note_type_id),
        "collapseTime": 1200,
        "newDeck": 1
    }

    decks = {
        "1": {
            "desc": "Chinese dictionary from Wiktionary",
            "name": "Chinese",
            "extendRev": 50,
            "usn": 0,
            "collapsed": False,
            "newToday": [0, 0],
            "timeToday": [0, 0],
            "dyn": 0,
            "extendNew": 10,
            "conf": 1,
            "revToday": [0, 0],
            "lrnToday": [0, 0],
            "id": 1,
            "mod": int(time.time())
        }
    }

    dconf = {
        "1": {
            "name": "Chinese",
            "replayq": True,
            "lapse": {
                "leechFails": 8,
                "delays": [10],
                "minInt": 1,
                "leechAction": 0,
                "mult": 0
            },
            "rev": {
                "perDay": 200,
                "ivlFct": 1,
                "maxIvl": 36500,
                "ease4": 1.3,
                "bury": True,
                "minSpace": 1,
                "fuzz": 0.05
            },
            "timer": 0,
            "maxTaken": 60,
            "usn": 0,
            "new": {
                "delays": [1, 10],
                "ints": [1, 4, 7],
                "initialFactor": 2500,
                "separate": True,
                "perDay": 20,
                "bury": True,
                "order": 1
            },
            "mod": 0,
            "id": 1,
            "autoplay": True
        }
    }

    cursor.execute('''
        INSERT INTO col (id, crt, mod, scm, ver, dty, usn, ls, conf, models, decks, dconf, tags)
        VALUES (1, ?, ?, ?, 11, 0, 0, 0, ?, ?, ?, ?, '{}')
    ''', (
        int(time.time()),
        int(time.time() * 1000),
        int(time.time() * 1000),
        json.dumps(conf),
        json.dumps(note_type),
        json.dumps(decks),
        json.dumps(dconf)
    ))

    return note_type_id

def insert_deck(cursor):
    return 1

def insert_cards_from_csv(cursor, csv_file, note_type_id, deck_id):
    import csv

    if not os.path.exists(csv_file):
        print(f"Warning: CSV file {csv_file} not found. Creating empty package.")
        return

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for i, row in enumerate(reader):

            note_id = int(time.time() * 1000) + i
            card_id = note_id + 1000000

            front_word = row.get('Front', '')
            stroke_order = generate_stroke_order(front_word)
            fields = '\x1f'.join([
                front_word,
                row.get('Back', ''),
                row.get('Part of Speech', ''),
                row.get('IPA', ''),
                row.get('Audio', ''),
                row.get('Etymology', ''),
                row.get('Forms', ''),
                row.get('Hyphenation', ''),
                stroke_order,
                row.get('Tags', ''),
                row.get('Frequency', '')
            ])

            cursor.execute('''
                INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
                VALUES (?, ?, ?, ?, 0, '', ?, ?, 0, 0, '')
            ''', (
                note_id,
                f"note_{note_id}",
                note_type_id,
                int(time.time()),
                fields,
                row.get('Front', '')[:64]
            ))

            cursor.execute('''
                INSERT INTO cards (id, nid, did, ord, mod, usn, type, queue, due, ivl, factor, reps, lapses, left, odue, odid, flags, data)
                VALUES (?, ?, ?, 0, ?, -1, 0, -1, ?, 0, 0, 0, 0, 0, 0, 0, 0, '')
            ''', (
                card_id,
                note_id,
                deck_id,
                int(time.time()),
                i + 1
            ))

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create Anki package with Wiktionary note type')
    parser.add_argument('csv_file', help='CSV file with card data')
    parser.add_argument('-o', '--output', default='chinese.apkg',
                       help='Output .apkg file')

    args = parser.parse_args()

    create_anki_package(args.csv_file, args.output)