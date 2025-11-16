"""
Arc Raiders Recipe Calculator
Analyzes item recipes and breaks them down into base resources.
"""

import json
from pathlib import Path
from collections import defaultdict
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# @app.route('/images/<path:filename>')
# def serve_item_image(filename):
#    """Serve item images from the local directory."""
#    return send_from_directory('static/images', filename)

class RecipeCalculator:
    def __init__(self, data_path="static/items"):
        self.data_path = Path(data_path)
        self.items = {}
        self.load_items()

    def load_items(self):
        """Load all item JSON files from the data directory."""
        for json_file in self.data_path.glob("*.json"):
            with open(json_file, 'r', encoding='utf-8') as f:
                item_data = json.load(f)
                item_id = item_data.get('id')
                if item_id:
                    self.items[item_id] = item_data

        print(f"Loaded {len(self.items)} items")

    def is_base_resource(self, item_id):
        """Check if an item is a base resource (has no recipe or upgradeCost)."""
        item = self.items.get(item_id)
        if not item:
            return True  # Unknown items are treated as base
        # Check for both recipe and upgradeCost
        has_recipe = 'recipe' in item and item['recipe']
        has_upgrade_cost = 'upgradeCost' in item and item['upgradeCost']
        return not (has_recipe or has_upgrade_cost)

    def get_previous_upgrade_level(self, item_id):
        """Get the previous upgrade level for a weapon (e.g., renegade_iii -> renegade_ii)."""
        # Map of current level suffix to previous level
        upgrade_map = {
            '_iv': '_iii',
            '_iii': '_ii',
            '_ii': '_i'
        }

        for current, previous in upgrade_map.items():
            if item_id.endswith(current):
                return item_id[:-len(current)] + previous

        return None

    def get_direct_requirements(self, selected_items):
        """
        Calculate direct requirements for selected items (no recursion).

        Args:
            selected_items: dict of {item_id: quantity}

        Returns:
            dict of {item_id: quantity} for direct requirements
        """
        requirements = defaultdict(int)

        for item_id, quantity in selected_items.items():
            item = self.items.get(item_id)
            if not item:
                continue

            # Check if it has an upgrade cost (weapon upgrade system)
            if 'upgradeCost' in item and item['upgradeCost']:
                # Add upgrade cost materials
                for ingredient_id, ingredient_qty in item['upgradeCost'].items():
                    requirements[ingredient_id] += ingredient_qty * quantity

                # Also need the previous upgrade level of this weapon
                previous_level = self.get_previous_upgrade_level(item_id)
                if previous_level:
                    requirements[previous_level] += quantity

            # Check if it has a regular recipe
            elif 'recipe' in item and item['recipe']:
                recipe = item['recipe']
                for ingredient_id, ingredient_qty in recipe.items():
                    requirements[ingredient_id] += ingredient_qty * quantity

        return dict(requirements)

    def get_weapon_upgrade_info(self, item_id, is_weapon):
        """Extract weapon upgrade level information if applicable."""
        # Map suffixes to roman numerals
        upgrade_levels = {
            '_i': 'I',
            '_ii': 'II',
            '_iii': 'III',
            '_iv': 'IV'
        }

        if not is_weapon:
            return {'is_weapon_upgrade': False}

        for suffix, roman in upgrade_levels.items():
            if item_id.endswith(suffix):
                base_name = item_id[:-len(suffix)]
                return {
                    'is_weapon_upgrade': True,
                    'base_name': base_name,
                    'upgrade_level': roman,
                    'previous_level': roman if suffix != '_i' else None
                }

        return {'is_weapon_upgrade': False}

    def get_item_info(self, item_id):
        """Get display information for an item."""
        item = self.items.get(item_id, {})

        # Check if this is a weapon upgrade
        weapon_info = self.get_weapon_upgrade_info(item_id, item.get('type', 'Unknown') != 'Modification')

        # Try to get image from item data first
        imageFilename = item.get('imageFilename', '')
        if len(imageFilename):
            image_path = f'static/images/{imageFilename}'
        else:
            # For weapon upgrades (level II and above), use base weapon image
            if weapon_info['is_weapon_upgrade']:
                image_path = f'static/images/{weapon_info["base_name"]}.png'
            else:
                image_path = f'static/images/{item_id}.png'

        # Handle both string and dict formats for name
        name_data = item.get('name', item_id)
        if isinstance(name_data, dict):
            name = name_data.get('en', item_id)
        else:
            name = name_data

        result = {
            'id': item_id,
            'name': name,
            'image': image_path,
            'rarity': item.get('rarity', 'Common'),
            'type': item.get('type', 'Unknown')
        }

        # Add weapon upgrade information if applicable
        if weapon_info['is_weapon_upgrade'] and weapon_info['upgrade_level'] != 'I':
            result['weapon_upgrade'] = True
            result['upgrade_level'] = weapon_info['upgrade_level']
            # For display, we need the previous level (what you need to have)
            # For renegade_iii, you need renegade_ii, so show overlay "II"
            level_map = {'II': 'I', 'III': 'II', 'IV': 'III'}
            result['required_level'] = level_map.get(weapon_info['upgrade_level'], 'I')

        return result

