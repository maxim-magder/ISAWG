#!/usr/bin/env python3
import csv

with open('output_master/enhanced_snp_table.tsv', 'r', newline='', encoding='utf-8') as f:
    reader = csv.reader(f, delimiter='\t')
    for i, row in enumerate(reader, 1):
        if i == 171:
            print(f'Row 171 has {len(row)} columns:')
            for j, field in enumerate(row):
                print(f'  [{j}] {repr(field)[:100]}')
            break
