"""
Quick Image URL Fixer - Extract product IDs and construct Sephora image URLs
"""
import json
import re


def extract_product_id_from_url(url):
    """
    Extract Sephora product ID from URL
    Example: https://www.sephora.com/product/dior-rouge-dior-on-stage-lipstick-P517621?skuId=2916419
    Returns: P517621
    """
    match = re.search(r'P\d+', url)
    if match:
        return match.group(0)
    return None


def construct_sephora_image_url(product_id, sku_id=None):
    """
    Construct Sephora CDN image URL from product ID
    Sephora's image URLs typically follow this pattern
    """
    if not product_id:
        return None
    
    # Remove 'P' prefix and use numeric ID
    numeric_id = product_id.replace('P', '')
    
    # Sephora image URL patterns (try multiple)
    patterns = [
        f"https://www.sephora.com/productimages/sku/s{sku_id}-main-zoom.jpg" if sku_id else None,
        f"https://www.sephora.com/productimages/product/p{numeric_id}-av-01-zoom.jpg",
        f"https://www.sephora.com/productimages/product/{product_id}-main-Lhero.jpg",
    ]
    
    # Return first valid pattern
    for pattern in patterns:
        if pattern:
            return pattern
    
    return None


def extract_sku_from_url(url):
    """Extract SKU ID from URL"""
    match = re.search(r'skuId=(\d+)', url)
    if match:
        return match.group(1)
    return None


def extract_ulta_sku(url):
    """
    Extract Ulta SKU ID from URL
    Example: https://www.ulta.com/p/glow-reviver-lip-oil-pimprod2042290?sku=2615654
    Returns: 2615654
    """
    match = re.search(r'sku=(\d+)', url)
    if match:
        return match.group(1)
    return None


def construct_ulta_image_url(url):
    """
    Construct Ulta image URL from product URL
    Ulta uses SKU-based image URLs
    """
    sku_id = extract_ulta_sku(url)
    if not sku_id:
        return None
    
    # Ulta image URL pattern uses SKU ID
    return f"https://images.ulta.com/is/image/Ulta/{sku_id}?sw=500"


def update_products_with_image_urls():
    """
    Update products.json with constructed image URLs from Sephora and Ulta
    """
    print('🖼️  Updating product images...')
    
    # Load products
    try:
        with open('products.json', 'r') as f:
            products = json.load(f)
        print(f'✅ Loaded {len(products)} products')
    except FileNotFoundError:
        print('❌ products.json not found!')
        return
    
    sephora_updated = 0
    ulta_updated = 0
    
    for product in products:
        url = product.get('url', '')
        
        # Check if it's a Sephora or Ulta URL
        if 'sephora.com' in url.lower():
            # Extract product ID and SKU for Sephora
            product_id = extract_product_id_from_url(url)
            sku_id = extract_sku_from_url(url)
            
            if product_id:
                # Try SKU-based URL first (most reliable)
                if sku_id:
                    image_url = f"https://www.sephora.com/productimages/sku/s{sku_id}-main-zoom.jpg"
                else:
                    # Fallback to product ID
                    numeric_id = product_id.replace('P', '')
                    image_url = f"https://www.sephora.com/productimages/product/p{numeric_id}-av-01-zoom.jpg"
                
                product['image'] = image_url
                sephora_updated += 1
        
        elif 'ulta.com' in url.lower():
            # Extract Ulta image URL
            image_url = construct_ulta_image_url(url)
            
            if image_url:
                product['image'] = image_url
                ulta_updated += 1
    
    # Save updated products
    with open('products.json', 'w') as f:
        json.dump(products, f, indent=2)
    
    print(f'✅ Updated {sephora_updated} Sephora products with image URLs')
    print(f'✅ Updated {ulta_updated} Ulta products with image URLs')
    print(f'💾 Saved to products.json')
    
    # Show some examples
    print('\n📸 Sample image URLs:')
    count = 0
    for product in products:
        if count >= 5:
            break
        if product.get('image') and 'placeholder' not in product['image']:
            count += 1
            store = 'Sephora' if 'sephora' in product['image'] else 'Ulta' if 'ulta' in product['image'] else 'Other'
            print(f"  {count}. [{store}] {product['name'][:40]}...")
            print(f"     {product['image']}")


if __name__ == '__main__':
    update_products_with_image_urls()
