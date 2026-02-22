"""
Kerala Electoral Roll PDF Extractor (OCR-based)
================================================
Extracts voter details from image-based Kerala Electoral Roll PDFs
using Tesseract OCR with Malayalam + English language support.

Usage:
    python extract_voters.py [--output voters_data.json]
"""

import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import json
import re
import os
import sys
import glob
import argparse
from datetime import datetime

# ─── Tesseract Configuration ─────────────────────────────────────────────────
TESSERACT_CMD = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESSDATA_DIR = os.path.join(os.environ.get('USERPROFILE', ''), 'tessdata')

if os.path.exists(TESSERACT_CMD):
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD
if os.path.exists(TESSDATA_DIR):
    os.environ['TESSDATA_PREFIX'] = TESSDATA_DIR

# ─── Malayalam-to-English Transliteration ─────────────────────────────────────
# Comprehensive syllable-based mapping for accurate transliteration

# Consonant + virama combinations (conjuncts)
CONJUNCTS = {
    'ക്ക': 'kka', 'ക്ഷ': 'ksha', 'ക്ത': 'ktha',
    'ങ്ക': 'nka', 'ങ്ങ': 'nga',
    'ച്ച': 'ccha', 'ഞ്ച': 'ncha', 'ഞ്ഞ': 'nja',
    'ട്ട': 'tta', 'ണ്ട': 'nda', 'ണ്ണ': 'nna',
    'ത്ത': 'ttha', 'ന്ത': 'ntha', 'ന്ന': 'nna', 'ന്ദ': 'nda',
    'ന്ധ': 'ndha', 'ന്റ': 'nra',
    'പ്പ': 'ppa', 'മ്പ': 'mba', 'മ്മ': 'mma',
    'യ്യ': 'yya', 'ല്ല': 'lla', 'ള്ള': 'lla', 'വ്വ': 'vva',
    'ശ്ശ': 'shsha', 'സ്സ': 'ssa', 'റ്റ': 'tta',
    'ഷ്ട': 'shta', 'ഷ്ണ': 'shna',
    'സ്ക': 'ska', 'സ്ത': 'stha', 'സ്ഥ': 'stha', 'സ്മ': 'sma',
    'സ്ന': 'sna', 'സ്പ': 'spa', 'സ്ഫ': 'spha', 'സ്ര': 'sra',
    'ദ്ദ': 'dda', 'ദ്ധ': 'ddha', 'ദ്ര': 'dra',
    'ബ്ബ': 'bba', 'ബ്ദ': 'bda', 'ബ്ധ': 'bdha', 'ബ്ര': 'bra',
    'ജ്ജ': 'jja', 'ജ്ഞ': 'gna',
    'ഗ്ഗ': 'gga', 'ഗ്ന': 'gna', 'ഗ്മ': 'gma', 'ഗ്ര': 'gra',
    'ക്ര': 'kra', 'ക്ല': 'kla',
    'പ്ര': 'pra', 'പ്ല': 'pla',
    'ത്ര': 'thra', 'ത്മ': 'thma',
    'ഫ്ര': 'phra',
    'ശ്ര': 'shra',
    'ന്ദ്ര': 'ndra',
}

# Base consonants (without virama = implicit 'a')
CONSONANTS = {
    'ക': 'k', 'ഖ': 'kh', 'ഗ': 'g', 'ഘ': 'gh', 'ങ': 'ng',
    'ച': 'ch', 'ഛ': 'chh', 'ജ': 'j', 'ഝ': 'jh', 'ഞ': 'nj',
    'ട': 't', 'ഠ': 'th', 'ഡ': 'd', 'ഢ': 'dh', 'ണ': 'n',
    'ത': 'th', 'ഥ': 'thh', 'ദ': 'd', 'ധ': 'dh', 'ന': 'n',
    'പ': 'p', 'ഫ': 'ph', 'ബ': 'b', 'ഭ': 'bh', 'മ': 'm',
    'യ': 'y', 'ര': 'r', 'ല': 'l', 'വ': 'v', 'ശ': 'sh',
    'ഷ': 'sh', 'സ': 's', 'ഹ': 'h', 'ള': 'l', 'ഴ': 'zh', 'റ': 'r',
}

