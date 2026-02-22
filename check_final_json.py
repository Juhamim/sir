import json
try:
    with open('voters_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"Total voters in voters_data.json: {data['metadata']['total_voters']}")
    print(f"PDFs processed: {len(data['metadata']['pdfs_processed'])}")
    for pdf in data['metadata']['pdfs_processed']:
        print(f" - {pdf}")
except Exception as e:
    print(f"Error reading voters_data.json: {e}")
