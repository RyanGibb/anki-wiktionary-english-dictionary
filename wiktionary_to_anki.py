#!/usr/bin/env python3

import json
import csv
import re
from pathlib import Path
from urllib.parse import urlparse
import argparse

def load_frequency_data(frequency_file="wikipedia-frequency-2023.txt"):
    frequency_dict = {}
    try:
        with open(frequency_file, 'r', encoding='utf-8') as f:
            for rank, line in enumerate(f, 1):
                parts = line.strip().split(' ', 1)
                if len(parts) == 2:
                    word = parts[0].lower()
                    frequency_dict[word] = rank
    except FileNotFoundError:
        print(f"Warning: Frequency file {frequency_file} not found. Frequency data will be empty.")
    return frequency_dict

def get_frequency_rank(word, frequency_dict):
    if not frequency_dict:
        return ""
    rank = frequency_dict.get(word.lower())
    if rank and rank <= 100000:
        return str(rank)
    return ""

def clean_html(text):
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def format_etymology(etymology_text):
    if not etymology_text:
        return ""
    etymology = clean_html(etymology_text)
    etymology = etymology.replace("Etymology tree", "")
    etymology = re.sub(r'\n+', '<br>', etymology)
    return etymology.strip()

def format_pronunciation(sounds):
    if not sounds:
        return "", ""
    
    ipa_list = []
    audio_elements = []
    
    for sound in sounds:
        if 'ipa' in sound:
            tags = sound.get('tags', [])
            tag_str = f" ({', '.join(tags)})" if tags else ""
            ipa_list.append(f"{sound['ipa']}{tag_str}")
        
        if 'mp3_url' in sound:
            label = "Audio"
            if 'audio' in sound:
                label = sound['audio'].replace('.ogg', '')
            
            audio_elements.append(f'<div><strong>{label}:</strong> <audio controls><source src="{sound["mp3_url"]}" type="audio/mpeg">🔊 <a href="{sound["mp3_url"]}" target="_blank">Audio</a></audio></div>')
    
    ipa_text = '<br>'.join(ipa_list)
    audio_text = ''.join(audio_elements)
    
    return ipa_text, audio_text

def format_definitions(senses):
    if not senses:
        return ""
    
    definitions = []
    for i, sense in enumerate(senses, 1):
        definition_text = ""
        tags_text = ""
        
        if 'raw_glosses' in sense:
            definition_text = '; '.join(sense['raw_glosses'])
        elif 'glosses' in sense:
            definition_text = '; '.join(sense['glosses'])
        
        if 'qualifier' in sense and sense['qualifier']:
            tags_text = f"({sense['qualifier']}) "
        elif 'topics' in sense and sense['topics']:
            tags_text = f"({', '.join(sense['topics'])}) "
        elif 'categories' in sense and sense['categories']:
            relevant_cats = []
            for cat in sense['categories']:
                if isinstance(cat, str) and not cat.startswith('English ') and len(cat) < 20:
                    relevant_cats.append(cat)
            if relevant_cats:
                tags_text = f"({', '.join(relevant_cats[:3])}) "
        
        if definition_text:
            clean_def = clean_html(definition_text)
            if clean_def.startswith('('):
                formatted_def = f"{i}. {clean_def}"
            else:
                formatted_def = f"{i}. {tags_text}{clean_def}"
            definitions.append(formatted_def)
    
    return '<br>'.join(definitions)

def format_forms(forms):
    if not forms:
        return ""
    
    form_list = []
    for form in forms:
        form_text = form.get('form', '')
        tags = form.get('tags', [])
        if form_text and tags:
            form_list.append(f"{form_text} ({', '.join(tags)})")
    
    return '; '.join(form_list)

def extract_translations(translations, max_translations=10):
    if not translations:
        return ""
    
    trans_list = []
    for trans in translations[:max_translations]:
        lang = trans.get('lang', '')
        word = trans.get('word', '')
        if lang and word:
            trans_list.append(f"{lang}: {word}")
    
    result = '; '.join(trans_list)
    if len(translations) > max_translations:
        result += f" ... (+{len(translations) - max_translations} more)"
    
    return result

