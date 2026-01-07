#!/usr/bin/env python3
"""
ISOGG Y-DNA Haplogroup Tree Data Processor

Converts archived ISOGG HTML pages (2006-2017+) into clean, machine-parseable JSON.

Usage:
    python isogg_processor.py --year 2006 --input ./files/ --output ./output/
    python isogg_processor.py --batch --input ./all_years/ --output ./output/
    python isogg_processor.py --merge --input ./output/individual/ --output ./output/merged/

Author: Max (with Claude assistance)
Version: 1.0.0
"""

import argparse
import html
import json
import os
import re
import sys
import csv
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from bs4 import BeautifulSoup, NavigableString

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG = {
    'encoding_fixes': {
        'ï¿½': '•',
        'Ã¢': '',
        'Â': '',
        'â€™': "'",
        'â€"': '—',
        'â€œ': '"',
        'â€\x9d': '"',
        '&nbsp;': ' ',
    },
    
    'snp_status_classes': {
        'snp': 'normal',
        'snp-new': 'new',
        'snp-conf': 'confirmed',
        'snp-prov': 'provisional',
        'snp-priv': 'private',
        'snp-inv': 'investigation',
    },
    
    'clade_status_classes': {
        'hap': 'normal',
        'hap-new': 'new',
        'hap-ren': 'renamed',
        'hap-nyi': 'nyi',
    },
    
    'file_patterns': {
        'tree_trunk': [r'TreeTrunk', r'Tree.Trunk', r'Haplogroup.Tree.Trunk'],
        'haplogroup': [r'Hapgrp([A-T])', r'Haplogroup.([A-T])\.html'],
        'snp_index': [r'SNP.Index', r'SNP_index'],
        'glossary': [r'Glossary'],
        'papers': [r'Papers', r'All_Papers'],
        'criteria': [r'Requirements', r'Criteria', r'Listing.Criteria'],
        'main_index': [r'^index', r'^Main', r'_index'],
    },
    
    'year_patterns': [
        r'_(\d{4})_',
        r'(\d{4})_ISOGG',
        r'(\d{2})\.html$',
    ],
}

# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class SNP:
    """Represents a single SNP marker."""
    name: str
    status: str = 'normal'
    is_representative: bool = False
    aliases: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        d = {'name': self.name, 'status': self.status, 'is_representative': self.is_representative}
        if self.aliases:
            d['aliases'] = self.aliases
        return d


@dataclass
class SNPRecord:
    """Full SNP record from SNP Index."""
    name: str
    haplogroup: str
    status: str = 'normal'
    aliases: List[str] = field(default_factory=list)
    rs_id: Optional[str] = None
    position_ncbi36: Optional[int] = None  # Build 36 / hg18
    position_grch37: Optional[int] = None  # Build 37 / hg19
    position_grch38: Optional[int] = None  # Build 38 / hg38
    mutation: Optional[str] = None
    citations: List[dict] = field(default_factory=list)
    source_version: str = ''
    versions_present: List[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None and v != []}


@dataclass
class HaplogroupNode:
    """Represents a node in the haplogroup tree."""
    id: str
    name: str
    parent_id: Optional[str] = None
    depth: int = 0
    order_index: int = 0  # Preserves document order for tree building
    status: str = 'normal'
    is_paragroup: bool = False
    defining_snps: List[SNP] = field(default_factory=list)
    description: Optional[str] = None
    populations: List[str] = field(default_factory=list)
    frequency_notes: Optional[str] = None
    detail_page: Optional[str] = None
    children: List[str] = field(default_factory=list)
    source_version: str = ''
    revision_date: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'depth': self.depth,
            'status': self.status,
            'is_paragroup': self.is_paragroup,
            'defining_snps': [s.to_dict() for s in self.defining_snps],
            'description': self.description,
            'populations': self.populations if self.populations else None,
            'frequency_notes': self.frequency_notes,
            'detail_page': self.detail_page,
            'children': self.children,
            'source_version': self.source_version,
            'revision_date': self.revision_date,
        }

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ''
    for bad, good in CONFIG['encoding_fixes'].items():
        text = text.replace(bad, good)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def detect_year(filepath: str, content: str = None) -> Optional[str]:
    """Detect the ISOGG year from filename or content."""
    filename = os.path.basename(filepath)
    
    for pattern in CONFIG['year_patterns']:
        match = re.search(pattern, filename)
        if match:
            year = match.group(1)
            if len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year
            return year
    
    if content:
        match = re.search(r'Haplogroup Tree (\d{4})', content)
        if match:
            return match.group(1)
    return None


def identify_file_type(filepath: str) -> Optional[str]:
    """Identify the type of ISOGG file from its name."""
    filename = os.path.basename(filepath)
    
    for file_type, patterns in CONFIG['file_patterns'].items():
        for pattern in patterns:
            if re.search(pattern, filename, re.I):
                if file_type == 'haplogroup':
                    # Match both HapgrpA and Haplogroup A formats
                    match = re.search(r'hapgrp([a-t])|haplogroup.([a-t])\.html', filename, re.I)
                    if match:
                        letter = (match.group(1) or match.group(2)).upper()
                        return f'haplogroup_{letter}'
                return file_type
    return None


