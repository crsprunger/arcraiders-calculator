#!/usr/bin/env python3
"""
Reorganize item JSON fields:
1. Move 'imageFilename' to near bottom (above 'recipe')
2. Extract just filename from imageFilename URL
3. Move 'recipe' to bottom (only 'verified' below it)
"""

import json
from pathlib import Path
from collections import OrderedDict

def reorganize_item_json(json_file):
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract just the filename from imageFilename if it exists
    if 'imageFilename' in data and data['imageFilename']:
        url = data['imageFilename']
        if '/' in url:
            data['imageFilename'] = url.split('/')[-1]
    
    # Create ordered dict with desired field order
    ordered_data = OrderedDict()
    
    # List of fields to put at the bottom in specific order
    bottom_fields = ['imageFilename', 'recipe', 'upgradeCost', 'verified']
    
    # Add all fields except the bottom ones first
    for key, value in data.items():
        if key not in bottom_fields:
            ordered_data[key] = value
    
    # Add bottom fields in order (only if they exist)
    if 'imageFilename' in data:
        ordered_data['imageFilename'] = data['imageFilename']
    
    if 'recipe' in data:
        ordered_data['recipe'] = data['recipe']
    
    if 'upgradeCost' in data:
        ordered_data['upgradeCost'] = data['upgradeCost']
    
    if 'verified' in data:
        ordered_data['verified'] = data['verified']
    
    # Write back to file
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(ordered_data, f, indent=2, ensure_ascii=False)
        f.write('\n')  # Add newline at end of file
    
    return True

def main():
    items_path = Path("static/items")
    count = 0
    
    for json_file in sorted(items_path.glob("*.json")):
        reorganize_item_json(json_file)
        count += 1
        print(f"Updated: {json_file.name}")
    
    print(f"\nTotal files reorganized: {count}")

if __name__ == '__main__':
    main()
