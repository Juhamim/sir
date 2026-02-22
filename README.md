# SIR Voter Search — Kerala Electoral Roll Lookup

A web application that allows users from your local village in Kerala to search for their voter details (SIR details / Electoral Roll details) by **Name** or **Voter ID (EPIC Number)**.

Users can type names in **English (Manglish)** or **Malayalam** — the app uses **fuzzy search** to find matches even with slight spelling variations.

---

## 📁 Project Structure

```
sir/
├── pdfs/                    # Place your Electoral Roll PDFs here
├── extract_voters.py        # Phase 1: PDF → JSON extraction script
├── requirements.txt         # Python dependencies
├── voters_data.json         # Extracted voter data (output from Phase 1)
├── index.html               # Web app — main HTML
├── style.css                # Web app — styles
├── app.js                   # Web app — search logic (Fuse.js)
└── README.md                # This file
```

---

## 🚀 Quick Start

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Extract Data from PDFs (Phase 1)

Place your Kerala Electoral Roll PDF files in the `pdfs/` folder, then run:

```bash
# Process a single PDF
python extract_voters.py ./pdfs/your_electoral_roll.pdf

# Process all PDFs in a folder
python extract_voters.py ./pdfs/

# Custom output file
python extract_voters.py ./pdfs/ --output my_data.json
```

This will create `voters_data.json` with all extracted voter records, including automatically generated English transliterations.

> **Note:** If no PDFs are found or parsing yields no results, the script will create sample data for testing.

### Step 3: Run the Web App (Phase 2)

Simply open `index.html` in your browser, or serve it with a local HTTP server:

```bash
# Option 1: Python HTTP server
python -m http.server 8080

# Option 2: Node.js (if installed)
npx serve .

# Option 3: VS Code Live Server extension
# Just right-click index.html → "Open with Live Server"
```

Then open **http://localhost:8080** in your browser.

---

## 🔍 Features

- **Fuzzy Search**: Search by Voter ID, English name, or Malayalam name
- **Bilingual UI**: Results show both Malayalam original and English transliteration
- **Mobile Responsive**: Works perfectly on phones — designed mobile-first
- **Copy Voter ID**: Click on the voter ID badge to copy it
- **Keyboard Shortcuts**: Press `/` to focus search, `Escape` to clear
- **Instant Results**: Client-side search — no server needed
- **Beautiful Dark UI**: Premium glassmorphism design

---

## ⚙️ How It Works

### Phase 1: Data Extraction (`extract_voters.py`)

1. **OCR Processing**: Since the PDFs are image-based, the script uses **Tesseract OCR** with Malayalam support to recognize text.
2. **Card Layout Analysis**: Parses the 3-column voter card layout used in Kerala Electoral Rolls.
3. **Field Extraction**: Uses regex and keyword matching to identify voter ID, names, relation, house number, age, and gender.
4. **Rule-based Transliteration**: Converts Malayalam names to English using a robust syllable-based engine and a dictionary of common Kerala names.
5. **Deduplication**: Removes duplicate records based on Voter ID.
6. **Progressive Saving**: Saves results after each PDF.

### Phase 2: Web Application

1. **Stats Dashboard**: Displays total voters and wards processed.
2. **Instant Search**: Initializes Fuse.js with weighted keys.
3. **Bilingual UI**: Beautiful cards showing ML original and EN transliteration.
4. **Sharing**: Built-in share button for social media.

---

## 🛠 Customization

### Adjusting Fuzzy Search Sensitivity

In `app.js`, modify the Fuse.js configuration:

```javascript
fuse = new Fuse(votersData, {
    threshold: 0.35,    // Lower = stricter, Higher = more fuzzy
    distance: 200,      // How far from perfect match to search
    minMatchCharLength: 2,
});
```

### Adding More PDFs

Just add PDF files to the `pdfs/` folder and re-run the extraction script. The new data will be merged.

---

## 📋 Dependencies

### System
- **Tesseract OCR**: [Download UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **Malayalam Data**: Download `mal.traineddata` from [tessdata_best](https://github.com/tesseract-ocr/tessdata_best) and place in `tessdata` folder.

### Python (Phase 1)
- `PyMuPDF (fitz)` — PDF rendering
- `pytesseract` — Tesseract wrapper
- `Pillow` — Image processing

### Web (Phase 2)
- [Fuse.js](https://fusejs.io/) v7.0 — Client-side fuzzy search (loaded via CDN)
- [Inter](https://fonts.google.com/specimen/Inter) — English font
- [Noto Sans Malayalam](https://fonts.google.com/noto/specimen/Noto+Sans+Malayalam) — Malayalam font

---

## 📝 License

Built for community use. Free to modify and distribute.
