#!/usr/bin/env python3
"""
Create enhanced unified SNP table with:
- All build positions (36, 37, 38)
- Separate status column from haplogroup
- Alphanumeric haplogroup names from 2016
- Merged legacy SNPs with position matching
- Reverse liftOver for Build 36
"""

import os
import sys
import csv
import re
import subprocess
import tempfile
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Set

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser.xlsx_processor import XLSXSNPIndexParser
from parser.isogg_processor import ISOGGProcessor


@dataclass
class EnhancedSNP:
    """Enhanced SNP record with all data."""
    name: str
    haplogroup: str  # Clean haplogroup without status
    haplogroup_alpha: str = ""  # Alphanumeric name from 2016
    alternate_names: List[str] = field(default_factory=list)
    rs_number: Optional[str] = None
    build33_position: Optional[int] = None  # hg15 (April 2003)
    build34_position: Optional[int] = None  # hg16 (July 2003)
    build35_position: Optional[int] = None  # hg17 (May 2004)
    build36_position: Optional[int] = None  # hg18 (March 2006)
    build37_position: Optional[int] = None  # hg19 (Feb 2009)
    build38_position: Optional[int] = None  # hg38 (Dec 2013)
    build36_liftover: Optional[int] = None  # Derived via reverse liftOver
    mutation_info: Optional[str] = None
    snp_status: str = ""  # Investigation, Notes, Private, legacy, etc.
    source: str = "2019-2020"  # Data source year
    
    def to_tsv_row(self) -> str:
        """Convert to TSV row."""
        # Normalize alternate names - replace any problematic chars
        alt_names_str = ''
        if self.alternate_names:
            # Clean each name and join with semicolons
            cleaned = []
            for name in self.alternate_names:
                # Remove newlines, tabs, normalize slashes to separate entries
                clean = str(name).replace('\n', ' ').replace('\t', ' ').replace('/', ', ').strip()
                if clean:
                    cleaned.append(clean)
            alt_names_str = '; '.join(cleaned)
        
        return '\t'.join([
            self.name,
            self.haplogroup,
            self.haplogroup_alpha,
            alt_names_str,
            self.rs_number or '',
            str(self.build33_position) if self.build33_position else '',
            str(self.build34_position) if self.build34_position else '',
            str(self.build35_position) if self.build35_position else '',
            str(self.build36_position) if self.build36_position else '',
            str(self.build36_liftover) if self.build36_liftover else '',
            str(self.build37_position) if self.build37_position else '',
            str(self.build38_position) if self.build38_position else '',
            self.mutation_info or '',
            self.snp_status,
            self.source
        ])


def parse_haplogroup_status(haplo: str) -> tuple:
    """Extract status from haplogroup name.
    
    Returns: (clean_haplogroup, status)
    """
    # Extract bracket contents
    match = re.search(r'\(([^)]+)\)', haplo)
    if match:
        status = match.group(1)
        clean = re.sub(r'\s*\([^)]+\)\s*', '', haplo).strip()
        return clean, status
    
    # Check for tilde suffix (provisional)
    if haplo.endswith('~'):
        return haplo.rstrip('~'), 'provisional'
    
    return haplo, ''


