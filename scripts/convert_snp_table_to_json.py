#!/usr/bin/env python3
"""
Convert enhanced SNP TSV table to JSON format.
"""

import csv
import json
import sys


def convert_tsv_to_json(tsv_path: str, json_path: str):
    """Convert TSV to JSON."""
    
    snps = []
    
    with open(tsv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            # Convert to proper types
            snp = {
                'snp_name': row['snp_name'],
                'haplogroup': row['haplogroup'],
                'haplogroup_alpha': row['haplogroup_alpha'] or None,
                'alternate_names': [name.strip() for name in row['alternate_names'].split(';') if name.strip()] if row['alternate_names'] else [],
                'rs_number': row['rs_number'] or None,
                'build33_position': int(row['build33_position']) if row['build33_position'] else None,
                'build34_position': int(row['build34_position']) if row['build34_position'] else None,
                'build35_position': int(row['build35_position']) if row['build35_position'] else None,
                'build36_position': int(row['build36_position']) if row['build36_position'] else None,
                'build36_liftover': int(row['build36_liftover']) if row['build36_liftover'] else None,
                'build37_position': int(row['build37_position']) if row['build37_position'] else None,
                'build38_position': int(row['build38_position']) if row['build38_position'] else None,
                'mutation': row['mutation'] or None,
                'status': row['status'] or None,
                'source': row['source']
            }
            snps.append(snp)
    
    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(snps, f, indent=2, ensure_ascii=False)
    
    print(f"Converted {len(snps)} SNPs from TSV to JSON")
    print(f"Output: {json_path}")


if __name__ == '__main__':
    tsv_path = 'output_master/enhanced_snp_table.tsv'
    json_path = 'output_master/enhanced_snp_table.json'
    
    convert_tsv_to_json(tsv_path, json_path)
