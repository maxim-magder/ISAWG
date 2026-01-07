#!/usr/bin/env python3
"""Analyze haplogroup formats and patterns in the unified SNP table."""

import csv
import re

# Count different haplogroup suffixes/markers
stats = {
    'tilde': 0,      # ~ suffix
    'caret': 0,      # ^ suffix  
    'brackets': 0,   # has ()
    'clean': 0,      # no special chars
}

examples = {
    'tilde': [],
    'caret': [],
    'brackets': [],
}

with open('output_master/unified_snp_table.tsv', 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        haplo = row['haplogroup']
        if '~' in haplo:
            stats['tilde'] += 1
            if len(examples['tilde']) < 5:
                examples['tilde'].append(f"{row['snp_name']}: {haplo}")
        elif '^' in haplo:
            stats['caret'] += 1
            if len(examples['caret']) < 5:
                examples['caret'].append(f"{row['snp_name']}: {haplo}")
        elif '(' in haplo:
            stats['brackets'] += 1
            if len(examples['brackets']) < 5:
                examples['brackets'].append(f"{row['snp_name']}: {haplo}")
        else:
            stats['clean'] += 1

print("Haplogroup format statistics:")
print("=" * 50)
for key, count in stats.items():
    print(f"  {key:15}: {count:,}")
    if key in examples and examples[key]:
        for ex in examples[key]:
            print(f"      {ex}")
