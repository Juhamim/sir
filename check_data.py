"""Check quality of extracted voter data."""
import json

with open('voters_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

meta = data["metadata"]
voters = data["voters"]

print(f"Total voters: {meta['total_voters']}")
print()

# Show first 5 records
for i, v in enumerate(voters[:5]):
    print(f"--- Record {i+1} ---")
    for k, val in v.items():
        print(f"  {k}: {val}")
    print()

# Stats
ages = [v['age'] for v in voters if v.get('age')]
names = [v['name_ml'] for v in voters if v.get('name_ml')]
ids = [v['voter_id'] for v in voters if v.get('voter_id')]
name_en = [v['name_en'] for v in voters if v.get('name_en')]
houses = [v['house_number'] for v in voters if v.get('house_number')]
genders = [v['gender'] for v in voters if v.get('gender')]

print(f"Records with voter ID: {len(ids)}")
print(f"Records with Malayalam name: {len(names)}")
print(f"Records with English name: {len(name_en)}")
print(f"Records with age: {len(ages)}")
print(f"Records with house number: {len(houses)}")
print(f"Records with gender: {len(genders)}")
if ages:
    print(f"Age range: {min(ages)} - {max(ages)}")
print()

# Gender distribution
male = sum(1 for v in voters if v.get('gender') and 'Male' in v['gender'])
female = sum(1 for v in voters if v.get('gender') and 'Female' in v['gender'])
print(f"Male: {male}, Female: {female}")
print()

# Sample name pairs
print("Sample name pairs (ML -> EN):")
for v in voters[:15]:
    ml = v.get('name_ml', '—')
    en = v.get('name_en', '—')
    vid = v.get('voter_id', '—')
    age = v.get('age', '?')
    print(f"  [{vid}] {ml} -> {en} (Age: {age})")
