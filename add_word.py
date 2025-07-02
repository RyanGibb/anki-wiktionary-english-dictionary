#!/usr/bin/env python3

import json
import csv
import argparse
from pathlib import Path
import sys
import re

from wiktionary_to_anki import process_entry, combine_entries, load_frequency_data_for_words, get_frequency_rank

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

def find_words_in_wiktionary(words, wiktionary_file):
    target_words = {word.lower(): word for word in words}
    found_entries = {word: [] for word in words}
    
    print(f"Searching for {len(words)} words in {wiktionary_file}...")
    
    with open(wiktionary_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            if line_num % 100000 == 0:
                print(f"  Searched {line_num:,} entries...")
                found_count = sum(len(entries) for entries in found_entries.values())
                print(f"  Found {found_count} entries so far...")
            
            try:
                entry = json.loads(line.strip())
                word_lower = entry.get('word', '').lower()
                if word_lower in target_words:
                    original_word = target_words[word_lower]
                    found_entries[original_word].append(entry)
            except json.JSONDecodeError:
                continue
    
    for word in words:
        print(f"Found {len(found_entries[word])} entries for '{word}'")
    
    return found_entries

def process_words_to_cards(words, wiktionary_file="kaikki.org-dictionary-Chinese.jsonl"):
    all_entries = find_words_in_wiktionary(words, wiktionary_file)
    frequency_dict = load_frequency_data_for_words(set(words))
    cards = []
    
    for word in words:
        entries = all_entries[word]
        
        if not entries:
            print(f"Word '{word}' not found in Wiktionary data")
            continue
        
        processed_entries = []
        for entry in entries:
            card_data = process_entry(entry)
            if card_data:
                processed_entries.append(card_data)
        
        if not processed_entries:
            print(f"No valid card data could be created for '{word}'")
            continue
        
        entries_by_word = {word: processed_entries}
        combined_cards = combine_entries(entries_by_word)
        
        if word not in combined_cards:
            print(f"Failed to combine entries for '{word}'")
            continue
        
        card_data = combined_cards[word]
        card_data['Frequency'] = get_frequency_rank(word, frequency_dict)
        card_data['Stroke Order'] = generate_stroke_order(card_data.get('Front', word))
        cards.append(card_data)
    
    return cards

def create_card_for_word(word, wiktionary_file="kaikki.org-dictionary-Chinese.jsonl", output_file=None):
    cards = process_words_to_cards([word], wiktionary_file)
    
    if not cards:
        return None
    
    card_data = cards[0]
    
    if output_file:
        fieldnames = [
            'Front', 'Back', 'Part of Speech', 'IPA', 'Audio', 
            'Etymology', 'Forms', 'Hyphenation', 'Stroke Order', 'Tags', 'Frequency'
        ]
        
        with open(output_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(card_data)
        
        print(f"Card saved to {output_file}")
    else:
        print(f"\nCard for '{card_data['Front']}':")
        print(f"Front: {card_data['Front']}")
        print(f"Back: {card_data['Back'][:200]}...")
        print(f"Part of Speech: {card_data['Part of Speech']}")
        print(f"IPA: {card_data['IPA']}")
        print(f"Frequency: {card_data['Frequency']}")
        print(f"Etymology: {card_data['Etymology'][:100]}...")
    
    return card_data

def main():
    parser = argparse.ArgumentParser(description='Extract words from Wiktionary as Anki cards')
    parser.add_argument('words', nargs='+', help='Word(s) to extract')
    parser.add_argument('-i', '--input', default='kaikki.org-dictionary-Chinese.jsonl',
                       help='Wiktionary JSONL file')
    parser.add_argument('-o', '--output', 
                       help='Output CSV file (if not specified, prints to stdout)')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"Error: Input file {args.input} not found")
        return 1
    
    if args.output and len(args.words) > 1:
        all_cards = process_words_to_cards(args.words, args.input)
        
        if all_cards:
            fieldnames = [
                'Front', 'Back', 'Part of Speech', 'IPA', 'Audio', 
                'Etymology', 'Forms', 'Hyphenation', 'Stroke Order', 'Tags', 'Frequency'
            ]
            
            with open(args.output, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writerows(all_cards)
            
            print(f"Saved {len(all_cards)} cards to {args.output}")
        else:
            print("No valid cards found")
    else:
        for word in args.words:
            create_card_for_word(word, args.input, args.output if len(args.words) == 1 else None)

if __name__ == '__main__':
    main()