def run_liftover(positions: Dict[str, int], chain_file: str, base_dir: str) -> Dict[str, int]:
    """Run liftOver on a set of positions."""
    liftover_bin = os.path.join(base_dir, 'liftOver')
    if not os.path.exists(liftover_bin):
        print(f"  Warning: liftOver not found at {liftover_bin}")
        return {}
    
    if not os.path.exists(chain_file):
        print(f"  Warning: Chain file not found: {chain_file}")
        return {}
    
    # Create sanitized mapping for SNP names (BED format doesn't like spaces, brackets, etc.)
    name_mapping = {}
    sanitized_positions = {}
    for idx, (snp_name, pos) in enumerate(positions.items()):
        safe_name = f"SNP_{idx}"
        name_mapping[safe_name] = snp_name
        sanitized_positions[safe_name] = pos
    
    # Create temp file and write positions with sanitized names
    fd, bed_in_path = tempfile.mkstemp(suffix='.bed', text=True)
    with os.fdopen(fd, 'w') as bed_in:
        for safe_name, pos in sanitized_positions.items():
            bed_in.write(f"chrY\t{pos-1}\t{pos}\t{safe_name}\n")
        bed_in.flush()  # Ensure all data is written
    
    bed_out_path = bed_in_path.replace('.bed', '_lifted.bed')
    unmapped_path = bed_in_path.replace('.bed', '_unmapped.bed')
    
    try:
        result = subprocess.run(
            [liftover_bin, bed_in_path, chain_file, bed_out_path, unmapped_path],
            capture_output=True, text=True
        )
        
        lifted = {}
        if os.path.exists(bed_out_path):
            with open(bed_out_path) as f:
                for line in f:
                    parts = line.strip().split('\t')
                    if len(parts) >= 4:
                        safe_name = parts[3]
                        if safe_name in name_mapping:
                            original_name = name_mapping[safe_name]
                            lifted[original_name] = int(parts[2])
        return lifted
    finally:
        for path in [bed_in_path, bed_out_path, unmapped_path]:
            if os.path.exists(path):
                os.remove(path)


def load_2019_2020_snps(base_dir: str) -> Dict[str, EnhancedSNP]:
    """Load SNP data from 2019-2020 XLSX."""
    xlsx_path = os.path.join(
        base_dir, 
        'ISOGG_dna-differences_and_other_info',
        'Haplogroup Data 2019-2020-~',
        'SNP Index_.xlsx'
    )
    
    print(f"Loading 2019-2020 SNP Index...")
    parser = XLSXSNPIndexParser(xlsx_path)
    snp_data = parser.parse()
    
    unified = {}
    for name, entry in snp_data.items():
        clean_haplo, status = parse_haplogroup_status(entry.haplogroup)
        unified[name] = EnhancedSNP(
            name=entry.name,
            haplogroup=clean_haplo,
            alternate_names=entry.alternate_names,
            rs_number=entry.rs_number,
            build37_position=entry.build37_position,
            build38_position=entry.build38_position,
            mutation_info=entry.mutation_info,
            snp_status=status,
            source='2019-2020'
        )
    
    print(f"  Loaded {len(unified)} SNPs")
    return unified


def load_2016_alphanumeric(base_dir: str) -> Dict[str, str]:
    """Load alphanumeric haplogroup names from 2016 HTML."""
    year_dir = os.path.join(base_dir, '2016')
    if not os.path.exists(year_dir):
        return {}
    
    print(f"Loading 2016 alphanumeric haplogroups...")
    processor = ISOGGProcessor('2016', verbose=False)
    processor.process_directory(year_dir)
    
    # Build SNP -> alphanumeric haplogroup mapping
    alpha_map = {}
    for node_id, node in processor.tree.items():
        if hasattr(node, 'defining_snps') and node.defining_snps:
            for snp in node.defining_snps:
                snp_name = snp.name if hasattr(snp, 'name') else str(snp)
                alpha_map[snp_name] = node_id
    
    print(f"  Loaded {len(alpha_map)} SNP -> alphanumeric mappings")
    return alpha_map


def load_2013_build36(base_dir: str) -> Dict[str, dict]:
    """Load Build 36 positions from 2013."""
    year_dir = os.path.join(base_dir, '2013')
    if not os.path.exists(year_dir):
        return {}
    
    print(f"Loading 2013 SNP Index (Build 36)...")
    processor = ISOGGProcessor('2013', verbose=False)
    processor.process_directory(year_dir)
    
    build36_data = {}
    for snp_record in processor.snps:
        if snp_record.position_ncbi36:
            build36_data[snp_record.name] = {
                'position': snp_record.position_ncbi36,
                'rs_id': snp_record.rs_id,
                'haplogroup': snp_record.haplogroup
            }
    
    print(f"  Loaded {len(build36_data)} SNPs with Build 36 positions")
    return build36_data


def normalize_snp_name(name: str) -> str:
    """Normalize SNP name."""
    return re.sub(r'[._]\d+$', '', name)


def get_name_variants(name: str) -> list:
    """Generate name variants for matching."""
    variants = [name]
    normalized = normalize_snp_name(name)
    if normalized != name:
        variants.append(normalized)
    if name.isdigit():
        variants.append(f"IMS-JST{name}")
    if name.startswith('IMS-JST'):
        variants.append(name[7:])
    return variants