def get_line_content_before_span(span) -> str:
    """Get the content on the same line before the haplogroup span.
    
    Works by going backwards through previous siblings until hitting a <br> tag.
    This is needed because HTML uses <br> to separate lines within a single <p> tag.
    
    Special handling: In some years (e.g., 2017), the <br> tag may be INSIDE a 
    <span class="light"> tag rather than as a sibling. We need to detect this
    and extract only the content after the last <br> within such spans.
    """
    line_content = []
    sibling = span.previous_sibling
    
    while sibling:
        if hasattr(sibling, 'name') and sibling.name == 'br':
            break
        if isinstance(sibling, NavigableString):
            line_content.insert(0, str(sibling))
        elif hasattr(sibling, 'name'):
            # Check if this element CONTAINS a br tag (edge case in some years)
            if hasattr(sibling, 'find') and sibling.find('br'):
                # Get content after the last <br> within this element
                inner_html = str(sibling)
                # Find last <br> position
                br_pos = inner_html.rfind('<br')
                if br_pos >= 0:
                    # Find end of br tag
                    end_pos = inner_html.find('>', br_pos)
                    if end_pos >= 0:
                        after_br = inner_html[end_pos+1:]
                        line_content.insert(0, after_br)
                        break
                else:
                    line_content.insert(0, inner_html)
            else:
                line_content.insert(0, str(sibling))
        sibling = sibling.previous_sibling
    
    return ''.join(line_content)


def calculate_depth(line_content: str, year: str) -> int:
    """Calculate tree depth based on year format.
    
    Different years use different indentation schemes:
    - 2006-2008: Use <font color="#DEDEDE">�</font> bullets (corrupted encoding)
    - 2009-2013: Similar to 2006 with variations
    - 2014+: Use <span class="light">&#8226;</span> and <span class="dark">&#8226;</span>
    
    The depth is the number of bullet markers before the haplogroup name.
    The line_content should be the HTML content BEFORE the haplogroup span on the same line.
    """
    year_int = int(year)
    
    # Try different counting methods based on year
    if year_int <= 2008:
        # Old format: count corrupted bullet characters
        # The replacement character appears as \ufffd (�)
        count = line_content.count('\ufffd')
        if count > 0:
            return count
        count = line_content.count('•')
        if count > 0:
            return count
        # Fallback: count font color tags
        count = len(re.findall(r'<font\s+color\s*=\s*["\']?#DEDEDE["\']?\s*>', line_content, re.I))
        return count
    else:
        # 2009+: Count bullet entities and characters
        # First count actual bullet characters (•)
        count = line_content.count('•')
        if count > 0:
            return count
        # HTML entity
        count = line_content.count('&#8226;')
        if count > 0:
            return count
        # Replacement character
        count = line_content.count('\ufffd')
        if count > 0:
            return count
        # Fallback: count light/dark spans
        spans = re.findall(r'<span class="(?:light|dark)">', line_content)
        return len(spans)


def extract_snp_status(element) -> str:
    """Extract SNP status from element or class string."""
    if hasattr(element, 'get'):
        classes = element.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
    elif isinstance(element, str):
        classes = [element]
    else:
        classes = []
    
    for cls in classes:
        if cls in CONFIG['snp_status_classes']:
            return CONFIG['snp_status_classes'][cls]
    return 'normal'


def extract_clade_status(element) -> str:
    """Extract clade status from element."""
    if hasattr(element, 'get'):
        classes = element.get('class', [])
        if isinstance(classes, str):
            classes = classes.split()
    else:
        classes = []
    
    for cls in classes:
        if cls in CONFIG['clade_status_classes']:
            return CONFIG['clade_status_classes'][cls]
    return 'normal'


def parse_snp_list(snp_text: str) -> List[SNP]:
    """Parse a comma-separated list of SNPs."""
    snps = []
    if not snp_text:
        return snps
    
    if '<' in snp_text:
        temp_soup = BeautifulSoup(f'<div>{snp_text}</div>', 'html.parser')
        
        for element in temp_soup.div.children:
            if isinstance(element, NavigableString):
                text = str(element).strip()
                for snp_name in re.split(r'[,]\s*', text):
                    snp_name = snp_name.strip()
                    if snp_name and snp_name != '-' and not snp_name.startswith('('):
                        if '/' in snp_name:
                            parts = snp_name.split('/')
                            snps.append(SNP(name=parts[0].strip(), 
                                          aliases=[p.strip() for p in parts[1:]]))
                        else:
                            snps.append(SNP(name=snp_name))
            elif element.name == 'b':
                text = element.get_text().strip()
                inner_span = element.find('span')
                status = extract_snp_status(inner_span) if inner_span else 'normal'
                if inner_span:
                    text = inner_span.get_text().strip()
                for snp_name in re.split(r'[,/]\s*', text):
                    snp_name = snp_name.strip()
                    if snp_name and snp_name != '-':
                        snps.append(SNP(name=snp_name, status=status, is_representative=True))
            elif element.name == 'span':
                status = extract_snp_status(element)
                text = element.get_text().strip()
                is_rep = element.find('b') is not None
                for snp_name in re.split(r'[,/]\s*', text):
                    snp_name = snp_name.strip()
                    if snp_name and snp_name != '-':
                        snps.append(SNP(name=snp_name, status=status, is_representative=is_rep))
            elif element.name == 'i':
                text = element.get_text().strip()
                for snp_name in re.split(r'[,/]\s*', text):
                    snp_name = snp_name.strip()
                    if snp_name and snp_name != '-':
                        snps.append(SNP(name=snp_name, status='normal'))
    else:
        for snp_name in re.split(r'[,]\s*', snp_text):
            snp_name = snp_name.strip()
            if snp_name and snp_name != '-':
                if '/' in snp_name:
                    parts = snp_name.split('/')
                    snps.append(SNP(name=parts[0].strip(), 
                                  aliases=[p.strip() for p in parts[1:]]))
                else:
                    snps.append(SNP(name=snp_name))
    return snps

