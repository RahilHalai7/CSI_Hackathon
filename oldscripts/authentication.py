from google.cloud import vision
client = vision.ImageAnnotatorClient()
print("✅ Authenticated as:", client.transport._credentials.service_account_email)
