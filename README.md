# ISOGG Y-DNA Haplogroup Archive & Workbench

**Comprehensive historical archive of ISOGG Y-DNA haplogroup trees and SNP data (2006-2020) with enhanced analysis tools**

---

## 🎯 Project Overview

This project transforms 15 years of ISOGG (International Society of Genetic Genealogy) Y-DNA haplogroup data from scattered HTML and Excel files into a unified, structured, and queryable dataset. It provides researchers, genealogists, and genetic analysts with:

- **Complete historical record** of Y-DNA haplogroup evolution (2006-2020)
- **Unified SNP table** with all genome build positions (36, 37, 38)
- **Naming evolution tracking** showing how haplogroups were renamed over time
- **Multiple data formats** (JSON, JSONL, TSV) for different use cases
- **Clean, validated data** with all inconsistencies resolved

### Why This Matters

The original ISOGG data exists as:
- 📄 **HTML files** with inconsistent formatting and embedded visual markup
- 📊 **Excel files** with multi-line cells, mixed data types, and manual formatting
- 🔀 **Scattered across years** with no unified schema or cross-referencing
- ❌ **Missing critical mappings** between different genome builds
- 🎲 **Inconsistent naming** with frequent renames and reorganizations

**Our solution provides:**
- ✅ **Structured JSON/TSV** with validated, consistent schemas
- ✅ **Complete build coverage** (36/37/38) via liftOver conversion
- ✅ **Historical tracking** of all 1,920 haplogroup renames
- ✅ **91,807 SNPs** with full metadata and cross-references
- ✅ **Ready for analysis** in any language or database system

---

## 📊 Dataset Statistics

### Coverage Summary

| Metric | Value |
|--------|-------|
| **Years covered** | 2006-2020 (15 years) |
| **Total SNPs** | 91,807 unique markers |
| **Haplogroup renames tracked** | 1,920 changes |
| **SNP evolution records** | 68,401 SNPs tracked across years |
| **Genome builds** | 33, 34, 35, 36, 37, 38 (6 builds) |
| **rs_number coverage** | 49,027 SNPs (53.4%) |
| **Tree navigation** | Parent/child relationships for 54,618 SNPs |
| **Output formats** | JSON, JSONL, TSV |

### Build Position Coverage

| Build | Direct Positions | Coverage |
|-------|-----------------|----------|
| **Build 33** (2004) | ~90,000 | 98%+ |
| **Build 34** (2004) | ~90,000 | 98%+ |
| **Build 35** (2004) | ~90,000 | 98%+ |
| **Build 36** (2006) | 33,800 | 37% |
| **Build 37** (2009) | 91,672 | 99.9% |
| **Build 38** (2013) | 91,672 | 99.9% |

*Note: Build 36 has lower direct coverage because some early Y chromosome positions were not fully mapped.*

### Haplogroup Evolution

| Year | Haplogroups | Notes |
|------|-------------|-------|
| 2006 | 379 | Initial ISOGG tree |
| 2008 | 518 | Major E3→E1b1 rename |
| 2012 | 927 | Rapid expansion begins |
| 2016 | 4,221 | Last year with old naming |
| 2017 | 6,833 | Transition to longer names |
| 2020 | ~5,000 | Current nomenclature |

---

## 📁 Data Structure

