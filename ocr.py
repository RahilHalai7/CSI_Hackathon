import os
from google.cloud import vision

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

if __name__ == "__main__":
    # 👇 Update this path to your actual file
    image_path = r"C:\Users\RAHIL\Desktop\CSIHackathon\images\test3.jpg"
    
    text = extract_text_from_image(image_path)
    print("✅ Extracted Text:\n")
    print(text)