# Vowels (independent form)
VOWELS = {
    'അ': 'a', 'ആ': 'aa', 'ഇ': 'i', 'ഈ': 'ee', 'ഉ': 'u', 'ഊ': 'oo',
    'ഋ': 'ri', 'എ': 'e', 'ഏ': 'e', 'ഐ': 'ai', 'ഒ': 'o', 'ഓ': 'o', 'ഔ': 'au',
}

# Vowel signs (dependent form / matras)
MATRAS = {
    'ാ': 'a', 'ി': 'i', 'ീ': 'ee', 'ു': 'u', 'ൂ': 'oo',
    'ൃ': 'ri', 'െ': 'e', 'േ': 'e', 'ൈ': 'ai',
    'ൊ': 'o', 'ോ': 'o', 'ൌ': 'au', 'ൗ': 'au',
}

# Special characters
SPECIALS = {
    'ം': 'm', 'ഃ': 'h',
    '്': '',  # virama (used to kill inherent vowel)
    'ൻ': 'n', 'ൽ': 'l', 'ൾ': 'l', 'ർ': 'r', 'ൺ': 'n', 'ൿ': 'k',
    '\u200d': '', '\u200c': '',  # ZWJ and ZWNJ
    '‍': '', '‌': '',  # More ZWJ/ZWNJ variants
}

