# Species-sheet creation

Use the current Google Sheets workbook as the source for species-sheet structure and project designs.

When creating a species sheet, preserve calculated stat fields rather than inserting fixed results:

- Before (B4:B9) and After (C4:C9) are editable stat inputs.
- Diff (D4:D9) uses `=C4-B4` through `=C9-B9`.
- Before total (B10) uses `=SUM(B4:B9)`.
- After total (C10) uses `=SUM(C4:C9)`.
- Total difference (D10) uses `=C10-B10`.

Verify the native formulas as well as their displayed results before completing a new sheet. This requirement was clarified after the Pineco and Forretress sheets were created on 2026-10-12.
