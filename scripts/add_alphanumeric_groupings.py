#!/usr/bin/env python3
"""
Add alphanumeric groupings to JSON trees.
Groups haplogroups by name length (2, 3, 4, 5, 6+ characters).

Example: For E1b1b1a1c1 (E-M44):
  - 2-char: E, E1
  - 3-char: E1b
  - 4-char: E1b1
  - 5-char: E1b1b
  - 6-char: E1b1b1
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def extract_alphanumeric_name(haplo_name):
    """Extract alphanumeric part, removing tildes and parenthetical notes."""
    # Remove ~ and anything in parentheses
    clean = re.sub(r'[~]', '', haplo_name)
    clean = re.sub(r'\([^)]+\)', '', clean).strip()
    return clean


def group_by_length(haplogroups):
    """Group haplogroups by alphanumeric name length."""
    
    groups = {
        '1-char': defaultdict(list),
        '2-char': defaultdict(list),
        '3-char': defaultdict(list),
        '4-char': defaultdict(list),
        '5-char': defaultdict(list),
        '6-char': defaultdict(list),
        '7plus-char': defaultdict(list)
    }
    
    for haplo_name, haplo_data in haplogroups.items():
        clean_name = extract_alphanumeric_name(haplo_name)
        
        # Determine length category
        length = len(clean_name)
        
        if length == 1:
            prefix = clean_name[0]
            groups['1-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        elif length == 2:
            prefix = clean_name[:2]
            groups['2-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        elif length == 3:
            prefix = clean_name[:3]
            groups['3-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        elif length == 4:
            prefix = clean_name[:4]
            groups['4-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        elif length == 5:
            prefix = clean_name[:5]
            groups['5-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        elif length == 6:
            prefix = clean_name[:6]
            groups['6-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
        else:  # 7+
            prefix = clean_name[:7]
            groups['7plus-char'][prefix].append({
                'name': haplo_name,
                'clean_name': clean_name,
                'data': haplo_data
            })
    
    # Convert defaultdicts to regular dicts and sort
    result = {}
    for key, group in groups.items():
        result[key] = {k: sorted(v, key=lambda x: x['clean_name']) 
                      for k, v in sorted(group.items())}
    
    return result


def process_year_tree(tree_file):
    """Process a year's tree and add groupings."""
    
    with open(tree_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract nodes
    nodes = data.get('nodes', {})
    if not nodes:
        return None
    
    # Group by length
    groups = group_by_length(nodes)
    
    # Add groupings to data
    data['alphanumeric_groups'] = groups
    
    # Calculate stats
    stats = {key: len(group) for key, group in groups.items()}
    data['grouping_stats'] = stats
    
    return data


def main():
    """Add alphanumeric groupings to all tree files."""
    
    output_dir = Path('output_master')
    processed = []
    
    print("="*60)
    print("Adding Alphanumeric Groupings to Trees")
    print("="*60 + "\n")
    
    # Process each year's tree.json
    for year_dir in sorted(output_dir.glob('20*')):
        if not year_dir.is_dir():
            continue
        
        tree_file = year_dir / 'tree.json'
        if not tree_file.exists():
            continue
        
        print(f"Processing {year_dir.name}...")
        
        try:
            updated_data = process_year_tree(tree_file)
            
            if updated_data:
                # Save updated file
                grouped_file = year_dir / 'tree_grouped.json'
                with open(grouped_file, 'w', encoding='utf-8') as f:
                    json.dump(updated_data, f, indent=2, ensure_ascii=False)
                
                stats = updated_data['grouping_stats']
                print(f"  Groups: 1-char={stats['1-char']}, 2-char={stats['2-char']}, "
                      f"3-char={stats['3-char']}, 4-char={stats['4-char']}")
                processed.append(year_dir.name)
        
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\n{'='*60}")
    print(f"Processed {len(processed)} years")
    print(f"{'='*60}")
    
    # Show example
    if processed:
        example_year = processed[-1]
        example_file = output_dir / example_year / 'tree_grouped.json'
        with open(example_file, 'r') as f:
            example = json.load(f)
        
        print(f"\nExample from {example_year}:")
        groups = example['alphanumeric_groups']
        
        # Show some 3-char groups
        if '3-char' in groups:
            print("\nSample 3-character groups:")
            for prefix in list(groups['3-char'].keys())[:5]:
                items = groups['3-char'][prefix]
                print(f"  {prefix}: {len(items)} haplogroups")
                for item in items[:3]:
                    snps = item['data'].get('snps', [])
                    snp_str = snps[0] if snps else 'no SNPs'
                    print(f"    - {item['name']} ({snp_str})")


if __name__ == '__main__':
    main()
