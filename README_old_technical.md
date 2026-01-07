# ISOGG Y-DNA Haplogroup Tree Data Processor

## A Comprehensive Guide for Extracting, Parsing, and Merging ISOGG Y-DNA Data

**Version:** 1.0.0  
**Author:** Maxim Magder  
**Date:** January 2026  
**Purpose:** Convert archived ISOGG HTML pages (2006-2017+) into clean, machine-parseable JSON

---

## Table of Contents

1. [Overview](#1-overview)
2. [Understanding ISOGG Data Structure](#2-understanding-isogg-data-structure)
3. [File Inventory by Year](#3-file-inventory-by-year)
4. [HTML Structure Analysis](#4-html-structure-analysis)
5. [JSON Schema Specification](#5-json-schema-specification)
6. [Processing Pipeline](#6-processing-pipeline)
7. [Code Reference](#7-code-reference)
8. [Usage Instructions](#8-usage-instructions)
9. [Troubleshooting](#9-troubleshooting)
10. [Version Differences](#10-version-differences)

---

## 1. Overview

### 1.1 What This Does

This processor converts archived ISOGG (International Society of Genetic Genealogy) Y-DNA Haplogroup Tree HTML pages into structured JSON format. The output enables:

- **Programmatic querying** of Y-DNA haplogroup hierarchies
- **SNP lookups** with genomic positions, aliases, and haplogroup assignments
- **Cross-version comparison** to track phylogenetic tree evolution over time
- **Population genetics research** with clean, normalized data

### 1.2 Input Files (Per Year)

Each ISOGG year typically contains these HTML files:

| File Type | Filename Pattern | Content |
|-----------|------------------|---------|
| **Tree Trunk** | `*TreeTrunk*.html` | Main haplogroup hierarchy (A through R) |
| **Haplogroup Pages** | `*HapgrpA*.html`, `*HapgrpB*.html`, etc. | Detailed subclades for each major haplogroup |
| **SNP Index** | `*SNP_Index*.html` | Complete SNP database with positions and metadata |
| **Glossary** | `*Glossary*.html` | Term definitions |
| **Papers Cited** | `*Papers*.html` or `*All_Papers*.html` | Bibliography |
| **Listing Criteria** | `*Requirements*.html` or `*Criteria*.html` | SNP inclusion rules |
| **Main Index** | `index*.html` or `Main*.html` | Version info and links |

### 1.3 Output Structure

```
output/
├── individual_years/
│   ├── 2006/
│   │   ├── tree.json                      # Complete haplogroup tree
│   │   ├── snp_index.json                 # All SNPs with metadata
│   │   ├── glossary.json                  # Term definitions
│   │   ├── metadata.json                  # Version info
│   │   ├── haplogroups.csv                # Flat haplogroup export
│   │   ├── snps.csv                       # Flat SNP export
│   │   └── individual_haplogroups/        # Per-haplogroup files
│   │       ├── TreeTrunk-2006.json        # Top-level clades (BR, CR, DE, etc.)
│   │       ├── Haplogroup_A-2006.json     # All A subclades
│   │       ├── Haplogroup_B-2006.json     # All B subclades
│   │       ├── Haplogroup_C-2006.json
│   │       └── ... (through R)
│   ├── 2007/
│   │   └── ...
│   └── 2017/
│       └── ...
├── merged/
│   ├── master_tree.json        # All years merged with version tracking
│   ├── master_snps.json        # All SNPs across all years
│   └── evolution_log.json      # Changes between versions
└── exports/
    ├── all_haplogroups.csv     # Flat export for spreadsheets
    └── all_snps.csv            # SNP data in tabular format
```

**Individual Haplogroup Files:**

Each year directory contains an `individual_haplogroups/` subfolder with:

- `TreeTrunk-{year}.json` - Contains combined/root haplogroups (Y-Adam, BR, CR, DE, IJ, NO, BT, CT, CF, etc.)
- `Haplogroup_{letter}-{year}.json` - Contains all subclades for each major haplogroup (A through T)

---

## 2. Understanding ISOGG Data Structure

### 2.1 Haplogroup Naming Convention

Y-DNA haplogroups follow a hierarchical naming scheme:

```
A                    # Major haplogroup (single letter)
├── A*               # Paragroup (derived for A, ancestral for all subclades)
├── A1               # First-level subclade
│   ├── A1*          # Paragroup of A1
│   ├── A1a          # Second-level subclade
│   │   ├── A1a1     # Third-level subclade
│   │   └── A1a2
│   └── A1b
│       ├── A1b1
│       │   ├── A1b1a
│       │   │   └── A1b1a1
│       │   └── A1b1b
│       └── BT       # Combined haplogroup (special case)
└── A2
    └── ...
```

**Key Points:**

- **Paragroups (`*`)**: Individuals positive for parent SNP but negative for all known child SNPs
- **Combined haplogroups**: `BR`, `CR`, `DE`, `IJ`, `NO`, `BT` represent branching points
- **Depth increases** with each alphanumeric addition (A → A1 → A1a → A1a1 → A1a1a)

### 2.2 SNP Classification System

ISOGG uses CSS classes to categorize SNPs:

| Status | CSS Class | Meaning |
|--------|-----------|---------|
| **Normal** | `.snp` or no class | Established, well-confirmed SNP |
| **New** | `.snp-new` | Added since previous year's tree |
| **Confirmed** | `.snp-conf` | Confirmed within subclade but awaiting full phylogenetic placement |
| **Provisional** | `.snp-prov` | Tentatively placed, awaiting verification |
| **Private** | `.snp-priv` | Observed in single lineage or closely related individuals |
| **Investigation** | `.snp-inv` | Under active research (2014+ only) |

### 2.3 SNP Naming Conventions

SNPs have various naming prefixes based on their source:

| Prefix | Source |
|--------|--------|
| M | Stanford (Underhill lab) |
| P | Arizona (Hammer lab) |
| L | Family Tree DNA / Walk Through the Y |
| S | Ethnoancestry / ScotlandsDNA |
| V | Sardinian project |
| Z | Full Genomes Corp |
| PF | 1000 Genomes Project |
| CTS | Complete Genomics |
| AF | Albert Perry (A00 discovery) |
| BY | Big Y (FTDNA) |
| FGC | Full Genomes Corp |
| YP | YFull |

**Aliases**: Many SNPs have multiple names (e.g., `M207` = `UTY2`, `L1085` = `AF3`)

---

## 3. File Inventory by Year

### 3.1 2006 Files (Original Format)

```
ISOGG_2006_Y-DNA_Haplogroup_Tree_Trunk.html
ISOGG_2006_Y-DNA_Haplogroup_A.html
ISOGG_2006_Y-DNA_Haplogroup_B.html
... (through R)
ISOGG_2006_Y-DNA_SNP_Index.html
ISOGG_2006_Y-DNA_Glossary.html
ISOGG_2006_Y-DNA_Papers_Cited.html
ISOGG_2006_Y-DNA_Listing_Criteria.html
```

**Characteristics:**

- Encoding: `ISO-8859-1`
- Indentation: Corrupted Unicode (`ï¿½`) + `&nbsp;` sequences
- SNP Index: 4 columns (SNP, Haplogroup, Comments, RefSNP ID)
- No genomic positions

### 3.2 2014 Files (Modernized Format)

```
2014_index14.html
2014_ISOGG_YDNATreeTrunk14.html
2014_ISOGG_HapgrpA14.html
2014_ISOGG_HapgrpB14.html
... (through R)
2014_ISOGG_YDNA_SNP_Index14.html
2014_ISOGG_Glossary14.html
2014_ISOGG_All_Papers14.html
2014_ISOGG_SNP_Requirements14.html
```

**Characteristics:**

- Encoding: `UTF-8`
- Indentation: Unicode bullets (`&#8226;` = •) with `<span class="light">` / `<span class="dark">`
- SNP Index: 6 columns (adds Other Names, Y-position, Mutation)
- Includes GRCh37 (hg19) genomic coordinates
- External CSS file (`IsoggStyle.css`)

### 3.3 Identifying Year-Specific Patterns

When processing a new year, check:

1. **Encoding declaration**: `<meta charset="utf-8">` vs `charset=ISO-8859-1`
2. **Indentation markers**: Look for `ï¿½`, `&#8226;`, `•`, or `<span class="light">`
3. **SNP Index columns**: Count `<td>` elements in header row
4. **CSS**: Inline `<style>` vs external `<link rel="stylesheet">`
5. **File naming**: Year suffix pattern (`06`, `07`, `14`, etc.)

---

## 4. HTML Structure Analysis

### 4.1 Tree Trunk Structure

The Tree Trunk page contains the top-level hierarchy. Each haplogroup line follows this pattern:

**2006 Format:**

```html
<!-- Comment indicating haplogroup and indent level -->
<! A3b2 - indent 4>
<font color="#DEDEDE">ï¿½&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ï¿½&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
ï¿½&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ï¿½&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</font>
<span class="hap"><b>A3b2</b></span>&nbsp;&nbsp;&nbsp;M13, M63, M127, M202, M219,
<span class="snp-new">M305</span><br>
```

**2014 Format:**

```html
<!--A1b1- indent 4-->
<span class="light">&#8226;&nbsp;&#8226;&nbsp;&#8226;&nbsp;&#8226;</span>
<span class="hap"><a class=bl href="ISOGG_HapgrpA14.html"><b>A1b1</b></a></span>&nbsp;&nbsp;&nbsp;<b>L419/PF712</b><br>
```

### 4.2 Parsing Algorithm

```
1. Find all lines containing <span class="hap">
2. For each line:
   a. Calculate depth by counting indentation markers
   b. Extract haplogroup name from <span class="hap"><b>NAME</b></span>
   c. Extract SNPs from text after </span> and before <br>
   d. Classify each SNP by its CSS class
   e. Check for link to detailed haplogroup page
3. Build parent-child relationships using depth stack
```

**Depth Calculation:**

```python
# 2006: Count "ï¿½" occurrences
depth_2006 = line.count('ï¿½')

# 2014: Count bullet characters
depth_2014 = line.count('&#8226;') or line.count('•')

# Alternative 2014: Count spans
import re
spans = re.findall(r'<span class="(light|dark)">', line)
depth_2014 = len(spans)  # Each span represents one level
```

### 4.3 Haplogroup Page Structure

Individual haplogroup pages (e.g., `HapgrpA14.html`) contain:

1. **Full subclade tree** for that haplogroup
2. **Population descriptions** (geographic distribution, frequencies)
3. **References** (citations for that specific lineage)
4. **Contact information** (haplogroup project administrators)

The parsing is similar to Tree Trunk but goes deeper into the hierarchy.

### 4.4 SNP Index Table Structure

**2006 Table:**

```html
<table Border="2" Cellpadding=4>
<tr>
    <td><b>SNP</b></td>
    <td><b>Hapgrp.</b></td>
    <td><b>Comments</b></td>
    <td><b>RefSNP ID</b></td>
</tr>
<tr>
    <td>M91</td>
    <td><a href="ISOGG_HapgrpA06.html">A</a></td>
    <td>Underhill et al (2000); YCC (2002); ...</td>
    <td>rs2032652</td>
</tr>
```

**2014 Table:**

```html
<table class="bord">
<tr>
    <td><b>SNP</b></td>
    <td><b>Haplogroup</b></td>
    <td><b>Other Names</b></td>
    <td><b>RefSNP ID</b></td>
    <td><b>Y-position</b> (GRCh37)</td>
    <td><b>Mutation</b></td>
</tr>
<tr>
    <td>M91</td>
    <td><a href="ISOGG_HapgrpA14.html">BT</a></td>
    <td>&nbsp;&nbsp;&nbsp;</td>
    <td><a href="http://ncbi...">rs2032652</a></td>
    <td><a href="http://ybrowse...">8608515</a></td>
    <td>G->A</td>
</tr>
```

---

## 5. JSON Schema Specification

### 5.1 Haplogroup Node Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "string",
      "description": "Haplogroup identifier (e.g., 'A3b2', 'R1b1a1a2a1a1')"
    },
    "name": {
      "type": "string",
      "description": "Display name (usually same as id)"
    },
    "parent_id": {
      "type": ["string", "null"],
      "description": "Parent haplogroup id, null for root"
    },
    "depth": {
      "type": "integer",
      "minimum": 0,
      "description": "Tree depth (0 = root)"
    },
    "status": {
      "type": "string",
      "enum": ["normal", "new", "renamed", "nyi"],
      "description": "Clade status from CSS class"
    },
    "is_paragroup": {
      "type": "boolean",
      "description": "True if name ends with '*'"
    },
    "defining_snps": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "status": {
            "type": "string",
            "enum": ["normal", "new", "confirmed", "provisional", "private", "investigation"]
          },
          "is_representative": {
            "type": "boolean",
            "description": "True if displayed in bold (primary defining SNP)"
          }
        }
      }
    },
    "description": {
      "type": ["string", "null"],
      "description": "Population/geographic description if available"
    },
    "populations": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Associated populations/regions"
    },
    "frequency_notes": {
      "type": ["string", "null"],
      "description": "Frequency information if available"
    },
    "detail_page": {
      "type": ["string", "null"],
      "description": "Link to detailed haplogroup page"
    },
    "children": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Child haplogroup ids"
    },
    "source_version": {
      "type": "string",
      "description": "ISOGG year this data comes from"
    },
    "revision_date": {
      "type": ["string", "null"],
      "format": "date",
      "description": "Last revision date for this entry"
    }
  },
  "required": ["id", "name", "depth", "defining_snps", "source_version"]
}
```

### 5.2 SNP Record Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Primary SNP name"
    },
    "aliases": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Alternative names for this SNP"
    },
    "haplogroup": {
      "type": "string",
      "description": "Assigned haplogroup"
    },
    "haplogroup_path": {
      "type": "array",
      "items": { "type": "string" },
      "description": "Full path from root (e.g., ['Y-Adam', 'A', 'A1', 'A1b'])"
    },
    "status": {
      "type": "string",
      "enum": ["normal", "new", "confirmed", "provisional", "private", "investigation"]
    },
    "rs_id": {
      "type": ["string", "null"],
      "pattern": "^rs[0-9]+$",
      "description": "dbSNP reference ID"
    },
    "position_grch37": {
      "type": ["integer", "null"],
      "description": "Genomic position on Y chromosome (GRCh37/hg19)"
    },
    "position_grch38": {
      "type": ["integer", "null"],
      "description": "Genomic position on Y chromosome (GRCh38/hg38) if available"
    },
    "mutation": {
      "type": ["string", "null"],
      "pattern": "^[ACGT]->[ACGT]$",
      "description": "Base change (e.g., 'G->A')"
    },
    "ancestral_allele": {
      "type": ["string", "null"],
      "description": "Ancestral (negative) allele"
    },
    "derived_allele": {
      "type": ["string", "null"],
      "description": "Derived (positive) allele"
    },
    "citations": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "short": { "type": "string" },
          "full": { "type": ["string", "null"] },
          "doi": { "type": ["string", "null"] },
          "url": { "type": ["string", "null"] }
        }
      }
    },
    "source_version": {
      "type": "string"
    },
    "versions_present": {
      "type": "array",
      "items": { "type": "string" },
      "description": "All ISOGG versions where this SNP appears"
    },
    "version_history": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "version": { "type": "string" },
          "haplogroup": { "type": "string" },
          "status": { "type": "string" },
          "position": { "type": ["integer", "null"] }
        }
      },
      "description": "Track changes across versions"
    }
  },
  "required": ["name", "haplogroup", "source_version"]
}
```

### 5.3 Complete Tree File Schema

```json
{
  "metadata": {
    "source": "ISOGG Y-DNA Haplogroup Tree",
    "version": "2014",
    "extraction_date": "2026-01-06",
    "revision_date": "2014-10-25",
    "total_haplogroups": 2847,
    "total_snps": 15234,
    "encoding": "UTF-8",
    "processor_version": "1.0.0"
  },
  "tree": {
    "Y-Adam": {
      "id": "Y-Adam",
      "name": "Root",
      "parent_id": null,
      "depth": 0,
      "defining_snps": [],
      "children": ["A00", "A0-T"]
    },
    "A00": {
      "id": "A00",
      "name": "A00",
      "parent_id": "Y-Adam",
      "depth": 1,
      "defining_snps": [
        {"name": "AF6", "status": "normal", "is_representative": true},
        {"name": "L1284", "status": "normal", "is_representative": true}
      ],
      "children": ["A00a", "A00b"]
    }
  },
  "haplogroup_index": {
    "A00": "Y-Adam.A00",
    "A0-T": "Y-Adam.A0-T",
    "A0": "Y-Adam.A0-T.A0"
  }
}
```

---

## 6. Processing Pipeline

### 6.1 Pipeline Overview

```
┌─────────────────┐
│  HTML Files     │
│  (per year)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  1. CLEAN       │  Fix encoding, remove boilerplate
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. PARSE       │  Extract tree structure, SNPs, metadata
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. NORMALIZE   │  Standardize naming, resolve aliases
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. VALIDATE    │  Check parent-child relationships
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│  5a. EXPORT     │     │  5b. MERGE      │
│  (per year)     │     │  (all years)    │
└─────────────────┘     └─────────────────┘
```

### 6.2 Step 1: Cleaning

```python
def clean_html(content: str, year: str) -> str:
    """
    Clean raw HTML content for parsing.
    
    Operations:
    1. Normalize encoding to UTF-8
    2. Fix corrupted characters (ï¿½ → •)
    3. Remove Google Analytics scripts
    4. Remove Cloudflare scripts
    5. Strip navigation boilerplate
    6. Normalize whitespace
    """
    
    # Fix 2006-era encoding issues
    content = content.replace('ï¿½', '•')
    content = content.replace('Ã', '')  # Common encoding artifact
    
    # Remove tracking scripts
    content = re.sub(r'<script>.*?ga\(.*?</script>', '', content, flags=re.DOTALL)
    content = re.sub(r'<script.*?cloudflare.*?</script>', '', content, flags=re.DOTALL)
    
    # Normalize HTML entities
    content = html.unescape(content)
    
    return content
```

### 6.3 Step 2: Parsing

**Tree Extraction:**

```python
def parse_tree_line(line: str, year: str) -> dict:
    """
    Parse a single haplogroup line from the tree.
    
    Returns:
    {
        'depth': int,
        'haplogroup': str,
        'status': str,
        'snps': [{'name': str, 'status': str, 'is_representative': bool}],
        'detail_link': str or None
    }
    """
    
    # Calculate depth
    if year <= '2008':
        depth = line.count('ï¿½') or line.count('•')
    else:
        depth = len(re.findall(r'&#8226;|•', line))
    
    # Extract haplogroup name
    hap_match = re.search(r'<span class="hap[^"]*"[^>]*>.*?<b>([^<]+)</b>', line)
    haplogroup = hap_match.group(1) if hap_match else None
    
    # Determine clade status
    if 'hap-new' in line:
        status = 'new'
    elif 'hap-ren' in line:
        status = 'renamed'
    elif 'hap-nyi' in line:
        status = 'nyi'
    else:
        status = 'normal'
    
    # Extract SNPs
    snps = extract_snps(line)
    
    # Check for detail page link
    link_match = re.search(r'href="([^"]*Hapgrp[^"]*\.html)"', line)
    detail_link = link_match.group(1) if link_match else None
    
    return {
        'depth': depth,
        'haplogroup': haplogroup,
        'status': status,
        'snps': snps,
        'detail_link': detail_link
    }


def extract_snps(line: str) -> list:
    """
    Extract SNPs from a haplogroup line.
    
    Handles:
    - Normal SNPs (plain text)
    - New SNPs (<span class="snp-new">)
    - Confirmed SNPs (<span class="snp-conf">)
    - Provisional SNPs (<span class="snp-prov">)
    - Private SNPs (<span class="snp-priv">)
    - Representative SNPs (<b>SNP</b>)
    - Aliases (SNP1/SNP2 or SNP1 (SNP2))
    """
    
    snps = []
    
    # Find the SNP portion (after haplogroup span, before <br>)
    snp_section = re.search(r'</span>\s*&nbsp;[^<]*(.+?)(?:<br|$)', line, re.DOTALL)
    if not snp_section:
        return snps
    
    snp_text = snp_section.group(1)
    
    # Parse SNP spans and plain text
    # ... (detailed parsing logic)
    
    return snps
```

**SNP Index Extraction:**

```python
def parse_snp_index(filepath: str, year: str) -> list:
    """
    Parse the SNP Index HTML table into a list of SNP records.
    """
    
    soup = BeautifulSoup(open(filepath), 'html.parser')
    table = soup.find('table', class_='bord') or soup.find('table', {'border': True})
    
    snps = []
    rows = table.find_all('tr')[1:]  # Skip header row
    
    for row in rows:
        cells = row.find_all('td')
        
        if year >= '2014':
            # 6-column format
            snp = {
                'name': cells[0].get_text(strip=True),
                'haplogroup': extract_haplogroup_from_link(cells[1]),
                'aliases': parse_aliases(cells[2].get_text(strip=True)),
                'rs_id': extract_rs_id(cells[3]),
                'position_grch37': extract_position(cells[4]),
                'mutation': cells[5].get_text(strip=True) or None
            }
        else:
            # 4-column format (2006-2013)
            snp = {
                'name': cells[0].get_text(strip=True),
                'haplogroup': extract_haplogroup_from_link(cells[1]),
                'citations_raw': cells[2].get_text(strip=True),
                'rs_id': extract_rs_id(cells[3]),
                'position_grch37': None,
                'mutation': None
            }
        
        snps.append(snp)
    
    return snps
```

### 6.4 Step 3: Normalization

```python
def normalize_haplogroup_name(name: str) -> str:
    """
    Standardize haplogroup naming.
    
    Examples:
    - 'A3b2*' → 'A3b2*' (preserve paragroup marker)
    - 'A-M91' → 'A' (remove SNP suffix)
    - 'R1b1a1a2a1a1' → 'R1b1a1a2a1a1' (preserve long names)
    """
    
    # Remove SNP-style suffixes (A-M91 → A)
    name = re.sub(r'-[A-Z][0-9]+$', '', name)
    
    # Normalize whitespace
    name = name.strip()
    
    return name


def resolve_snp_aliases(snps: list) -> dict:
    """
    Build alias resolution map.
    
    Input: List of SNP records with 'aliases' field
    Output: {alias: primary_name} mapping
    """
    
    alias_map = {}
    
    for snp in snps:
        primary = snp['name']
        for alias in snp.get('aliases', []):
            alias_map[alias] = primary
    
    return alias_map
```

### 6.5 Step 4: Validation

```python
def validate_tree(tree: dict) -> list:
    """
    Validate tree structure integrity.
    
    Checks:
    1. All children reference valid parent
    2. No circular references
    3. Depth values are consistent
    4. All haplogroups have at least one defining SNP (except paragroups)
    """
    
    errors = []
    
    for hap_id, node in tree.items():
        # Check parent exists
        parent_id = node.get('parent_id')
        if parent_id and parent_id not in tree:
            errors.append(f"Invalid parent '{parent_id}' for '{hap_id}'")
        
        # Check depth consistency
        if parent_id:
            parent_depth = tree[parent_id]['depth']
            if node['depth'] != parent_depth + 1:
                errors.append(f"Depth mismatch for '{hap_id}': expected {parent_depth + 1}, got {node['depth']}")
        
        # Check children exist
        for child_id in node.get('children', []):
            if child_id not in tree:
                errors.append(f"Invalid child '{child_id}' for '{hap_id}'")
    
    return errors
```

### 6.6 Step 5: Merging Multiple Years

```python
def merge_trees(trees: dict) -> dict:
    """
    Merge multiple year trees into a master tree with version tracking.
    
    Args:
        trees: {'2006': tree_dict, '2014': tree_dict, ...}
    
    Returns:
        Master tree with version_history for each node
    """
    
    master = {}
    
    # Process years in chronological order
    for year in sorted(trees.keys()):
        tree = trees[year]
        
        for hap_id, node in tree.items():
            if hap_id not in master:
                # New haplogroup
                master[hap_id] = {
                    **node,
                    'first_appeared': year,
                    'versions_present': [year],
                    'version_history': [{
                        'version': year,
                        'status': node['status'],
                        'parent_id': node.get('parent_id'),
                        'defining_snps': node['defining_snps']
                    }]
                }
            else:
                # Existing haplogroup - track changes
                existing = master[hap_id]
                existing['versions_present'].append(year)
                
                # Record any changes
                history_entry = {
                    'version': year,
                    'status': node['status'],
                    'parent_id': node.get('parent_id'),
                    'defining_snps': node['defining_snps']
                }
                
                # Detect changes
                prev = existing['version_history'][-1]
                if (node['status'] != prev['status'] or 
                    node.get('parent_id') != prev['parent_id'] or
                    node['defining_snps'] != prev['defining_snps']):
                    history_entry['changes'] = detect_changes(prev, node)
                
                existing['version_history'].append(history_entry)
                
                # Update to latest data
                existing.update({
                    'status': node['status'],
                    'parent_id': node.get('parent_id'),
                    'defining_snps': node['defining_snps'],
                    'children': node.get('children', [])
                })
    
    return master
```

---

## 7. Code Reference

### 7.1 Main Processor Script

See `isogg_processor.py` for the complete implementation.

### 7.2 Key Functions

| Function | Purpose |
|----------|---------|
| `process_year(year, input_dir)` | Process all files for a single year |
| `parse_tree_trunk(filepath)` | Extract main tree hierarchy |
| `parse_haplogroup_page(filepath)` | Extract detailed subclade tree |
| `parse_snp_index(filepath)` | Extract SNP database |
| `merge_haplogroup_trees(trunk, pages)` | Combine trunk with detail pages |
| `build_parent_child_relationships(nodes)` | Construct tree from flat list |
| `export_json(data, filepath)` | Write JSON output |
| `export_csv(data, filepath)` | Write CSV export |

### 7.3 Configuration

```python
CONFIG = {
    'encoding_fixes': {
        'ï¿½': '•',
        'â€™': "'",
        'â€"': '—',
        'â€œ': '"',
        'â€': '"'
    },
    'snp_status_classes': {
        'snp-new': 'new',
        'snp-conf': 'confirmed',
        'snp-prov': 'provisional',
        'snp-priv': 'private',
        'snp-inv': 'investigation'
    },
    'clade_status_classes': {
        'hap-new': 'new',
        'hap-ren': 'renamed',
        'hap-nyi': 'nyi'
    }
}
```

---

## 8. Usage Instructions

### 8.1 Processing a Single Year

```bash
# Basic usage
python isogg_processor.py --year 2006 --input ./2006_files/ --output ./output/

# With verbose logging
python isogg_processor.py --year 2006 --input ./2006_files/ --output ./output/ --verbose

# Specific file types only
python isogg_processor.py --year 2006 --input ./2006_files/ --output ./output/ --types tree,snps
```

### 8.2 Processing Multiple Years

```bash
# Process all years in a directory
python isogg_processor.py --batch --input ./all_years/ --output ./output/

# Merge after processing
python isogg_processor.py --merge --input ./output/individual_years/ --output ./output/merged/
```

### 8.3 File Organization

**Input directory structure:**

```
input/
├── 2006/
│   ├── ISOGG_2006_Y-DNA_Haplogroup_Tree_Trunk.html
│   ├── ISOGG_2006_Y-DNA_Haplogroup_A.html
│   └── ...
├── 2007/
│   └── ...
└── 2014/
    └── ...
```

**Or flat structure with year prefixes:**

```
input/
├── ISOGG_2006_Y-DNA_Haplogroup_Tree_Trunk.html
├── 2014_ISOGG_YDNATreeTrunk14.html
└── ...
```

### 8.4 For Claude (Processing Instructions)

When asked to process ISOGG files:

1. **Identify the year** from filenames or content
2. **Determine the encoding** (ISO-8859-1 for 2006-2008, UTF-8 for 2009+)
3. **Locate key files**: Tree Trunk, Haplogroup pages, SNP Index
4. **Parse in order**: Tree Trunk first (establishes hierarchy), then Haplogroup pages (adds depth), then SNP Index (adds metadata)
5. **Validate output**: Check parent-child relationships, SNP counts
6. **Export**: Generate JSON for each file type, then merge

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue: Corrupted characters in output**

```
Symptom: "ï¿½" or "Â" appear in JSON
Solution: Apply encoding fixes before parsing
```

**Issue: Missing haplogroups in tree**

```
Symptom: Child references non-existent parent
Solution: Ensure Tree Trunk is parsed before Haplogroup pages
```

**Issue: Duplicate SNPs**

```
Symptom: Same SNP appears multiple times with different haplogroups
Solution: This may be valid (SNP defines multiple levels); check if same SNP at different tree depths
```

**Issue: SNP Index has more entries than tree**

```
Symptom: SNPs in index not found in tree
Solution: Normal - Index includes investigation/removed SNPs; filter by status if needed
```

### 9.2 Validation Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid parent` | Parent haplogroup not in tree | Check Tree Trunk parsing |
| `Depth mismatch` | Incorrect indent counting | Verify depth calculation for that year's format |
| `Circular reference` | A is parent of B, B is parent of A | Data error - check source HTML |
| `No defining SNPs` | Haplogroup has no SNPs listed | May be valid for combined haplogroups (BR, CR, etc.) |

---

## 10. Version Differences

### 10.1 Major Changes by Year

| Year | Key Changes |
|------|-------------|
| **2006** | Original format, ISO-8859-1, 4-column SNP index |
| **2007** | Minor updates, same format |
| **2008** | Last year of original format |
| **2009** | Transition to UTF-8 begins |
| **2010** | New haplogroup A structure (A0, A1 split) |
| **2012** | Major tree reorganization |
| **2013** | A00 discovered and added |
| **2014** | 6-column SNP index with positions, HTML5/CSS modernization |
| **2015** | Continued expansion |
| **2016** | Big Y data integration |
| **2017** | Further NGS integration |

### 10.2 Haplogroup Renaming Events

Track these when merging:

```
2006 → 2014 Major Changes:
- A (M91) → BT (M91)  [M91 moved down tree]
- A1 (M31) → A1a (M31)
- A2 (M6) → A1b1a (M6) [major restructure]
- New root: A00, A0-T, A0, A1
```

### 10.3 SNP Position Reference Genome

| Years | Reference Build |
|-------|-----------------|
| 2006-2013 | No positions |
| 2014-2018 | GRCh37 (hg19) |
| 2019+ | GRCh38 (hg38) may be available |

### 10.4 SNPs with Extensions (Multi-Position SNPs)

Some SNPs appear in multiple haplogroups or have multiple Y-chromosome positions. ISOGG uses extension notation to distinguish these:

**Haplogroup Extensions (`.1`, `.2` notation):**

SNPs found in more than one haplogroup used to be given names ending in `a` or `b`. More recent papers and ISOGG trees show these SNPs ending in `.1` or `.2`.

| Current Notation | Former Notation |
|-----------------|-----------------|
| `12f2.1` | `12f2a` |
| `12f2.2` | `12f2b` |

**Position Extensions (`_1`, `_2` notation):**

SNPs that appear in a single haplogroup but have multiple Y-chromosome positions are shown with underscore extensions:

| Example | Meaning |
|---------|---------|
| `P7_1` | First Y-position for P7 |
| `P7_2` | Second Y-position for P7 |
| `P7_3` | Third Y-position for P7 |

**Note:** Earlier ISOGG tree versions show both naming conventions, but current trees use only the modern notation (`.1/.2` for haplogroup extensions, `_1/_2` for position extensions).

---

## 11. Known Issues & Errata

### 11.1 ISOGG 2018 China Users Data File

**Issue:** The landing page for the China users branch (`HaplogroupA18.html`) lists a broken download link for the Excel data file.

| Field | Value |
|-------|-------|
| Haplogroup | A |
| Region/Userbase | China Users (2018 Tree) |
| Official Page | `HaplogroupA18.html` |
| Broken URL | `https://isogg.org/tree/2018/HaplogroupAdata.xlsx` (404 Error) |
| Corrected URL | `https://isogg.org/tree/2018/HaplogroupAData.xlsx` |
| Issue | Case-sensitivity mismatch on "data" vs "Data" |

**Citation:**
> International Society of Genetic Genealogy (2018). Y-DNA Haplogroup A (for China users). Retrieved from the 2018 Main Tree Index: <https://isogg.org/tree/2018/HaplogroupA18.html>

### 11.2 2016-2017 SNP Index

Starting in 2016, the SNP Index was moved from an HTML table to a Google Spreadsheet. The HTML files for these years no longer contain the full SNP data. The spreadsheet data is available separately in the `ISOGG_dna-differences_and_other_info/Haplogroup Data 2016/` and `Haplogroup Data 2017/` directories as Excel files.

---

## Appendix A: Quick Reference Card

```
HAPLOGROUP LINE PATTERN:
[indent markers] <span class="hap[-status]"><b>NAME</b></span> SNP1, SNP2, <span class="snp-new">SNP3</span><br>

INDENT MARKERS:
- 2006: ï¿½ (corrupted) or font color="#DEDEDE"
- 2014: • or &#8226; inside <span class="light">

SNP STATUSES:
- (none)     → normal
- snp-new    → new
- snp-conf   → confirmed
- snp-prov   → provisional
- snp-priv   → private
- snp-inv    → investigation

CLADE STATUSES:
- hap        → normal
- hap-new    → added
- hap-ren    → renamed
- hap-nyi    → SNP not yet identified

OUTPUT JSON:
{
  "metadata": {...},
  "tree": {
    "HAPLOGROUP_ID": {
      "id": "...",
      "parent_id": "...",
      "depth": N,
      "defining_snps": [...],
      "children": [...]
    }
  }
}
```

---

## Appendix B: Regex Patterns

```python
# Haplogroup name extraction
HAP_NAME = r'<span class="hap[^"]*"[^>]*>(?:<a[^>]*>)?<b>([^<]+)</b>'

# SNP list extraction (after haplogroup)
SNP_SECTION = r'</b>(?:</a>)?</span>\s*&nbsp;([^<]+(?:<span[^>]*>[^<]+</span>[^<]*)*)'

# Individual SNP with status
SNP_WITH_STATUS = r'<span class="(snp-\w+)">([^<]+)</span>'

# Position from YBrowse link
POSITION = r'chrY:(\d+)-\d+'

# RS ID
RS_ID = r'(rs\d+)'

# Depth from 2006 indent
DEPTH_2006 = r'(ï¿½|•)'

# Depth from 2014 indent
DEPTH_2014 = r'&#8226;|•|<span class="(?:light|dark)">'
```

---

*End of Documentation*
