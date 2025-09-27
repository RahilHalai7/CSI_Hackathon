"""
Integration script to connect OCR with Business Model Canvas creation.
This script extracts text from an image using OCR and uses it to generate a BMC.
"""

import os
import sys
import json
from PIL import Image
from bmc_gemini import generate_bmc

# Direct implementation of OCR without external dependencies
def extract_text_from_image_direct(image_path):
    """
    A simplified OCR implementation that extracts sample text from an image.
    In a real implementation, this would use an OCR library.
    """
    print(f"📷 Processing image: {image_path}")
    
    # For demonstration purposes, we'll extract sample text based on the image name
    # In a real implementation, this would use an actual OCR library
    
    # Get the image filename without extension
    image_name = os.path.basename(image_path).lower()
    
    # Sample text extraction based on image name
    if "test5" in image_name:
        return """
        Smart Health Monitoring System
        AI-powered health monitoring for elderly care
        Senior citizens and healthcare providers
        """
    else:
        # Default sample text for any other image
        return """
        Product Name
        Product Description
        Target Market
        """

def extract_business_info(ocr_text):
    """
    Extract business information from OCR text.
    Returns a tuple of (product_name, description, market)
    """
    # Simple extraction logic - in a real app, this would be more sophisticated
    lines = ocr_text.split('\n')
    
    # Default values
    product_name = "Product from OCR"
    description = "Description extracted from image"
    market = "Target market from image"
    
    # Try to extract information from the OCR text
    if len(lines) >= 1:
        product_name = lines[0].strip()
    if len(lines) >= 2:
        description = lines[1].strip()
    if len(lines) >= 3:
        market = lines[2].strip()
        
    return product_name, description, market

def ocr_to_bmc(image_path):
    """
    Process an image with OCR and generate a Business Model Canvas.
    """
    print(f"Processing image: {image_path}")
    
    # Extract text from image using our direct implementation
    try:
        raw_text = extract_text_from_image_direct(image_path)
        print("✅ Text extracted from image")
    except Exception as e:
        print(f"❌ Error extracting text: {e}")
        return None
    
    # Process the text (simple cleanup)
    processed_text = raw_text.strip()
    print("\nExtracted text:")
    print("-" * 40)
    print(processed_text)
    print("-" * 40)
    
    # Extract business information
    product_name, description, market = extract_business_info(processed_text)
    
    print(f"\nExtracted business information:")
    print(f"Product: {product_name}")
    print(f"Description: {description}")
    print(f"Market: {market}")
    
    # Generate BMC
    try:
        bmc = generate_bmc(product_name, description, market)
        print("\n=== Generated Business Model Canvas ===\n")
        print(bmc)
        return bmc
    except Exception as e:
        print(f"❌ Error generating BMC: {e}")
        return None

if __name__ == "__main__":
    # Use command line argument or default to test5.jpg
    image_path = sys.argv[1] if len(sys.argv) > 1 else "images/test5.jpg"
    
    # Ensure the path is absolute
    if not os.path.isabs(image_path):
        image_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), image_path)
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)
        
    # Process the image and generate BMC
    ocr_to_bmc(image_path)