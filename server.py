from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import os
from dotenv import load_dotenv
from agent import LipDupeAgent
from product_loader import load_product_data, find_dupes as find_product_dupes
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ FIXED: Proper CORS configuration to allow requests from Vercel
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False
    }
})

# Initialize the agent
print("🤖 Initializing AI Agent...")
agent = LipDupeAgent()
print("✅ Agent ready!")

# Load real product data
print("📊 Loading real product data...")
try:
    # Try to load from JSON first (faster)
    if os.path.exists('products.json'):
        with open('products.json', 'r') as f:
            PRODUCTS = json.load(f)
        print(f"✅ Loaded {len(PRODUCTS)} products from products.json")
    else:
        # Load from Excel if JSON doesn't exist
        PRODUCTS = load_product_data('Lip_Product_dataset.xlsx')
        print(f"✅ Loaded {len(PRODUCTS)} products from Excel")
except Exception as e:
    print(f"⚠️  Warning: Could not load product data: {e}")
    print("   Using empty product list (will use mock data)")
    PRODUCTS = []

def rgb_to_hex(r, g, b):
    """Convert RGB values to hex color code"""
    return '#{:02x}{:02x}{:02x}'.format(r, g, b)

def extract_colors_from_image(image_bytes):
    """Extract dominant colors from image using Google Vision API"""
    # Check if Google credentials are set
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not credentials_path or not os.path.exists(credentials_path):
        print('⚠️  Warning: Google Vision API not configured, using basic extraction')
        return extract_colors_basic(image_bytes)
    
    try:
        from google.cloud import vision
        
        print('✅ Using Google Vision API for color detection')
        
        # Initialize Vision API client
        client = vision.ImageAnnotatorClient()
        
        # Create image object
        image = vision.Image(content=image_bytes)
        
        # Detect image properties
        response = client.image_properties(image=image)
        
        # Check for errors
        if response.error.message:
            raise Exception(response.error.message)
        
        props = response.image_properties_annotation
        
        # Extract top 3 colors
        colors = []
        color_names = ['Primary Color', 'Secondary Color', 'Accent Color']
        
        for i, color_info in enumerate(props.dominant_colors.colors[:3]):
            color = color_info.color
            colors.append({
                'hex': rgb_to_hex(
                    int(color.red) if color.red else 0,
                    int(color.green) if color.green else 0,
                    int(color.blue) if color.blue else 0
                ),
                'name': color_names[i],
                'confidence': round(color_info.score * 100, 2),
                'pixelFraction': round(color_info.pixel_fraction * 100, 2)
            })
        
        print(f'✅ Successfully extracted {len(colors)} colors using Google Vision')
        return colors
        
    except Exception as e:
        print(f'❌ Google Vision API error: {e}')
        print('   Falling back to basic extraction')
        return extract_colors_basic(image_bytes)