def merge_build36_data(
    unified: Dict[str, EnhancedSNP],
    build36_data: Dict[str, dict],
    base_dir: str
) -> tuple:
    """Merge Build 36 data into unified table."""
    
    # Build lookups
    alt_to_primary = {}
    normalized_to_primary = {}
    rs_to_primary = {}
    b37_to_primary = {}  # For position matching
    b38_to_primary = {}
    
    for name, snp in unified.items():
        for alt in snp.alternate_names:
            alt_to_primary[alt] = name
            for v in get_name_variants(alt):
                alt_to_primary[v] = name
        for v in get_name_variants(name):
            normalized_to_primary[v] = name
        if snp.rs_number:
            rs_to_primary[snp.rs_number] = name
        if snp.build37_position:
            b37_to_primary[snp.build37_position] = name
        if snp.build38_position:
            b38_to_primary[snp.build38_position] = name
    
    # First pass: direct matching
    matched_by_name = 0
    unmatched = []
    
    for snp_name, b36_info in build36_data.items():
        found = False
        for variant in get_name_variants(snp_name):
            target = None
            if variant in unified:
                target = variant
            elif variant in normalized_to_primary:
                target = normalized_to_primary[variant]
            elif variant in alt_to_primary:
                target = alt_to_primary[variant]
            
            if target:
                unified[target].build36_position = b36_info['position']
                matched_by_name += 1
                found = True
                break
        
        if not found:
            rs_id = b36_info.get('rs_id')
            if rs_id and rs_id != 'None' and rs_id in rs_to_primary:
                target = rs_to_primary[rs_id]
                unified[target].build36_position = b36_info['position']
                matched_by_name += 1
                found = True
        
        if not found:
            unmatched.append(snp_name)
    
    print(f"  Matched {matched_by_name} by name/rs")
    
    # Second pass: liftOver unmatched and check position matching
    if unmatched:
        print(f"  Processing {len(unmatched)} unmatched via liftOver...")
        positions_to_lift = {n: build36_data[n]['position'] for n in unmatched if n in build36_data}
        
        chain_37 = os.path.join(base_dir, 'hg18ToHg19.over.chain.gz')
        chain_38 = os.path.join(base_dir, 'hg18ToHg38.over.chain.gz')
        
        lifted_37 = run_liftover(positions_to_lift, chain_37, base_dir)
        lifted_38 = run_liftover(positions_to_lift, chain_38, base_dir)
        
        matched_by_pos = 0
        still_unmatched = []
        
        for snp_name in unmatched:
            found = False
            
            # Check if lifted position matches existing SNP
            if snp_name in lifted_37 and lifted_37[snp_name] in b37_to_primary:
                target = b37_to_primary[lifted_37[snp_name]]
                unified[target].build36_position = build36_data[snp_name]['position']
                # Add as alternate name
                if snp_name not in unified[target].alternate_names:
                    unified[target].alternate_names.append(snp_name)
                matched_by_pos += 1
                found = True
            elif snp_name in lifted_38 and lifted_38[snp_name] in b38_to_primary:
                target = b38_to_primary[lifted_38[snp_name]]
                unified[target].build36_position = build36_data[snp_name]['position']
                if snp_name not in unified[target].alternate_names:
                    unified[target].alternate_names.append(snp_name)
                matched_by_pos += 1
                found = True
            
            if not found:
                still_unmatched.append(snp_name)
        
        print(f"  Matched {matched_by_pos} by liftOver position")
        
        # Add truly unmatched as legacy SNPs
        print(f"  Adding {len(still_unmatched)} as legacy SNPs...")
        for snp_name in still_unmatched:
            b36_info = build36_data[snp_name]
            rs_id = b36_info.get('rs_id')
            if rs_id == 'None':
                rs_id = None
            
            clean_haplo, status = parse_haplogroup_status(b36_info.get('haplogroup', 'unknown'))
            
            unified[snp_name] = EnhancedSNP(
                name=snp_name,
                haplogroup=clean_haplo,
                rs_number=rs_id,
                build36_position=b36_info['position'],
                build37_position=lifted_37.get(snp_name),
                build38_position=lifted_38.get(snp_name),
                snp_status='legacy' if not status else f'legacy,{status}',
                source='2013'
            )
        
        return matched_by_name + matched_by_pos, still_unmatched
    
    return matched_by_name, []