# Known Kerala name corrections - common OCR-extracted names to proper English
KNOWN_NAMES = {
    'അബ്ദുള്ള': 'Abdulla', 'അബ്ദുല്‍': 'Abdul', 'മുഹമ്മദ്': 'Muhammed',
    'മുഹമ്മദ്‌': 'Muhammed', 'മുഹമ്മെദ്': 'Muhammed',
    'ഫാത്തിമ': 'Fathima', 'ആയിശ': 'Ayisha', 'ഹസൻ': 'Hasan',
    'ഹുസൈൻ': 'Hussain', 'ഇബ്രാഹിം': 'Ibrahim', 'കരീം': 'Kareem',
    'അഹമ്മദ്': 'Ahmed', 'അഹമ്മദ്‌': 'Ahmed', 'അഹമ്മെദ്': 'Ahmed',
    'റഹ്മാൻ': 'Rahman', 'റഹിമാൻ': 'Rahman', 'റഹിമാന്‍': 'Rahman',
    'നാസർ': 'Naser', 'നാസര്‍': 'Naser',
    'ബീരാൻ': 'Beeran', 'ബീരാന്‍': 'Beeran',
    'ഉമ്മർ': 'Ummar', 'ഉമ്മര്‍': 'Ummar',
    'മൊയ്തീൻ': 'Moitheen', 'മൊയ്തീന്‍': 'Moitheen',
    'അലി': 'Ali', 'ഹസീന': 'Haseena', 'ഹസീനാ': 'Haseena',
    'ആമിന': 'Amina', 'സൈനബ': 'Sainaba', 'ഖദീജ': 'Khadija',
    'നൂറുന്നീസ': 'Noornisa',
    'രാജേഷ്': 'Rajesh', 'രാജേഷ്‌': 'Rajesh',
    'ലക്ഷ്മി': 'Lakshmi', 'ജയലക്ഷ്മി': 'Jayalakshmi',
    'ഗോപിനാഥൻ': 'Gopinathan', 'ഗോപിനാഥന്‍': 'Gopinathan',
    'ഗോപാലകൃഷ്ണൻ': 'Gopalakrishnan', 'കൃഷ്ണൻ': 'Krishnan',
    'ബാലകൃഷ്ണൻ': 'Balakrishnan',
    'നാരായണൻ': 'Narayanan', 'ശങ്കരൻ': 'Shankaran',
    'വിജയൻ': 'Vijayan', 'ദിനേശൻ': 'Dineshan',
    'സുരേഷ്': 'Suresh', 'മനോജ്': 'Manoj',
    'പ്രദീപ്': 'Pradeep', 'അനിത': 'Anitha',
    'ശാന്ത': 'Shantha', 'കമല': 'Kamala', 'ഗീത': 'Geetha',
    'ശ്രീദേവി': 'Sreedevi', 'സഫിയ': 'Safiya',
    'കുമാർ': 'Kumar', 'കുമാര്‍': 'Kumar', 'കുമാരി': 'Kumari',
    'നായർ': 'Nair', 'നായര്‍': 'Nair',
    'മേനോൻ': 'Menon', 'മേനോന്‍': 'Menon',
    'പിള്ള': 'Pilla', 'പണിക്കർ': 'Panikkar',
    'ജോസ്': 'Jose', 'ജോസ്‌': 'Jose', 'ജോർജ്': 'George',
    'തോമസ്': 'Thomas', 'മാത്യു': 'Mathew',
    'ചന്ദ്രൻ': 'Chandran', 'രമേശ്': 'Ramesh',
    'ബഷീർ': 'Basheer', 'ബഷിര്‍': 'Basheer',
    'ഷാജി': 'Shaji', 'സജി': 'Saji', 'വിനോദ്': 'Vinod',
    'അനീസ്': 'Anees', 'സന്തോഷ്': 'Santhosh',
    'ഗണേഷ്': 'Ganesh', 'ഗണേഷ്‌': 'Ganesh', 'ഗണേശ്': 'Ganesh',
    'ബാബു': 'Babu', 'മോഹൻ': 'Mohan', 'മോഹന്‍': 'Mohan',
    'ദേവി': 'Devi', 'ബീവി': 'Beevi',
    'ഷിഹാബ്': 'Shihab', 'ഷിഹാബ്‌': 'Shihab',
    'അസ്മ': 'Asma', 'ആഷിറ': 'Ashira', 'ശോഭി': 'Shobhi',
    'എൽസ': 'Elsa', 'എല്‍സ': 'Elsa', 'എല്‍സാ': 'Elsa',
    'ആശ': 'Asha', 'നസീർ': 'Naseer', 'നസീര്‍': 'Naseer',
    'മൻസൂർ': 'Mansoor', 'മന്‍സൂര്‍': 'Mansoor',
    'ശംസുദ്ദീൻ': 'Shamsudeen', 'ശംസുദ്ധീന്‍': 'Shamsudeen',
    'അബൂബക്കർ': 'Abubakar', 'അബൂബക്കര്‍': 'Abubakar',
    'അബ്ദുറഹീം': 'Abdurraheem', 'സത്യൻ': 'Sathyan', 'സത്യന്‍': 'Sathyan',
    'നബീൽ': 'Nabeel', 'നബില്‍': 'Nabeel',
    'ഹാജറ': 'Hajara', 'ജോബിൻ': 'Jobin', 'ജോബിന്‍': 'Jobin',
    'പ്രദീഷ്': 'Pradeesh', 'മഞ്ജുള': 'Manjula',
    'മുജീബ്': 'Mujeeb', 'മുജീബ്‌': 'Mujeeb',
    'ഷൂഹൈബ്': 'Shuhaib', 'ഷൂഹൈബ്‌': 'Shuhaib',
    'ശാരിക്': 'Sharik', 'ശാരിക്‌': 'Sharik',
    'മുഹന്നദ്': 'Muhanned', 'മൊസ്തീൻ': 'Mostheen', 'മൊസ്തീന്‍': 'Mostheen',
    'അഷറഫ്': 'Ashraf', 'അഷറഫ്‌': 'Ashraf',
    'ഗഫൂർ': 'Ghafoor', 'ഗഫൂര്‍': 'Ghafoor',
    'കുഞ്ഞാലി': 'Kunjali', 'കൂഞ്ഞാലി': 'Kunjali',
    'നാസിറുദ്ദീൻ': 'Nasirudeen', 'നാസിറുദ്ദീന്‍': 'Nasirudeen',
    'ഉണ്ണിമോയിൻ': 'Unnimoyin', 'ഉണ്ണിമോയിന്‍': 'Unnimoyin',
    'സൈദലവി': 'Saidalavi',
}