# =============================================================================
# TREE PARSING
# =============================================================================

class TreeParser:
    """Parser for ISOGG haplogroup tree HTML files."""
    
    def __init__(self, year: str, verbose: bool = False):
        self.year = year
        self.verbose = verbose
        self.nodes: Dict[str, HaplogroupNode] = {}
        self.order_counter: int = 0  # Counter for document order
    
    def parse_tree_trunk(self, filepath: str) -> Dict[str, HaplogroupNode]:
        """Parse the main Tree Trunk HTML file."""
        if self.verbose:
            print(f"Parsing Tree Trunk: {filepath}")
        
        self.order_counter = 0  # Reset order counter
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        revision_date = self._extract_revision_date(soup)
        body = soup.find('body')
        if not body:
            raise ValueError("No body element found")
        
        hap_spans = body.find_all('span', class_=re.compile(r'^hap'))
        
        for span in hap_spans:
            node = self._parse_haplogroup_line(span, revision_date)
            if node:
                node.order_index = self.order_counter
                self.order_counter += 1
                self.nodes[node.id] = node
        
        self._build_relationships()
        return self.nodes
    
    def parse_haplogroup_page(self, filepath: str, letter: str) -> Dict[str, HaplogroupNode]:
        """Parse an individual haplogroup detail page."""
        if self.verbose:
            print(f"Parsing Haplogroup {letter}: {filepath}")
        
        self.order_counter = 0  # Reset order counter for each page
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        revision_date = self._extract_revision_date(soup)
        body = soup.find('body')
        hap_spans = body.find_all('span', class_=re.compile(r'^hap'))
        
        page_nodes = {}
        for span in hap_spans:
            node = self._parse_haplogroup_line(span, revision_date)
            if node:
                node.order_index = self.order_counter
                self.order_counter += 1
                page_nodes[node.id] = node
        
        self._extract_descriptions(soup, page_nodes, letter)
        return page_nodes
    
    def _parse_haplogroup_line(self, span, revision_date: str) -> Optional[HaplogroupNode]:
        """Parse a single haplogroup line.
        
        The haplogroup name can be:
        1. Inside a <b> tag within the span
        2. Inside an <a> tag within the span (for linked haplogroups)
        3. Directly as text content of the span (for root nodes like Y)
        """
        # Try to find name in <b> tag first
        bold = span.find('b')
        if bold:
            name = bold.get_text(strip=True)
        else:
            # Try <a> tag
            link = span.find('a')
            if link:
                name = link.get_text(strip=True)
            else:
                # Fallback to direct text content
                name = span.get_text(strip=True)
        
        if not name:
            return None
        
        # Skip known non-haplogroup entries (legend items)
        if name.lower() in ['added', 'renamed', 'redefined', 'not on', 'confirmed', 
                            'provisional', 'private', 'investigation']:
            return None
        
        status = extract_clade_status(span)
        is_paragroup = name.endswith('*')
        
        # Get line content BEFORE the span for depth calculation
        line_content = get_line_content_before_span(span)
        depth = calculate_depth(line_content, self.year)
        
        snp_text = ''
        for sibling in span.next_siblings:
            if isinstance(sibling, NavigableString):
                text = str(sibling)
                if '<br' in text.lower():
                    break
                snp_text += text
            elif hasattr(sibling, 'name'):
                if sibling.name == 'br':
                    break
                elif sibling.name in ['span', 'b', 'i']:
                    snp_text += str(sibling)
                else:
                    break
        
        snp_text = snp_text.replace('&nbsp;', ' ').strip()
        snp_text = re.sub(r'^\s*[-–—]\s*$', '', snp_text)
        defining_snps = parse_snp_list(snp_text)
        
        link = span.find('a')
        detail_page = link.get('href') if link else None
        
        return HaplogroupNode(
            id=name, name=name, depth=depth, status=status,
            is_paragroup=is_paragroup, defining_snps=defining_snps,
            detail_page=detail_page, source_version=self.year,
            revision_date=revision_date,
        )
    
    def _extract_revision_date(self, soup) -> Optional[str]:
        """Extract the revision date."""
        text = soup.get_text()
        match = re.search(r'Last\s+revision\s+date[^:]*:\s*(\d+\s+\w+\s+\d{4})', text)
        if match:
            date_str = match.group(1)
            for fmt in ['%d %B %Y', '%d %b %Y', '%B %d, %Y']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        return None
    
    def _extract_descriptions(self, soup, nodes: Dict[str, HaplogroupNode], letter: str):
        """Extract population descriptions."""
        for p in soup.find_all('p'):
            text = p.get_text()
            match = re.match(rf'\s*(?:Y-DNA\s+)?[Hh]aplogroup\s+({letter}\S*)', text)
            if match:
                hap_id = match.group(1)
                if hap_id in nodes:
                    nodes[hap_id].description = clean_text(text)
    
    def _build_relationships(self):
        """Build parent-child relationships based on depth.
        
        Uses a depth stack to track the current path from root to current node.
        Nodes MUST be processed in document order (the order they appear in HTML).
        The order_index field is used to maintain document order.
        """
        # Sort by order_index to preserve document order (critical for tree building)
        nodes_in_order = sorted(self.nodes.values(), key=lambda n: n.order_index)
        
        # depth_stack[i] = node_id at depth i
        depth_stack: List[str] = []
        
        for node in nodes_in_order:
            depth = node.depth
            
            # Pop stack until we're at the right level
            # If current depth is N, parent is at depth N-1
            while len(depth_stack) > depth:
                depth_stack.pop()
            
            # Set parent if stack is not empty
            if depth_stack:
                parent_id = depth_stack[-1]
                node.parent_id = parent_id
                if parent_id in self.nodes:
                    if node.id not in self.nodes[parent_id].children:
                        self.nodes[parent_id].children.append(node.id)
            
            # Push current node onto stack at its depth
            if len(depth_stack) < depth + 1:
                # Extend stack if needed
                while len(depth_stack) < depth:
                    depth_stack.append(depth_stack[-1] if depth_stack else '')
                depth_stack.append(node.id)
            else:
                depth_stack[depth] = node.id
                # Truncate stack to current depth + 1
                depth_stack = depth_stack[:depth + 1]

