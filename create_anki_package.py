#!/usr/bin/env python3

import json
import sqlite3
import zipfile
import tempfile
import os
from pathlib import Path
import time
import re
import hashlib

# the notetype already in the collection; a fresh id would duplicate the deck on import
NOTE_TYPE_ID = 1751458562786
NOTE_TYPE_NAME = "Chinese Dictionary"

BASE91 = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
          "!#$%&()*+,-./:;<=>?@[]^_`{|}~")


def guid_for(*values):
    """Anki's base91 guid, keyed on the entry rather than the clock."""
    h = int.from_bytes(hashlib.sha256("__".join(values).encode("utf-8")).digest()[:8],
                       "big")
    out = []
    while h > 0:
        out.append(BASE91[h % len(BASE91)])
        h //= len(BASE91)
    return "".join(reversed(out))


MAKEMEAHANZI = Path(os.environ.get("MAKEMEAHANZI", "makemeahanzi")).expanduser()
AUDIO_CMN = Path(os.environ.get("AUDIO_CMN", "audio-cmn")).expanduser()

MEDIA_REF = re.compile(r'\[sound:([^]]+)\]|<img[^>]*src="([^"]+)"')


def find_media(db_path):
    """Every file the notes point at, located in the sources that produced them.

    A package with an empty media list still renders <img> and [sound:] tags, so the
    deck looks intact and every card is silently missing its diagram.
    """
    con = sqlite3.connect(db_path)
    want = set()
    for (flds,) in con.execute("select flds from notes"):
        for sound, img in MEDIA_REF.findall(flds):
            want.add(sound or img)
    con.close()

    svgs = {f"{chr(int(p.name.split('-')[0]))}.svg": p
            for p in (MAKEMEAHANZI / "svgs-still").glob("*-still.svg")}
    audio = {p.name: p for d in ("96k/hsk", "64k/syllabs")
             for p in (AUDIO_CMN / d).glob("*.mp3")}   # hugolpz/audio-cmn
    found = {n: (svgs.get(n) or audio.get(n)) for n in want}
    missing = sorted(n for n, p in found.items() if p is None)
    if missing:
        print(f"  {len(missing)} referenced files not found, e.g. {missing[:3]}")
    return {n: p for n, p in found.items() if p is not None}


def available_svgs():
    """The characters makemeahanzi actually draws.

    Half the CJK block has no diagram -- \u5e2f, \u5b9f, \u7d4c are Japanese shinjitai -- and emitting
    an <img> for them leaves the collection with thousands of missing-media warnings.
    """
    d = MAKEMEAHANZI / "svgs-still"
    if not d.is_dir():
        raise SystemExit(f"missing {d} -- set MAKEMEAHANZI")
    return {chr(int(p.name.split("-")[0])) for p in d.glob("*-still.svg")}


def available_svgs():
    """The characters makemeahanzi actually draws.

    Half the CJK block has no diagram -- \u5e2f, \u5b9f, \u7d4c are Japanese shinjitai -- and emitting
    an <img> for them leaves the collection with thousands of missing-media warnings.
    """
    d = MAKEMEAHANZI / "svgs-still"
    if not d.is_dir():
        raise SystemExit(f"missing {d} -- set MAKEMEAHANZI")
    return {chr(int(p.name.split("-")[0])) for p in d.glob("*-still.svg")}


def generate_stroke_order(word, have):
    if not word:
        return ""
    chars = [c for c in re.findall(r'[\u4e00-\u9fff]', word) if c in have]
    return ''.join(f'<img width="640" src="{c}.svg">' for c in chars)