def is_malayalam(char):
    """Check if a character is Malayalam."""
    return '\u0D00' <= char <= '\u0D7F'


def transliterate_to_english(text):
    """
    Transliterate Malayalam text to English using a rule-based system.
    Handles conjuncts, matras, and known names.
    """
    if not text or not text.strip():
        return ""

    text = text.strip()
    # Remove ZWJ/ZWNJ characters
    text = text.replace('\u200d', '').replace('\u200c', '')
    text = text.replace('‍', '').replace('‌', '')

    # If text is already ASCII, return as-is
    if all(c.isascii() or c in ' /-.' for c in text):
        return text

    # Check if the whole text or individual words match known names
    words = text.split()
    result_words = []

    for word in words:
        # Clean the word
        clean_word = word.strip()
        if not clean_word:
            continue

        # Check known names dictionary
        matched = False
        for known_ml, known_en in KNOWN_NAMES.items():
            if clean_word == known_ml or clean_word.rstrip('്‌‍') == known_ml.rstrip('്‌‍'):
                result_words.append(known_en)
                matched = True
                break

        if matched:
            continue

        # If not in dictionary, transliterate character by character
        result_words.append(transliterate_word(clean_word))

    return ' '.join(result_words)


def transliterate_word(word):
    """Transliterate a single Malayalam word to English."""
    result = []
    i = 0
    chars = list(word)
    n = len(chars)

    while i < n:
        c = chars[i]

        # Skip non-Malayalam characters
        if not is_malayalam(c) and c not in SPECIALS:
            if c.isascii():
                result.append(c)
            i += 1
            continue

        # Check for special characters
        if c in SPECIALS:
            result.append(SPECIALS[c])
            i += 1
            continue

        # Check for independent vowels
        if c in VOWELS:
            result.append(VOWELS[c])
            i += 1
            continue

        # Check for vowel matras
        if c in MATRAS:
            result.append(MATRAS[c])
            i += 1
            continue

        # Check for consonants
        if c in CONSONANTS:
            # Look ahead for virama + consonant (conjunct)
            if i + 2 < n and chars[i + 1] == '്':
                # Check 3-char conjunct (C + virama + C)
                conjunct_key = c + '്' + chars[i + 2]
                if conjunct_key in CONJUNCTS:
                    # Check if followed by a matra
                    if i + 3 < n and chars[i + 3] in MATRAS:
                        result.append(CONJUNCTS[conjunct_key] + MATRAS[chars[i + 3]])
                        i += 4
                        continue
                    else:
                        result.append(CONJUNCTS[conjunct_key])
                        # Check if next char is not a matra — add inherent 'a'
                        if i + 3 < n and chars[i + 3] not in MATRAS and chars[i + 3] != '്':
                            result.append('a')
                        elif i + 3 >= n:
                            pass  # Word-final: no inherent vowel
                        i += 3
                        continue
                else:
                    # Virama but no recognized conjunct: consonant with killed vowel
                    result.append(CONSONANTS[c])
                    i += 2  # skip virama
                    continue

            # Check if followed by a matra
            if i + 1 < n and chars[i + 1] in MATRAS:
                result.append(CONSONANTS[c] + MATRAS[chars[i + 1]])
                i += 2
                continue

            # Standalone consonant — add inherent 'a' unless word-final
            result.append(CONSONANTS[c])
            # Add inherent 'a' if not at end and next is not virama or matra
            if i + 1 < n and chars[i + 1] not in MATRAS and chars[i + 1] != '്':
                result.append('a')
            elif i + 1 >= n:
                pass  # Don't add 'a' at end of word (common for Malayalam names)
            i += 1
            continue

        # Unknown character
        i += 1

    transliterated = ''.join(result)
    # Capitalize first letter of each word
    return transliterated.title() if transliterated else word


# ─── OCR Page Extraction ─────────────────────────────────────────────────────

def ocr_page(page, resolution=3.0):
    """Extract text from a PDF page image using Tesseract OCR."""
    mat = fitz.Matrix(resolution, resolution)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    text = pytesseract.image_to_string(img, lang='mal+eng', config='--oem 3 --psm 4')
    return text


