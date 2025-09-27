"""
Image to Business Model Canvas Pipeline

This script combines OCR text extraction with Gemini API to generate
a Business Model Canvas from an input image containing business description.

Setup:
- Set `GEMINI_API_KEY` in your environment (Google AI Studio key)
- Set up Google Cloud Vision API credentials
- Install deps: `pip install -r requirements.txt`

Usage:
python image_to_bmc.py --image "path/to/business_description.jpg"
python image_to_bmc.py --image "path/to/image.jpg" --product "Custom Product Name" --market "Custom Market"
"""

import os
import argparse
from typing import Optional
import re

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

import google.generativeai as genai
from google.cloud import vision
import unicodedata



class ImageToBMCPipeline:
    def __init__(self):
        """Initialize the pipeline with API configurations."""
        if load_dotenv:
            load_dotenv()
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise RuntimeError(
                "Missing GEMINI_API_KEY. Set it in your environment or .env file."
            )
        
        genai.configure(api_key=self.gemini_api_key)
        self.vision_client = vision.ImageAnnotatorClient()
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from an image using Google Cloud Vision OCR."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        with open(image_path, "rb") as f:
            content = f.read()

        image = vision.Image(content=content)
        
        # Use document_text_detection (better for handwriting and documents)
        response = self.vision_client.document_text_detection(image=image)

        if response.error.message:
            raise Exception(f"Vision API Error: {response.error.message}")

        return response.full_text_annotation.text if response.full_text_annotation else ""
    
    def preprocess_ocr_text(self, raw_text: str) -> str:
        """
        Preprocess raw OCR output into clean text.
        Steps:
        1. Strip lines and empty lines
        2. Normalize spaces
        3. Unicode normalization
        4. Remove non-text artifacts
        """
        if not raw_text.strip():
            return ""
        
        # Step 1: Strip lines and remove empty lines
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        
        # Step 2: Join lines and normalize spaces
        text = " ".join(lines)
        text = re.sub(r'\s+', ' ', text)
        
        # Step 3: Unicode normalization
        text = unicodedata.normalize('NFC', text)
        
        # Step 4: Remove most non-text artifacts but keep essential punctuation
        text = re.sub(r'[^\u0900-\u097Fa-zA-Z0-9\s.,!?()-]', '', text)
        
        return text.strip()
    
    def extract_business_info_from_text(self, text: str, product_override: Optional[str] = None, 
                                      market_override: Optional[str] = None) -> dict:
        """
        Use Gemini to extract structured business information from OCR text.
        """
        if not text.strip():
            raise ValueError("No text extracted from image. Please check if the image contains readable text.")
        
        extraction_prompt = f"""
        Analyze the following text extracted from an image and identify key business information:

        TEXT: {text}

        Extract and return ONLY the following information in this exact format:
        Product Name: [product/company name]
        Description: [one-line business description]
        Target Market: [target market/customer segment]

        If any information is unclear or missing, make reasonable assumptions based on the available text.
        Be concise and specific. Avoid marketing jargon.
        """
        
        model_name = self._choose_available_model()
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(extraction_prompt)
        
        extracted_text = response.text or ""
        
        # Parse the structured response
        business_info = self._parse_business_info(extracted_text)
        
        # Override with user-provided values if available
        if product_override:
            business_info['product'] = product_override
        if market_override:
            business_info['market'] = market_override
        
        return business_info
    
    def _parse_business_info(self, extracted_text: str) -> dict:
        """Parse the structured business information from Gemini's response."""
        business_info = {
            'product': 'Unknown Product',
            'description': 'Business description not available',
            'market': 'General market'
        }
        
        # Extract using regex patterns
        product_match = re.search(r'Product Name:\s*(.+)', extracted_text, re.IGNORECASE)
        description_match = re.search(r'Description:\s*(.+)', extracted_text, re.IGNORECASE)
        market_match = re.search(r'Target Market:\s*(.+)', extracted_text, re.IGNORECASE)
        
        if product_match:
            business_info['product'] = product_match.group(1).strip()
        if description_match:
            business_info['description'] = description_match.group(1).strip()
        if market_match:
            business_info['market'] = market_match.group(1).strip()
        
        return business_info
    
    def build_bmc_prompt(self, product: str, description: str, market: str, 
                        original_text: Optional[str] = None) -> str:
        """Create a structured prompt for Business Model Canvas generation."""
        lines = [
            "You are a startup strategist. Create a comprehensive Business Model Canvas.",
            f"Product: {product}",
            f"Description: {description}",
            f"Target Market: {market}",
        ]
        
        if original_text:
            lines.append(f"Additional Context from Source: {original_text}")
        
        lines.extend([
            "",
            "Create the 9 standard Business Model Canvas sections with 3-6 specific bullet points each:",
            "1. Customer Segments",
            "2. Value Propositions", 
            "3. Channels",
            "4. Customer Relationships",
            "5. Revenue Streams",
            "6. Key Activities",
            "7. Key Resources",
            "8. Key Partners",
            "9. Cost Structure",
            "",
            "Make outputs practical, specific, and actionable. Avoid generic marketing language.",
            "Base recommendations on the provided business context."
        ])
        
        return "\n".join(lines)
    
    def _choose_available_model(self) -> str:
        """Choose the best available Gemini model."""
        preferred = (
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash", 
            "gemini-1.5-pro-latest",
            "gemini-1.5-pro",
        )
        
        try:
            models = list(genai.list_models())
            supported = [
                m.name for m in models
                if "generateContent" in getattr(m, "supported_generation_methods", [])
            ]
            
            # Prefer flash models (free-tier friendly)
            flash = [n for n in supported if "flash" in n and "exp" not in n]
            if flash:
                return flash[0]
            
            pro = [n for n in supported if "pro" in n and "exp" not in n]
            if pro:
                return pro[0]
            
            # Try preferred aliases
            for pref in preferred:
                for name in supported:
                    if pref in name:
                        return name
            
            # Fallback to first supported
            if supported:
                return supported[0]
        except Exception:
            pass
        
        return preferred[0]
    
    def generate_bmc_from_info(self, business_info: dict, original_text: Optional[str] = None) -> str:
        """Generate Business Model Canvas from extracted business information."""
        model_name = self._choose_available_model()
        model = genai.GenerativeModel(model_name)
        
        prompt = self.build_bmc_prompt(
            business_info['product'],
            business_info['description'], 
            business_info['market'],
            original_text
        )
        
        response = model.generate_content(prompt)
        return response.text or "(No content returned)"
    
    def process_image_to_bmc(self, image_path: str, product_override: Optional[str] = None,
                           market_override: Optional[str] = None, 
                           show_intermediate: bool = False) -> str:
        """
        Complete pipeline: Image -> OCR -> Business Info Extraction -> BMC Generation
        """
        print(f"📸 Processing image: {image_path}")
        
        # Step 1: Extract text from image
        print("🔍 Extracting text from image...")
        raw_text = self.extract_text_from_image(image_path)
        clean_text = self.preprocess_ocr_text(raw_text)
        
        if show_intermediate:
            print(f"\n📝 Extracted text:\n{clean_text}\n")
        
        # Step 2: Extract business information
        print("🎯 Analyzing business information...")
        business_info = self.extract_business_info_from_text(
            clean_text, product_override, market_override
        )
        
        if show_intermediate:
            print(f"📊 Identified business info:")
            print(f"  Product: {business_info['product']}")
            print(f"  Description: {business_info['description']}")
            print(f"  Market: {business_info['market']}\n")
        
        # Step 3: Generate Business Model Canvas
        print("🏗️ Generating Business Model Canvas...")
        bmc = self.generate_bmc_from_info(business_info, clean_text)
        
        return bmc


def main():
    parser = argparse.ArgumentParser(
        description="Generate Business Model Canvas from business description image"
    )
    parser.add_argument(
        "--image", 
        required=True, 
        help="Path to image containing business description"
    )
    parser.add_argument(
        "--product", 
        required=False, 
        help="Override product name (optional)"
    )
    parser.add_argument(
        "--market", 
        required=False, 
        help="Override target market (optional)"
    )
    parser.add_argument(
        "--show-steps", 
        action="store_true",
        help="Show intermediate processing steps"
    )
    
    args = parser.parse_args()
    
    try:
        pipeline = ImageToBMCPipeline()
        canvas = pipeline.process_image_to_bmc(
            args.image, 
            args.product, 
            args.market,
            args.show_steps
        )
        
        print("\n" + "="*50)
        print("📋 BUSINESS MODEL CANVAS")
        print("="*50 + "\n")
        print(canvas)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())