```
output_master/
├── enhanced_snp_table.tsv       # Master SNP table (TSV)
├── enhanced_snp_table.json      # Master SNP table (JSON)
├── enhanced_snp_table.jsonl     # Master SNP table (JSON Lines)
├── haplogroup_renames.tsv       # Naming changes (TSV)
├── haplogroup_renames.json      # Naming changes (JSON)
├── haplogroup_evolution.tsv     # SNP→haplogroup mapping by year
├── haplogroup_evolution.json    # Full evolution data
├── summary.json                 # Dataset statistics
│
├── 2006/                        # Year-specific data
│   ├── tree.json                # Haplogroup tree structure
│   ├── tree_grouped.json        # Tree with alphanumeric groupings
│   ├── snp_index.json           # SNP definitions
│   ├── glossary.json            # Term definitions
│   ├── metadata.json            # Year metadata
│   └── individual_haplogroups/  # Per-haplogroup files
│       ├── A.json
│       ├── B.json
│       └── ...
│
├── 2007/ ... 2015/              # Similar structure
│
├── 2016-2017/                   # Hybrid HTML+XLSX
│   ├── tree.json
│   ├── snp_index.json           # From HTML
│   ├── snp_index_xlsx.json      # From Excel
│   └── ...
│
└── 2018-2020/                   # Pure XLSX data
    ├── tree.json
    ├── tree_grouped.json
    ├── tree_trunk.json          # Trunk structure
    ├── snp_index.json
    └── ...
```

---

## 🗃️ File Formats

### Enhanced SNP Table

**File:** `enhanced_snp_table.tsv` / `.json` / `.jsonl`

The master SNP dataset with 16 columns - a complete navigable tree:

| Column | Type | Description |
|--------|------|-------------|
| `snp_name` | string | Primary SNP identifier (e.g., M168, Z5009) |
| `haplogroup` | string | Clean haplogroup name (no status markers) |
| `haplogroup_alpha` | string | Alphanumeric name from 2016 (last year available) |
| `alternate_names` | list | All known aliases (semicolon-separated in TSV) |
| `rs_number` | string | dbSNP reference SNP ID (53.4% coverage) |
| `build33_position` | integer | Y-chromosome position in NCBI33 |
| `build34_position` | integer | Y-chromosome position in NCBI34 |
| `build35_position` | integer | Y-chromosome position in NCBI35 |
| `build36_position` | integer | Y-chromosome position in NCBI36/hg18 |
| `build36_liftover` | integer | Reverse-lifted Build 37→36 position |
| `build37_position` | integer | Y-chromosome position in GRCh37/hg19 |
| `build38_position` | integer | Y-chromosome position in GRCh38 |
| `mutation` | string | Nucleotide change (e.g., A→G) |
| `status` | string | Investigation/Notes/Private/provisional/legacy |
| `source` | string | Data source year (2019-2020 or 2013) |
| `parent_name` | string | Parent haplogroup for tree navigation |
| `child_haplogroups` | list | Child haplogroups for tree navigation |
| `normative_names` | list | Standard nomenclature variations (e.g., E-M44, E1a-M44) |

**Example JSON:**
```json
{
  "snp_name": "M44",
  "haplogroup": "E1a1",
  "haplogroup_alpha": "E1a1",
  "alternate_names": [],
  "rs_number": "rs796742903",
  "build36_position": 20212032,
  "build37_position": 21752644,
  "build38_position": 19590758,
  "mutation": "G->C",
  "status": null,
  "source": "2019-2020",
  "parent_name": "E1a",
  "child_haplogroups": ["E1a1a", "E1a1b~"],
  "normative_names": ["E-M44", "E1-M44", "E1a-M44", "E1a1-M44"]
}
```

### Haplogroup Renames

**File:** `haplogroup_renames.tsv` / `.json`

Tracks all haplogroup naming changes between consecutive years.

**Example:**
```
2007    2008    E3a     E1b1a   M58
2007    2008    E3b     E1b1b   M215
```

### Alphanumeric Groupings

**File:** `YEAR/tree_grouped.json`

Groups haplogroups by name length (1-7+ characters) for easier navigation.

**Example:** E1b1b1a1c1 appears in:
- 1-char: E
- 2-char: E1
- 3-char: E1b
- 4-char: E1b1
- 5-char: E1b1b
- 6-char: E1b1b1
- 7plus: E1b1b1a

---

## 🚀 Usage Examples

### Python: Load Enhanced SNP Table