def is_data_page(text):
    """Check if a page contains voter data."""
    # Case-insensitive voter id check
    has_voter_id = bool(re.search(r'[A-Za-z]{2,3}\d{6,10}', text))
    has_name_label = 'പേര' in text or 'പേർ' in text or 'Gald' in text or 'Cad' in text
    return has_voter_id and has_name_label


# ─── Parse OCR Text into Voter Records ───────────────────────────────────────

def parse_ocr_text(text):
    """
    Parse OCR output from a Kerala Electoral Roll page.
    Format: 3 voters per row in card layout.
    """
    voters = []
    lines = text.strip().split('\n')
    lines = [l.strip() for l in lines if l.strip()]

    if not lines:
        return voters

    # Find start of data
    start_idx = 0
    for i, line in enumerate(lines):
        if re.search(r'\d+\s+[A-Z]{2,3}\d{6,}', line):
            start_idx = i
            break

    i = start_idx
    while i < len(lines):
        line = lines[i]

        voter_ids_in_line = re.findall(r'[A-Za-z]{2,3}\d{6,10}', line)

        if voter_ids_in_line:
            # More robust serial number find (matches digit followed by Voter ID)
            serial_nums = re.findall(r'(?:^|\s)(\d{1,4})\s+[A-Za-z]{2,3}\d', line)

            # Collect block lines
            block_lines = [line]
            j = i + 1
            while j < len(lines):
                next_line = lines[j]
                if re.search(r'(?:^|\s)\d{1,4}\s+[A-Za-z]{2,3}\d{6,}', next_line):
                    break
                if 'വയസ്സ്' in next_line or 'ആകെ പേജ' in next_line or 'സപ്പിമെന്റ' in next_line:
                    break
                # Skip photo placeholder lines
                if next_line.strip() in ['ഫോട്ടോ', ''] or re.match(r'^(ഫോട്ടോ\s*)+$', next_line.strip()):
                    j += 1
                    continue
                block_lines.append(next_line)
                j += 1

            block_text = '\n'.join(block_lines)
            parsed = parse_voter_block(block_text, voter_ids_in_line, serial_nums)
            voters.extend(parsed)
            i = j
        else:
            i += 1

    return voters


