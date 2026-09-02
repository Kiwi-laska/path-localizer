#!/usr/bin/env python3
"""
Script to update PDF language codes in DITA files.
Updates xref href paths associated with PDF download icons based on the language of the folder.
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, Tuple
import xml.etree.ElementTree as ET


def load_language_mappings(script_dir: str) -> Dict[str, Tuple[str, str]]:
    """
    Load language code mappings from language_codes.txt.
    Returns a dict mapping language code (e.g., 'de', 'es-MX') to (path_code, pdf_suffix).
    """
    mappings = {}
    language_codes_file = os.path.join(script_dir, 'language_codes.txt')
    
    if not os.path.exists(language_codes_file):
        print(f"Warning: language_codes.txt not found at {language_codes_file}")
        return {}
    
    try:
        with open(language_codes_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(',')
                if len(parts) >= 3:
                    lang_code = parts[0].strip()
                    path_code = parts[1].strip()
                    pdf_suffix = parts[2].strip()
                    mappings[lang_code] = (path_code, pdf_suffix)
    except Exception as e:
        print(f"Error reading language_codes.txt: {e}")
        return {}
    
    return mappings


def extract_language_code(folder_path: str) -> str:
    """
    Extract language code from folder name.
    E.g., '/path/Sub_2131791_de-DE/' -> 'de-DE'
    """
    # Look for folder patterns like Sub_XXXXXX_XX-XX or Sub_XXXXXX_XX
    match = re.search(r'Sub_\d+_([a-z]{2}(?:-[A-Z]{2})?)', folder_path, re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def find_language_code_in_mappings(lang_code: str, language_mappings: Dict[str, Tuple[str, str]]) -> str:
    """
    Find matching language code in language_codes.txt, handling various formats.
    Tries exact match first, then case-insensitive match, then short code match.
    E.g., 'de-DE' could match 'de' or 'de-DE' in the mappings.
    
    Args:
        lang_code: Language code extracted from folder name (e.g., 'de-DE', 'es-MX')
        language_mappings: Dict of available language codes from language_codes.txt
    
    Returns:
        Matched language code from language_codes.txt, or None if not found
    """
    if not lang_code:
        return None
    
    # 1. Try exact match (case-sensitive)
    if lang_code in language_mappings:
        return lang_code
    
    # 2. Try case-insensitive match
    lang_code_lower = lang_code.lower()
    for code in language_mappings.keys():
        if code.lower() == lang_code_lower:
            return code
    
    # 3. Try matching short code (first 2 chars) against short codes in mappings
    short_code = lang_code[:2].lower()
    for code in language_mappings.keys():
        if code[:2].lower() == short_code:
            return code
    
    # 4. Try matching with underscores vs hyphens
    # E.g., 'de-DE' -> try 'de_de'
    alt_lang_code = lang_code.replace('-', '_')
    alt_lang_code_lower = alt_lang_code.lower()
    for code in language_mappings.keys():
        if code.lower() == alt_lang_code_lower:
            return code
    
    return None


def find_pdf_xrefs_and_update(file_path: str, path_code: str, pdf_suffix: str) -> bool:
    """
    Find and update PDF xref hrefs in a DITA file.
    Only updates xref elements with format="pdf" that contain image elements.
    Returns True if file was modified, False otherwise.
    """
    try:
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to find xref with format="pdf" containing an image tag
        # This regex finds: <xref ... format="pdf" ... href="...en...pdf" ...>...<image...>...</xref>
        # We need to be careful to only match xref elements that contain images
        
        # First, let's use a more robust approach with regex that handles the structure
        # Pattern: <xref with format="pdf" and href containing /en/ or -en
        pattern = r'(<xref[^>]*format="pdf"[^>]*href=")([^"]*?)/en/([^"]*?-en\.pdf)("[^>]*>.*?<image[^>]*>)'
        
        def replace_href(match):
            prefix = match.group(1)
            path_before_en = match.group(2)
            path_after_en = match.group(3)
            suffix = match.group(4)
            
            # Replace /en/ with the language-specific path
            new_path = path_before_en + f'/{path_code}/' + path_after_en
            # Replace -en with language-specific suffix in the PDF name
            new_path = new_path.replace('-en.pdf', f'-{pdf_suffix}.pdf')
            
            return prefix + new_path + suffix
        
        # Apply the replacement
        new_content = re.sub(pattern, replace_href, content, flags=re.DOTALL)
        
        # Also handle cases where there's no /en/ but still -en in the filename
        pattern2 = r'(<xref[^>]*format="pdf"[^>]*href=")([^"]*?)(-en\.pdf)("[^>]*>.*?<image[^>]*>)'
        
        def replace_href2(match):
            prefix = match.group(1)
            path_part = match.group(2)
            suffix = match.group(3)
            tag_suffix = match.group(4)
            
            # Only replace if /en/ is already in the path, otherwise replace -en
            if '/en/' not in path_part:
                new_path = path_part.replace('-en.pdf', f'-{pdf_suffix}.pdf')
                return prefix + new_path + tag_suffix
            return match.group(0)
        
        new_content = re.sub(pattern2, replace_href2, new_content, flags=re.DOTALL)
        
        # Check if content changed
        if new_content != original_content:
            # Write back the updated content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        
        return False
    
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def find_dita_folders(root_path: str) -> list:
    """
    Find all DITA translation folders recursively.
    Looks for folders matching the pattern: Zebra_DITA_*_Translated
    
    Args:
        root_path: Root folder to search from
    
    Returns:
        List of tuples: (folder_path, language_code) or empty list if none found
    """
    dita_folders = []
    
    for root, dirs, files in os.walk(root_path):
        for dir_name in dirs:
            # Look for Zebra_DITA_XX-XX_Translated pattern
            if dir_name.startswith('Zebra_DITA_') and dir_name.endswith('_Translated'):
                # Extract language code from folder name
                # E.g., 'Zebra_DITA_de-DE_Translated' -> 'de-DE'
                parts = dir_name.replace('Zebra_DITA_', '').replace('_Translated', '')
                if parts:
                    full_path = os.path.join(root, dir_name)
                    dita_folders.append((full_path, parts))
    
    return dita_folders


def process_dita_folder(folder_path: str, language_mappings: Dict[str, Tuple[str, str]]) -> int:
    """
    Process a single DITA folder and update PDF language codes.
    
    Args:
        folder_path: Path to the folder containing DITA files
        language_mappings: Language code mappings
    
    Returns:
        Number of files modified, or -1 if error
    """
    # Extract language code from folder structure
    # Try to extract from parent folder name (Sub_XXXXXX_XX-XX pattern)
    lang_code = extract_language_code(folder_path)
    
    if not lang_code:
        # Try extracting from current folder name (Zebra_DITA_XX-XX_Translated pattern)
        match = re.search(r'Zebra_DITA_([a-z]{2}(?:-[A-Z]{2})?)', folder_path, re.IGNORECASE)
        if match:
            lang_code = match.group(1)
    
    if not lang_code:
        print(f"  ⚠ Warning: Could not extract language code from {folder_path}")
        return 0
    
    # Find matching language code in mappings
    matched_lang_code = find_language_code_in_mappings(lang_code, language_mappings)
    
    if matched_lang_code is None:
        print(f"  ⚠ Warning: Language code '{lang_code}' not found in language_codes.txt")
        return 0
    
    path_code, pdf_suffix = language_mappings[matched_lang_code]
    
    # Find all .dita files in this folder
    dita_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.dita'):
                dita_files.append(os.path.join(root, file))
    
    if not dita_files:
        print(f"  ⚠ No .dita files found")
        return 0
    
    # Process files
    modified_count = 0
    for file_path in dita_files:
        if find_pdf_xrefs_and_update(file_path, path_code, pdf_suffix):
            modified_count += 1
    
    return modified_count


def main():
    """Main function."""
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Load language mappings
    language_mappings = load_language_mappings(script_dir)
    
    if not language_mappings:
        print("Error: Could not load language mappings from language_codes.txt")
        sys.exit(1)
    
    print("Available language mappings:")
    for code, (path_code, pdf_suffix) in language_mappings.items():
        print(f"  {code} -> path: {path_code}, suffix: {pdf_suffix}")
    print()
    
    # Ask user for root folder path
    while True:
        root_folder = input("Enter the path to the folder containing all translated files: ").strip()
        
        if not root_folder:
            print("Folder path cannot be empty.")
            continue
        
        # Remove quotes if present
        root_folder = root_folder.strip('"\'')
        
        if not os.path.isdir(root_folder):
            print(f"Error: {root_folder} is not a valid directory.")
            continue
        
        break
    
    print(f"\nSearching for DITA translation folders in: {root_folder}\n")
    
    # Find all DITA translation folders
    dita_folders = find_dita_folders(root_folder)
    
    if not dita_folders:
        print("No DITA translation folders found (looking for Zebra_DITA_*_Translated pattern)")
        sys.exit(0)
    
    print(f"Found {len(dita_folders)} translation folder(s):\n")
    
    # Process each folder
    total_modified = 0
    total_files = 0
    
    for folder_path, lang_code in dita_folders:
        print(f"Processing {lang_code}...")
        
        # Count total DITA files in this folder
        dita_file_count = 0
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                if file.endswith('.dita'):
                    dita_file_count += 1
        
        modified_count = process_dita_folder(folder_path, language_mappings)
        
        if modified_count > 0:
            print(f"  ✓ Updated {modified_count} file(s) out of {dita_file_count} total")
        else:
            print(f"  • No updates needed ({dita_file_count} file(s))")
        
        total_modified += modified_count
        total_files += dita_file_count
    
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"Total folders processed: {len(dita_folders)}")
    print(f"Total files modified: {total_modified}")
    print(f"Total files scanned: {total_files}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
