import anthropic
import os
import json
from dotenv import load_dotenv

load_dotenv()

class LipDupeAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
        
        # Define tools the agent can use
        self.tools = [
            {
                "name": "analyze_lip_product_image",
                "description": "Analyzes an uploaded image of a lip product to extract color information, finish type (matte/glossy/satin), and visual characteristics. Use this when you need to understand what the uploaded product looks like.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "image_data": {
                            "type": "string",
                            "description": "Base64 encoded image data or image analysis results"
                        }
                    },
                    "required": ["image_data"]
                }
            },
            {
                "name": "search_lip_dupes",
                "description": "Searches for affordable lip product alternatives based on color, finish, and price criteria. Returns drugstore and affordable brand options that match the specified characteristics.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "color_hex": {
                            "type": "string",
                            "description": "The hex color code to match (e.g., #DC143C)"
                        },
                        "finish_type": {
                            "type": "string",
                            "description": "The finish type: matte, glossy, satin, cream, or any",
                            "enum": ["matte", "glossy", "satin", "cream", "any"]
                        },
                        "max_price": {
                            "type": "number",
                            "description": "Maximum price in dollars"
                        },
                        "product_type": {
                            "type": "string",
                            "description": "Type of lip product: lipstick, lip_gloss, lip_liner, lip_stain",
                            "enum": ["lipstick", "lip_gloss", "lip_liner", "lip_stain", "any"]
                        }
                    },
                    "required": ["color_hex"]
                }
            },
            {
                "name": "compare_formulas",
                "description": "Compares lip product formulas to determine similarity. Useful for finding products with similar texture, longevity, and feel.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "product_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of product IDs to compare"
                        }
                    },
                    "required": ["product_ids"]
                }
            }
        ]
    
    def analyze_lip_product_image(self, color_data):
        """
        Tool implementation: Analyze the image data
        This uses the color data already extracted by Google Vision
        """
        # Guess the finish type based on color brightness/saturation
        # In a real implementation, this would use more sophisticated analysis
        primary_color = color_data[0]
        hex_color = primary_color['hex']
        
        # Simple heuristic: brighter colors might be glossy
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        brightness = (r + g + b) / 3
        
        finish = "satin"  # default
        if brightness > 180:
            finish = "glossy"
        elif brightness < 100:
            finish = "matte"
        
        return {
            "primary_color": hex_color,
            "secondary_colors": [c['hex'] for c in color_data[1:]] if len(color_data) > 1 else [],
            "estimated_finish": finish,
            "color_description": self._describe_color(hex_color)
        }
    
    def search_lip_dupes(self, color_hex, finish_type="any", max_price=20, product_type="lipstick"):
        """
        Tool implementation: Search for lip product dupes
        In production, this would call real product APIs
        """
        # Expanded mock data with various price points
        all_dupes = [
            # Budget tier ($3-10)
            {
                "id": "elf_1",
                "name": "e.l.f. Lip Color - Berry Kiss",
                "brand": "e.l.f.",
                "price": 3,
                "color_hex": "#C41E3A",
                "finish": "satin",
                "type": "lipstick",
                "color_match": 96,
                "formula_notes": "Creamy, moisturizing formula",
                "where": "Target, Walmart, elfcosmetics.com",
                "reviews": 4.5,
                "review_count": 1203,
                "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=200&h=200&fit=crop"
            },
            {
                "id": "nyx_1",
                "name": "NYX Soft Matte Lip Cream - Copenhagen",
                "brand": "NYX",
                "price": 7,
                "color_hex": "#B22222",
                "finish": "matte",
                "type": "lipstick",
                "color_match": 93,
                "formula_notes": "Long-lasting, non-drying matte",
                "where": "Ulta, CVS, Target",
                "reviews": 4.3,
                "review_count": 2847,
                "image": "https://images.unsplash.com/photo-1631214524020-7e18db9a8f92?w=200&h=200&fit=crop"
            },
            {
                "id": "maybelline_1",
                "name": "Maybelline SuperStay Matte Ink - Pioneer",
                "brand": "Maybelline",
                "price": 9,
                "color_hex": "#DC143C",
                "finish": "matte",
                "type": "lipstick",
                "color_match": 94,
                "formula_notes": "Up to 16hr wear, lightweight",
                "where": "Drugstores nationwide",
                "reviews": 4.6,
                "review_count": 5621,
                "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=200&h=200&fit=crop"
            },
            # Mid-tier ($10-25)
            {
                "id": "revlon_1",
                "name": "Revlon ColorStay Satin Ink - Silky Sienna",
                "brand": "Revlon",
                "price": 10,
                "color_hex": "#CD5C5C",
                "finish": "satin",
                "type": "lipstick",
                "color_match": 88,
                "formula_notes": "Comfortable satin finish, long-wearing",
                "where": "Walgreens, CVS, Target",
                "reviews": 4.2,
                "review_count": 892,
                "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=200&h=200&fit=crop"
            },
            {
                "id": "loreal_1",
                "name": "L'Oreal Colour Riche - Spice",
                "brand": "L'Oreal",
                "price": 12,
                "color_hex": "#C41E3A",
                "finish": "cream",
                "type": "lipstick",
                "color_match": 92,
                "formula_notes": "Luxurious creamy formula with shea butter",
                "where": "Drugstores, Target, Ulta",
                "reviews": 4.5,
                "review_count": 2103,
                "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=200&h=200&fit=crop"
            },
            {
                "id": "mac_1",
                "name": "MAC Lipstick - Russian Red",
                "brand": "MAC",
                "price": 21,
                "color_hex": "#DC143C",
                "finish": "matte",
                "type": "lipstick",
                "color_match": 97,
                "formula_notes": "Iconic shade, professional quality",
                "where": "MAC stores, Ulta, Nordstrom",
                "reviews": 4.8,
                "review_count": 5234,
                "image": "https://images.unsplash.com/photo-1596462502278-27bfdc403348?w=200&h=200&fit=crop"
            },
            # Premium tier ($25-45)
            {
                "id": "nars_1",
                "name": "NARS Audacious Lipstick - Vera",
                "brand": "NARS",
                "price": 34,
                "color_hex": "#C41E3A",
                "finish": "satin",
                "type": "lipstick",
                "color_match": 94,
                "formula_notes": "Intense color, luxurious feel",
                "where": "Sephora, NARS.com, Nordstrom",
                "reviews": 4.7,
                "review_count": 2341,
                "image": "https://images.unsplash.com/photo-1617897903246-719242758050?w=200&h=200&fit=crop"
            },
            {
                "id": "ysl_1",
                "name": "YSL Rouge Pur Couture - Le Rouge",
                "brand": "YSL",
                "price": 42,
                "color_hex": "#DC143C",
                "finish": "satin",
                "type": "lipstick",
                "color_match": 96,
                "formula_notes": "Luxury formula, iconic packaging",
                "where": "Sephora, YSL.com, Nordstrom",
                "reviews": 4.8,
                "review_count": 3156,
                "image": "https://images.unsplash.com/photo-1586495777744-4413f21062fa?w=200&h=200&fit=crop"
            }
        ]
        
        # Filter by criteria
        filtered = []
        for dupe in all_dupes:
            if dupe['price'] > max_price:
                continue
            if finish_type != "any" and dupe['finish'] != finish_type:
                continue
            if product_type != "any" and dupe['type'] != product_type:
                continue
            
            similarity = self._color_similarity(color_hex, dupe['color_hex'])
            dupe['color_match'] = int(similarity * 100)
            filtered.append(dupe)
        
        filtered.sort(key=lambda x: x['color_match'], reverse=True)
        return filtered[:8]

    def compare_formulas(self, product_ids):
        """
        Tool implementation: Compare product formulas
        """
        # Mock implementation
        return {
            "comparison": "All products have similar creamy formulas with good pigmentation",
            "most_similar": product_ids[0] if product_ids else None
        }
    
    def _color_similarity(self, hex1, hex2):
        """Calculate color similarity (0-1, where 1 is identical)"""
        r1, g1, b1 = int(hex1[1:3], 16), int(hex1[3:5], 16), int(hex1[5:7], 16)
        r2, g2, b2 = int(hex2[1:3], 16), int(hex2[3:5], 16), int(hex2[5:7], 16)
        
        distance = ((r2-r1)**2 + (g2-g1)**2 + (b2-b1)**2) ** 0.5
        max_distance = (255**2 * 3) ** 0.5
        
        similarity = 1 - (distance / max_distance)
        return similarity
    
    def _describe_color(self, hex_color):
        """Generate a human-readable color description"""
        r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
        
        if r > 200 and g < 100 and b < 100:
            return "bright red"
        elif r > 150 and g < 100 and b < 100:
            return "deep red"
        elif r > 150 and g > 100 and b < 100:
            return "coral or orange-red"
        elif r > 100 and g < 80 and b < 80:
            return "burgundy or wine"
        elif r > 180 and g > 150 and b > 150:
            return "light pink or nude"
        elif r > 150 and g > 100 and b > 100:
            return "mauve or dusty rose"
        else:
            return "unique shade"
    
    def find_dupes(self, user_query, color_data, original_price=None):
        """
        Main agent function: processes user query and finds dupes
        """
        print(f"\n🤖 Agent received query: '{user_query}'")
        print(f"📊 Color data available: {len(color_data)} colors")
        
        # Build the conversation
        messages = [
            {
                "role": "user",
                "content": f"""I need help finding affordable lip product dupes. 

User's request: {user_query}

I've analyzed the uploaded image and found these colors:
{json.dumps(color_data, indent=2)}

{f"Original product price: ${original_price}" if original_price else ""}

Please help me find the best drugstore dupes. Use your tools to:
1. Analyze the image data to understand the product
2. Search for similar affordable alternatives
3. Provide recommendations with clear reasoning

Focus on lip products only (lipstick, lip gloss, lip liner, lip stain).
"""
            }
        ]
        
        # Agent loop
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Agent iteration {iteration}")
            
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=4096,
                tools=self.tools,
                messages=messages
            )
            
            print(f"🤔 Agent stop reason: {response.stop_reason}")
            
            # Check if agent wants to use a tool
            if response.stop_reason == "tool_use":
                # Extract tool calls
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        tool_name = block.name
                        tool_input = block.input
                        
                        print(f"🔧 Agent using tool: {tool_name}")
                        print(f"   Input: {json.dumps(tool_input, indent=2)}")
                        
                        # Execute the tool
                        if tool_name == "analyze_lip_product_image":
                            result = self.analyze_lip_product_image(color_data)
                        elif tool_name == "search_lip_dupes":
                            result = self.search_lip_dupes(**tool_input)
                        elif tool_name == "compare_formulas":
                            result = self.compare_formulas(**tool_input)
                        else:
                            result = {"error": f"Unknown tool: {tool_name}"}
                        
                        print(f"✅ Tool result: {json.dumps(result, indent=2)[:200]}...")
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": json.dumps(result)
                        })
                
                # Add assistant's response and tool results to conversation
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                
            else:
                # Agent is done, extract final response
                final_response = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        final_response += block.text
                
                print(f"\n✅ Agent finished!")
                return final_response
        
        return "Sorry, I couldn't complete the analysis. Please try again."


# Test function
if __name__ == "__main__":
    # Test the agent
    agent = LipDupeAgent()
    
    # Mock color data
    test_colors = [
        {"hex": "#DC143C", "name": "Primary Color", "confidence": 95},
        {"hex": "#8B0000", "name": "Secondary Color", "confidence": 85}
    ]
    
    response = agent.find_dupes(
        user_query="Find me affordable dupes for this red lipstick under $15",
        color_data=test_colors,
        original_price=45
    )
    
    print("\n" + "="*50)
    print("AGENT RESPONSE:")
    print("="*50)
    print(response)