"""
PDF Text Detection Pipeline with Intelligent Structuring

This script processes PDF documents (both text-based and image-based) to extract
and structure text content using OCR and Gemini AI.

Features:
- Handles text-based PDFs with direct text extraction
- Processes image-based/scanned PDFs using OCR
- Converts PDF pages to images for OCR processing
- Uses Gemini AI to intelligently structure extracted text
- Combines text from multiple pages
- Clean text preprocessing and formatting

Setup:
- Set `GEMINI_API_KEY` in your environment (Google AI Studio key)
- Set up Google Cloud Vision API credentials for OCR
- Install deps: `pip install -r requirements.txt`

Dependencies needed:
- PyMuPDF (fitz): `pip install PyMuPDF`
- Pillow: `pip install Pillow`
- pdf2image: `pip install pdf2image` (optional, fallback to PyMuPDF)
- google-generativeai: `pip install google-generativeai`
- google-cloud-vision: `pip install google-cloud-vision`

Usage:
python pdf_text_detector.py --pdf "path/to/document.pdf"
python pdf_text_detector.py --pdf "path/to/document.pdf" --pages "1-3"
python pdf_text_detector.py --pdf "path/to/document.pdf" --ocr-only
python pdf_text_detector.py --pdf "path/to/document.pdf" --no-structure
python pdf_text_detector.py --pdf "path/to/document.pdf" --output "extracted_text.txt"
"""

import os
import argparse
from typing import Optional, List, Tuple
import re
import io
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


class PDFTextDetector:
    def __init__(self, use_gemini_structuring: bool = True):
        """Initialize the text detector with Vision API and optionally Gemini configuration."""
        self.vision_client = vision.ImageAnnotatorClient()
        self.use_gemini_structuring = use_gemini_structuring
        
        if self.use_gemini_structuring:
            if load_dotenv:
                load_dotenv()
            
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not self.gemini_api_key:
                print("⚠️  Warning: GEMINI_API_KEY not found. Text structuring will be disabled.")
                self.use_gemini_structuring = False
            else:
                genai.configure(api_key=self.gemini_api_key)
    
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
        all_text = []
        
        for pil_image, page_num in image_page_pairs:
            print(f"  📄 Processing page {page_num + 1} with OCR...")
            
            # Convert PIL image to bytes
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
    
    def structure_text_with_gemini(self, raw_text: str) -> str:
        """
        Use Gemini to structure and clean up the extracted text.
        """
        if not self.use_gemini_structuring:
            return raw_text
        
        structuring_prompt = f"""
        Please analyze and restructure the following text that was extracted from a PDF using OCR. 
        The text may be jumbled, have formatting issues, or missing punctuation.

        Raw extracted text:
        {raw_text}

        Please:
        1. Organize the information into logical sections with clear headings
        2. Fix obvious OCR errors and formatting issues
        3. Add proper punctuation and capitalization where needed
        4. Group related information together
        5. Maintain all the original information - don't remove or add content
        6. If it appears to be a business profile or form, structure it accordingly
        7. Use markdown formatting for better readability

        Return only the structured text without any explanations or comments.
        """
        
        try:
            model_name = self._choose_available_model()
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(structuring_prompt)
            
            structured_text = response.text or raw_text
            return structured_text.strip()
            
        except Exception as e:
            print(f"⚠️  Gemini structuring failed: {e}")
            print("📝 Returning original text...")
            return raw_text
    
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
    
    def process_pdf_text_detection(self, pdf_path: str, page_range: Optional[str] = None,
                                  ocr_only: bool = False,
                                  show_intermediate: bool = False,
                                  output_file: Optional[str] = None,
                                  structure_text: bool = True) -> str:
        """
        Complete pipeline: PDF -> Text Extraction/OCR -> Text Processing -> Optional Structuring
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
        
        # Step 4: Structure text with Gemini (if enabled)
        structured_text = clean_text
        if structure_text and self.use_gemini_structuring:
            print("🏗️  Structuring text with Gemini...")
            structured_text = self.structure_text_with_gemini(clean_text)
            print("✅ Text structuring completed")
        
        if show_intermediate:
            print(f"\n📝 Raw extracted text:")
            print("-" * 50)
            print(extracted_text)
            print("-" * 50)
            print(f"\n🧹 Cleaned text:")
            print("-" * 50)
            print(clean_text)
            print("-" * 50)
            if structure_text and self.use_gemini_structuring:
                print(f"\n🏗️  Structured text:")
                print("-" * 50)
                print(structured_text)
                print("-" * 50)
        
        # Step 5: Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(structured_text)
            print(f"💾 Text saved to: {output_file}")
        
        return structured_text


def main():
    parser = argparse.ArgumentParser(
        description="Extract and detect text from PDF documents with intelligent structuring"
    )
    parser.add_argument(
        "--pdf", 
        required=True, 
        help="Path to PDF file"
    )
    parser.add_argument(
        "--pages",
        required=False,
        help="Page range to process (e.g., '1-3', '1,3,5', '1-3,5-7'). Default: all pages"
    )
    parser.add_argument(
        "--ocr-only", 
        action="store_true",
        help="Force OCR processing even if text can be extracted directly"
    )
    parser.add_argument(
        "--show-steps", 
        action="store_true",
        help="Show intermediate processing steps and raw extracted content"
    )
    parser.add_argument(
        "--no-structure", 
        action="store_true",
        help="Skip text structuring with Gemini (return raw cleaned text only)"
    )
    parser.add_argument(
        "--output", 
        required=False,
        help="Save extracted text to file (optional)"
    )
    
    args = parser.parse_args()
    
    try:
        detector = PDFTextDetector(use_gemini_structuring=not args.no_structure)
        extracted_text = detector.process_pdf_text_detection(
            args.pdf, 
            args.pages,
            args.ocr_only,
            args.show_steps,
            args.output,
            structure_text=not args.no_structure
        )
        
        print("\n" + "="*60)
        if args.no_structure:
            print("📝 EXTRACTED TEXT (RAW)")
        else:
            print("📝 STRUCTURED TEXT")
        print("="*60 + "\n")
        print(extracted_text)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())