def process_entry(entry):
    word = entry.get('word', '')
    if not word:
        return None
    
    lang = entry.get('lang', '')
    if lang != 'English':
        return None
    
    pos = entry.get('pos', '')
    senses = entry.get('senses', [])
    definitions = format_definitions(senses)
    if not definitions:
        return None
    sounds = entry.get('sounds', [])
    ipa, audio = format_pronunciation(sounds)
    
    etymology = format_etymology(entry.get('etymology_text', ''))
    
    forms = format_forms(entry.get('forms', []))
    
    translations = ""
    
    hyphenation = entry.get('hyphenation', [])
    hyphen_text = '-'.join(hyphenation) if hyphenation else ""
    
    return {
        'Front': word,
        'Back': definitions,
        'Part of Speech': pos,
        'IPA': ipa,
        'Audio': audio,
        'Etymology': etymology,
        'Forms': forms,
        'Translations': translations,
        'Hyphenation': hyphen_text,
        'Tags': f"wiktionary {pos}" if pos else "wiktionary",
        'Frequency': ''
    }

def combine_entries(entries_dict):
    combined_cards = {}
    
    for word, entries in entries_dict.items():
        if not entries:
            continue
            
        first_entry = entries[0]
        combined = {
            'Front': word,
            'Back': '',
            'Part of Speech': '',
            'IPA': first_entry.get('IPA', ''),
            'Audio': first_entry.get('Audio', ''),
            'Etymology': first_entry.get('Etymology', ''),
            'Forms': '',
            'Translations': '',
            'Hyphenation': first_entry.get('Hyphenation', ''),
            'Tags': 'wiktionary',
            'Frequency': ''
        }
        
        pos_definitions = {}
        all_pos = []
        all_forms = []
        
        for entry in entries:
            pos = entry.get('Part of Speech', 'Unknown')
            back = entry.get('Back', '')
            forms = entry.get('Forms', '')
            
            if pos and pos not in all_pos:
                all_pos.append(pos)
            
            if pos and back:
                if pos in pos_definitions:
                    pos_definitions[pos] += f"<br>{back}"
                else:
                    pos_definitions[pos] = back
            
            if forms and forms not in all_forms:
                all_forms.append(forms)
        
        combined_back = []
        for pos in all_pos:
            if pos in pos_definitions:
                combined_back.append(f"<strong>{pos}:</strong><br>{pos_definitions[pos]}")
        
        combined['Back'] = '<br><br>'.join(combined_back)
        combined['Part of Speech'] = ', '.join(all_pos)
        combined['Forms'] = '; '.join(all_forms)
        combined['Tags'] = f"wiktionary {' '.join(all_pos)}"
        
        combined_cards[word] = combined
    
    return combined_cards

def main():
    parser = argparse.ArgumentParser(description='Convert Wiktionary JSONL to Anki CSV')
    parser.add_argument('input_file', help='Input JSONL file from kaikki.org')
    parser.add_argument('-o', '--output', default='english.csv', 
                       help='Output CSV file for Anki import')
    parser.add_argument('-l', '--limit', type=int, 
                       help='Limit number of entries to process (for testing)')
    parser.add_argument('--min-def-length', type=int, default=10,
                       help='Minimum definition length to include')
    
    args = parser.parse_args()
    
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: Input file {args.input_file} not found")
        return 1
    
    output_path = Path(args.output)
    
    fieldnames = [
        'Front', 'Back', 'Part of Speech', 'IPA', 'Audio', 
        'Etymology', 'Forms', 'Translations', 'Hyphenation', 'Tags', 'Frequency'
    ]
    processed_count = 0
    entries_by_word = {}
    frequency_dict = load_frequency_data()
    
    print(f"Processing {args.input_file}...")
    print(f"Output will be written to {args.output}")
    
    with open(input_path, 'r', encoding='utf-8') as infile:
        for line_num, line in enumerate(infile, 1):
            if args.limit and processed_count >= args.limit:
                break
                
            try:
                entry = json.loads(line.strip())
                processed_count += 1
                
                if processed_count % 10000 == 0:
                    print(f"Processed {processed_count} entries...")
                
                card_data = process_entry(entry)
                if card_data:
                    word = card_data['Front']
                    if word not in entries_by_word:
                        entries_by_word[word] = []
                    entries_by_word[word].append(card_data)
                
            except json.JSONDecodeError as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
            except Exception as e:
                print(f"Error processing entry on line {line_num}: {e}")
                continue
    
    print("Combining entries by word...")
    combined_cards = combine_entries(entries_by_word)
    
    print("Adding frequency data...")
    for word, card_data in combined_cards.items():
        card_data['Frequency'] = get_frequency_rank(word, frequency_dict)

    written_count = 0
    with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for word, card_data in combined_cards.items():
            if len(card_data['Back']) >= args.min_def_length:
                writer.writerow(card_data)
                written_count += 1
    
    print(f"\nCompleted!")
    print(f"Processed: {processed_count} entries")
    print(f"Combined into: {len(combined_cards)} unique words")
    print(f"Created: {written_count} Anki cards")
    print(f"Output: {args.output}")

if __name__ == '__main__':
    main()