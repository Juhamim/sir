"""
Test Surya OCR on a single page to check Malayalam text extraction quality.
"""
import fitz
from PIL import Image
import io

print("Loading Surya OCR models... (this takes 1-2 minutes on first run)")

from surya.foundation import FoundationPredictor
from surya.recognition import RecognitionPredictor
from surya.detection import DetectionPredictor

foundation = FoundationPredictor()
det_predictor = DetectionPredictor()
rec_predictor = RecognitionPredictor(foundation)

print("Models loaded!")

# Extract page 3 (index 2) as image - this is the first data page
pdf_path = './pdfs/2026-EROLLGEN-S11-32-SIR-FinalRoll-Revision1-MAL-173-WI.pdf'
doc = fitz.open(pdf_path)
page = doc[2]
mat = fitz.Matrix(2.5, 2.5)  # 2.5x zoom for better OCR
pix = page.get_pixmap(matrix=mat)
img_bytes = pix.tobytes('png')
img = Image.open(io.BytesIO(img_bytes))

print(f"Image size: {img.size}")
print("Running OCR on page 3...")

langs = ["ml", "en"]
predictions = rec_predictor([img], [langs], det_predictor)

page_pred = predictions[0]
print(f"\nExtracted {len(page_pred.text_lines)} text lines:")
print("=" * 70)

for i, line in enumerate(page_pred.text_lines):
    print(f"{i+1:3d}. [{line.confidence:.2f}] {line.text}")

doc.close()
print("\n=== DONE ===")
