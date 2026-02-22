"""
Test Tesseract OCR on a single page - full output
"""
import fitz
from PIL import Image
import io
import os
import pytesseract

# Configure Tesseract
tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
tessdata_dir = os.path.join(os.environ['USERPROFILE'], 'tessdata')
pytesseract.pytesseract.tesseract_cmd = tesseract_path
os.environ['TESSDATA_PREFIX'] = tessdata_dir

# Extract page 3 as image
pdf_path = './pdfs/2026-EROLLGEN-S11-32-SIR-FinalRoll-Revision1-MAL-173-WI.pdf'
doc = fitz.open(pdf_path)
page = doc[2]

mat = fitz.Matrix(3.0, 3.0)
pix = page.get_pixmap(matrix=mat)
img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

print("Running OCR...")

# Try with PSM 4 (single column of text of variable sizes)
text = pytesseract.image_to_string(img, lang='mal+eng', config='--oem 3 --psm 4')

# Save full output
with open('ocr_test_output.txt', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Saved {len(text)} chars to ocr_test_output.txt")
print()
print("FULL OCR OUTPUT:")
print("=" * 70)
print(text)
print("=" * 70)

# Also try with data output (bounding boxes + text)
print("\n\nTrying with TSV output (structured data with positions)...")
data = pytesseract.image_to_data(img, lang='mal+eng', config='--oem 3 --psm 4', output_type=pytesseract.Output.DICT)

# Show text with positions
with open('ocr_test_structured.txt', 'w', encoding='utf-8') as f:
    for i in range(len(data['text'])):
        text_val = data['text'][i].strip()
        if text_val:
            conf = data['conf'][i]
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            line = f"[{conf:3d}%] ({x:4d},{y:4d},{w:3d}x{h:3d}) {text_val}"
            f.write(line + '\n')

print("Saved structured data to ocr_test_structured.txt")

doc.close()
