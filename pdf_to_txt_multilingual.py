"""
Enhanced PDF Text Detection Pipeline with Hindi/English Optimization

This script processes PDF documents (both text-based and image-based) to extract
and structure text content using OCR and Gemini AI, optimized for Hindi and English.

Features:
- Enhanced Hindi and English language support
- Automatic text file saving with restructuring
- Improved OCR accuracy for Indic scripts
- Better text preprocessing for multilingual content
- Intelligent structuring with language-aware prompts

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
- langdetect: `pip install langdetect`

Usage:
python pdf_text_detector_enhanced.py --pdf "path/to/document.pdf"
python pdf_text_detector_enhanced.py --pdf "path/to/document.pdf" --pages "1-3"
python pdf_text_detector_enhanced.py --pdf "path/to/document.pdf" --ocr-only
python pdf_text_detector_enhanced.py --pdf "path/to/document.pdf" --output "custom_output.txt"
"""

import os
import argparse
from typing import Optional, List, Tuple, Dict
import re
import io
import string
import langdetect
from pathlib import Path
from datetime import datetime

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


class EnhancedPDFTextDetector:
    def __init__(self, gemini_api_key: Optional[str] = None):
        """Initialize the enhanced text detector with Vision API and Gemini configuration."""
        self.vision_client = vision.ImageAnnotatorClient()
        
        # Setup Gemini API
        if load_dotenv:
            load_dotenv()
        
        # Use provided API key or fallback to environment variable
        self.gemini_api_key = gemini_api_key or os.getenv("GEMINI_API_KEY") or "AIzaSyDdu5zOLyaZgZcbIEFmR3dB_HSPmhKGjpM"
        
        if self.gemini_api_key:
            genai.configure(api_key=self.gemini_api_key)
            print("✅ Gemini API configured successfully")
        else:
            print("⚠️ No Gemini API key found. Text restructuring will be disabled.")
    
    def extract_text_from_pdf(self, pdf_path: str, page_range: Optional[str] = None) -> Tuple[str, bool]:
        """
        Extract text from PDF using PyMuPDF with enhanced Hindi/English support.
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
                # Try different text extraction methods for better Unicode support
                page_text = page.get_text("text").strip()  # Default method
                
                if not page_text:
                    # Try dict method for better formatting
                    text_dict = page.get_text("dict")
                    page_text = self._extract_from_dict(text_dict)
                
                if page_text:
                    # Clean and normalize text immediately
                    page_text = self._clean_unicode_text(page_text)
                    extracted_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                    text_found = True
                else:
                    extracted_text.append(f"--- Page {page_num + 1} (No text found) ---")
        
        doc.close()
        
        full_text = "\n\n".join(extracted_text)
        return full_text, text_found
    
    def _extract_from_dict(self, text_dict: dict) -> str:
        """Extract text from PyMuPDF dictionary format with better Unicode handling."""
        text_lines = []
        
        for block in text_dict.get("blocks", []):
            if "lines" in block:
                block_lines = []
                for line in block["lines"]:
                    line_text = ""
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        if span_text:
                            line_text += span_text
                    if line_text.strip():
                        block_lines.append(line_text.strip())
                
                if block_lines:
                    text_lines.append(" ".join(block_lines))
        
        return "\n".join(text_lines)
    
    def _clean_unicode_text(self, text: str) -> str:
        """Clean and normalize Unicode text for Hindi/English."""
        # Unicode normalization - NFKC works best for Indic scripts
        text = unicodedata.normalize('NFKC', text)
        
        # Remove control characters but preserve line breaks
        text = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', text)
        
        # Fix common OCR issues in Hindi text
        text = re.sub(r'([।])([^\s])', r'\1 \2', text)  # Add space after devanagari danda
        text = re.sub(r'([a-zA-Z])([।])', r'\1 \2', text)  # Add space before devanagari danda
        
        return text
    
    def convert_pdf_to_images(self, pdf_path: str, page_range: Optional[str] = None, 
                             dpi: int = 300) -> List[Tuple[Image.Image, int]]:
        """
        Convert PDF pages to images for OCR processing with higher DPI for better Hindi recognition.
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
        """Convert using pdf2image library with enhanced settings."""
        try:
            if len(pages_to_process) < len(fitz.open(pdf_path)):
                first_page = min(pages_to_process) + 1
                last_page = max(pages_to_process) + 1
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi,
                    first_page=first_page,
                    last_page=last_page,
                    fmt='PNG',
                    thread_count=1  # Better for memory management
                )
                image_page_pairs = [(img, pages_to_process[i]) for i, img in enumerate(images)]
            else:
                images = convert_from_path(
                    pdf_path, 
                    dpi=dpi,
                    fmt='PNG',
                    thread_count=1
                )
                image_page_pairs = [(img, i) for i, img in enumerate(images)]
            
            return image_page_pairs
        except Exception as e:
            print(f"pdf2image failed: {e}")
            print("Falling back to PyMuPDF...")
            doc = fitz.open(pdf_path)
            return self._convert_with_pymupdf(doc, pages_to_process, dpi)
    
    def _convert_with_pymupdf(self, doc, pages_to_process: List[int], dpi: int) -> List[Tuple[Image.Image, int]]:
        """Convert using PyMuPDF with enhanced settings for text clarity."""
        image_page_pairs = []
        
        # Calculate zoom factor from DPI
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        
        for page_num in pages_to_process:
            if page_num < len(doc):
                page = doc[page_num]
                
                # Render page to image with enhanced settings
                pix = page.get_pixmap(matrix=mat, alpha=False)  # No alpha for better OCR
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Enhance image for better OCR
                pil_image = self._enhance_image_for_ocr(pil_image)
                
                image_page_pairs.append((pil_image, page_num))
        
        doc.close()
        return image_page_pairs
    
    def _enhance_image_for_ocr(self, image: Image.Image) -> Image.Image:
        """Enhance image quality for better OCR results."""
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # You can add more image enhancement here if needed
        # For now, we'll keep it simple to avoid over-processing
        return image
    
    def extract_text_from_pdf_images(self, image_page_pairs: List[Tuple[Image.Image, int]], 
                                   pdf_path: str = "") -> str:
        """Extract text from PDF images using Google Cloud Vision OCR with optimized Hindi/English support."""
        all_text = []
        
        # Detect language hints from filename
        language_hints = self._get_language_hints(pdf_path)
        
        for pil_image, page_num in image_page_pairs:
            print(f"  📄 Processing page {page_num + 1} with OCR...")
            
            # Convert PIL image to bytes
            img_byte_arr = io.BytesIO()
            pil_image.save(img_byte_arr, format='PNG', optimize=True)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Create Vision API image
            image = vision.Image(content=img_byte_arr)
            
            # Configure image context with language hints
            image_context = vision.ImageContext(language_hints=language_hints)
            
            # Use document_text_detection for better layout preservation
            response = self.vision_client.document_text_detection(
                image=image,
                image_context=image_context
            )
            
            if response.error.message:
                print(f"Error on page {page_num + 1}: {response.error.message}")
                continue
            
            # Extract text from response with better formatting
            if response.full_text_annotation:
                page_text = response.full_text_annotation.text
                # Clean the OCR text immediately
                page_text = self._clean_ocr_text(page_text)
                
                if page_text:
                    all_text.append(f"--- Page {page_num + 1} ---\n{page_text}")
                else:
                    all_text.append(f"--- Page {page_num + 1} (No text found) ---")
            else:
                all_text.append(f"--- Page {page_num + 1} (No text found) ---")
        
        return "\n\n".join(all_text)
    
    def _get_language_hints(self, pdf_path: str) -> List[str]:
        """Get language hints based on filename and default priorities."""
        hints = []
        
        # Check filename for language indicators
        filename_lower = pdf_path.lower() if pdf_path else ""
        
        if "hindi" in filename_lower or "हिंदी" in filename_lower:
            hints = ['hi', 'hi', 'hi', 'en']  # Strong Hindi preference
        elif "english" in filename_lower:
            hints = ['en', 'en', 'hi']  # Strong English preference
        else:
            # Default: balanced Hindi-English
            hints = ['hi', 'en', 'hi', 'en']
        
        return hints
    
    def _clean_ocr_text(self, text: str) -> str:
        """Clean OCR text with Hindi/English specific improvements."""
        if not text:
            return ""
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Fix common OCR errors for Hindi
        ocr_fixes = {
            # Common Hindi OCR corrections
            'ा़': 'ा',  # Fix nukta combinations
            'ि़': 'ि',
            '।।': '।',  # Fix double danda
            ' ।': '।',   # Fix space before danda
            '।।': '।',  # Fix repeated danda
        }
        
        for wrong, right in ocr_fixes.items():
            text = text.replace(wrong, right)
        
        # Clean up spacing
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Fix punctuation spacing
        text = re.sub(r'([।])([^\s])', r'\1 \2', text)  # Space after danda
        text = re.sub(r'([.!?])([A-Z])', r'\1 \2', text)  # Space after English punctuation
        
        return text.strip()
    
    def _parse_page_range(self, page_range: Optional[str], total_pages: int) -> List[int]:
        """Parse page range string into list of page numbers (0-indexed)."""
        if not page_range:
            return list(range(total_pages))
        
        pages = []
        for part in page_range.split(','):
            part = part.strip()
            if '-' in part:
                start, end = part.split('-', 1)
                start_idx = max(0, int(start.strip()) - 1)  # Convert to 0-indexed
                end_idx = min(total_pages, int(end.strip()))  # End is inclusive, but cap at total_pages
                pages.extend(range(start_idx, end_idx))
            else:
                page_idx = int(part.strip()) - 1  # Convert to 0-indexed
                if 0 <= page_idx < total_pages:
                    pages.append(page_idx)
        
        # Remove duplicates and sort
        return sorted(list(set(pages)))
    
    def preprocess_text(self, raw_text: str) -> str:
        """Enhanced text preprocessing for Hindi/English content."""
        if not raw_text.strip():
            return ""
        
        # Detect language for appropriate processing
        try:
            lang = langdetect.detect(raw_text)
            print(f"📝 Detected primary language: {lang}")
        except:
            lang = 'unknown'
            print("⚠️ Could not detect language reliably")
        
        # Remove page separators but keep structure
        text = re.sub(r'--- Page \d+ \(No text.*?\) ---\s*', '', raw_text)
        text = re.sub(r'--- Page \d+ ---\s*', '\n[PAGE_BREAK]\n', text)
        
        # Clean up whitespace while preserving paragraph structure
        lines = []
        for line in text.splitlines():
            line = line.strip()
            if line and line != '[PAGE_BREAK]':
                lines.append(line)
            elif line == '[PAGE_BREAK]':
                lines.append('')  # Convert to empty line for paragraph break
        
        # Join lines with proper spacing
        text = '\n'.join(lines)
        
        # Fix multiple spaces but preserve paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs to single space
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Multiple newlines to double newline
        
        # Unicode normalization
        text = unicodedata.normalize('NFKC', text)
        
        # Language-specific cleaning
        if lang == 'hi' or 'hi' in str(lang):
            # Hindi-specific cleaning
            text = re.sub(r'[^\u0900-\u097F\u0A00-\u0A7F\u0B00-\u0B7F\w\s.,!?()[\]"\'-।॥]', '', text)
        else:
            # General cleaning for English and mixed content
            text = re.sub(r'[^\u0900-\u097F\u0A00-\u0A7F\u0B00-\u0B7F\w\s.,!?()[\]"\'-।॥]', '', text)
        
        return text.strip()
    
    def structure_text_with_gemini(self, raw_text: str, detected_lang: str = 'unknown') -> str:
        """Enhanced text structuring with Gemini AI for Hindi/English content."""
        if not self.gemini_api_key or not raw_text.strip():
            print("⚠️ Gemini API not available or no text to structure")
            return raw_text
        
        try:
            # Detect language if not provided
            if detected_lang == 'unknown':
                try:
                    detected_lang = langdetect.detect(raw_text)
                except:
                    detected_lang = 'mixed'
            
            # Create language-specific prompts
            if detected_lang == 'hi' or 'hindi' in detected_lang.lower():
                language_instruction = """
                यह टेक्स्ट मुख्यतः हिंदी में है। कृपया निम्नलिखित बातों का ध्यान रखें:
                - सभी हिंदी वर्णों और विराम चिह्नों को सुरक्षित रखें
                - देवनागरी लिपि की स्वरूपण को बनाए रखें
                - वाक्य संरचना और व्याकरण को सुधारें यदि आवश्यक हो
                """
                format_instruction = "Please structure this Hindi text with proper formatting, headings, and organization."
            elif detected_lang == 'en' or 'english' in detected_lang.lower():
                language_instruction = "The text is primarily in English. Maintain proper English grammar and formatting."
                format_instruction = "Please structure this English text with proper formatting, headings, and organization."
            else:
                language_instruction = """
                यह टेक्स्ट हिंदी और अंग्रेजी दोनों भाषाओं में है। कृपया:
                - हिंदी और अंग्रेजी दोनों भाषाओं के सभी वर्णों को सुरक्षित रखें
                - उचित भाषा अनुसार स्वरूपण करें
                This text contains both Hindi and English. Please preserve all characters from both languages.
                """
                format_instruction = "Please structure this mixed Hindi-English text with proper formatting."
            
            # Enhanced prompt for better structuring
            prompt = f"""
            मैंने एक PDF दस्तावेज़ से टेक्स्ट निकाला है। कृपया इसे व्यवस्थित और पढ़ने योग्य बनाने में मदद करें।
            I have extracted text from a PDF document. Please help structure and format this text.
            
            {language_instruction}
            
            Original extracted text:
            
            {raw_text}
            
            Please structure this text following these guidelines:
            
            1. **Headers and Sections**: Create clear headings using # ## ### for different section levels
            2. **Lists**: Convert appropriate content to bullet points or numbered lists
            3. **Tables**: Format tabular data properly if present
            4. **Paragraphs**: Maintain proper paragraph breaks and flow
            5. **Punctuation**: Fix any obvious punctuation errors
            6. **Spacing**: Ensure proper spacing between words and sentences
            7. **Preserve Content**: DO NOT add new information or remove existing content
            8. **Language Preservation**: Keep all original text in the same language (हिंदी/English)
            9. **Character Preservation**: Maintain all Unicode characters, especially Devanagari script
            10. **Structure Only**: Focus on organizing existing content, not summarizing
            
            {format_instruction}
            
            Return only the structured text without any additional commentary.
            """
            
            print("🔄 Sending text to Gemini for intelligent restructuring...")
            
            # Configure Gemini with optimal settings
            generation_config = {
                'temperature': 0.1,  # Low temperature for consistent formatting
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 8192,
            }
            
            model = genai.GenerativeModel(
                'gemini-pro',
                generation_config=generation_config
            )
            
            response = model.generate_content(prompt)
            
            if response.text:
                structured_text = response.text.strip()
                
                # Clean up markdown artifacts
                structured_text = re.sub(r'^```(?:markdown|text)?\s*', '', structured_text, flags=re.MULTILINE)
                structured_text = re.sub(r'\s*```\s*$', '', structured_text, flags=re.MULTILINE)
                
                # Validate that we haven't lost significant content
                original_length = len(raw_text.replace(' ', '').replace('\n', ''))
                structured_length = len(structured_text.replace(' ', '').replace('\n', ''))
                
                if structured_length < original_length * 0.7:  # Lost more than 30% of content
                    print("⚠️ Gemini response seems to have lost significant content, using original")
                    return raw_text
                
                print(f"✅ Text successfully restructured with Gemini ({len(structured_text)} characters)")
                return structured_text
            else:
                print("⚠️ Gemini returned empty response, using original text")
                return raw_text
                
        except Exception as e:
            print(f"⚠️ Error structuring text with Gemini: {e}")
            return raw_text
    
    def save_text_to_file(self, text: str, pdf_path: str, output_path: Optional[str] = None) -> str:
        """Save extracted and structured text to a file with intelligent naming."""
        if not text.strip():
            print("⚠️ No text to save.")
            return ""
        
        if not output_path:
            # Generate intelligent filename
            pdf_name = Path(pdf_path).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Try to detect document type for better naming
            text_lower = text.lower()
            if 'invoice' in text_lower or 'बिल' in text:
                doc_type = 'invoice'
            elif 'report' in text_lower or 'रिपोर्ट' in text:
                doc_type = 'report'
            elif 'letter' in text_lower or 'पत्र' in text:
                doc_type = 'letter'
            else:
                doc_type = 'document'
            
            output_path = f"{pdf_name}_{doc_type}_extracted_{timestamp}.txt"
        
        # Ensure output directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            # Write with UTF-8 encoding to preserve Hindi characters
            with open(output_path, 'w', encoding='utf-8') as f:
                # Add header with metadata
                f.write(f"# Extracted and Structured Text\n\n")
                f.write(f"**Source PDF:** {Path(pdf_path).name}\n")
                f.write(f"**Extraction Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Text Length:** {len(text)} characters\n\n")
                f.write("---\n\n")
                f.write(text)
                
                # Add footer
                f.write("\n\n---\n")
                f.write("*Text extracted and structured using Enhanced PDF Text Detector*\n")
            
            print(f"✅ Structured text saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error saving file: {e}")
            return ""
    
    def process_pdf(self, pdf_path: str, page_range: Optional[str] = None, 
                   ocr_only: bool = False, output_path: Optional[str] = None) -> Tuple[str, str]:
        """
        Process a PDF document and extract text with automatic structuring and saving.
        
        Returns:
            Tuple of (extracted_text, saved_file_path)
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        print(f"🔍 Processing PDF: {Path(pdf_path).name}")
        
        # Step 1: Try direct text extraction first (unless ocr_only is True)
        extracted_text = ""
        
        if not ocr_only:
            print("📄 Attempting direct text extraction...")
            extracted_text, is_text_based = self.extract_text_from_pdf(pdf_path, page_range)
            
            if is_text_based and extracted_text.strip():
                print("✅ Text successfully extracted directly from PDF!")
            else:
                print("⚠️ No extractable text found, will use OCR...")
                extracted_text = ""
        
        # Step 2: Use OCR if direct extraction failed or was skipped
        if not extracted_text.strip():
            print("🔍 Converting PDF to images for OCR processing...")
            image_page_pairs = self.convert_pdf_to_images(pdf_path, page_range, dpi=300)
            
            if not image_page_pairs:
                raise Exception("Failed to convert PDF to images for OCR processing")
            
            print(f"🖼️ Processing {len(image_page_pairs)} page(s) with OCR...")
            extracted_text = self.extract_text_from_pdf_images(image_page_pairs, pdf_path)
        
        if not extracted_text.strip():
            raise Exception("No text could be extracted from the PDF")
        
        # Step 3: Preprocess the extracted text
        print("🔄 Preprocessing extracted text...")
        processed_text = self.preprocess_text(extracted_text)
        
        # Detect language for better structuring
        try:
            detected_lang = langdetect.detect(processed_text)
        except:
            detected_lang = 'unknown'
        
        # Step 4: Structure the text with Gemini
        print("🤖 Restructuring text with Gemini AI...")
        final_text = self.structure_text_with_gemini(processed_text, detected_lang)
        
        if not final_text.strip():
            print("⚠️ Structuring failed, using processed text")
            final_text = processed_text
        
        # Step 5: Automatically save the structured text
        print("💾 Saving structured text to file...")
        saved_file_path = self.save_text_to_file(final_text, pdf_path, output_path)
        
        print("✅ PDF processing completed successfully!")
        return final_text, saved_file_path


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced PDF Text Extractor for Hindi/English documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_text_detector_enhanced.py --pdf document.pdf
  python pdf_text_detector_enhanced.py --pdf document.pdf --pages "1-5"
  python pdf_text_detector_enhanced.py --pdf document.pdf --ocr-only
  python pdf_text_detector_enhanced.py --pdf document.pdf --output my_output.txt
        """
    )
    
    parser.add_argument(
        "--pdf", 
        required=True, 
        help="Path to the PDF file to process"
    )
    parser.add_argument(
        "--pages", 
        help="Page range to process (e.g., '1-3,5,7-9')"
    )
    parser.add_argument(
        "--ocr-only", 
        action="store_true", 
        help="Skip direct text extraction and use OCR only"
    )
    parser.add_argument(
        "--output", 
        help="Custom path for the output text file"
    )
    parser.add_argument(
        "--api-key",
        help="Gemini API key (can also use GEMINI_API_KEY environment variable)"
    )
    
    args = parser.parse_args()
    
    try:
        # Create enhanced detector
        detector = EnhancedPDFTextDetector(gemini_api_key=args.api_key)
        
        # Process the PDF
        extracted_text, saved_file = detector.process_pdf(
            pdf_path=args.pdf,
            page_range=args.pages,
            ocr_only=args.ocr_only,
            output_path=args.output
        )
        
        # Display results
        print("\n" + "=" * 80)
        print("📋 EXTRACTED AND STRUCTURED TEXT")
        print("=" * 80)
        print(extracted_text)
        print("=" * 80)
        print(f"💾 Text saved to: {saved_file}")
        print("=" * 80)
        
    except FileNotFoundError as e:
        print(f"❌ File Error: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Processing Error: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Ensure Google Cloud Vision API credentials are set up")
        print("2. Check that the PDF file exists and is readable")
        print("3. Verify Gemini API key is valid")
        print("4. Try with --ocr-only flag if direct extraction fails")
        exit(1)


if __name__ == "__main__":
    main()