def reverse_liftover_to_build36(unified: Dict[str, EnhancedSNP], base_dir: str):
    """LiftOver Build 37/38 positions back to Build 36 for SNPs missing Build 36."""
    
    # Find SNPs with Build 37 but no Build 36
    need_lift = {}
    for name, snp in unified.items():
        if snp.build37_position and not snp.build36_position:
            need_lift[name] = snp.build37_position
    
    if not need_lift:
        print("  No SNPs need reverse liftOver")
        return 0
    
    print(f"  Reverse lifting {len(need_lift)} positions from Build 37 to Build 36...")
    
    # Download reverse chain if needed
    chain_file = os.path.join(base_dir, 'hg19ToHg18.over.chain.gz')
    if not os.path.exists(chain_file):
        print("  Downloading hg19ToHg18 chain file...")
        import urllib.request
        url = "https://hgdownload.cse.ucsc.edu/goldenPath/hg19/liftOver/hg19ToHg18.over.chain.gz"
        urllib.request.urlretrieve(url, chain_file)
    
    lifted = run_liftover(need_lift, chain_file, base_dir)
    
    # Apply lifted positions
    for name, pos in lifted.items():
        unified[name].build36_liftover = pos
    
    print(f"  Lifted {len(lifted)}/{len(need_lift)} positions")
    return len(lifted)


def liftover_to_older_builds(unified: Dict[str, EnhancedSNP], base_dir: str):
    """LiftOver positions to older genome builds (Build 35, 34, 33)."""
    
    print("\nLifting over to older genome builds...")
    
    # Step 1: hg18 (Build 36) -> hg17 (Build 35)
    positions_b36 = {}
    for name, snp in unified.items():
        # Use direct Build 36 position, or liftOver-derived one
        pos = snp.build36_position or snp.build36_liftover
        if pos:
            positions_b36[name] = pos
    
    if positions_b36:
        print(f"  Lifting {len(positions_b36)} Build 36 positions to Build 35 (hg17)...")
        chain_file = os.path.join(base_dir, 'hg18ToHg17.over.chain.gz')
        lifted_35 = run_liftover(positions_b36, chain_file, base_dir)
        
        # Apply only for SNPs that exist in unified dict
        applied_35 = 0
        for name, pos in lifted_35.items():
            if name in unified:
                unified[name].build35_position = pos
                applied_35 += 1
        
        print(f"    → {applied_35} positions lifted to Build 35")
        
        # Step 2: hg17 (Build 35) -> hg16 (Build 34)
        if lifted_35:
            print(f"  Lifting {len(lifted_35)} Build 35 positions to Build 34 (hg16)...")
            chain_file = os.path.join(base_dir, 'hg17ToHg16.over.chain.gz')
            lifted_34 = run_liftover(lifted_35, chain_file, base_dir)
            
            applied_34 = 0
            for name, pos in lifted_34.items():
                if name in unified:
                    unified[name].build34_position = pos
                    applied_34 += 1
            
            print(f"    → {applied_34} positions lifted to Build 34")
        
        # Step 3: hg17 (Build 35) -> hg15 (Build 33)
        if lifted_35:
            print(f"  Lifting {len(lifted_35)} Build 35 positions to Build 33 (hg15)...")
            chain_file = os.path.join(base_dir, 'hg17ToHg15.over.chain.gz')
            lifted_33 = run_liftover(lifted_35, chain_file, base_dir)
            
            applied_33 = 0
            for name, pos in lifted_33.items():
                if name in unified:
                    unified[name].build33_position = pos
                    applied_33 += 1
            
            print(f"    → {applied_33} positions lifted to Build 33")
        
        return applied_35, applied_34 if lifted_35 else 0, applied_33 if lifted_35 else 0
    
    return 0, 0, 0


