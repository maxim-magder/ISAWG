#!/usr/bin/env python3
"""
Update rs_numbers in ALL output_master JSON/JSONL files.
Merges new rs_numbers while preserving existing ones.
"""

import json
import os
from pathlib import Path

# Load the rs_number mapping from haplogroup files
print("Loading rs_number mapping from haplogroup files...")
with open('haplogroup_rs_numbers.json') as f:
    rs_map = json.load(f)

rs_lookup = {}
for snp_name, data in rs_map.items():
    if data.get('rs_number'):
        rs_lookup[snp_name] = data['rs_number']

print(f"  Loaded {len(rs_lookup):,} SNPs with rs_numbers\n")

def update_snp_index_file(filepath):
    """Update a snp_index.json or snp_index.jsonl file."""
    print(f"Processing: {filepath}")
    
    is_jsonl = filepath.endswith('.jsonl')
    
    # Load data
    if is_jsonl:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # Check if it's a dict (with keys) or array
    is_dict = isinstance(data, dict)
    
    if is_dict:
        items = data.values()
    else:
        items = data
    
    # Update rs_numbers
    added = 0
    had_existing = 0
    
    for item in items:
        if not isinstance(item, dict):
            continue
        
        # Get SNP name - could be in 'name', '_key', or 'snp_name'
        snp_name = item.get('name') or item.get('_key') or item.get('snp_name')
        
        if not snp_name:
            continue
        
        current_rs = item.get('rs_number')
        new_rs = rs_lookup.get(snp_name)
        
        if new_rs:
            if not current_rs or current_rs in ['None', 'null', '']:
                item['rs_number'] = new_rs
                added += 1
            else:
                had_existing += 1
    
    # Save updated data
    if is_jsonl:
        with open(filepath, 'w', encoding='utf-8') as f:
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    else:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"  Added: {added}, Had existing: {had_existing}\n")
    return added, had_existing


def update_tree_file(filepath):
    """Update tree.json or tree.jsonl files if they contain SNP data."""
    print(f"Processing: {filepath}")
    
    is_jsonl = filepath.endswith('.jsonl')
    
    # Load data
    if is_jsonl:
        data = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    else:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    # Tree files usually have a 'nodes' dict
    # Each node can have 'snps' array
    # We don't update tree files as they don't have rs_number fields
    print(f"  Skipped (tree files don't contain rs_number fields)\n")
    return 0, 0


def main():
    """Update all files in output_master."""
    
    total_added = 0
    total_existing = 0
    files_updated = 0
    
    # Find all snp_index files
    snp_index_files = []
    for root, dirs, files in os.walk('output_master'):
        for file in files:
            if 'snp_index' in file and (file.endswith('.json') or file.endswith('.jsonl')):
                snp_index_files.append(os.path.join(root, file))
    
    print(f"Found {len(snp_index_files)} snp_index files to process\n")
    print("="*60)
    
    for filepath in sorted(snp_index_files):
        added, existing = update_snp_index_file(filepath)
        total_added += added
        total_existing += existing
        if added > 0:
            files_updated += 1
    
    print("="*60)
    print(f"\nSUMMARY:")
    print(f"  Files processed: {len(snp_index_files)}")
    print(f"  Files updated: {files_updated}")
    print(f"  Total rs_numbers added: {total_added:,}")
    print(f"  Total with existing rs_numbers: {total_existing:,}")
    
    # Verify M44 in 2019-2020
    print("\n" + "="*60)
    print("Verifying M44 in 2019-2020/snp_index.json...")
    with open('output_master/2019-2020/snp_index.json') as f:
        data = json.load(f)
        if 'M44' in data:
            print(json.dumps(data['M44'], indent=2))
        else:
            print("M44 not found!")
    
    print("\n✓ All files updated!")


if __name__ == '__main__':
    main()
