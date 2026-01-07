#!/usr/bin/env python3
"""
Create a unified SNP table with Build 36, Build 37, and Build 38 positions.

Uses:
- 2019-2020 XLSX as primary source (Build 37 + Build 38)
- 2013 HTML as Build 36 source
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.xlsx_processor import XLSXSNPIndexParser
from parser.isogg_processor import ISOGGProcessor


@dataclass
class UnifiedSNP:
    """Unified SNP record with all build positions."""
    name: str
    haplogroup: str
    alternate_names: list = field(default_factory=list)
    rs_number: Optional[str] = None
    build36_position: Optional[int] = None
    build37_position: Optional[int] = None
    build38_position: Optional[int] = None
    mutation_info: Optional[str] = None
    # For legacy SNPs not in 2019-2020 data
    is_legacy: bool = False
    build37_liftover: Optional[int] = None  # Position derived from liftOver
    build38_liftover: Optional[int] = None  # Position derived from liftOver
    
    def to_tsv_row(self) -> str:
        """Convert to TSV row."""
        return '\t'.join([
            self.name,
            self.haplogroup,
            ';'.join(self.alternate_names) if self.alternate_names else '',
            self.rs_number or '',
            str(self.build36_position) if self.build36_position else '',
            str(self.build37_position) if self.build37_position else '',
            str(self.build38_position) if self.build38_position else '',
            self.mutation_info or '',
            'legacy' if self.is_legacy else '',
            str(self.build37_liftover) if self.build37_liftover else '',
            str(self.build38_liftover) if self.build38_liftover else ''
        ])


def load_2019_2020_snps(base_dir: str) -> Dict[str, UnifiedSNP]:
    """Load SNP data from 2019-2020 XLSX (Build 37 + Build 38)."""
    
    xlsx_path = os.path.join(
        base_dir, 
        'ISOGG_dna-differences_and_other_info',
        'Haplogroup Data 2019-2020-~',
        'SNP Index_.xlsx'
    )
    
    if not os.path.exists(xlsx_path):
        print(f"Error: 2019-2020 SNP Index not found at {xlsx_path}")
        return {}
    
    print(f"Loading 2019-2020 SNP Index...")
    parser = XLSXSNPIndexParser(xlsx_path)
    snp_data = parser.parse()
    
    unified = {}
    for name, entry in snp_data.items():
        unified[name] = UnifiedSNP(
            name=entry.name,
            haplogroup=entry.haplogroup,
            alternate_names=entry.alternate_names,
            rs_number=entry.rs_number,
            build37_position=entry.build37_position,
            build38_position=entry.build38_position,
            mutation_info=entry.mutation_info
        )
    
    print(f"  Loaded {len(unified)} SNPs with Build 37 + Build 38 positions")
    return unified


def load_2013_build36(base_dir: str) -> Dict[str, dict]:
    """Load Build 36 positions from 2013 HTML data."""
    
    year_dir = os.path.join(base_dir, '2013')
    if not os.path.exists(year_dir):
        print(f"Error: 2013 directory not found at {year_dir}")
        return {}
    
    print(f"Loading 2013 SNP Index (Build 36)...")
    processor = ISOGGProcessor('2013', verbose=False)
    processor.process_directory(year_dir)
    
    build36_data = {}
    for snp_record in processor.snps:  # snps is a list
        if snp_record.position_ncbi36:
            build36_data[snp_record.name] = {
                'position': snp_record.position_ncbi36,
                'rs_id': snp_record.rs_id,
                'haplogroup': snp_record.haplogroup
            }
    
    print(f"  Loaded {len(build36_data)} SNPs with Build 36 positions")
    return build36_data


def normalize_snp_name(name: str) -> str:
    """Normalize SNP name by removing extensions like .1, .2, _1, _2, etc."""
    import re
    # Remove trailing .N or _N where N is a number
    return re.sub(r'[._]\d+$', '', name)


def get_name_variants(name: str) -> list:
    """Generate possible name variants for matching."""
    variants = [name]
    normalized = normalize_snp_name(name)
    if normalized != name:
        variants.append(normalized)
    
    # If it's a number, try with IMS-JST prefix
    if name.isdigit() or (name[0].isdigit() and name.replace('-', '').isdigit()):
        variants.append(f"IMS-JST{name}")
    
    # If it has IMS-JST prefix, try without
    if name.startswith('IMS-JST'):
        variants.append(name[7:])
    
    return variants


def merge_build36(unified: Dict[str, UnifiedSNP], build36_data: Dict[str, dict]) -> int:
    """Merge Build 36 positions into unified SNP table."""
    
    # Build reverse lookup: alternate_name -> primary_name
    alt_to_primary = {}
    for name, snp in unified.items():
        for alt in snp.alternate_names:
            alt_to_primary[alt] = name
            alt_to_primary[normalize_snp_name(alt)] = name
            # Also index IMS-JST variants
            for variant in get_name_variants(alt):
                alt_to_primary[variant] = name
    
    # Build normalized name lookup
    normalized_to_primary = {}
    for name in unified.keys():
        normalized_to_primary[normalize_snp_name(name)] = name
        for variant in get_name_variants(name):
            normalized_to_primary[variant] = name
    
    # Build rs_number lookup
    rs_to_primary = {}
    for name, snp in unified.items():
        if snp.rs_number:
            rs_to_primary[snp.rs_number] = name
    
    matched = 0
    unmatched_snps = []
    
    for snp_name, b36_info in build36_data.items():
        found = False
        
        # Try all name variants
        for variant in get_name_variants(snp_name):
            if variant in unified:
                unified[variant].build36_position = b36_info['position']
                matched += 1
                found = True
                break
            
            if variant in normalized_to_primary:
                primary = normalized_to_primary[variant]
                unified[primary].build36_position = b36_info['position']
                matched += 1
                found = True
                break
            
            if variant in alt_to_primary:
                primary = alt_to_primary[variant]
                unified[primary].build36_position = b36_info['position']
                matched += 1
                found = True
                break
        
        if found:
            continue
        
        # Try rs_number match
        rs_id = b36_info.get('rs_id')
        if rs_id and rs_id != 'None' and rs_id in rs_to_primary:
            primary = rs_to_primary[rs_id]
            unified[primary].build36_position = b36_info['position']
            matched += 1
            continue
        
        # Not found
        unmatched_snps.append(snp_name)
    
    print(f"  Matched {matched} Build 36 positions to 2019-2020 SNPs")
    print(f"  {len(unmatched_snps)} Build 36 SNPs not found in 2019-2020 data")
    
    return matched, unmatched_snps


def export_tsv(unified: Dict[str, UnifiedSNP], output_path: str):
    """Export unified SNP table to TSV."""
    
    header = '\t'.join([
        'snp_name',
        'haplogroup', 
        'alternate_names',
        'rs_number',
        'build36_position',
        'build37_position', 
        'build38_position',
        'mutation',
        'status',
        'build37_liftover',
        'build38_liftover'
    ])
    
    # Sort by SNP name
    sorted_snps = sorted(unified.values(), key=lambda x: x.name)
    
    with open(output_path, 'w') as f:
        f.write(header + '\n')
        for snp in sorted_snps:
            f.write(snp.to_tsv_row() + '\n')
    
    print(f"\nExported {len(sorted_snps)} SNPs to {output_path}")
    
    # Stats
    legacy_count = sum(1 for s in sorted_snps if s.is_legacy)
    has_b36 = sum(1 for s in sorted_snps if s.build36_position)
    has_b37 = sum(1 for s in sorted_snps if s.build37_position)
    has_b38 = sum(1 for s in sorted_snps if s.build38_position)
    has_b37_lift = sum(1 for s in sorted_snps if s.build37_liftover)
    has_b38_lift = sum(1 for s in sorted_snps if s.build38_liftover)
    
    print(f"  Current SNPs: {len(sorted_snps) - legacy_count:,}")
    print(f"  Legacy SNPs: {legacy_count:,}")
    print(f"  With Build 36: {has_b36:,}")
    print(f"  With Build 37: {has_b37:,}")
    print(f"  With Build 38: {has_b38:,}")
    print(f"  With Build 37 (liftOver): {has_b37_lift:,}")
    print(f"  With Build 38 (liftOver): {has_b38_lift:,}")


def run_liftover(positions: Dict[str, int], chain_file: str, base_dir: str) -> Dict[str, int]:
    """Run liftOver on a set of positions.
    
    Args:
        positions: Dict of snp_name -> build36_position
        chain_file: Path to chain file (e.g., hg18ToHg19.over.chain.gz)
        base_dir: Base directory containing liftOver binary
    
    Returns:
        Dict of snp_name -> lifted_position
    """
    import subprocess
    import tempfile
    
    liftover_bin = os.path.join(base_dir, 'liftOver')
    if not os.path.exists(liftover_bin):
        print(f"  Warning: liftOver not found at {liftover_bin}")
        return {}
    
    if not os.path.exists(chain_file):
        print(f"  Warning: Chain file not found: {chain_file}")
        return {}
    
    # Create BED file from positions (chrY positions)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.bed', delete=False) as bed_in:
        for snp_name, pos in positions.items():
            # BED format: chrom, start (0-based), end, name
            bed_in.write(f"chrY\t{pos-1}\t{pos}\t{snp_name}\n")
        bed_in_path = bed_in.name
    
    bed_out_path = bed_in_path.replace('.bed', '_lifted.bed')
    unmapped_path = bed_in_path.replace('.bed', '_unmapped.bed')
    
    try:
        # Run liftOver
        result = subprocess.run(
            [liftover_bin, bed_in_path, chain_file, bed_out_path, unmapped_path],
            capture_output=True,
            text=True
        )
        
        # Parse results
        lifted = {}
        if os.path.exists(bed_out_path):
            with open(bed_out_path) as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        snp_name = parts[3]
                        new_pos = int(parts[2])  # end position (1-based)
                        lifted[snp_name] = new_pos
        
        return lifted
    
    finally:
        # Cleanup
        for path in [bed_in_path, bed_out_path, unmapped_path]:
            if os.path.exists(path):
                os.remove(path)


def add_legacy_snps_with_liftover(
    unified: Dict[str, UnifiedSNP],
    unmatched: list,
    build36_data: Dict[str, dict],
    base_dir: str
) -> int:
    """Add legacy SNPs to unified table with liftOver positions.
    
    Args:
        unified: The unified SNP dictionary to add to
        unmatched: List of unmatched SNP names
        build36_data: Build 36 data from 2013
        base_dir: Base directory for liftOver and chain files
    
    Returns:
        Number of legacy SNPs added
    """
    if not unmatched:
        return 0
    
    print(f"\nProcessing {len(unmatched)} legacy SNPs...")
    
    # Collect Build 36 positions for liftOver
    positions_to_lift = {}
    for snp_name in unmatched:
        if snp_name in build36_data:
            positions_to_lift[snp_name] = build36_data[snp_name]['position']
    
    # Run liftOver to Build 37
    chain_37 = os.path.join(base_dir, 'hg18ToHg19.over.chain.gz')
    lifted_37 = run_liftover(positions_to_lift, chain_37, base_dir)
    print(f"  LiftOver to Build 37: {len(lifted_37)}/{len(positions_to_lift)} succeeded")
    
    # Run liftOver to Build 38
    chain_38 = os.path.join(base_dir, 'hg18ToHg38.over.chain.gz')
    lifted_38 = run_liftover(positions_to_lift, chain_38, base_dir)
    print(f"  LiftOver to Build 38: {len(lifted_38)}/{len(positions_to_lift)} succeeded")
    
    # Add legacy SNPs to unified table
    added = 0
    for snp_name in unmatched:
        if snp_name not in build36_data:
            continue
        
        b36_info = build36_data[snp_name]
        rs_id = b36_info.get('rs_id')
        if rs_id == 'None':
            rs_id = None
        
        # Get haplogroup from 2013 data
        haplogroup = b36_info.get('haplogroup', 'unknown')
        
        unified[snp_name] = UnifiedSNP(
            name=snp_name,
            haplogroup=haplogroup,
            rs_number=rs_id,
            build36_position=b36_info['position'],
            is_legacy=True,
            build37_liftover=lifted_37.get(snp_name),
            build38_liftover=lifted_38.get(snp_name)
        )
        added += 1
    
    print(f"  Added {added} legacy SNPs to unified table")
    return added


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create unified SNP table with Build 36/37/38 positions'
    )
    parser.add_argument(
        '--input-dir', '-i',
        default='.',
        help='Base input directory'
    )
    parser.add_argument(
        '--output', '-o',
        default='unified_snp_table.tsv',
        help='Output TSV file'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Creating Unified SNP Table")
    print("=" * 60)
    
    # Load 2019-2020 as base (Build 37 + 38)
    unified = load_2019_2020_snps(args.input_dir)
    if not unified:
        print("Failed to load 2019-2020 data")
        return 1
    
    # Load and merge Build 36 from 2013
    build36_data = load_2013_build36(args.input_dir)
    unmatched = []
    if build36_data:
        matched, unmatched = merge_build36(unified, build36_data)
    
    # Add legacy SNPs with liftOver positions
    if unmatched:
        add_legacy_snps_with_liftover(unified, unmatched, build36_data, args.input_dir)
    
    # Export
    export_tsv(unified, args.output)
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
