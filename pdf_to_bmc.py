"""
PDF to Business Model Canvas Pipeline

This script processes PDF documents (both text-based and image-based) to generate
a Business Model Canvas using OCR and Gemini API.

Features:
- Handles text-based PDFs with direct text extraction
- Processes image-based/scanned PDFs using OCR
- Converts PDF pages to images for OCR processing
- Combines text from multiple pages
- Generates comprehensive Business Model Canvas

Setup:
- Set `GEMINI_API_KEY` in your environment (Google AI Studio key)
- Set up Google Cloud Vision API credentials
- Install deps: `pip install -r requirements.txt`

New dependencies needed:
- PyMuPDF (fitz): `pip install PyMuPDF`
- Pillow: `pip install Pillow`
- pdf2image: `pip install pdf2image`

Usage:
python pdf_to_bmc.py --pdf "path/to/business_plan.pdf"
python pdf_to_bmc.py --pdf "path/to/document.pdf" --product "Custom Product" --market "Custom Market"
python pdf_to_bmc.py --pdf "path/to/document.pdf" --pages "1-3" --ocr-only
"""
import io
import os
import argparse
from typing import Optional, List, Tuple
import re
from pathlib import Path

try:
    from dotenv import load_dotenv  # type: ignore
except Exception:
    load_dotenv = None

import google.generativeai as genai
from google.cloud import vision
import unicodedata

try:
    import fitz  # PyMuPDF
except ImportError:
    raise ImportError("Please install PyMuPDF: pip install PyMuPDF")

try:
    from PIL import Image
except ImportError:
    raise ImportError("Please install Pillow: pip install Pillow")

try:
    from pdf2image import convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available. Will use PyMuPDF for image conversion.")