# =============================================================================
# SNP INDEX PARSING
# =============================================================================

class SNPIndexParser:
    """Parser for ISOGG SNP Index HTML files."""
    
    def __init__(self, year: str, verbose: bool = False):
        self.year = year
        self.verbose = verbose
    
    def parse(self, filepath: str) -> List[SNPRecord]:
        """Parse the SNP Index HTML file."""
        if self.verbose:
            print(f"Parsing SNP Index: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        
        table = soup.find('table', class_='bord')
        if not table:
            table = soup.find('table', {'border': True})
        if not table:
            for t in soup.find_all('table'):
                if t.find('td', string=re.compile(r'SNP', re.I)):
                    table = t
                    break
        
        if not table:
            raise ValueError("Could not find SNP Index table")
        
        header_row = table.find('tr')
        headers = [td.get_text(strip=True) for td in header_row.find_all(['td', 'th'])]
        num_columns = len(headers)
        
        if self.verbose:
            print(f"  Found {num_columns} columns: {headers}")
        
        snps = []
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) < 4 and num_columns >= 4:
                continue
            if len(cells) < 2:
                continue
            
            record = self._parse_row(cells, num_columns)
            if record:
                snps.append(record)
        
        if self.verbose:
            print(f"  Extracted {len(snps)} SNP records")
        
        return snps
    
    def _parse_row(self, cells: list, num_columns: int) -> Optional[SNPRecord]:
        """Parse a single table row."""
        name = cells[0].get_text(strip=True)
        if not name or name == '&nbsp;':
            return None
        
        haplogroup = ''
        hap_cell = cells[1]
        link = hap_cell.find('a')
        if link:
            haplogroup = link.get_text(strip=True)
        else:
            haplogroup = hap_cell.get_text(strip=True)
        
        record = SNPRecord(
            name=name, haplogroup=haplogroup,
            source_version=self.year, versions_present=[self.year],
        )
        
        year_int = int(self.year) if self.year.isdigit() else 2020
        
        if num_columns >= 7:
            # 2011-2013 format: Name, Haplogroup, Aliases, RefSNP, Y-pos(NCBI36), Y-pos(GRCh37), Mutation
            aliases_text = cells[2].get_text(strip=True)
            if aliases_text and aliases_text != '&nbsp;':
                record.aliases = [a.strip() for a in re.split(r'[;,/]', aliases_text) if a.strip()]
            
            rs_cell = cells[3]
            rs_link = rs_cell.find('a')
            rs_text = rs_link.get_text(strip=True) if rs_link else rs_cell.get_text(strip=True)
            if rs_text and re.match(r'rs\d+', rs_text):
                record.rs_id = rs_text
            
            # Build 36 position (column 4)
            pos36_cell = cells[4]
            pos36_link = pos36_cell.find('a')
            if pos36_link:
                href = pos36_link.get('href', '')
                pos_match = re.search(r'chrY:(\d+)', href)
                if pos_match:
                    record.position_ncbi36 = int(pos_match.group(1))
                else:
                    pos_text = pos36_link.get_text(strip=True)
                    if pos_text.isdigit():
                        record.position_ncbi36 = int(pos_text)
            else:
                pos_text = pos36_cell.get_text(strip=True)
                if pos_text.isdigit():
                    record.position_ncbi36 = int(pos_text)
            
            # Build 37 position (column 5)
            pos37_cell = cells[5]
            pos37_link = pos37_cell.find('a')
            if pos37_link:
                href = pos37_link.get('href', '')
                pos_match = re.search(r'chrY:(\d+)', href)
                if pos_match:
                    record.position_grch37 = int(pos_match.group(1))
                else:
                    pos_text = pos37_link.get_text(strip=True)
                    if pos_text.isdigit():
                        record.position_grch37 = int(pos_text)
            else:
                pos_text = pos37_cell.get_text(strip=True)
                if pos_text.isdigit():
                    record.position_grch37 = int(pos_text)
            
            # Mutation (column 6)
            if len(cells) > 6:
                mut_text = cells[6].get_text(strip=True)
                if mut_text and '->' in mut_text:
                    record.mutation = mut_text
        
        elif num_columns >= 6:
            # 2014+ format: Name, Haplogroup, Aliases, RefSNP, Y-pos(GRCh37), Mutation
            aliases_text = cells[2].get_text(strip=True)
            if aliases_text and aliases_text != '&nbsp;':
                record.aliases = [a.strip() for a in re.split(r'[;,/]', aliases_text) if a.strip()]
            
            rs_cell = cells[3]
            rs_link = rs_cell.find('a')
            rs_text = rs_link.get_text(strip=True) if rs_link else rs_cell.get_text(strip=True)
            if rs_text and re.match(r'rs\d+', rs_text):
                record.rs_id = rs_text
            
            pos_cell = cells[4]
            pos_link = pos_cell.find('a')
            if pos_link:
                href = pos_link.get('href', '')
                pos_match = re.search(r'chrY:(\d+)', href)
                if pos_match:
                    record.position_grch37 = int(pos_match.group(1))
                else:
                    pos_text = pos_link.get_text(strip=True)
                    if pos_text.isdigit():
                        record.position_grch37 = int(pos_text)
            else:
                pos_text = pos_cell.get_text(strip=True)
                if pos_text.isdigit():
                    record.position_grch37 = int(pos_text)
            
            mut_text = cells[5].get_text(strip=True)
            if mut_text and '->' in mut_text:
                record.mutation = mut_text
        
        elif num_columns >= 4:
            # 2006-2008 format: Name, Haplogroup, Citations, RefSNP+Position
            citations_text = cells[2].get_text(strip=True)
            if citations_text and citations_text != '&nbsp;':
                citations = re.split(r';\s*', citations_text)
                record.citations = [{'short': c.strip()} for c in citations if c.strip()]
            
            # 2008 combines rs_id and position: "rs2075181; 7606726"
            rs_cell = cells[3]
            rs_text = rs_cell.get_text(strip=True)
            if rs_text:
                # Try to split rs_id and position
                rs_match = re.match(r'(rs\d+)\s*[;,]\s*(\d+)', rs_text)
                if rs_match:
                    record.rs_id = rs_match.group(1)
                    # This is Build 36 (NCBI36/hg18) for 2008 data
                    record.position_ncbi36 = int(rs_match.group(2))
                elif re.match(r'rs\d+', rs_text):
                    record.rs_id = rs_text
        
        return record