def create_anki_package(csv_file, output_file="chinese.apkg", bundle_media=True):

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        db_path = temp_path / "collection.anki2"
        create_anki_database(db_path, csv_file)

        media = find_media(db_path) if bundle_media else {}
        manifest = {str(i): name for i, name in enumerate(sorted(media))}
        media_path = temp_path / "media"
        media_path.write_text(json.dumps(manifest, ensure_ascii=False))

        with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as apkg:
            apkg.write(db_path, "collection.anki2")
            apkg.write(media_path, "media")
            for i, name in manifest.items():
                apkg.write(media[name], i)
        print(f"  bundled {len(manifest)} media files")

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

    note_type_id = NOTE_TYPE_ID

    note_type = {
        str(note_type_id): {
            "id": note_type_id,
            "vers": [],
            "name": NOTE_TYPE_NAME,
            "tags": [],
            "did": 1,
            "usn": -1,
            "req": [[0, "any", [0]]],
            "type": 0,
            "flds": [
                {"name": "Simplified", "ord": 0, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Traditional", "ord": 1, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Pinyin", "ord": 2, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Definition", "ord": 3, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Part of Speech", "ord": 4, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "IPA", "ord": 5, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Audio", "ord": 6, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Etymology", "ord": 7, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Forms", "ord": 8, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Hyphenation", "ord": 9, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Tags", "ord": 10, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "Frequency", "ord": 11, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "StrokeOrder", "ord": 12, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False},
                {"name": "GlyphOrigin", "ord": 13, "sticky": False, "rtl": False, "font": "Arial", "size": 20, "media": [], "collapsed": False, "description": "", "plainText": False}
            ],
            "sortf": 11,
            "tmpls": [
                {
                    "name": "Card 1",
                    "ord": 0,
                    "qfmt": "<div class=\"hanzi\">{{Simplified}}</div>\n",
                    "afmt": "<div class=hanzi><a href=\"https://en.wiktionary.org/wiki/{{Traditional}}#Chinese\">{{Simplified}}</a></div>\n{{#Pinyin}}<div class=pinyin>{{Pinyin}}</div>{{/Pinyin}}\n{{#Definition}}<div class=english>{{Definition}}</div>{{/Definition}}\n{{#Part of Speech}}<div class=description>{{Part of Speech}}</div>{{/Part of Speech}}\n<hr>\n{{#GlyphOrigin}}<div class=etym><b class=en>Glyph origin</b>{{GlyphOrigin}}</div>{{/GlyphOrigin}}\n{{Audio}}\n{{#Etymology}}<div class=etym>{{Etymology}}</div>{{/Etymology}}\n{{#Forms}}<div class=more>{{Forms}}</div>{{/Forms}}\n<br>\n<div class=\"vertical-column\">{{StrokeOrder}}</div>\n",
                    "bqfmt": "{{Simplified}}",
                    "bafmt": "{{Definition}}",
                    "did": None,
                    "bfont": "",
                    "bsize": 0
                }
            ],
            "mod": int(time.time()),
            "css": ":root {\n  --link: #1666c0;\n}\n\n.nightMode, .night_mode {\n  --link: #6cf;\n}\n\n.card {\n    font-family: arial;\n    font-size: 10px;\n    text-align: center;\n}\n\n.hanzi {\n    font-family: SimSun;\n    font-size: 60px;\n}\n\n.pinyin {\n    font-family: Gentium Plus;\n    font-size: 22px;\n}\n\n.english {\n    font-family: Georgia;\n    font-size: 16px;\n}\n\n.sentence{\n    font-family: SimSun;\n    font-size: 24px;\n}\n\n.description{\n    font-family: Georgia;\n    font-size: 16px;\n    opacity: 0.65;\n}\n\n.horizontal-container {\n  display: flex;\n  gap: 2rem;\n  justify-content: center;\n}\n\n.vertical-column {\n  display: flex;\n  flex-direction: column;\n  gap: 1rem;\n  align-items: center;\n}\n\n.big-button {\n  font-size: 1.5em;\n  cursor: pointer;\n  min-width: 4em;\n  min-height: 3em;\n  touch-action: manipulation;\n  -webkit-user-select: none;\n  -webkit-touch-callout: none;\n  user-select: none;\n  margin: 0pt;\n}\n\na {\n  color: var(--link);\n  text-decoration: none;\n}\n\na:hover {\n  text-decoration: underline;\n}\n.homograph {\n    font-family: Georgia;\n    font-size: 14px;\n    opacity: 0.55;\n}\n\n.examples {\n    font-family: SimSun;\n    font-size: 20px;\n    text-align: left;\n    display: inline-block;\n}\n\n.examples li { margin: 6px 0; }\n\n.vertical-column img {\n  max-width: 100%;\n  height: auto;\n  margin: 2px;\n}\n\n\n\n.drawbox {\n  border: 1px solid currentColor;\n  border-radius: 4px;\n  opacity: 0.9;\n}\n\n.en {\n  font-family: Georgia;\n  opacity: 0.6;\n}\n\n.more {\n  font-size: 0.82em;\n  opacity: 0.7;\n  margin-top: 4px;\n}\n\n.pinyinSen {\n  font-family: Gentium Plus;\n  font-size: 0.8em;\n  opacity: 0.7;\n}\n\n.etym {\n  font-family: Georgia;\n  font-size: 13px;\n  text-align: left;\n  max-width: 34em;\n  margin: 10px auto 0;\n  opacity: 0.75;\n}\n\n.etymItem { margin: 4px 0; }\n\n.etymTrad {\n  font-family: SimSun;\n  font-size: 22px;\n  float: right;\n  margin-left: 8px;\n  opacity: 0.5;\n}\n\n.example {\n  font-family: Georgia;\n  font-size: 15px;\n  opacity: 0.7;\n  margin-top: 6px;\n}\n\n.exPinyin { font-family: Gentium Plus; }\n\n.etymology, .etym { font-family: Georgia; font-size: 13px; text-align: left;\n  max-width: 34em; margin: 10px auto 0; opacity: 0.75; }\n.centre { text-align: center; }\n"
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

        # Wiktionary lists a headword once per part of speech, so 中国 arrives twice.
        have = available_svgs()
        best = {}
        for row in reader:
            key = (row.get('Simplified', ''), row.get('Traditional', ''))
            if not key[0]:
                continue
            if len(row.get('Definition', '')) > len(best.get(key, {}).get('Definition', '')):
                best[key] = row

        for i, ((simplified, traditional), row) in enumerate(best.items()):

            # the Wiktionary headword
            guid = guid_for("chinese-dict", traditional)
            note_id = int(time.time() * 1000) + i
            card_id = note_id + 1000000

            front_word = simplified
            stroke_order = generate_stroke_order(front_word, have)
            fields = '\x1f'.join([
                front_word,
                traditional,
                row.get('Pinyin', ''),
                row.get('Definition', ''),
                row.get('Part of Speech', ''),
                row.get('IPA', ''),
                row.get('Audio', ''),
                row.get('Etymology', ''),
                row.get('Forms', ''),
                row.get('Hyphenation', ''),
                row.get('Tags', ''),
                row.get('Frequency', ''),
                stroke_order,
                row.get('GlyphOrigin', '')
            ])

            cursor.execute('''
                INSERT INTO notes (id, guid, mid, mod, usn, tags, flds, sfld, csum, flags, data)
                VALUES (?, ?, ?, ?, 0, '', ?, ?, 0, 0, '')
            ''', (
                note_id,
                guid,
                note_type_id,
                int(time.time()),
                fields,
                row.get('Simplified', '')[:64]
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
    parser.add_argument('--no-media', action='store_true',
                       help='Leave stroke diagrams and audio out of the package')

    args = parser.parse_args()

    create_anki_package(args.csv_file, args.output,
                        bundle_media=not args.no_media)