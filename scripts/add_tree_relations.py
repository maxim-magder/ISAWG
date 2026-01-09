#!/usr/bin/env python3
"""
Add parent_name, child_haplogroups, and normative haplogroup names to enhanced_snp_table.jsonl.

Adds:
- parent_name: The parent haplogroup (e.g., E1a for E1a1)
- child_haplogroups: Array of child haplogroups
- normative_names: Array of nomenclature variations like E-M44, E1-M44, E1a-M44, E1a1-M44
"""

import json
import re
from pathlib import Path
from collections import defaultdict


def get_haplogroup_prefix_levels(haplogroup: str) -> list[str]:
    """
    Extract all prefix levels from a haplogroup name.
    E.g., "E1a1" -> ["E", "E1", "E1a", "E1a1"]
    """
    if not haplogroup:
        return []
    
    # Remove trailing ~ or other markers for processing
    clean_haplo = haplogroup.rstrip('~')
    
    prefixes = []
    current = ""
    
    for char in clean_haplo:
        current += char
        prefixes.append(current)
    
    return prefixes


def generate_normative_names(snp_name: str, haplogroup: str) -> list[str]:
    """
    Generate normative nomenclature names.
    E.g., for M44 with haplogroup E1a1:
    - E-M44
    - E1-M44
    - E1a-M44  
    - E1a1-M44
    """
    if not haplogroup or not snp_name:
        return []
    
    # Clean up haplogroup name
    clean_haplo = haplogroup.rstrip('~')
    
    # Get all prefix levels
    prefixes = get_haplogroup_prefix_levels(clean_haplo)
    
    # Generate names for each prefix level
    normative_names = []
    for prefix in prefixes:
        normative_names.append(f"{prefix}-{snp_name}")
    
    return normative_names


def build_haplogroup_tree() -> tuple[dict, dict]:
    """
    Build parent and children mappings from all individual haplogroup files.
    Returns (parent_map, children_map)
    """
    parent_map = {}  # haplogroup -> parent_name
    children_map = defaultdict(list)  # haplogroup -> [children]
    
    haplogroup_dir = Path('output_master/2019-2020/individual_haplogroups')
    
    for json_file in haplogroup_dir.glob('haplogroup_*.json'):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            nodes = data.get('nodes', {})
            
            for name, node in nodes.items():
                if isinstance(node, dict):
                    parent_id = node.get('parent_id')
                    children = node.get('children', [])
                    
                    if parent_id:
                        parent_map[name] = parent_id
                    
                    if children:
                        children_map[name] = children
                        
        except Exception as e:
            print(f"Warning: Error processing {json_file}: {e}")
    
    return parent_map, dict(children_map)


def main():
    print("Building haplogroup tree from individual files...")
    parent_map, children_map = build_haplogroup_tree()
    print(f"Loaded {len(parent_map)} parent relationships, {len(children_map)} with children")
    
    # Read enhanced_snp_table.jsonl
    input_path = Path('output_master/enhanced_snp_table.jsonl')
    output_path = Path('output_master/enhanced_snp_table_new.jsonl')
    
    print(f"Processing {input_path}...")
    
    updated_count = 0
    normative_count = 0
    total_count = 0
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8') as outfile:
        
        for line in infile:
            total_count += 1
            entry = json.loads(line.strip())
            
            snp_name = entry.get('snp_name', '')
            haplogroup = entry.get('haplogroup', '')
            
            # Add parent_name
            if haplogroup:
                parent = parent_map.get(haplogroup)
                entry['parent_name'] = parent  # Will be None if not found
                
                # Add child_haplogroups
                children = children_map.get(haplogroup, [])
                entry['child_haplogroups'] = children
                
                if parent or children:
                    updated_count += 1
            else:
                entry['parent_name'] = None
                entry['child_haplogroups'] = []
            
            # Generate normative names
            normative_names = generate_normative_names(snp_name, haplogroup)
            entry['normative_names'] = normative_names
            if normative_names:
                normative_count += 1
            
            outfile.write(json.dumps(entry, ensure_ascii=False) + '\n')
    
    print(f"\nProcessed {total_count} SNPs")
    print(f"Added tree relations to {updated_count} SNPs")
    print(f"Added normative names to {normative_count} SNPs")
    
    # Replace original file
    import shutil
    shutil.move(output_path, input_path)
    print(f"\nUpdated {input_path}")
    
    # Show sample entries
    print("\n=== Sample entries ===")
    with open(input_path, 'r', encoding='utf-8') as f:
        for line in f:
            entry = json.loads(line)
            if entry.get('snp_name') in ['M44', 'M132', 'M33', 'M253']:
                print(f"\n{entry['snp_name']}:")
                print(f"  haplogroup: {entry.get('haplogroup')}")
                print(f"  parent_name: {entry.get('parent_name')}")
                print(f"  child_haplogroups: {entry.get('child_haplogroups')}")
                print(f"  normative_names: {entry.get('normative_names')}")


if __name__ == '__main__':
    main()