# =============================================================================
# GLOSSARY PARSING
# =============================================================================

def parse_glossary(filepath: str, year: str, verbose: bool = False) -> Dict[str, str]:
    """Parse the Glossary HTML file."""
    if verbose:
        print(f"Parsing Glossary: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    glossary = {}
    
    for span in soup.find_all('span', class_='def'):
        term = span.get_text(strip=True).rstrip(':')
        definition = ''
        for sibling in span.next_siblings:
            if hasattr(sibling, 'name') and sibling.name == 'span':
                break
            if isinstance(sibling, NavigableString):
                definition += str(sibling)
            elif hasattr(sibling, 'get_text'):
                definition += sibling.get_text()
        
        definition = clean_text(definition)
        if term and definition:
            glossary[term] = definition
    
    for p in soup.find_all('p'):
        span = p.find('span', class_='def')
        if span:
            term = span.get_text(strip=True).rstrip(':')
            definition = p.get_text().replace(term + ':', '').replace(term, '')
            definition = clean_text(definition)
            if term and definition and term not in glossary:
                glossary[term] = definition
    
    if verbose:
        print(f"  Extracted {len(glossary)} glossary terms")
    
    return glossary

# =============================================================================
# MAIN PROCESSOR
# =============================================================================

class ISOGGProcessor:
    """Main processor for ISOGG data files."""
    
    def __init__(self, year: str, verbose: bool = False):
        self.year = year
        self.verbose = verbose
        self.tree: Dict[str, HaplogroupNode] = {}
        self.snps: List[SNPRecord] = []
        self.glossary: Dict[str, str] = {}
        self.metadata: Dict[str, Any] = {
            'source': 'ISOGG Y-DNA Haplogroup Tree',
            'version': year,
            'extraction_date': datetime.now().strftime('%Y-%m-%d'),
            'processor_version': '1.0.0',
        }
    
    def process_directory(self, input_dir: str) -> None:
        """Process all ISOGG files in a directory."""
        input_path = Path(input_dir)
        
        if self.verbose:
            print(f"\nProcessing ISOGG {self.year} data from: {input_dir}")
        
        files = {
            'tree_trunk': None,
            'haplogroups': {},
            'snp_index': None,
            'glossary': None,
        }
        
        for filepath in input_path.glob('*.html'):
            file_type = identify_file_type(str(filepath))
            
            if file_type == 'tree_trunk':
                files['tree_trunk'] = filepath
            elif file_type and file_type.startswith('haplogroup_'):
                letter = file_type.split('_')[1]
                files['haplogroups'][letter] = filepath
            elif file_type == 'snp_index':
                files['snp_index'] = filepath
            elif file_type == 'glossary':
                files['glossary'] = filepath
        
        if files['tree_trunk']:
            parser = TreeParser(self.year, self.verbose)
            self.tree = parser.parse_tree_trunk(str(files['tree_trunk']))
            
            for letter, filepath in sorted(files['haplogroups'].items()):
                page_nodes = parser.parse_haplogroup_page(str(filepath), letter)
                for node_id, node in page_nodes.items():
                    if node_id in self.tree:
                        existing = self.tree[node_id]
                        if node.description:
                            existing.description = node.description
                        if node.populations:
                            existing.populations = node.populations
                        if node.frequency_notes:
                            existing.frequency_notes = node.frequency_notes
                        existing_snp_names = {s.name for s in existing.defining_snps}
                        for snp in node.defining_snps:
                            if snp.name not in existing_snp_names:
                                existing.defining_snps.append(snp)
                    else:
                        self.tree[node_id] = node
        
        if files['snp_index']:
            parser = SNPIndexParser(self.year, self.verbose)
            try:
                self.snps = parser.parse(str(files['snp_index']))
            except ValueError as e:
                if self.verbose:
                    print(f"  Warning: {e}")
                    print(f"  (2016+ SNP Index moved to Google Spreadsheet)")
                self.snps = []
        
        if files['glossary']:
            self.glossary = parse_glossary(str(files['glossary']), self.year, self.verbose)
        
        self.metadata['total_haplogroups'] = len(self.tree)
        self.metadata['total_snps'] = len(self.snps)
        self.metadata['glossary_terms'] = len(self.glossary)
    
    def export_json(self, output_dir: str) -> None:
        """Export processed data to JSON files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        tree_output = {
            'metadata': self.metadata,
            'tree': {k: v.to_dict() for k, v in self.tree.items()},
        }
        
        with open(output_path / 'tree.json', 'w', encoding='utf-8') as f:
            json.dump(tree_output, f, indent=2, ensure_ascii=False)
        
        snp_output = {
            'metadata': {**self.metadata, 'record_count': len(self.snps)},
            'snps': [s.to_dict() for s in self.snps],
        }
        
        with open(output_path / 'snp_index.json', 'w', encoding='utf-8') as f:
            json.dump(snp_output, f, indent=2, ensure_ascii=False)
        
        if self.glossary:
            glossary_output = {
                'metadata': {'source': 'ISOGG Glossary', 'version': self.year},
                'terms': self.glossary,
            }
            with open(output_path / 'glossary.json', 'w', encoding='utf-8') as f:
                json.dump(glossary_output, f, indent=2, ensure_ascii=False)
        
        with open(output_path / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        
        if self.verbose:
            print(f"\nExported to: {output_dir}")
            print(f"  - tree.json ({len(self.tree)} haplogroups)")
            print(f"  - snp_index.json ({len(self.snps)} SNPs)")
    
    def export_csv(self, output_dir: str) -> None:
        """Export data to CSV files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        with open(output_path / 'haplogroups.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'name', 'parent_id', 'depth', 'status', 
                           'is_paragroup', 'defining_snps', 'source_version'])
            for node in self.tree.values():
                snps_str = ', '.join(s.name for s in node.defining_snps)
                writer.writerow([node.id, node.name, node.parent_id or '', node.depth,
                               node.status, node.is_paragroup, snps_str, node.source_version])
        
        with open(output_path / 'snps.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'haplogroup', 'status', 'aliases', 'rs_id',
                           'position_ncbi36', 'position_grch37', 'position_grch38', 
                           'mutation', 'source_version'])
            for snp in self.snps:
                aliases_str = ', '.join(snp.aliases) if snp.aliases else ''
                writer.writerow([snp.name, snp.haplogroup, snp.status, aliases_str,
                               snp.rs_id or '', snp.position_ncbi36 or '',
                               snp.position_grch37 or '', snp.position_grch38 or '',
                               snp.mutation or '', snp.source_version])
    
    def export_individual_haplogroups(self, output_dir: str) -> Dict[str, str]:
        """Export individual haplogroup files for this year."""
        tree_dict = {k: v.to_dict() for k, v in self.tree.items()}
        return export_individual_haplogroups(tree_dict, self.year, output_dir, self.verbose)

