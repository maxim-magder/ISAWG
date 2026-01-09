#!/usr/bin/env python3
"""
Diagnose why rs numbers aren't being parsed correctly.
Check the 2019-2020 snp_index to see what column mappings were used.
"""

import json
import sys

# Load the parsed SNP index
with open('output_master/2019-2020/snp_index.json') as f:
    data = json.load(f)

# Check M44 specifically
if 'M44' in data:
    print("M44 entry:")
    print(json.dumps(data['M44'], indent=2))
    print()

# Find some SNPs that DO have rs_numbers
with_rs = [(k, v) for k, v in data.items() if v.get('rs_number')]
print(f"SNPs with rs_numbers: {len(with_rs)} / {len(data)}")
print("\nExample SNPs with rs_numbers:")
for name, snp in with_rs[:5]:
    print(f"  {name}: rs_number={snp['rs_number']}")

print("\n" + "="*60)
print("ISSUE: The XLSX parser needs to be re-run on the source files")
print("But the source XLSX files were deleted during cleanup.")
print("\nOptions:")
print("1. Re-download the XLSX files from Google Sheets")
print("2. Manually patch the rs_numbers from a known source")
print("3. Use dbSNP API to fetch rs_numbers by position")
