#!/usr/bin/env python3
"""
Fix encoding issues in JSON files by removing � characters and cleaning up formatting.
"""

import json
import re
from pathlib import Path

def clean_snp_value(value):
    """Remove � characters and clean up whitespace."""
    if not isinstance(value, str):
        return value
    
    # Remove � characters and excessive whitespace
    cleaned = value.replace('�', '')
    # Clean up multiple spaces
    cleaned = re.sub(r' +', ' ', cleaned)
    # Clean up multiple newlines
    cleaned = re.sub(r'\n\n+', '\n\n', cleaned)
    # Remove trailing/leading whitespace from each line
    cleaned = '\n'.join(line.strip() for line in cleaned.split('\n'))
    # Remove empty lines at start/end
    cleaned = cleaned.strip()
    
    return cleaned

def fix_json_file(filepath):
    """Fix encoding issues in a JSON file."""
    print(f"Processing {filepath.name}...")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    changes = 0
    
    # Handle different file structures
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                for key, value in item.items():
                    if isinstance(value, str) and '�' in value:
                        item[key] = clean_snp_value(value)
                        changes += 1
                    elif isinstance(value, list):
                        for i, v in enumerate(value):
                            if isinstance(v, str) and '�' in v:
                                value[i] = clean_snp_value(v)
                                changes += 1
    elif isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, str) and '�' in item:
                        value[i] = clean_snp_value(item)
                        changes += 1
    
    if changes > 0:
        print(f"  Fixed {changes} encoding issues")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"  Saved {filepath.name}")
    else:
        print(f"  No changes needed")
    
    return changes

def fix_jsonl_file(filepath):
    """Fix encoding issues in a JSONL file."""
    print(f"Processing {filepath.name}...")
    
    lines = []
    changes = 0
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if '�' in line:
                obj = json.loads(line)
                for key, value in obj.items():
                    if isinstance(value, str) and '�' in value:
                        obj[key] = clean_snp_value(value)
                        changes += 1
                lines.append(json.dumps(obj, ensure_ascii=False))
            else:
                lines.append(line.rstrip('\n'))
    
    if changes > 0:
        print(f"  Fixed {changes} encoding issues")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
        print(f"  Saved {filepath.name}")
    else:
        print(f"  No changes needed")
    
    return changes

def main():
    output_dir = Path('/Users/maximmagder/ISAWG/ISAWG/output_master')
    
    total_changes = 0
    
    # Fix JSON files
    json_files = [
        'haplogroup_evolution.json',
        'haplogroup_renames.json',
    ]
    
    for filename in json_files:
        filepath = output_dir / filename
        if filepath.exists():
            total_changes += fix_json_file(filepath)
    
    # Fix JSONL files
    jsonl_files = [
        'haplogroup_evolution.jsonl',
        'haplogroup_renames.jsonl',
    ]
    
    for filename in jsonl_files:
        filepath = output_dir / filename
        if filepath.exists():
            total_changes += fix_jsonl_file(filepath)
    
    print(f"\n✓ Total: {total_changes} encoding issues fixed")

if __name__ == '__main__':
    main()
