# PDF Language Code Updater Script

## Overview
This Python script automatically updates PDF language codes in DITA files. It identifies `<xref>` elements associated with PDF download icons and replaces the language codes in the href paths based on the language of the folder being processed.

## Features
- ✅ Automatically detects language from folder name (e.g., `Sub_XXXXX_de-DE`)
- ✅ Reads language mappings from `language_codes.txt`
- ✅ Finds `<xref>` elements with `format="pdf"` that contain image tags (PDF download icons)
- ✅ Replaces `/en/` with language-specific path codes (e.g., `/de/`, `/es_mx/`, `/zh_tw/`)
- ✅ Replaces `-en` suffix with language-specific suffix (e.g., `-de`, `-esla`, `-zhtw`)
- ✅ Overwrites files with updated content
- ✅ Provides progress feedback showing which files were modified

## Supported Languages

| Language | Folder Code | Path Code | PDF Suffix |
|----------|-------------|-----------|-----------|
| German | de-DE | de | de |
| Spanish (Mexico) | es-MX | es_mx | esla |
| French | fr-FR | fr | fr |
| Italian | it-IT | it | it |
| Japanese | ja-JP | ja | ja |
| Korean | ko-KR | ko | ko |
| Portuguese (Brazil) | pt-BR | pt_br | ptbr |
| Russian | ru-RU | ru | ru |
| Chinese (Simplified) | zh-CN | zh_cn | zhcn |
| Chinese (Traditional) | zh-TW | zh_tw | zhtw |
| Swedish | sv | sv | sv |

## Requirements
- Python 3.6+
- `language_codes.txt` file in the same directory as the script
- `.dita` files with the standard Zebra DITA structure

## Usage

### Basic Usage
```bash
python update_pdf_language_codes.py
```

### Step-by-Step
1. Run the script from the terminal:
   ```bash
   python update_pdf_language_codes.py
   ```

2. When prompted, enter the path to the folder containing DITA files:
   ```
   Enter the path to the folder containing DITA files: deliverables_XXXXXX_YYYY.MM.DD_HH.MM/Sub_XXXXXX_xx-XX/Zebra_DITA_xx-XX_Translated
   ```

3. The script will:
   - Detect the language from the folder name
   - Find all `.dita` files in the folder
   - Update all PDF xref paths
   - Display progress with a ✓ for each modified file
   - Show a summary of how many files were modified

## Example

### Input Folder
```
deliverables_2131797_2026.09.01_18.55/Sub_2131797_es-MX/Zebra_DITA_es-MX_Translated/
```

### Language Detection
```
Detected language: es-MX -> es-MX
Language mapping: path_code='es_mx', pdf_suffix='esla'
```

### File Changes
**Before:**
```xml
<xref format="pdf" href="../../../../../support-dam/en/documentation/unrestricted/guide/product/0001/kc401-qsg-en.pdf" scope="external">
  <image alt="PDF Download Icon" height="1em" href="GUID-xxx.svg" id="image_1" width="1em"/>
</xref>
```

**After:**
```xml
<xref format="pdf" href="../../../../../support-dam/es_mx/documentation/unrestricted/guide/product/0001/kc401-qsg-esla.pdf" scope="external">
  <image alt="PDF Download Icon" height="1em" href="GUID-xxx.svg" id="image_1" width="1em"/>
</xref>
```

## How It Works

1. **Language Detection**: Extracts language code from folder path using the pattern `Sub_XXXXXX_XX-XX`
2. **Language Mapping**: Normalizes the folder language code and looks up the path code and PDF suffix from `language_codes.txt`
3. **File Processing**: 
   - Scans all `.dita` files recursively in the target folder
   - Uses regex patterns to find `<xref format="pdf">` elements containing `<image>` tags
   - Replaces `/en/` with the language-specific path code
   - Replaces `-en.pdf` with the language-specific PDF suffix
4. **File Overwriting**: Saves changes directly to the original files

## Technical Details

The script uses regex patterns to reliably match PDF xref elements:
- Pattern 1: Matches `<xref format="pdf" ... href="..."/en/...-en.pdf"...>...<image...>`
- Pattern 2: Matches `<xref format="pdf" ... href="..."-en.pdf"...>...<image...>` (fallback)

This ensures only PDF download xref elements are updated, leaving other xref elements unchanged.

## Safety Notes
- **Backup First**: Always keep backups of your DITA files before running the script
- **Test Run**: Test the script on a single folder first before running on all folders
- **Atomic Updates**: Each file is either fully updated or not modified; there are no partial updates

## Troubleshooting

### Script cannot find language_codes.txt
**Solution**: Ensure `language_codes.txt` is in the same directory as `update_pdf_language_codes.py`

### Language code not recognized
**Solution**: Check that the folder path follows the pattern `Sub_XXXXXX_XX-XX`. The language code must be in the correct format and present in `language_codes.txt`

### No files were modified
This is normal if:
- The folder contains no `.dita` files
- The `.dita` files don't have PDF xref elements with image tags
- The xref elements already have the correct language codes

## Example Command Sequence

```powershell
# Navigate to the script directory
cd "c:\path\to\translated-files"

# Run the script
python update_pdf_language_codes.py

# Enter the folder path when prompted
# Example: deliverables_2131791_2026.09.01_18.56/Sub_2131791_de-DE/Zebra_DITA_de-DE_Translated
```

## Output Example

```
Available language mappings:
  de -> path: de, suffix: de
  es-MX -> path: es_mx, suffix: esla
  ... (other languages)

Enter the path to the folder containing DITA files: deliverables_2131797_2026.09.01_18.55/Sub_2131797_es-MX/Zebra_DITA_es-MX_Translated

Detected language: es-MX -> es-MX
Language mapping: path_code='es_mx', pdf_suffix='esla'
Processing folder: deliverables_2131797_2026.09.01_18.55/Sub_2131797_es-MX/Zebra_DITA_es-MX_Translated

Found 17 .dita files

✓ Updated: FMLANG-GUID-303380a5-efe8-426a-a81b-a4dbb4521c5f-en_706bb81b.dita

Completed! Modified 1 files out of 17 files.
```
