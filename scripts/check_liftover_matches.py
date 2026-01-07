#!/usr/bin/env python3
"""Check if liftOver positions match existing SNP positions in 2019-2020 data."""

import csv

# Load all Build 37 and Build 38 positions from current SNPs
current_b37 = {}
current_b38 = {}

with open('output_master/unified_snp_table.tsv', 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row['status'] != 'legacy':
            if row['build37_position']:
                pos = int(row['build37_position'])
                current_b37[pos] = row['snp_name']
            if row['build38_position']:
                pos = int(row['build38_position'])
                current_b38[pos] = row['snp_name']

print(f"Loaded {len(current_b37)} current Build 37 positions")
print(f"Loaded {len(current_b38)} current Build 38 positions")

# Check legacy SNPs liftOver positions against current data
matches_b37 = []
matches_b38 = []

with open('output_master/unified_snp_table.tsv', 'r') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if row['status'] == 'legacy':
            if row['build37_liftover']:
                lifted_pos = int(row['build37_liftover'])
                if lifted_pos in current_b37:
                    matches_b37.append({
                        'legacy_name': row['snp_name'],
                        'legacy_haplo': row['haplogroup'],
                        'lifted_pos': lifted_pos,
                        'current_name': current_b37[lifted_pos],
                    })
            if row['build38_liftover']:
                lifted_pos = int(row['build38_liftover'])
                if lifted_pos in current_b38:
                    matches_b38.append({
                        'legacy_name': row['snp_name'],
                        'legacy_haplo': row['haplogroup'],
                        'lifted_pos': lifted_pos,
                        'current_name': current_b38[lifted_pos],
                    })

print(f"\nLegacy SNPs with liftOver Build 37 matching current SNPs: {len(matches_b37)}")
print(f"Legacy SNPs with liftOver Build 38 matching current SNPs: {len(matches_b38)}")
print()

if matches_b37:
    print("Build 37 matches (legacy -> current):")
    for m in matches_b37[:30]:
        print(f"  {m['legacy_name']:20} ({m['legacy_haplo']:25}) @ {m['lifted_pos']:>10} -> {m['current_name']}")
    if len(matches_b37) > 30:
        print(f"  ... and {len(matches_b37) - 30} more")