def parse_voter_block(block_text, voter_ids, serial_nums):
    """Parse a block of text containing 1-3 voters in columns."""
    voters = []
    lines = block_text.split('\n')

    name_line = ""
    relative_line = ""
    house_line = ""
    age_gender_line = ""

    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        if re.search(r'[A-Z]{2,3}\d{6,}', line_stripped):
            pass
        elif re.search(r'പേര്?[്‌]*\s*[:+]', line_stripped) and not re.search(r'(അച്ഛ|ഭര്‍ത്താ|മറ്റ)', line_stripped):
            name_line += " " + line_stripped
        elif re.search(r'(അച്ഛന്റെ|ഭര്‍ത്താവിന്റെ|മറ്റുള്ളവ)', line_stripped):
            relative_line += " " + line_stripped
        elif re.search(r'(വീട്ടു|വിട്ടു)\s*നമ്പ', line_stripped):
            house_line += " " + line_stripped
        elif re.search(r'പ്രായം', line_stripped):
            age_gender_line += " " + line_stripped

    # Split names
    names = re.split(r'പേര്?[്‌]*\s*[:+]\s*', name_line.strip())
    names = [n.strip() for n in names if n.strip()]

    # Split relative names
    rel_parts = re.split(r'(?:അച്ഛന്റെ|ഭര്‍ത്താവിന്റെ|മറ്റുള്ളവ)\s*(?:പേര്?[്‌]*\s*)?[:+]?\s*', relative_line.strip())
    rel_names = [r.strip() for r in rel_parts if r.strip()]

    # Determine relation types
    relation_types = []
    for match in re.finditer(r'(അച്ഛന്റെ|ഭര്‍ത്താവിന്റെ|മറ്റുള്ളവ)', relative_line):
        rel_type = match.group(1)
        if 'അച്ഛ' in rel_type:
            relation_types.append("Father's Name / അച്ഛന്റെ പേര്")
        elif 'ഭര്‍ത്താ' in rel_type:
            relation_types.append("Husband's Name / ഭർത്താവിന്റെ പേര്")
        else:
            relation_types.append("Other / മറ്റുള്ളവ")

    # Split house numbers
    house_parts = re.split(r'(?:വീട്ടു|വിട്ടു)\s*നമ്പര്?[്‍]*\s*[:+]\s*', house_line.strip())
    houses = [h.strip() for h in house_parts if h.strip()]
    houses = [re.sub(r'\s*(ടോ|oes|ലു|ല്ല|ലല|llo)\s*$', '', h).strip() for h in houses]

    # Split age/gender
    age_gender_parts = re.split(r'പ്രായം\s*[:+]\s*', age_gender_line.strip())
    age_gender_parts = [p.strip() for p in age_gender_parts if p.strip()]

    ages = []
    genders = []
    for part in age_gender_parts:
        age_match = re.search(r'(\d{2,3})', part)
        age_val = int(age_match.group(1)) if age_match else None
        if age_val and (age_val < 18 or age_val > 120):
            age_val = None
        ages.append(age_val)

        if 'സ്ത്രീ' in part or 'സ്രീ' in part or 'ay)' in part.lower():
            genders.append("Female / സ്ത്രീ")
        else:
            genders.append("Male / പുരുഷൻ")

    # Build voter records
    num_voters = len(voter_ids)
    for idx in range(num_voters):
        voter_id = voter_ids[idx].upper() if idx < len(voter_ids) else None
        voter = {
            "serial_no": int(serial_nums[idx]) if idx < len(serial_nums) else None,
            "voter_id": voter_id,
            "name_ml": names[idx] if idx < len(names) else None,
            "name_en": None,
            "relative_name_ml": rel_names[idx] if idx < len(rel_names) else None,
            "relative_name_en": None,
            "relation_type": relation_types[idx] if idx < len(relation_types) else "Father's Name / അച്ഛന്റെ പേര്",
            "house_number": houses[idx] if idx < len(houses) else None,
            "age": ages[idx] if idx < len(ages) else None,
            "gender": genders[idx] if idx < len(genders) else None,
        }

        # Clean up names
        if voter["name_ml"]:
            voter["name_ml"] = re.sub(r'\s*(ഫോട്ടോ|ടോ|oes|ലു|ല്ല)\s*$', '', voter["name_ml"]).strip()
            voter["name_ml"] = re.sub(r'\s*\|\s*$', '', voter["name_ml"]).strip()

        if voter["relative_name_ml"]:
            voter["relative_name_ml"] = re.sub(r'\s*(ഫോട്ടോ|ടോ|oes|ലു|ല്ല)\s*$', '', voter["relative_name_ml"]).strip()

        if voter["voter_id"]:
            voters.append(voter)

    return voters


# ─── Main Processing ─────────────────────────────────────────────────────────

def process_pdf(pdf_path, resolution=2.0, verbose=True):
    """Process a single PDF file using OCR."""
    if verbose:
        print(f"\n{'='*60}")
        print(f"  Processing: {os.path.basename(pdf_path)}")
        print(f"{'='*60}")

    voters = []
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        if verbose:
            print(f"  Total pages: {total_pages}")

        for page_idx in range(total_pages):
            page = doc[page_idx]
            text = ocr_page(page, resolution=resolution)

            if not text.strip() or not is_data_page(text):
                if verbose and page_idx < 3:
                    print(f"  Page {page_idx+1}: Skipped (header/blank)")
                continue

            page_voters = parse_ocr_text(text)
            for v in page_voters:
                v["pdf_source"] = os.path.basename(pdf_path)
            
            if page_voters:
                voters.extend(page_voters)

            if verbose:
                print(f"  Page {page_idx+1}/{total_pages}: {len(page_voters)} voters (total: {len(voters)})")

        doc.close()
    except Exception as e:
        print(f"  ERROR: {e}")
        import traceback
        traceback.print_exc()

    if verbose:
        print(f"\n  Total: {len(voters)} voters from {os.path.basename(pdf_path)}")
    return voters


