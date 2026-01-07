#!/usr/bin/env python3
"""
ISOGG Unified Processor

Processes ISOGG Y-DNA Haplogroup data from multiple formats:
- HTML files (2006-2017)
- XLSX files (2018-2020)

Outputs JSON files with:
- Tree structure (nodes, parent/child relationships)
- SNP Index with mutation information
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add parser directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.isogg_processor import ISOGGProcessor
from parser.xlsx_processor import process_year_xlsx, ConversionTableParser, XLSXSNPIndexParser


def load_xlsx_snp_index_for_html_year(xlsx_base: str, year: str):
    """Load XLSX SNP Index for years that have HTML trees but XLSX SNP data (2016, 2017)."""
    
    # Map year to XLSX SNP Index location
    xlsx_snp_paths = {
        '2016': os.path.join(xlsx_base, 'Haplogroup Data 2016', 'SNP Index_.xlsx'),
        '2017': os.path.join(xlsx_base, 'Haplogroup Data 2017', 'SNP Index .xlsx'),
    }
    
    if year not in xlsx_snp_paths:
        return None
    
    snp_path = xlsx_snp_paths[year]
    if not os.path.exists(snp_path):
        return None
    
    print(f"  Loading XLSX SNP Index for {year}...")
    parser = XLSXSNPIndexParser(snp_path)
    snp_data = parser.parse()
    print(f"    Loaded {len(snp_data)} SNPs from XLSX")
    return snp_data


def process_html_years(base_dir: str, output_dir: str, years: list = None):
    """Process HTML files for years 2006-2017."""
    
    html_years = [str(y) for y in range(2006, 2018)]
    if years:
        html_years = [y for y in html_years if y in years]
    
    xlsx_base = os.path.join(base_dir, 'ISOGG_dna-differences_and_other_info')
    stats = {}
    
    for year in html_years:
        year_dir = os.path.join(base_dir, year)
        if not os.path.exists(year_dir):
            print(f"  Skipping {year} - directory not found")
            continue
        
        # Check if there are HTML files
        html_files = [f for f in os.listdir(year_dir) if f.endswith('.html')]
        if not html_files:
            print(f"  Skipping {year} - no HTML files found")
            continue
        
        print(f"\nProcessing HTML year {year}...")
        
        year_output = os.path.join(output_dir, year)
        os.makedirs(year_output, exist_ok=True)
        
        try:
            processor = ISOGGProcessor(year, verbose=False)
            processor.process_directory(year_dir)
            
            # For 2016 and 2017, load SNP Index from XLSX files instead
            xlsx_snps = load_xlsx_snp_index_for_html_year(xlsx_base, year)
            if xlsx_snps:
                # Convert SNPEntry objects to dicts for JSON serialization
                snps_dict = {k: v.to_dict() for k, v in xlsx_snps.items()}
                
                # Export the XLSX SNP data alongside the HTML tree
                snp_index_path = os.path.join(year_output, 'snp_index_xlsx.json')
                with open(snp_index_path, 'w') as f:
                    json.dump({
                        'metadata': {
                            'source': 'ISOGG Y-DNA SNP Index (XLSX)',
                            'version': year,
                            'record_count': len(snps_dict)
                        },
                        'snps': snps_dict
                    }, f, indent=2)
                print(f"    Exported XLSX SNP Index: {len(snps_dict)} SNPs")
            
            processor.export_json(year_output)
            processor.export_individual_haplogroups(year_output)
            
            node_count = len(processor.tree)
            snp_count = len(xlsx_snps) if xlsx_snps else len(processor.snps)
            
            stats[year] = {
                'nodes': node_count,
                'snps': snp_count
            }
            print(f"  {year}: {node_count} haplogroups, {snp_count} SNPs")
            
        except Exception as e:
            print(f"  Error processing {year}: {e}")
            import traceback
            traceback.print_exc()
    
    return stats


def process_xlsx_years(base_dir: str, output_dir: str, years: list = None, include_china: bool = False):
    """Process XLSX files for years 2018-2020.
    
    Args:
        base_dir: Base directory containing ISOGG_dna-differences_and_other_info
        output_dir: Output directory for JSON files
        years: Optional list of years to process
        include_china: If True, also process China user data to separate directory
    """
    
    xlsx_years = ['2018', '2019-2020']
    if years:
        # Map numeric years to xlsx year keys
        year_map = {'2018': '2018', '2019': '2019-2020', '2020': '2019-2020'}
        xlsx_years = list(set(year_map.get(y, y) for y in years if year_map.get(y, y) in xlsx_years))
    
    xlsx_base = os.path.join(base_dir, 'ISOGG_dna-differences_and_other_info')
    if not os.path.exists(xlsx_base):
        print(f"  XLSX directory not found: {xlsx_base}")
        return {}
    
    stats = {}
    
    # Process main (non-China) data
    for year in xlsx_years:
        print(f"\nProcessing XLSX year {year}...")
        process_year_xlsx(xlsx_base, year, output_dir)
        
        # Get stats from output
        year_tree = os.path.join(output_dir, year, 'tree.json')
        if os.path.exists(year_tree):
            with open(year_tree) as f:
                data = json.load(f)
                stats[year] = {
                    'nodes': len(data.get('nodes', {}))
                }
    
    # Process China data to separate directory (if requested)
    if include_china:
        china_output = os.path.join(output_dir, 'china_users')
        os.makedirs(china_output, exist_ok=True)
        
        china_years = ['2018-china', '2019-2020-china']
        for year in china_years:
            print(f"\nProcessing China user data {year}...")
            process_year_xlsx(xlsx_base, year, china_output)
    
    # Process conversion table
    conv_table_path = os.path.join(xlsx_base, 'Haplogroup-Conversion-Table.tsv')
    if os.path.exists(conv_table_path):
        print(f"\nProcessing Haplogroup Conversion Table...")
        parser = ConversionTableParser(conv_table_path)
        conversions = parser.parse()
        parser.to_json(os.path.join(output_dir, 'haplogroup_conversions.json'))
        print(f"  Parsed {sum(len(v) for v in conversions.values())} conversion mappings")
    
    return stats


def create_summary(output_dir: str, html_stats: dict, xlsx_stats: dict):
    """Create a summary of all processed data."""
    
    summary = {
        'generated': datetime.now().isoformat(),
        'years': {},
        'total_nodes': 0
    }
    
    for year, stats in {**html_stats, **xlsx_stats}.items():
        summary['years'][year] = stats
        summary['total_nodes'] += stats.get('nodes', 0)
    
    with open(os.path.join(output_dir, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary


def main():
    parser = argparse.ArgumentParser(
        description='ISOGG Unified Processor - Parse HTML and XLSX haplogroup data'
    )
    parser.add_argument(
        '--input-dir', '-i',
        default='.',
        help='Base input directory containing year folders and XLSX data'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='output',
        help='Output directory for JSON files'
    )
    parser.add_argument(
        '--years', '-y',
        nargs='+',
        help='Specific years to process (default: all)'
    )
    parser.add_argument(
        '--format', '-f',
        choices=['html', 'xlsx', 'all'],
        default='all',
        help='Format to process'
    )
    parser.add_argument(
        '--include-china',
        action='store_true',
        help='Also process China user data (stored separately)'
    )
    
    args = parser.parse_args()
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 60)
    print("ISOGG Y-DNA Haplogroup Data Processor")
    print("=" * 60)
    
    html_stats = {}
    xlsx_stats = {}
    
    if args.format in ['html', 'all']:
        print("\n--- Processing HTML files (2006-2017) ---")
        html_stats = process_html_years(args.input_dir, args.output_dir, args.years)
    
    if args.format in ['xlsx', 'all']:
        print("\n--- Processing XLSX files (2018-2020) ---")
        xlsx_stats = process_xlsx_years(args.input_dir, args.output_dir, args.years, 
                                         include_china=args.include_china)
    
    # Create summary
    summary = create_summary(args.output_dir, html_stats, xlsx_stats)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    for year in sorted(summary['years'].keys()):
        stats = summary['years'][year]
        print(f"  {year}: {stats.get('nodes', 0):,} nodes")
    print(f"\n  TOTAL: {summary['total_nodes']:,} nodes across {len(summary['years'])} years")
    print("=" * 60)


if __name__ == '__main__':
    main()