# Initialize the calculator
calculator = RecipeCalculator()

@app.route('/')
def index():
    """Main page with item selection interface."""
    return render_template('index.html')

@app.route('/api/items')
def get_items():
    """API endpoint to get all items."""
    items_list = []
    for item_id, item_data in calculator.items.items():
        # Check if this item should be displayed
        # Only show items that have a recipe, upgradeCost, or are weapon upgrades
        has_recipe = 'recipe' in item_data and item_data['recipe']
        has_upgrade_cost = 'upgradeCost' in item_data and item_data['upgradeCost']
        weapon_info = calculator.get_weapon_upgrade_info(item_id, 'type' in item_data and item_data['type'] != 'Modification')
        is_weapon = weapon_info['is_weapon_upgrade']

        # Skip items that have no recipe/upgradeCost and aren't weapons
        if not has_recipe and not has_upgrade_cost and not is_weapon:
            continue

        # Handle both string and dict formats for name
        name_data = item_data.get('name', item_id)
        if isinstance(name_data, dict):
            name = name_data.get('en', item_id)
        else:
            name = name_data

        # Try to get image from item data first
        imageFilename = item_data.get('imageFilename', '')
        if len(imageFilename):
            image_path = f'static/images/{imageFilename}'
        else:
            # For weapon upgrades (level II and above), use base weapon image
            if weapon_info['is_weapon_upgrade']:
                image_path = f'static/images/{weapon_info["base_name"]}.png'
            else:
                image_path = f'static/images/{item_id}.png'

        items_list.append({
            'id': item_id,
            'name': name,
            'image': image_path,
            'rarity': item_data.get('rarity', 'Common'),
            'type': item_data.get('type', 'Unknown'),
            'has_recipe': has_recipe
        })

    # Sort by name
    items_list.sort(key=lambda x: x['name'].lower())
    return jsonify(items_list)

@app.route('/api/calculate', methods=['POST'])
def calculate_resources():
    """API endpoint to calculate direct requirements for selected items."""
    data = request.json
    selected_items = data.get('items', {})

    # Calculate direct requirements (no recursion)
    requirements = calculator.get_direct_requirements(selected_items)

    # Add display information
    result = []
    for item_id, quantity in sorted(requirements.items(),
                                   key=lambda x: calculator.get_item_info(x[0])['name']):
        info = calculator.get_item_info(item_id)
        info['quantity'] = quantity
        info['can_expand'] = not calculator.is_base_resource(item_id)
        result.append(info)

    return jsonify(result)

@app.route('/api/expand', methods=['POST'])
def expand_item():
    """API endpoint to get the recipe for a specific item."""
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity', 1)

    if not item_id:
        return jsonify({'error': 'item_id required'}), 400

    # Get direct requirements for this single item
    requirements = calculator.get_direct_requirements({item_id: quantity})

    # Add display information
    result = []
    for req_id, req_qty in sorted(requirements.items(),
                                  key=lambda x: calculator.get_item_info(x[0])['name']):
        info = calculator.get_item_info(req_id)
        info['quantity'] = req_qty
        info['can_expand'] = not calculator.is_base_resource(req_id)
        result.append(info)

    return jsonify(result)

if __name__ == '__main__':
    print("Starting Arc Raiders Recipe Calculator...")
    print(f"Access the application at: http://localhost:5000")
    app.run(debug=True, port=5000)