def export_enhanced_tsv(unified: Dict[str, EnhancedSNP], output_path: str):
    """Export enhanced SNP table to TSV."""
    
    header = '\t'.join([
        'snp_name',
        'haplogroup',
        'haplogroup_alpha',
        'alternate_names',
        'rs_number',
        'build33_position',
        'build34_position',
        'build35_position',
        'build36_position',
        'build36_liftover',
        'build37_position',
        'build38_position',
        'mutation',
        'status',
        'source'
    ])
    
    sorted_snps = sorted(unified.values(), key=lambda x: x.name)
    
    with open(output_path, 'w') as f:
        f.write(header + '\n')
        for snp in sorted_snps:
            f.write(snp.to_tsv_row() + '\n')
    
    print(f"\nExported {len(sorted_snps)} SNPs to {output_path}")
    
    # Stats
    legacy_count = sum(1 for s in sorted_snps if 'legacy' in s.snp_status)
    has_b33 = sum(1 for s in sorted_snps if s.build33_position)
    has_b34 = sum(1 for s in sorted_snps if s.build34_position)
    has_b35 = sum(1 for s in sorted_snps if s.build35_position)
    has_b36 = sum(1 for s in sorted_snps if s.build36_position)
    has_b36_lift = sum(1 for s in sorted_snps if s.build36_liftover)
    has_b37 = sum(1 for s in sorted_snps if s.build37_position)
    has_b38 = sum(1 for s in sorted_snps if s.build38_position)
    has_alpha = sum(1 for s in sorted_snps if s.haplogroup_alpha)
    
    print(f"  Total SNPs: {len(sorted_snps):,}")
    print(f"  Current (2019-2020): {len(sorted_snps) - legacy_count:,}")
    print(f"  Legacy (2013 only): {legacy_count:,}")
    print(f"  With Build 33 (hg15): {has_b33:,}")
    print(f"  With Build 34 (hg16): {has_b34:,}")
    print(f"  With Build 35 (hg17): {has_b35:,}")
    print(f"  With Build 36 (hg18): {has_b36:,}")
    print(f"  With Build 36 (liftOver): {has_b36_lift:,}")
    print(f"  With Build 37 (hg19): {has_b37:,}")
    print(f"  With Build 38 (hg38): {has_b36:,}")
    print(f"  With Build 36 (liftOver): {has_b36_lift:,}")
    print(f"  With Build 37: {has_b37:,}")
    print(f"  With Build 38: {has_b38:,}")
    print(f"  With alphanumeric haplogroup: {has_alpha:,}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create enhanced unified SNP table')
    parser.add_argument('--input-dir', '-i', default='.', help='Base input directory')
    parser.add_argument('--output', '-o', default='output_master/enhanced_snp_table.tsv', help='Output TSV')
    parser.add_argument('--skip-reverse-lift', action='store_true', help='Skip reverse liftOver')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Creating Enhanced Unified SNP Table")
    print("=" * 60)
    
    # Load 2019-2020 as base
    unified = load_2019_2020_snps(args.input_dir)
    
    # Load and merge 2016 alphanumeric names
    alpha_map = load_2016_alphanumeric(args.input_dir)
    if alpha_map:
        matched_alpha = 0
        for snp_name, alpha_haplo in alpha_map.items():
            if snp_name in unified:
                # Skip if alpha_haplo looks corrupted (contains newlines, commas, or slashes)
                # These are SNP lists mistakenly parsed as haplogroup names
                alpha_str = str(alpha_haplo).strip()
                if '\n' in alpha_str or ',' in alpha_str or '/' in alpha_str:
                    continue  # Skip corrupted data
                
                unified[snp_name].haplogroup_alpha = alpha_str
                matched_alpha += 1
        print(f"  Applied {matched_alpha} alphanumeric haplogroup names")
    
    # Load and merge Build 36 data
    build36_data = load_2013_build36(args.input_dir)
    if build36_data:
        merge_build36_data(unified, build36_data, args.input_dir)
    
    # Reverse liftOver for SNPs missing Build 36
    if not args.skip_reverse_lift:
        reverse_liftover_to_build36(unified, args.input_dir)
    
    # LiftOver to older builds (35, 34, 33)
    liftover_to_older_builds(unified, args.input_dir)
    
    # Export
    export_enhanced_tsv(unified, args.output)
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)


if __name__ == '__main__':
    main()