def add_transliterations(voters, verbose=True):
    """Add English transliterations."""
    if verbose:
        print(f"\n  Transliterating {len(voters)} records...")

    for i, voter in enumerate(voters):
        if voter.get("name_ml"):
            voter["name_en"] = transliterate_to_english(voter["name_ml"])
        if voter.get("relative_name_ml"):
            voter["relative_name_en"] = transliterate_to_english(voter["relative_name_ml"])

        if verbose and (i + 1) % 500 == 0:
            print(f"  Transliterated {i+1}/{len(voters)}...")

    if verbose:
        print(f"  Done transliterating.")
    return voters


def deduplicate(voters):
    """Remove duplicates by voter_id."""
    seen = set()
    unique = []
    for v in voters:
        vid = v.get("voter_id")
        if vid and vid in seen:
            continue
        if vid:
            seen.add(vid)
        unique.append(v)
    return unique


def save_data(voters, output_path, pdf_names=None):
    """Save to JSON."""
    data = {
        "metadata": {
            "extracted_at": datetime.now().isoformat(),
            "total_voters": len(voters),
            "source": "Kerala Electoral Roll PDF (OCR extraction)",
            "pdfs_processed": pdf_names or [],
        },
        "voters": voters
    }
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\n  Saved {len(voters)} records to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Extract voter data from Kerala Electoral Roll PDFs")
    parser.add_argument("--input", "-i", default="./pdfs", help="PDF file or folder")
    parser.add_argument("--output", "-o", default="voters_data.json", help="Output JSON file")
    parser.add_argument("--no-transliterate", action="store_true", help="Skip transliteration")
    parser.add_argument("--res", "-r", type=float, default=2.0, help="OCR resolution (default 2.0)")
    parser.add_argument("--resume", action="store_true", help="Resume from existing output file")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  Kerala Electoral Roll OCR Extractor")
    print("  SIR Voter Details - Image PDF to JSON")
    print("="*60)

    # Collect PDFs
    pdf_files = []
    if os.path.isfile(args.input) and args.input.lower().endswith('.pdf'):
        pdf_files = [args.input]
    elif os.path.isdir(args.input):
        pdf_files = sorted(glob.glob(os.path.join(args.input, '*.pdf')))
        pdf_files += sorted(glob.glob(os.path.join(args.input, '*.PDF')))
        seen_base = set()
        filtered = []
        for f in pdf_files:
            base = os.path.basename(f)
            clean_name = re.sub(r'\s*\(\d+\)', '', base)
            if clean_name not in seen_base:
                seen_base.add(clean_name)
                filtered.append(f)
        pdf_files = filtered

    if not pdf_files:
        print(f"\n  No PDFs found in '{args.input}'")
        return

    print(f"\n  Found {len(pdf_files)} PDF(s)")

    all_voters = []
    processed_pdfs = []

    # Check for resume
    if args.resume and os.path.exists(args.output):
        try:
            with open(args.output, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
                all_voters = existing_data.get('voters', [])
                processed_pdfs = existing_data.get('metadata', {}).get('pdfs_processed', [])
                print(f"  Resuming: {len(all_voters)} voters already extracted from {len(processed_pdfs)} PDFs.")
        except Exception as e:
            print(f"  Could not resume: {e}")

    for pdf_path in pdf_files:
        pdf_name = os.path.basename(pdf_path)
        if pdf_name in processed_pdfs:
            print(f"  Skipping already processed PDF: {pdf_name}")
            continue

        voters = process_pdf(pdf_path, resolution=args.res)
        all_voters.extend(voters)
        processed_pdfs.append(pdf_name)

        # Progressive backup/save after each PDF
        print(f"  Deduplicating and saving progress...")
        all_voters = deduplicate(all_voters)
        if not args.no_transliterate:
            all_voters = add_transliterations(all_voters)
        save_data(all_voters, args.output, processed_pdfs)

    print("\n" + "="*60)
    print(f"  COMPLETE! Total Records: {len(all_voters)}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
