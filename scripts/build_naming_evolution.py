#!/usr/bin/env python3
"""
Build haplogroup naming evolution table showing how names changed over time.
Tracks all haplogroup renames across all years (2006-2020).
"""

import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parser.isogg_processor import ISOGGProcessor


def extract_haplogroup_names_by_year():
    """Extract all haplogroup names for each year."""
    
    years_data = {}
    
    # Process HTML years (2006-2017)
    for year in range(2006, 2018):
        year_str = str(year)
        year_dir = Path(year_str)
        
        if not year_dir.exists():
            continue
        
        print(f"Processing {year_str}...")
        processor = ISOGGProcessor(year_str, verbose=False)
        processor.process_directory(str(year_dir))
        
        # Extract haplogroup names and their defining SNPs
        haplogroups = {}
        for node_id, node in processor.tree.items():
            snps = []
            if hasattr(node, 'defining_snps'):
                snps = [s.name if hasattr(s, 'name') else str(s) for s in node.defining_snps]
            
            haplogroups[node_id] = {
                'snps': snps,
                'depth': getattr(node, 'depth', 0)
            }
        
        years_data[year_str] = haplogroups
        print(f"  Found {len(haplogroups)} haplogroups")
    
    return years_data


def build_evolution_table(years_data):
    """Build evolution table showing name changes."""
    
    # Track SNP to haplogroup mappings per year
    snp_to_haplo = {}
    
    for year, haplogroups in sorted(years_data.items()):
        snp_to_haplo[year] = {}
        for haplo_name, info in haplogroups.items():
            for snp in info['snps']:
                if snp not in snp_to_haplo[year]:
                    snp_to_haplo[year][snp] = []
                snp_to_haplo[year][snp].append(haplo_name)
    
    # Find all unique SNPs across all years
    all_snps = set()
    for year_snps in snp_to_haplo.values():
        all_snps.update(year_snps.keys())
    
    # Build evolution records
    evolution = []
    
    for snp in sorted(all_snps):
        record = {'snp': snp}
        
        # Track which haplogroup this SNP was in for each year
        for year in sorted(years_data.keys()):
            if snp in snp_to_haplo[year]:
                haplos = snp_to_haplo[year][snp]
                record[year] = haplos if len(haplos) > 1 else haplos[0]
            else:
                record[year] = None
        
        evolution.append(record)
    
    return evolution


def find_haplogroup_renames(years_data):
    """Find direct haplogroup renames (same SNPs, different name)."""
    
    years = sorted(years_data.keys())
    renames = []
    
    for i in range(len(years) - 1):
        year1, year2 = years[i], years[i + 1]
        
        # Build SNP signature to haplogroup mapping
        sig_to_haplo_1 = {}
        sig_to_haplo_2 = {}
        
        for haplo, info in years_data[year1].items():
            sig = tuple(sorted(info['snps']))
            if sig:
                sig_to_haplo_1[sig] = haplo
        
        for haplo, info in years_data[year2].items():
            sig = tuple(sorted(info['snps']))
            if sig:
                sig_to_haplo_2[sig] = haplo
        
        # Find matching signatures with different names
        for sig in sig_to_haplo_1:
            if sig in sig_to_haplo_2:
                name1 = sig_to_haplo_1[sig]
                name2 = sig_to_haplo_2[sig]
                
                if name1 != name2:
                    renames.append({
                        'from_year': year1,
                        'to_year': year2,
                        'old_name': name1,
                        'new_name': name2,
                        'defining_snps': list(sig)
                    })
    
    return renames


def main():
    """Build naming evolution table."""
    
    print("="*60)
    print("Building Haplogroup Naming Evolution Table")
    print("="*60 + "\n")
    
    # Extract data
    years_data = extract_haplogroup_names_by_year()
    
    # Build evolution table
    print("\nBuilding SNP evolution table...")
    evolution = build_evolution_table(years_data)
    
    # Find renames
    print("Finding haplogroup renames...")
    renames = find_haplogroup_renames(years_data)
    
    # Save results
    output_dir = Path('output_master')
    
    # Save full evolution table
    with open(output_dir / 'haplogroup_evolution.json', 'w') as f:
        json.dump(evolution, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Saved SNP evolution table: {len(evolution)} SNPs")
    
    # Save renames
    with open(output_dir / 'haplogroup_renames.json', 'w') as f:
        json.dump(renames, f, indent=2, ensure_ascii=False)
    print(f"✓ Saved haplogroup renames: {len(renames)} changes")
    
    # Create TSV versions
    years = sorted(years_data.keys())
    
    # Evolution TSV
    with open(output_dir / 'haplogroup_evolution.tsv', 'w') as f:
        f.write('snp\t' + '\t'.join(years) + '\n')
        for record in evolution:
            row = [record['snp']]
            for year in years:
                val = record.get(year)
                if val is None:
                    row.append('')
                elif isinstance(val, list):
                    row.append(', '.join(val))
                else:
                    row.append(val)
            f.write('\t'.join(row) + '\n')
    print(f"✓ Saved evolution TSV")
    
    # Renames TSV
    with open(output_dir / 'haplogroup_renames.tsv', 'w') as f:
        f.write('from_year\tto_year\told_name\tnew_name\tdefining_snps\n')
        for rename in renames:
            f.write(f"{rename['from_year']}\t{rename['to_year']}\t"
                   f"{rename['old_name']}\t{rename['new_name']}\t"
                   f"{', '.join(rename['defining_snps'])}\n")
    print(f"✓ Saved renames TSV")
    
    print("\n" + "="*60)
    print("Done!")
    print("="*60)


if __name__ == '__main__':
    main()