def extract_colors_basic(image_bytes):
    """Basic color extraction without Google Vision API"""
    print('ℹ️  Using basic color extraction (no AI)')
    
    # Open image
    img = Image.open(io.BytesIO(image_bytes))
    
    # Resize for faster processing
    img = img.resize((150, 150))
    
    # Convert to RGB if necessary
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Get all pixels
    pixels = list(img.getdata())
    
    # Count color frequency (simplified - sample every 10th pixel)
    color_count = {}
    for i in range(0, len(pixels), 10):
        pixel = pixels[i]
        # Round colors to reduce variations
        rounded = (
            (pixel[0] // 20) * 20,
            (pixel[1] // 20) * 20,
            (pixel[2] // 20) * 20
        )
        color_count[rounded] = color_count.get(rounded, 0) + 1
    
    # Get top 3 colors
    top_colors = sorted(color_count.items(), key=lambda x: x[1], reverse=True)[:3]
    
    # Format results
    colors = []
    color_names = ['Primary Color', 'Secondary Color', 'Accent Color']
    for i, (color, count) in enumerate(top_colors):
        colors.append({
            'hex': rgb_to_hex(color[0], color[1], color[2]),
            'name': color_names[i],
            'confidence': round(count / len(pixels) * 100, 2)
        })
    
    return colors

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running!',
        'products_loaded': len(PRODUCTS)
    })

@app.route('/api/analyze', methods=['POST', 'OPTIONS'])
def analyze_image():
    """Analyze uploaded image using AI agent and real product data"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        print('\n' + '='*50)
        print('📥 Received image analysis request')
        
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image uploaded'
            }), 400
        
        # Get uploaded file
        file = request.files['image']
        image_bytes = file.read()
        
        # Get parameters
        category = request.form.get('category', 'Lipstick')
        original_price = request.form.get('price', None)
        original_price_float = float(original_price) if original_price else None
        
        # Build user query
        if original_price:
            user_query = f"Find affordable dupes for this {category.lower()} that costs ${original_price}"
        else:
            user_query = f"Find affordable dupes for this {category.lower()}"
        
        print(f'💬 User query: {user_query}')
        print(f'📝 Category: {category}, Price: ${original_price if original_price else "not specified"}')
        
        # Extract colors from image
        print('🎨 Extracting colors from image...')
        colors = extract_colors_from_image(image_bytes)
        print(f'✅ Extracted {len(colors)} colors: {[c["hex"] for c in colors]}')
        
        # Use REAL product data to find dupes!
        print(f'\n🔍 Searching through {len(PRODUCTS)} real products...')
        detected_hex_colors = [c['hex'] for c in colors]
        
        if PRODUCTS:
            # Use real product data
            dupes = find_product_dupes(
                products=PRODUCTS,
                detected_colors=detected_hex_colors,
                original_price=original_price_float,
                product_type=category,
                limit=10
            )
            print(f'✅ Found {len(dupes)} real product dupes!')
        else:
            # Fallback to agent's mock data
            print('⚠️  No real products loaded, using agent mock data')
            primary_color = colors[0]['hex'] if colors else "#DC143C"
            dupes = agent.search_lip_dupes(
                color_hex=primary_color,
                max_price=original_price_float if original_price_float else 50
            )
        
        # Also get AI agent explanation
        print('\n🤖 Getting AI Agent explanation...')
        agent_response = agent.find_dupes(
            user_query=user_query,
            color_data=colors,
            original_price=original_price_float
        )
        
        print(f'📊 Returning {len(dupes)} dupes to frontend')
        print('='*50 + '\n')
        
        # Return results
        return jsonify({
            'success': True,
            'colors': colors,
            'dupes': dupes,
            'originalPrice': original_price,
            'agent_explanation': agent_response
        })
        
    except Exception as e:
        print(f'❌ Error: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/chat', methods=['POST', 'OPTIONS'])
def chat():
    """Chat with the AI agent"""
    # Handle preflight OPTIONS request
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.json
        user_message = data.get('message', '')
        colors = data.get('colors', [])
        history = data.get('history', [])
        
        print(f'\n💬 Chat message: {user_message}')
        
        # Build context for the agent
        context = f"User's question: {user_message}\n\n"
        context += f"Available products in database: {len(PRODUCTS)}\n\n"
        
        if colors:
            context += f"Recently analyzed colors: {colors}\n"
        
        if history:
            context += "\nPrevious conversation:\n"
            for item in history[-3:]:  # Last 3 exchanges
                context += f"User: {item['user']}\nAgent: {item['agent']}\n"
        
        # Use the agent to respond
        response = agent.find_dupes(
            user_query=context,
            color_data=colors if colors else [{"hex": "#DC143C", "name": "Red", "confidence": 90}],
            original_price=None
        )
        
        print(f'✅ Chat response generated')
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f'❌ Chat error: {str(e)}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
if __name__ == '__main__':
    port = int(os.getenv('PORT', 3001))
    print(f'🚀 Backend server running on http://localhost:{port}')
    print(f'📝 Test it: http://localhost:{port}/api/health')
    print(f'📊 Loaded {len(PRODUCTS)} real products')
    app.run(host='0.0.0.0', port=port, debug=True)
