from mistralai import Mistral
from dotenv import load_dotenv
import datauri
import os
import argparse
import PyPDF2
import requests

# source https://www.datacamp.com/de/tutorial/mistral-ocr

def save_image(image, output_dir):
    parsed = datauri.parse(image.image_base64)
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"{image.id}.png"), "wb") as file:
        file.write(parsed.data)

def create_markdown_file(ocr_response, output_filename="output.md"):
    with open(output_filename, "wt") as f:
        for page in ocr_response.pages:
            f.write(page.markdown)
            for image in page.images:
                save_image(image, os.path.dirname(output_filename))

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

def count_pdf_pages(pdf_path):
    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        return len(reader.pages)

def count_url_pages(url):
    response = requests.get(url)
    with open('temp.pdf', 'wb') as file:
        file.write(response.content)
    page_count = count_pdf_pages('temp.pdf')
    os.remove('temp.pdf')
    return page_count

def calculate_cost(page_count):
    return page_count * 0.002

def main():
    parser = argparse.ArgumentParser(description="Mistral OCR CLI App")
    parser.add_argument("input", help="Input folder, PDF, JPEG, or URL")
    parser.add_argument("--outputDir", default="output", help="Output directory")
    parser.add_argument("--MistralApiKey", default=None, help="Mistral API Key")
    parser.add_argument("--loadImages", action="store_true", default=True, help="Load images")

    args = parser.parse_args()

    load_dotenv()
    api_key = args.MistralApiKey or os.environ.get("MISTRAL_API_KEY")

    if not api_key:
        print("MISTRAL_API_KEY not found. Please provide it via --MistralApiKey or set it in the environment.")
        return

    if not check_api_key(api_key):
        print("Invalid or non-working API Key. Please check your API Key.")
        return

    client = Mistral(api_key=api_key)

    if args.input.startswith(('http://', 'https://')):
        page_count = count_url_pages(args.input)
    elif args.input.lower().endswith('.pdf'):
        page_count = count_pdf_pages(args.input)
    else:
        print("Unsupported input type. Please provide a URL, PDF, or JPEG.")
        return

    cost = calculate_cost(page_count)
    print(f"Estimated cost: ${cost:.2f}")
    confirm = input("Do you want to continue? (yes/no): ").strip().lower()
    if confirm != 'yes':
        print("Operation cancelled.")
        return

    output_dir = os.path.join(args.outputDir, os.path.basename(args.input).split('.')[0])
    os.makedirs(output_dir, exist_ok=True)

    if args.input.startswith(('http://', 'https://')):
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": args.input,
            },
            include_image_base64=args.loadImages,
        )
    elif args.input.lower().endswith('.pdf'):
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": upload_pdf(args.input),
            },
            include_image_base64=args.loadImages,
        )
    else:
        print("Unsupported input type. Please provide a URL, PDF, or JPEG.")
        return

    create_markdown_file(ocr_response, os.path.join(output_dir, "output.md"))

if __name__ == "__main__":
    main()