class PDFToBMCPipeline:
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
    
    def extract_text_from_pdf(self, pdf_path: str, page_range: Optional[str] = None) -> Tuple[str, bool]:
        """
        Extract text from PDF using PyMuPDF.
        Returns (text, is_text_based) - is_text_based=False means we need OCR.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        doc = fitz.open(pdf_path)
        pages_to_process = self._parse_page_range(page_range, len(doc))
        
        extracted_text = []
        text_found = False
        
        for page_num in pages_to_process:
            if page_num < len(doc):
                page = doc[page_num]
                page_text = page.get_text().strip()
                
                if page_text:
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    text_found = True
                else:
                    extracted_text.append(f"--- Page {page_num + 1} (No text found) ---")
        
        doc.close()
        
        full_text = "\n\n".join(extracted_text)
        return full_text, text_found
    
    def convert_pdf_to_images(self, pdf_path: str, page_range: Optional[str] = None, 
                             dpi: int = 200) -> List[Tuple[Image.Image, int]]:
        """
        Convert PDF pages to images for OCR processing.
        Returns list of (PIL Image, page_number) tuples.
        Uses pdf2image if available, otherwise falls back to PyMuPDF.
        """
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        pages_to_process = self._parse_page_range(page_range, total_pages)
        
        if PDF2IMAGE_AVAILABLE:
            doc.close()
            return self._convert_with_pdf2image(pdf_path, pages_to_process, dpi)
        else:
            return self._convert_with_pymupdf(doc, pages_to_process, dpi)
    
    def _convert_with_pdf2image(self, pdf_path: str, pages_to_process: List[int], dpi: int) -> List[Tuple[Image.Image, int]]:
        """Convert using pdf2image library."""
        try:
            if len(pages_to_process) < len(fitz.open(pdf_path)):  # Not all pages
                first_page = min(pages_to_process) + 1  # pdf2image uses 1-based indexing
                last_page = max(pages_to_process) + 1
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi,
                    first_page=first_page,
                    last_page=last_page
                )
                # Pair images with their actual page numbers
                image_page_pairs = [(img, pages_to_process[i]) for i, img in enumerate(images)]
            else:
                images = convert_from_path(pdf_path, dpi=dpi)
                image_page_pairs = [(img, i) for i, img in enumerate(images)]
            
            return image_page_pairs
        except Exception as e:
            print(f"pdf2image failed: {e}")
            print("Falling back to PyMuPDF...")
            doc = fitz.open(pdf_path)
            return self._convert_with_pymupdf(doc, pages_to_process, dpi)
    
    def _convert_with_pymupdf(self, doc, pages_to_process: List[int], dpi: int) -> List[Tuple[Image.Image, int]]:
        """Convert using PyMuPDF as fallback."""
        image_page_pairs = []
        
        # Calculate zoom factor from DPI (72 is default PDF DPI)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in pages_to_process:
            if page_num < len(doc):
                page = doc[page_num]
                
                # Render page to image
                pix = page.get_pixmap(matrix=mat)
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                image_page_pairs.append((pil_image, page_num))
        
        doc.close()
        return image_page_pairs
    
    def extract_text_from_pdf_images(self, image_page_pairs: List[Tuple[Image.Image, int]]) -> str:
        """Extract text from PDF images using Google Cloud Vision OCR."""
        import io
        
        all_text = []
        
        for pil_image, page_num in image_page_pairs:
            print(f"  📄 Processing page {page_num + 1} with OCR...")
            
            # Convert PIL image to bytes
            import io
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image
            image = vision.Image(content=img_byte_arr)
            
            # Use document_text_detection for better results
            response = self.vision_client.document_text_detection(image=image)
            
            if response.error.message:
                print(f"    ⚠️  OCR error on page {page_num + 1}: {response.error.message}")
                continue
            
            page_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            if page_text.strip():
                all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
            else:
                all_text.append(f"--- Page {page_num + 1} (No text extracted) ---")
        
        return "\n\n".join(all_text)
    
    def _parse_page_range(self, page_range: Optional[str], total_pages: int) -> List[int]:
        """
        Parse page range string like '1-3', '1,3,5', or '1-3,5-7' into list of page indices (0-based).
        """
        if not page_range:
            return list(range(total_pages))
        
        pages = set()
        
        for part in page_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = map(int, part.split('-'))
                # Convert to 0-based indexing and ensure within bounds
                start_idx = max(0, start - 1)
                end_idx = min(total_pages - 1, end - 1)
                pages.update(range(start_idx, end_idx + 1))
            else:
                # Single page number
                page_idx = max(0, min(total_pages - 1, int(part) - 1))
                pages.add(page_idx)
        
        return sorted(list(pages))
    
    def preprocess_text(self, raw_text: str) -> str:
        """
        Preprocess extracted text (from direct PDF extraction or OCR).
        """
        if not raw_text.strip():
            return ""
        
        # Remove page separators but keep page structure info
        text = re.sub(r'--- Page \d+ \(No text.*?\) ---', '', raw_text)
        text = re.sub(r'--- Page \d+ ---\s*', '\n[PAGE BREAK]\n', text)
        
        # Clean up the text
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        text = " ".join(lines)
        text = re.sub(r'\s+', ' ', text)
        
        # Unicode normalization
        text = unicodedata.normalize('NFC', text)
        
        # Remove most artifacts but keep essential punctuation and page breaks
        text = re.sub(r'[^\u0900-\u097Fa-zA-Z0-9\s.,!?()[\]-]', '', text)
        text = re.sub(r'\[PAGE BREAK\]', '\n\n', text)
        
        return text.strip()
    
    def extract_business_info_from_text(self, text: str, product_override: Optional[str] = None, 
                                      market_override: Optional[str] = None) -> dict:
        """
        Use Gemini to extract structured business information from PDF text.
        """
        if not text.strip():
            raise ValueError("No text extracted from PDF. Please check if the PDF contains readable content.")
        
        # Truncate text if too long (Gemini has input limits)
        max_chars = 30000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n... [Content truncated for analysis]"
        
        extraction_prompt = f"""
        Analyze the following text extracted from a business document/PDF and identify key business information:

        DOCUMENT TEXT:
        {text}

        Extract and return ONLY the following information in this exact format:
        Product Name: [product/service/company name]
        Description: [concise business description in one line]
        Target Market: [primary target market/customer segment]

        Instructions:
        - Look for the main product/service being offered
        - Identify the core value proposition or business model
        - Determine the primary customer segment or market
        - If multiple products/services exist, focus on the primary one
        - Make reasonable assumptions based on available context
        - Be specific and avoid generic terms
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
            'product': 'Unknown Product/Service',
            'description': 'Business description not available from document',
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
            "You are a business strategy consultant. Create a comprehensive Business Model Canvas based on the provided business information.",
            "",
            f"BUSINESS INFORMATION:",
            f"Product/Service: {product}",
            f"Description: {description}",
            f"Target Market: {market}",
        ]
        
        if original_text and len(original_text.strip()) > 50:
            # Include relevant excerpts from original document
            context_text = original_text[:2000] + "..." if len(original_text) > 2000 else original_text
            lines.extend([
                "",
                f"ADDITIONAL CONTEXT FROM SOURCE DOCUMENT:",
                context_text
            ])
        
        lines.extend([
            "",
            "CREATE A BUSINESS MODEL CANVAS with the following 9 sections:",
            "Provide 4-7 specific, actionable bullet points for each section.",
            "",
            "1. CUSTOMER SEGMENTS",
            "2. VALUE PROPOSITIONS", 
            "3. CHANNELS",
            "4. CUSTOMER RELATIONSHIPS",
            "5. REVENUE STREAMS",
            "6. KEY ACTIVITIES",
            "7. KEY RESOURCES",
            "8. KEY PARTNERS",
            "9. COST STRUCTURE",
            "",
            "REQUIREMENTS:",
            "- Make each point specific and actionable (avoid generic statements)",
            "- Base recommendations on the business context provided",
            "- Consider industry best practices and realistic implementation",
            "- Format each section clearly with bullet points",
            "- Ensure recommendations are practical for the identified market"
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
    
    def process_pdf_to_bmc(self, pdf_path: str, page_range: Optional[str] = None,
                          product_override: Optional[str] = None,
                          market_override: Optional[str] = None, 
                          ocr_only: bool = False,
                          show_intermediate: bool = False) -> str:
        """
        Complete pipeline: PDF -> Text Extraction/OCR -> Business Info Extraction -> BMC Generation
        """
        print(f"📄 Processing PDF: {pdf_path}")
        
        if page_range:
            print(f"📋 Processing pages: {page_range}")
        
        # Step 1: Try direct text extraction first (unless OCR-only is specified)
        extracted_text = ""
        
        if not ocr_only:
            print("📝 Attempting direct text extraction...")
            text_content, has_text = self.extract_text_from_pdf(pdf_path, page_range)
            
            if has_text and text_content.strip():
                extracted_text = text_content
                print("✅ Direct text extraction successful")
            else:
                print("⚠️  No extractable text found, switching to OCR...")
                ocr_only = True
        
        # Step 2: Use OCR if needed
        if ocr_only or not extracted_text.strip():
            print("🔍 Converting PDF to images for OCR processing...")
            image_page_pairs = self.convert_pdf_to_images(pdf_path, page_range)
            
            print(f"🖼️  Processing {len(image_page_pairs)} page(s) with OCR...")
            ocr_text = self.extract_text_from_pdf_images(image_page_pairs)
            
            if ocr_text.strip():
                extracted_text = ocr_text
                print("✅ OCR text extraction completed")
            else:
                raise ValueError("No text could be extracted from the PDF using either method.")
        
        # Step 3: Preprocess the extracted text
        clean_text = self.preprocess_text(extracted_text)
        
        if show_intermediate:
            print(f"\n📝 Extracted text preview (first 500 chars):")
            print(f"{clean_text[:500]}{'...' if len(clean_text) > 500 else ''}\n")
        
        # Step 4: Extract business information
        print("🎯 Analyzing business information...")
        business_info = self.extract_business_info_from_text(
            clean_text, product_override, market_override
        )
        
        if show_intermediate:
            print(f"📊 Identified business info:")
            print(f"  Product: {business_info['product']}")
            print(f"  Description: {business_info['description']}")
            print(f"  Market: {business_info['market']}\n")
        
        # Step 5: Generate Business Model Canvas
        print("🏗️ Generating Business Model Canvas...")
        bmc = self.generate_bmc_from_info(business_info, clean_text)
        
        return bmc


def main():
    parser = argparse.ArgumentParser(
        description="Generate Business Model Canvas from PDF business document"
    )
    parser.add_argument(
        "--pdf", 
        required=True, 
        help="Path to PDF containing business information"
    )
    parser.add_argument(
        "--pages",
        required=False,
        help="Page range to process (e.g., '1-3', '1,3,5', '1-3,5-7'). Default: all pages"
    )
    parser.add_argument(
        "--product", 
        required=False, 
        help="Override product/service name (optional)"
    )
    parser.add_argument(
        "--market", 
        required=False, 
        help="Override target market (optional)"
    )
    parser.add_argument(
        "--ocr-only", 
        action="store_true",
        help="Force OCR processing even if text can be extracted directly"
    )
    parser.add_argument(
        "--show-steps", 
        action="store_true",
        help="Show intermediate processing steps and extracted content"
    )
    
    args = parser.parse_args()
    
    try:
        pipeline = PDFToBMCPipeline()
        canvas = pipeline.process_pdf_to_bmc(
            args.pdf, 
            args.pages,
            args.product, 
            args.market,
            args.ocr_only,
            args.show_steps
        )
        
        print("\n" + "="*60)
        print("📋 BUSINESS MODEL CANVAS")
        print("="*60 + "\n")
        print(canvas)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())