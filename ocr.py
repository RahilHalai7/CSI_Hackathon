import os
from google.cloud import vision
from google.oauth2 import service_account

def _load_credentials():
    """Load service account credentials from env or local swift-key.json."""
    # If GOOGLE_APPLICATION_CREDENTIALS is set, let the client pick it up
    env_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if env_path and os.path.isfile(env_path):
        return None  # Using default credentials from env

    # Otherwise, try local swift-key.json next to this file/project root
    repo_root = os.path.dirname(os.path.abspath(__file__))
    local_key = os.path.join(repo_root, "swift-key.json")
    if os.path.isfile(local_key):
        return service_account.Credentials.from_service_account_file(local_key)

    # Fall back to default; client will error if none available
    return None


def extract_text_from_image(image_path: str) -> str:
    """Extract text from an image using Google Cloud Vision OCR."""
    credentials = _load_credentials()
    client = vision.ImageAnnotatorClient(credentials=credentials) if credentials else vision.ImageAnnotatorClient()

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
