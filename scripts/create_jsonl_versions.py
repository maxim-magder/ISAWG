#!/usr/bin/env python3
"""
Create JSONL (JSON Lines) versions of all JSON files.
Each object on a separate line for streaming/processing efficiency.
"""

import json
import os
from pathlib import Path


def convert_json_to_jsonl(json_path: str, jsonl_path: str):
    """Convert JSON array to JSONL format."""
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle different data structures
    count = 0
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        if isinstance(data, list):
            # Array of objects - write each object as a line
            for item in data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
                count += 1
        elif isinstance(data, dict):
            # Dict of objects - write each value as a line with key
            for key, value in data.items():
                # Add the key to the object if it's a dict
                if isinstance(value, dict):
                    obj = {'_key': key, **value}
                else:
                    obj = {'_key': key, 'value': value}
                f.write(json.dumps(obj, ensure_ascii=False) + '\n')
                count += 1
    
    return count


def main():
    """Convert all JSON files to JSONL."""
    
    base_dir = Path('output_master')
    converted = []
    
    # Find all .json files
    for json_file in base_dir.rglob('*.json'):
        # Skip if already JSONL
        if json_file.suffix == '.jsonl':
            continue
        
        # Create JSONL path
        jsonl_file = json_file.with_suffix('.jsonl')
        
        try:
            count = convert_json_to_jsonl(str(json_file), str(jsonl_file))
            rel_path = json_file.relative_to(base_dir)
            converted.append((str(rel_path), count))
            print(f"✓ {rel_path} → {count} lines")
        except Exception as e:
            print(f"✗ {json_file.relative_to(base_dir)}: {e}")
    
    print(f"\n{'='*60}")
    print(f"Converted {len(converted)} JSON files to JSONL")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