```python
import json

# Load JSON version
with open('output_master/enhanced_snp_table.json') as f:
    snps = json.load(f)

# Find all SNPs for haplogroup E1b1a
e1b1a_snps = [s for s in snps if s['haplogroup'].startswith('E1b1a')]
print(f"Found {len(e1b1a_snps)} SNPs in E1b1a")

# Find SNPs with Build 36 positions
build36_snps = [s for s in snps if s['build36_position']]
print(f"{len(build36_snps)} SNPs have Build 36 positions")
```

### Shell: Query with jq

```bash
# Count SNPs per haplogroup
jq -r '.[].haplogroup' output_master/enhanced_snp_table.json | sort | uniq -c | sort -rn | head

# Find all M172 variants
jq '.[] | select(.snp_name | contains("M172"))' output_master/enhanced_snp_table.json
```

### R: Load for Analysis

```r
library(jsonlite)

# Load SNP data
snps <- fromJSON('output_master/enhanced_snp_table.json')
df <- as.data.frame(snps)

# Analyze build coverage
table(is.na(df$build36_position))
```

---

## 🔬 Research Applications

1. **Phylogenetic Analysis** - Track haplogroup evolution over 15 years
2. **Tree Navigation** - Traverse up/down the Y-DNA tree from any SNP using parent_name/child_haplogroups
3. **Nomenclature Lookup** - Search by normative names (E-M44, R-M269, etc.)
4. **Genome Build Conversion** - Convert SNP positions between builds 33-38
5. **SNP Discovery** - Identify newly discovered SNPs by year
6. **Genealogical Research** - Map family test results to historical haplogroups
7. **Database Construction** - Build comprehensive Y-DNA reference databases

---

## 📜 License & Attribution

**Data Source:** International Society of Genetic Genealogy (ISOGG)  
**Original Data:** https://isogg.org/tree/

