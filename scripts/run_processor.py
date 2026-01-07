#!/usr/bin/env python3
"""
Batch processor for all ISOGG years (2006-2017).

This script processes all available ISOGG HTML files and generates:
1. Individual year JSON files in output/individual_years/YYYY/
2. Merged master files in output/merged/
3. CSV exports in output/exports/
"""

import os
import sys
from pathlib import Path

# Add parser directory to path
sys.path.insert(0, str(Path(__file__).parent / 'parser'))

from isogg_processor import ISOGGProcessor, merge_years, detect_year

# Configuration
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / 'output'
YEARS_TO_PROCESS = ['2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013', '2014', '2015', '2016', '2017']

def get_year_directory(year: str) -> Path:
    """Get the input directory for a given year."""
    return BASE_DIR / year

def process_all_years(verbose: bool = True):
    """Process all available years."""
    individual_output = OUTPUT_DIR / 'individual_years'
    individual_output.mkdir(parents=True, exist_ok=True)
    
    processed_years = []
    
    for year in YEARS_TO_PROCESS:
        year_dir = get_year_directory(year)
        
        if not year_dir.exists():
            if verbose:
                print(f"Skipping {year}: directory not found")
            continue
        
        # Check if there are HTML files
        html_files = list(year_dir.glob('*.html'))
        if not html_files:
            if verbose:
                print(f"Skipping {year}: no HTML files found")
            continue
        
        output_path = individual_output / year
        output_path.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            print(f"\n{'='*60}")
            print(f"Processing ISOGG {year}")
            print(f"{'='*60}")
        
        try:
            processor = ISOGGProcessor(year, verbose)
            processor.process_directory(str(year_dir))
            processor.export_json(str(output_path))
            processor.export_csv(str(output_path))
            processor.export_individual_haplogroups(str(output_path))
            processed_years.append(str(output_path))
            
            if verbose:
                print(f"✓ {year}: {len(processor.tree)} haplogroups, {len(processor.snps)} SNPs")
        except Exception as e:
            print(f"✗ Error processing {year}: {e}")
            import traceback
            traceback.print_exc()
    
    return processed_years


def merge_all_years(year_dirs: list, verbose: bool = True):
    """Merge all processed years into master files."""
    merged_output = OUTPUT_DIR / 'merged'
    merged_output.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"\n{'='*60}")
        print(f"Merging {len(year_dirs)} years into master files")
        print(f"{'='*60}")
    
    try:
        merge_years(year_dirs, str(merged_output), verbose)
        if verbose:
            print("✓ Merged files created successfully")
    except Exception as e:
        print(f"✗ Error merging years: {e}")
        import traceback
        traceback.print_exc()


def create_combined_exports(verbose: bool = True):
    """Create combined CSV exports from merged data."""
    import json
    import csv
    
    merged_dir = OUTPUT_DIR / 'merged'
    exports_dir = OUTPUT_DIR / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"\n{'='*60}")
        print("Creating combined exports")
        print(f"{'='*60}")
    
    # Export haplogroups
    tree_file = merged_dir / 'master_tree.json'
    if tree_file.exists():
        with open(tree_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        tree = data.get('tree', {})
        
        with open(exports_dir / 'all_haplogroups.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'id', 'name', 'parent_id', 'depth', 'status', 'is_paragroup',
                'defining_snps', 'first_appeared', 'versions_present'
            ])
            
            for hap_id, node in sorted(tree.items()):
                snps = node.get('defining_snps', [])
                if snps:
                    snps_str = ', '.join(s.get('name', '') if isinstance(s, dict) else str(s) for s in snps)
                else:
                    snps_str = ''
                
                versions = node.get('versions_present', [])
                versions_str = ', '.join(versions) if versions else ''
                
                writer.writerow([
                    hap_id,
                    node.get('name', ''),
                    node.get('parent_id', ''),
                    node.get('depth', 0),
                    node.get('status', 'normal'),
                    node.get('is_paragroup', False),
                    snps_str,
                    node.get('first_appeared', ''),
                    versions_str
                ])
        
        if verbose:
            print(f"✓ all_haplogroups.csv: {len(tree)} entries")
    
    # Export SNPs
    snp_file = merged_dir / 'master_snps.json'
    if snp_file.exists():
        with open(snp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        snps = data.get('snps', [])
        
        with open(exports_dir / 'all_snps.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'name', 'haplogroup', 'status', 'aliases', 'rs_id',
                'position_grch37', 'mutation', 'first_appeared', 'versions_present'
            ])
            
            for snp in snps:
                aliases = snp.get('aliases', [])
                aliases_str = ', '.join(aliases) if aliases else ''
                
                versions = snp.get('versions_present', [])
                versions_str = ', '.join(versions) if versions else ''
                
                writer.writerow([
                    snp.get('name', ''),
                    snp.get('haplogroup', ''),
                    snp.get('status', 'normal'),
                    aliases_str,
                    snp.get('rs_id', ''),
                    snp.get('position_grch37', ''),
                    snp.get('mutation', ''),
                    snp.get('first_appeared', ''),
                    versions_str
                ])
        
        if verbose:
            print(f"✓ all_snps.csv: {len(snps)} entries")


def print_summary():
    """Print a summary of the processing results."""
    print(f"\n{'='*60}")
    print("PROCESSING COMPLETE")
    print(f"{'='*60}")
    
    individual_dir = OUTPUT_DIR / 'individual_years'
    if individual_dir.exists():
        years = sorted([d.name for d in individual_dir.iterdir() if d.is_dir()])
        print(f"\nIndividual years processed: {', '.join(years)}")
    
    merged_dir = OUTPUT_DIR / 'merged'
    if merged_dir.exists():
        files = list(merged_dir.glob('*.json'))
        print(f"\nMerged files: {', '.join(f.name for f in files)}")
    
    exports_dir = OUTPUT_DIR / 'exports'
    if exports_dir.exists():
        files = list(exports_dir.glob('*.csv'))
        print(f"\nCSV exports: {', '.join(f.name for f in files)}")
    
    print(f"\nOutput directory: {OUTPUT_DIR}")


def main():
    """Main entry point."""
    print("ISOGG Y-DNA Haplogroup Tree Data Processor")
    print("="*60)
    
    # Process all years
    year_dirs = process_all_years(verbose=True)
    
    # Merge all years
    if year_dirs:
        merge_all_years(year_dirs, verbose=True)
        create_combined_exports(verbose=True)
    
    print_summary()


if __name__ == '__main__':
    main()
