"""
Product Data Loader - Load real lip product data from Excel
"""
import pandas as pd
import json


def load_product_data(excel_path='Lip_Product_dataset.xlsx'):
    """
    Load product data from Excel file
    
    Returns:
        List of product dictionaries
    """
    print(f'📊 Loading product data from {excel_path}...')
    
    # Read Excel file
    df = pd.read_excel(excel_path)
    
    # Clean column names (remove trailing spaces)
    df.columns = df.columns.str.strip()
    
    print(f'✅ Loaded {len(df)} products')
    print(f'📋 Columns: {list(df.columns)}')
    
    # Convert to list of dictionaries
    products = []
    
    for idx, row in df.iterrows():
        # Extract color info from description
        color_desc = str(row['Colors'])
        hex_color = extract_hex_from_description(color_desc)
        
        product = {
            "id": idx,
            "name": row['Product_Name'],
            "brand": row['Brand'],
            "price": float(row['Price']) if pd.notna(row['Price']) else 0.0,
            "type": row['Product_Type'],
            "finish": row['Finish_Type'],
            "color_description": color_desc,
            "hex_color": hex_color,
            "url": row['Product_url'],
            # Extract "where to buy" from URL
            "where": extract_store_from_url(row['Product_url']),
            # Placeholder image (you can add real images later)
            "image": f"https://via.placeholder.com/150/{hex_color[1:]}/FFFFFF?text={row['Brand'].replace(' ', '+')}"
        }
        products.append(product)
    
    print(f'✅ Processed {len(products)} products')
    return products


def extract_hex_from_description(color_desc):
    """
    Extract or estimate hex color from color description
    Maps color keywords to hex codes
    """
    # Color keyword mapping
    color_map = {
        'pink': '#FF69B4',
        'rose': '#FF007F',
        'red': '#DC143C',
        'nude': '#F5E6D3',
        'beige': '#F5F5DC',
        'brown': '#8B4513',
        'rosewood': '#C67171',
        'copper': '#B87333',
        'berry': '#8E4585',
        'mauve': '#E0B0FF',
        'coral': '#FF7F50',
        'peach': '#FFE5B4',
        'plum': '#8E4585',
        'burgundy': '#800020',
        'wine': '#722F37',
        'orange': '#FF8C00',
        'purple': '#800080',
        'violet': '#8F00FF',
        'magenta': '#FF00FF',
        'fuchsia': '#FF00FF',
        'maroon': '#800000',
        'crimson': '#DC143C',
        'blush': '#DE5D83',
        'taupe': '#483C32',
    }
    
    # Convert to lowercase for matching
    desc_lower = str(color_desc).lower()
    
    # Try to find color keywords
    for color_name, hex_code in color_map.items():
        if color_name in desc_lower:
            return hex_code
    
    # Default to a neutral rose/pink if no match
    return '#D4A5A5'


def extract_store_from_url(url):
    """Extract store name from URL"""
    if 'sephora' in url.lower():
        return 'Sephora'
    elif 'ulta' in url.lower():
        return 'Ulta'
    elif 'amazon' in url.lower():
        return 'Amazon'
    else:
        return 'Online'


def calculate_color_similarity(color1_hex, color2_hex):
    """
    Calculate similarity between two hex colors (0-100%)
    Uses Euclidean distance in RGB space
    """
    try:
        # Remove '#' and convert hex to RGB
        r1 = int(color1_hex[1:3], 16)
        g1 = int(color1_hex[3:5], 16)
        b1 = int(color1_hex[5:7], 16)
        
        r2 = int(color2_hex[1:3], 16)
        g2 = int(color2_hex[3:5], 16)
        b2 = int(color2_hex[5:7], 16)
        
        # Calculate Euclidean distance
        distance = ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
        
        # Convert to similarity percentage (max distance in RGB is ~441)
        similarity = max(0, 100 - (distance / 441 * 100))
        return int(similarity)
    except:
        return 50  # Default similarity


def find_dupes(products, detected_colors, original_price=None, product_type="Lipstick", limit=10):
    """
    Find product dupes based on detected colors
    
    Args:
        products: List of all products
        detected_colors: List of hex color codes from image
        original_price: Original product price (optional)
        product_type: Type of product
        limit: Max number of dupes to return
    
    Returns:
        List of dupe dictionaries
    """
    # Filter by product type
    filtered = [p for p in products if p['type'].lower() == product_type.lower()]
    
    # If price given, filter for cheaper options
    if original_price:
        filtered = [p for p in filtered if p['price'] < original_price]
    
    # Calculate color match for each product
    for product in filtered:
        # Find best match with detected colors
        similarities = [calculate_color_similarity(product['hex_color'], detected) 
                       for detected in detected_colors]
        product['colorMatch'] = max(similarities) if similarities else 0
    
    # Sort by color match (desc) then price (asc)
    sorted_products = sorted(filtered, key=lambda x: (-x['colorMatch'], x['price']))
    
    # Format for frontend
    dupes = []
    for p in sorted_products[:limit]:
        dupe = {
            "name": p['name'],
            "brand": p['brand'],
            "price": p['price'],
            "description": p['color_description'],
            "where": p['where'],
            "image": p['image'],
            "colorMatch": p['colorMatch']
        }
        dupes.append(dupe)
    
    return dupes


def save_products_json(products, output_path='products.json'):
    """Save products to JSON file"""
    with open(output_path, 'w') as f:
        json.dump(products, f, indent=2)
    print(f'💾 Saved {len(products)} products to {output_path}')


if __name__ == '__main__':
    # Test the loader
    products = load_product_data()
    
    print(f'\n📦 Sample product:')
    print(json.dumps(products[0], indent=2))
    
    # Save to JSON
    save_products_json(products)
    
    # Test finding dupes
    detected_colors = ['#FF69B4', '#DC143C']
    dupes = find_dupes(products, detected_colors, original_price=50, limit=5)
    
    print(f'\n🔍 Found {len(dupes)} dupes for colors {detected_colors}:')
    for dupe in dupes:
        print(f'  - {dupe["name"]} ({dupe["brand"]}): ${dupe["price"]} - {dupe["colorMatch"]}% match')