# =============================================================================
# INDIVIDUAL HAPLOGROUP EXPORT
# =============================================================================

# Combined/meta haplogroups that belong in trunk
TRUNK_HAPLOGROUPS = {
    'Y-Adam', 'BT', 'CT', 'CF', 'DE', 'GHIJK', 'HIJK', 'IJK', 'IJ', 'LT', 
    'NO', 'NOP', 'BR', 'CR',  # Older naming
    'A0-T', 'A0', 'A1',  # Modern A structure
}

# Major haplogroup letters (roots of each tree)
MAJOR_HAPLOGROUPS = set('ABCDEFGHIJKLMNOPQRST')


def get_major_haplogroup_letter(hap_id: str) -> Optional[str]:
    """
    Determine which major haplogroup a subclade belongs to.
    Returns the letter (A-T) or None if it's a trunk/combined haplogroup.
    """
    clean_id = hap_id.rstrip('*')
    
    # Check if it's a combined/trunk haplogroup
    if clean_id in TRUNK_HAPLOGROUPS:
        return None
    
    # Check if it starts with a major haplogroup letter
    if clean_id and clean_id[0] in MAJOR_HAPLOGROUPS:
        return clean_id[0]
    
    return None


def export_individual_haplogroups(tree: Dict[str, Any], year: str, output_dir: str, 
                                   verbose: bool = False) -> Dict[str, str]:
    """
    Export individual haplogroup files, one per major haplogroup + tree trunk.
    
    Creates:
    - individual_haplogroups/TreeTrunk-{year}.json (combined clades + major haplogroup roots)
    - individual_haplogroups/Haplogroup_A-{year}.json (A and all A subclades)
    - individual_haplogroups/Haplogroup_B-{year}.json (B and all B subclades)
    - etc.
    
    The TreeTrunk includes:
    - Combined haplogroups: BR, CR, DE, IJ, NO, BT, CT, CF, Y-Adam, etc.
    - Major haplogroup roots: A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T
    
    Each Haplogroup_X file includes:
    - The root haplogroup (X) with its parent reference
    - All subclades (X*, X1, X1a, X1a1, etc.) with proper parent references
    
    Returns mapping of haplogroup letter to output file path.
    """
    output_path = Path(output_dir) / 'individual_haplogroups'
    output_path.mkdir(parents=True, exist_ok=True)
    
    if verbose:
        print(f"  Exporting individual haplogroup files to: {output_path}")
    
    exported_files = {}
    
    # Group haplogroups by their major letter
    haplogroup_groups: Dict[str, Dict[str, Any]] = defaultdict(dict)
    trunk_nodes = {}
    
    for hap_id, node in tree.items():
        letter = get_major_haplogroup_letter(hap_id)
        
        if letter is None:
            # It's a trunk/combined haplogroup
            trunk_nodes[hap_id] = node
        else:
            # It belongs to a major haplogroup
            haplogroup_groups[letter][hap_id] = node
    
    # Also add major haplogroup roots to trunk (A, B, C, etc.)
    for letter in sorted(haplogroup_groups.keys()):
        # Add the root node (e.g., "A") to trunk if it exists
        if letter in haplogroup_groups[letter]:
            trunk_nodes[letter] = haplogroup_groups[letter][letter]
        # Also add paragroup (e.g., "A*") if it exists
        paragroup = f"{letter}*"
        if paragroup in haplogroup_groups[letter]:
            trunk_nodes[paragroup] = haplogroup_groups[letter][paragroup]
    
    # Build children list for trunk nodes
    trunk_children = defaultdict(list)
    for hap_id, node in trunk_nodes.items():
        parent_id = node.get('parent_id')
        if parent_id and parent_id in trunk_nodes:
            if hap_id not in trunk_children[parent_id]:
                trunk_children[parent_id].append(hap_id)
    
    # Update trunk nodes with children info
    for hap_id in trunk_nodes:
        if hap_id in trunk_children:
            trunk_nodes[hap_id]['children'] = sorted(trunk_children[hap_id])
    
    # Export tree trunk
    trunk_file = output_path / f'TreeTrunk-{year}.json'
    trunk_output = {
        'metadata': {
            'source': 'ISOGG Y-DNA Haplogroup Tree',
            'version': year,
            'type': 'tree_trunk',
            'description': 'Top-level haplogroups including combined clades (BR, CR, DE, etc.) and major haplogroup roots (A, B, C, etc.)',
            'extraction_date': datetime.now().strftime('%Y-%m-%d'),
            'total_nodes': len(trunk_nodes),
            'major_haplogroups': sorted([h for h in trunk_nodes.keys() if h.rstrip('*') in MAJOR_HAPLOGROUPS]),
        },
        'tree': trunk_nodes,
    }
    
    with open(trunk_file, 'w', encoding='utf-8') as f:
        json.dump(trunk_output, f, indent=2, ensure_ascii=False)
    
    exported_files['TreeTrunk'] = str(trunk_file)
    
    if verbose:
        print(f"    TreeTrunk-{year}.json: {len(trunk_nodes)} nodes")
    
    # Export each major haplogroup
    for letter in sorted(haplogroup_groups.keys()):
        nodes = haplogroup_groups[letter]
        
        if not nodes:
            continue
        
        # Find the root node for this haplogroup
        root_id = letter
        root_node = nodes.get(letter)
        
        # Get parent of root from the original tree (for reference to trunk)
        root_parent = root_node.get('parent_id') if root_node else None
        
        # Build children lists within this haplogroup
        hap_children = defaultdict(list)
        for hap_id, node in nodes.items():
            parent_id = node.get('parent_id')
            if parent_id and parent_id in nodes:
                if hap_id not in hap_children[parent_id]:
                    hap_children[parent_id].append(hap_id)
        
        # Update nodes with children info
        for hap_id in nodes:
            if hap_id in hap_children:
                nodes[hap_id]['children'] = sorted(hap_children[hap_id])
        
        hap_file = output_path / f'Haplogroup_{letter}-{year}.json'
        hap_output = {
            'metadata': {
                'source': 'ISOGG Y-DNA Haplogroup Tree',
                'version': year,
                'type': 'haplogroup',
                'major_haplogroup': letter,
                'root_haplogroup': root_id,
                'root_parent': root_parent,
                'extraction_date': datetime.now().strftime('%Y-%m-%d'),
                'total_subclades': len(nodes),
            },
            'tree': nodes,
        }
        
        with open(hap_file, 'w', encoding='utf-8') as f:
            json.dump(hap_output, f, indent=2, ensure_ascii=False)
        
        exported_files[letter] = str(hap_file)
        
        if verbose:
            print(f"    Haplogroup_{letter}-{year}.json: {len(nodes)} subclades")
    
    return exported_files


