#!/usr/bin/env python3
"""Quick inspection of Haplogroup E file structure."""
import openpyxl

wb = openpyxl.load_workbook('Haplogroup Data 2019-2020-~/2019-2020 Haplogroup E Tree.xlsx')
ws = wb.active

print("First 50 rows:")
for row_idx in range(1, 51):
    row_data = []
    for col_idx in range(1, 15):
        val = ws.cell(row=row_idx, column=col_idx).value
        if val:
            row_data.append(f"C{col_idx}:{val}")
    if row_data:
        print(f"Row {row_idx}: {' | '.join(row_data)}")