All ISOGG Y-DNA tree data is licensed under the [Creative Commons Attribution-ShareAlike 3.0 Unported License](https://creativecommons.org/licenses/by-sa/3.0/).

---

## 📚 Data Sources

Complete archive of source URLs used to compile this dataset:

### 2019-2020 (Current Version)
- **Main Index:** https://isogg.org/tree/index.html
- **Tree Trunk:** https://isogg.org/tree/ISOGG_YDNATreeTrunk.html
- **SNP Index:** https://isogg.org/tree/ISOGG_YDNA_SNP_Index.html
- **Papers Cited:** https://isogg.org/tree/ISOGG_All_Papers.html
- **Glossary:** https://isogg.org/tree/ISOGG_Glossary.html
- **Requirements:** https://isogg.org/tree/ISOGG_SNP_Requirements.html
- **Version History:** https://isogg.org/tree/ISOGG_YDNA_Version_History.html
- **Haplogroup Pages:** https://isogg.org/tree/ISOGG_Hapgrp[A-T].html

**Google Sheets (2018-2020 XLSX source):**
- **Main Tree:** https://docs.google.com/spreadsheets/d/1hW2SxSLFSJS3r_MIdw9zxsS8NXo_4PG0_fFFeXGwEyc/
- **China Users:** https://docs.google.com/spreadsheets/d/1MtQMv3ozCnxy9qB2gwqeFdmqnYJ_wRV1qu6AlZO-V3s/
- **SNP Index 1:** https://docs.google.com/spreadsheets/d/1_tnKfewXqxTCe0zFuJRm8f9Ohkv8RwCImkgRC3s-pnM/
- **SNP Index 2:** https://docs.google.com/spreadsheets/d/1GKL9OIEtDEXg8ikSV1tuRSiWqeql0UshJrdaMMcCv6I/
- **SNP Index 3:** https://docs.google.com/spreadsheets/d/1W1fjqWxxfYrSSdoE6Wu16ILZHsdytW7A9N265n5Lwms/
- **Index Data:** https://docs.google.com/spreadsheets/d/1n9MBaZWKBWUx2DN9aEN0CLCDmtnp64Hts-GrYGGPRRI/
- **Tree CSV:** https://isogg.org/tree/indexdata.csv

### 2018
- https://isogg.org/tree/2018/Main18.html
- https://isogg.org/tree/2018/ISOGG_YDNATreeTrunk18.html
- https://isogg.org/tree/2018/ISOGG_YDNA_SNP_Index18.html
- https://isogg.org/tree/2018/ISOGG_Hapgrp[A-T]18.html
- https://isogg.org/tree/2018/ISOGG_All_Papers18.html
- https://isogg.org/tree/2018/ISOGG_Glossary18.html
- https://isogg.org/tree/2018/ISOGG_SNP_Requirements18.html

### 2017
- https://isogg.org/tree/2017/Main17.html
- https://isogg.org/tree/2017/ISOGG_YDNATreeTrunk17.html
- https://isogg.org/tree/2017/ISOGG_YDNA_SNP_Index17.html
- https://isogg.org/tree/2017/ISOGG_Hapgrp[A-T]17.html
- https://isogg.org/tree/2017/ISOGG_All_Papers17.html
- https://isogg.org/tree/2017/ISOGG_Glossary17.html
- https://isogg.org/tree/2017/ISOGG_SNP_Requirements17.html

### 2016
- https://isogg.org/tree/2016/Main16.html
- https://isogg.org/tree/2016/ISOGG_YDNATreeTrunk16.html
- https://isogg.org/tree/2016/ISOGG_YDNA_SNP_Index16.html
- https://isogg.org/tree/2016/ISOGG_Hapgrp[A-T]16.html
- https://isogg.org/tree/2016/ISOGG_All_Papers16.html
- https://isogg.org/tree/2016/ISOGG_Glossary16.html
- https://isogg.org/tree/2016/ISOGG_SNP_Requirements16.html

### 2015
- https://isogg.org/tree/2015/Main15.html
- https://isogg.org/tree/2015/ISOGG_YDNATreeTrunk15.html
- https://isogg.org/tree/2015/ISOGG_YDNA_SNP_Index15.html
- https://isogg.org/tree/2015/ISOGG_Hapgrp[A-T]15.html
- https://isogg.org/tree/2015/ISOGG_All_Papers15.html
- https://isogg.org/tree/2015/ISOGG_Glossary15.html
- https://isogg.org/tree/2015/ISOGG_SNP_Requirements15.html

### 2014
- https://isogg.org/tree/2014/Main14.html
- https://isogg.org/tree/2014/ISOGG_YDNATreeTrunk14.html
- https://isogg.org/tree/2014/ISOGG_YDNA_SNP_Index14.html
- https://isogg.org/tree/2014/ISOGG_Hapgrp[A-T]14.html
- https://isogg.org/tree/2014/ISOGG_All_Papers14.html
- https://isogg.org/tree/2014/ISOGG_Glossary14.html
- https://isogg.org/tree/2014/ISOGG_SNP_Requirements14.html

### 2013
- https://isogg.org/tree/2013/Main13.html
- https://isogg.org/tree/2013/ISOGG_YDNATreeTrunk13.html
- https://isogg.org/tree/2013/ISOGG_YDNA_SNP_Index13.html
- https://isogg.org/tree/2013/ISOGG_Hapgrp[A-T]13.html
- https://isogg.org/tree/2013/ISOGG_All_Papers13.html
- https://isogg.org/tree/2013/ISOGG_Glossary13.html
- https://isogg.org/tree/2013/ISOGG_SNP_Requirements13.html

### 2012
- https://isogg.org/tree/2012/Main12.html
- https://isogg.org/tree/2012/ISOGG_YDNATreeTrunk12.html
- https://isogg.org/tree/2012/ISOGG_YDNA_SNP_Index12.html
- https://isogg.org/tree/2012/ISOGG_Hapgrp[A-T]12.html
- https://isogg.org/tree/2012/ISOGG_All_Papers12.html
- https://isogg.org/tree/2012/ISOGG_Glossary12.html
- https://isogg.org/tree/2012/ISOGG_SNP_Requirements12.html

### 2011
- https://isogg.org/tree/2011/Main11.html
- https://isogg.org/tree/2011/ISOGG_YDNATreeTrunk11.html
- https://isogg.org/tree/2011/ISOGG_YDNA_SNP_Index11.html
- https://isogg.org/tree/2011/ISOGG_Hapgrp[A-T]11.html
- https://isogg.org/tree/2011/ISOGG_All_Papers11.html
- https://isogg.org/tree/2011/ISOGG_Glossary11.html
- https://isogg.org/tree/2011/ISOGG_SNP_Requirements11.html

### 2010
- https://isogg.org/tree/2010/Main10.html
- https://isogg.org/tree/2010/ISOGG_YDNATreeTrunk10.html
- https://isogg.org/tree/2010/ISOGG_YDNA_SNP_Index10.html
- https://isogg.org/tree/2010/ISOGG_Hapgrp[A-T]10.html
- https://isogg.org/tree/2010/ISOGG_All_Papers10.html
- https://isogg.org/tree/2010/ISOGG_Glossary10.html
- https://isogg.org/tree/2010/ISOGG_SNP_Requirements10.html

### 2009
- https://isogg.org/tree/2009/Main09.html
- https://isogg.org/tree/2009/ISOGG_YDNATreeTrunk09.html
- https://isogg.org/tree/2009/ISOGG_YDNA_SNP_Index09.html
- https://isogg.org/tree/2009/ISOGG_Hapgrp[A-T]09.html
- https://isogg.org/tree/2009/ISOGG_All_Papers09.html
- https://isogg.org/tree/2009/ISOGG_Glossary09.html
- https://isogg.org/tree/2009/ISOGG_SNP_Requirements09.html

### 2008
- https://isogg.org/tree/2008/Main08.html
- https://isogg.org/tree/2008/ISOGG_YDNATreeTrunk08.html
- https://isogg.org/tree/2008/ISOGG_YDNA_SNP_Index08.html
- https://isogg.org/tree/2008/ISOGG_Hapgrp[A-T]08.html
- https://isogg.org/tree/2008/ISOGG_All_Papers08.html
- https://isogg.org/tree/2008/ISOGG_Glossary08.html
- https://isogg.org/tree/2008/ISOGG_SNP_Requirements08.html

### 2007
- https://isogg.org/tree/2007/Main07.html
- https://isogg.org/tree/2007/ISOGG_YDNATreeTrunk07.html
- https://isogg.org/tree/2007/ISOGG_YDNA_SNP_Index07.html
- https://isogg.org/tree/2007/ISOGG_Hapgrp[A-T]07.html
- https://isogg.org/tree/2007/ISOGG_All_Papers07.html
- https://isogg.org/tree/2007/ISOGG_Glossary07.html
- https://isogg.org/tree/2007/ISOGG_SNP_Requirements07.html

### 2006
- https://isogg.org/tree/2006/Main06.html
- https://isogg.org/tree/2006/ISOGG_YDNATreeTrunk06.html
- https://isogg.org/tree/2006/ISOGG_YDNA_SNP_Index06.html
- https://isogg.org/tree/2006/ISOGG_Hapgrp[A-T]06.html
- https://isogg.org/tree/2006/ISOGG_All_Papers06.html
- https://isogg.org/tree/2006/ISOGG_Glossary06.html
- https://isogg.org/tree/2006/ISOGG_SNP_Requirements06.html

### Additional Resources
- **Haplogroup I Cross-Reference:** https://isogg.org/tree/Haplo%20I%20Cross-Ref08.5.10.xls
- **ISOGG Wiki:** https://isogg.org/wiki/

---

## 📖 Technical Documentation

For detailed technical information about data processing, HTML parsing, and the complete pipeline, see [README_old_technical.md](README_old_technical.md).

---

**Last Updated:** January 2026  
**Dataset Version:** 1.0  
**Coverage:** 2006-2020 (15 years)
