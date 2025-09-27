import os
from google.cloud import vision
import re
import unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image using Google Cloud Vision OCR."""
    client = vision.ImageAnnotatorClient()

    with open(image_path, "rb") as f:
        content = f.read()

    image = vision.Image(content=content)
    
    # Use document_text_detection (better for handwriting)
    response = client.document_text_detection(image=image)

    if response.error.message:
        raise Exception(f"Vision API Error: {response.error.message}")

    return response.full_text_annotation.text

def preprocess_ocr_text(raw_text: str, transliterate_to_latin=True, title_case=True):
    
    """
    Preprocess raw OCR output into clean text.
    Steps:
    1. Strip lines and empty lines
    2. Normalize spaces
    3. Unicode normalization
    4. Remove non-text artifacts
    5. Optional: Spell correction
    6. Optional: Transliteration to Latin
    7. Optional: Capitalization
    """
    
    # Step 1: Strip lines and remove empty lines
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    
    # Step 2: Join lines and normalize spaces
    text = " ".join(lines)
    text = re.sub(r'\s+', ' ', text)
    
    # Step 3: Unicode normalization
    text = unicodedata.normalize('NFC', text)
    
    # Step 4: Remove non-text artifacts (keep Devanagari, Latin, numbers, spaces)
    text = re.sub(r'[^ऀ-ॿa-zA-Z0-9\s]', '', text)
    return text

    

if __name__ == "__main__":
    # 👇 Update this path to your actual file
    image_path = r"C:\Users\RAHIL\Documents\Github\CSI_Hackathon\images\test4.jpg"
    
    text = extract_text_from_image(image_path)
    final_text = preprocess_ocr_text(text)
    print("✅ Extracted Text:\n")
    print(final_text)