# =============================================================================
# MERGER
# =============================================================================

def merge_years(year_dirs: List[str], output_dir: str, verbose: bool = False) -> None:
    """Merge multiple years into a master dataset."""
    if verbose:
        print(f"\nMerging {len(year_dirs)} years...")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_trees = {}
    all_snps = {}
    
    for year_dir in sorted(year_dirs):
        year_path = Path(year_dir)
        year = year_path.name
        
        tree_file = year_path / 'tree.json'
        if tree_file.exists():
            with open(tree_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_trees[year] = data.get('tree', {})
        
        snp_file = year_path / 'snp_index.json'
        if snp_file.exists():
            with open(snp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                all_snps[year] = data.get('snps', [])
    
    # Merge trees
    master_tree = {}
    for year in sorted(all_trees.keys()):
        tree = all_trees[year]
        for hap_id, node in tree.items():
            if hap_id not in master_tree:
                master_tree[hap_id] = {
                    **node,
                    'first_appeared': year,
                    'versions_present': [year],
                    'version_history': [{
                        'version': year,
                        'status': node.get('status'),
                        'parent_id': node.get('parent_id'),
                        'defining_snps': node.get('defining_snps', []),
                    }],
                }
            else:
                existing = master_tree[hap_id]
                existing['versions_present'].append(year)
                history_entry = {
                    'version': year,
                    'status': node.get('status'),
                    'parent_id': node.get('parent_id'),
                    'defining_snps': node.get('defining_snps', []),
                }
                existing['version_history'].append(history_entry)
                existing['status'] = node.get('status')
                existing['parent_id'] = node.get('parent_id')
                existing['defining_snps'] = node.get('defining_snps', [])
                existing['children'] = node.get('children', [])
                if node.get('description'):
                    existing['description'] = node['description']
    
    # Merge SNPs
    master_snps = {}
    for year in sorted(all_snps.keys()):
        snps = all_snps[year]
        for snp in snps:
            name = snp.get('name')
            if not name:
                continue
            if name not in master_snps:
                master_snps[name] = {
                    **snp,
                    'first_appeared': year,
                    'versions_present': [year],
                    'version_history': [{
                        'version': year,
                        'haplogroup': snp.get('haplogroup'),
                        'status': snp.get('status'),
                        'position_grch37': snp.get('position_grch37'),
                    }],
                }
            else:
                existing = master_snps[name]
                existing['versions_present'].append(year)
                history_entry = {
                    'version': year,
                    'haplogroup': snp.get('haplogroup'),
                    'status': snp.get('status'),
                    'position_grch37': snp.get('position_grch37'),
                }
                existing['version_history'].append(history_entry)
                for key in ['haplogroup', 'status', 'position_grch37', 'mutation', 'rs_id']:
                    if snp.get(key):
                        existing[key] = snp[key]
                if snp.get('aliases'):
                    existing_aliases = set(existing.get('aliases', []))
                    existing_aliases.update(snp['aliases'])
                    existing['aliases'] = list(existing_aliases)
    
    # Write outputs
    master_tree_output = {
        'metadata': {
            'source': 'ISOGG Y-DNA Haplogroup Tree (Merged)',
            'years_included': sorted(all_trees.keys()),
            'extraction_date': datetime.now().strftime('%Y-%m-%d'),
            'total_haplogroups': len(master_tree),
        },
        'tree': master_tree,
    }
    
    with open(output_path / 'master_tree.json', 'w', encoding='utf-8') as f:
        json.dump(master_tree_output, f, indent=2, ensure_ascii=False)
    
    master_snps_output = {
        'metadata': {
            'source': 'ISOGG SNP Index (Merged)',
            'years_included': sorted(all_snps.keys()),
            'extraction_date': datetime.now().strftime('%Y-%m-%d'),
            'total_snps': len(master_snps),
        },
        'snps': list(master_snps.values()),
    }
    
    with open(output_path / 'master_snps.json', 'w', encoding='utf-8') as f:
        json.dump(master_snps_output, f, indent=2, ensure_ascii=False)
    
    if verbose:
        print(f"Merged output written to: {output_dir}")
        print(f"  - master_tree.json ({len(master_tree)} haplogroups)")
        print(f"  - master_snps.json ({len(master_snps)} SNPs)")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='ISOGG Y-DNA Haplogroup Tree Data Processor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument('--year', type=str, help='ISOGG year to process (e.g., 2006, 2014)')
    parser.add_argument('--input', '-i', type=str, required=True, help='Input directory')
    parser.add_argument('--output', '-o', type=str, required=True, help='Output directory')
    parser.add_argument('--merge', action='store_true', help='Merge multiple year directories')
    parser.add_argument('--csv', action='store_true', help='Also export to CSV format')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.merge:
        input_path = Path(args.input)
        year_dirs = [str(d) for d in input_path.iterdir() if d.is_dir() and d.name.isdigit()]
        if not year_dirs:
            print("Error: No year directories found in input path")
            sys.exit(1)
        merge_years(year_dirs, args.output, args.verbose)
    else:
        if not args.year:
            for f in Path(args.input).glob('*.html'):
                year = detect_year(str(f))
                if year:
                    args.year = year
                    break
        
        if not args.year:
            print("Error: Could not detect year. Please specify with --year")
            sys.exit(1)
        
        processor = ISOGGProcessor(args.year, args.verbose)
        processor.process_directory(args.input)
        processor.export_json(args.output)
        
        if args.csv:
            processor.export_csv(args.output)
    
    print("\nDone!")


if __name__ == '__main__':
    main()
