#!/usr/bin/env python3
"""
Add 'verified': false to all item JSON files
"""

import json
from pathlib import Path

def add_verified_field():
    items_path = Path("static/items")
    count = 0
    
    for json_file in items_path.glob("*.json"):
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add verified field if it doesn't exist
        if 'verified' not in data:
            data['verified'] = False
            
            # Write back to file with proper formatting
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            count += 1
            print(f"Updated: {json_file.name}")
    
    print(f"\nTotal files updated: {count}")

if __name__ == '__main__':
    add_verified_field()
