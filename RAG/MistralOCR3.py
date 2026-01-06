from mistralai import Mistral
from dotenv import load_dotenv
import datauri
import os

# source https://www.datacamp.com/de/tutorial/mistral-ocr

def save_image(image):
    parsed = datauri.parse(image.image_base64)
    with open(image.id, "wb") as file:
      file.write(parsed.data)

def create_markdown_file(ocr_response, output_filename = "output.md"):
  with open(output_filename, "wt") as f:
    for page in ocr_response.pages:
      f.write(page.markdown)
      for image in page.images:
        save_image(image)

def upload_pdf(filename):
  uploaded_pdf = client.files.upload(
    file={
      "file_name": filename,
      "content": open(filename, "rb"),
    },
    purpose="ocr"
  )
  signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
  return signed_url.url

load_dotenv()
api_key = os.environ["MISTRAL_API_KEY"]
client = Mistral(api_key=api_key)

# handle url
# ocr_response = client.ocr.process(
#   model="mistral-ocr-latest",
#   document={
#     "type": "document_url",
#     "document_url": "https://arxiv.org/pdf/2501.00663",
#   },
#   include_image_base64=True,
# )

# handle .pdf
ocr_response = client.ocr.process(
  model="mistral-ocr-latest",
  document={
    "type": "document_url",
    "document_url": upload_pdf("RAG/input.pdf"),
  },
  include_image_base64=True,
)

# handle .jpeg
# ocr_response = client.ocr.process(
#   model="mistral-ocr-latest",
#   document={
#     "type": "image_url",
#     "image_url": load_image("receipt.jpeg"),
#   },
# )

print(ocr_response)

create_markdown_file(ocr_response, "mistral_ocr_output.md")