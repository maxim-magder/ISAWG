#!/usr/bin/env python3
"""
Merge rs numbers from haplogroup files into the enhanced SNP table.
Preserves existing rs numbers and adds new ones where available.
"""

import json
import sys

print("Loading haplogroup rs numbers...")
with open('haplogroup_rs_numbers.json') as f:
    hg_data = json.load(f)

print(f"  Loaded {len(hg_data):,} SNPs from haplogroup files")
with_rs_in_hg = sum(1 for s in hg_data.values() if s['rs_number'])
print(f"  {with_rs_in_hg:,} have rs numbers ({100*with_rs_in_hg/len(hg_data):.1f}%)")

print("\nLoading enhanced SNP table...")
with open('output_master/enhanced_snp_table.json') as f:
    enhanced = json.load(f)

print(f"  Loaded {len(enhanced):,} SNPs from enhanced table")
with_rs_before = sum(1 for s in enhanced if s['rs_number'])
print(f"  {with_rs_before:,} have rs numbers ({100*with_rs_before/len(enhanced):.1f}%)")

print("\nMerging rs numbers...")
updated_count = 0
added_count = 0

for snp in enhanced:
    name = snp['snp_name']
    
    if name in hg_data:
        hg_rs = hg_data[name]['rs_number']
        current_rs = snp['rs_number']
        
        if hg_rs:
            if not current_rs:
                # Add new rs number
                snp['rs_number'] = hg_rs
                added_count += 1
            elif current_rs != hg_rs:
                # Different rs number - keep existing but note it
                print(f"  Conflict for {name}: existing={current_rs}, new={hg_rs} (keeping existing)")
                updated_count += 1

with_rs_after = sum(1 for s in enhanced if s['rs_number'])

print(f"\nResults:")
print(f"  Added new rs numbers: {added_count:,}")
print(f"  Conflicts (kept existing): {updated_count}")
print(f"  Total with rs numbers: {with_rs_after:,} ({100*with_rs_after/len(enhanced):.1f}%)")
print(f"  Improvement: +{with_rs_after - with_rs_before:,} SNPs")

# Save updated data
print("\nSaving updated files...")

# JSON
with open('output_master/enhanced_snp_table.json', 'w', encoding='utf-8') as f:
    json.dump(enhanced, f, indent=2, ensure_ascii=False)

# JSONL
with open('output_master/enhanced_snp_table.jsonl', 'w', encoding='utf-8') as f:
    for snp in enhanced:
        f.write(json.dumps(snp, ensure_ascii=False) + '\n')

# TSV
with open('output_master/enhanced_snp_table.tsv', 'w', encoding='utf-8') as f:
    # Header
    f.write('\t'.join([
        'snp_name', 'haplogroup', 'haplogroup_alpha', 'alternate_names', 'rs_number',
        'build33_position', 'build34_position', 'build35_position',
        'build36_position', 'build36_liftover', 'build37_position', 'build38_position',
        'mutation', 'status', 'source'
    ]) + '\n')
    
    # Data
    for snp in enhanced:
        # Convert alternate_names list to semicolon-separated
        alt_names = '; '.join(snp.get('alternate_names', [])) if snp.get('alternate_names') else ''
        
        row = [
            str(snp.get('snp_name', '')),
            str(snp.get('haplogroup', '')),
            str(snp.get('haplogroup_alpha') or ''),
            alt_names,
            str(snp.get('rs_number') or ''),
            str(snp.get('build33_position') or ''),
            str(snp.get('build34_position') or ''),
            str(snp.get('build35_position') or ''),
            str(snp.get('build36_position') or ''),
            str(snp.get('build36_liftover') or ''),
            str(snp.get('build37_position') or ''),
            str(snp.get('build38_position') or ''),
            str(snp.get('mutation') or ''),
            str(snp.get('status') or ''),
            str(snp.get('source') or '')
        ]
        f.write('\t'.join(row) + '\n')

print("  ✓ enhanced_snp_table.json")
print("  ✓ enhanced_snp_table.jsonl")
print("  ✓ enhanced_snp_table.tsv")

# Check M44 specifically
print("\nVerifying M44...")
for snp in enhanced:
    if snp['snp_name'] == 'M44':
        print(json.dumps(snp, indent=2))
        break

print("\n✓ Done!")
