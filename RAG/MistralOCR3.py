from mistralai import Mistral
from dotenv import load_dotenv
import datauri
import os
import argparse
import PyPDF2
import requests
from urllib.parse import urlparse

SUPPORTED_EXTENSIONS = {".pdf", ".jpeg", ".jpg"}

# source https://www.datacamp.com/de/tutorial/mistral-ocr

def save_image(image, output_dir):
    parsed = datauri.parse(image.image_base64)
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, f"{image.id}"), "wb") as file:
        file.write(parsed.data)

def create_markdown_file(ocr_response, output_filename="output.md"):
    with open(output_filename, "wt") as f:
        for page in ocr_response.pages:
            f.write(page.markdown)
            for image in page.images:
                save_image(image, os.path.dirname(output_filename))

def upload_document(filename, client):
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
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            return len(reader.pages)
    except Exception as e:
        print(f"Error counting pages in PDF {pdf_path}: {str(e)}")
        return 0

def count_url_pages(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception for bad status codes
        with open('temp.pdf', 'wb') as file:
            file.write(response.content)
        page_count = count_pdf_pages('temp.pdf')
        os.remove('temp.pdf')
        return page_count
    except Exception as e:
        print(f"Error counting pages from URL {url}: {str(e)}")
        return 0
    finally:
        if os.path.exists('temp.pdf'):
            os.remove('temp.pdf')

def calculate_cost(page_count):
    return page_count * 0.002

def check_api_key(api_key):
    try:
        probe_client = Mistral(api_key=api_key)
        probe_client.models.list()
        return True
    except Exception:
        return False

def is_url(value):
    return value.startswith(("http://", "https://"))

def collect_inputs(input_arg):
    if is_url(input_arg):
        return [
            {
                "type": "url",
                "source": input_arg,
                "name": input_arg,
                "ext": None,
            }
        ]

    if os.path.isdir(input_arg):
        collected = []
        for entry in sorted(os.listdir(input_arg)):
            path = os.path.join(input_arg, entry)
            if not os.path.isfile(path):
                continue
            ext = os.path.splitext(entry)[1].lower()
            if ext in SUPPORTED_EXTENSIONS:
                collected.append(
                    {
                        "type": "file",
                        "source": path,
                        "name": entry,
                        "ext": ext,
                    }
                )
        return collected

    if os.path.isfile(input_arg):
        ext = os.path.splitext(input_arg)[1].lower()
        if ext in SUPPORTED_EXTENSIONS:
            return [
                {
                    "type": "file",
                    "source": input_arg,
                    "name": os.path.basename(input_arg),
                    "ext": ext,
                }
            ]

    return []

def derive_output_dir_name(source):
    if is_url(source):
        parsed = urlparse(source)
        filename = os.path.basename(parsed.path)
        if filename:
            return os.path.splitext(filename)[0] or "url"
        if parsed.netloc:
            return parsed.netloc.replace(":", "_")
        return "url"
    return os.path.splitext(os.path.basename(source))[0]

def count_pages_for_item(item):
    try:
      if item["type"] == "url":
          return count_url_pages(item["source"])
      if item.get("ext") == ".pdf":
          return count_pdf_pages(item["source"])
      return 1
    except Exception as e:
        print(f"Error counting pages for {item['name']}: {str(e)}")
        return 0

def print_cost_table(items):
    name_header = "Name"
    pages_header = "Pages"
    cost_header = "Cost ($)"
    name_width = max(len(name_header), *(len(item["name"]) for item in items)) if items else len(name_header)
    rows = []
    total_cost = 0
    total_pages = 0
    for item in items:
        pages = item["page_count"]
        cost = item["cost"]
        total_cost += cost
        total_pages += pages
        rows.append((item["name"], pages, cost))

    print("Planned documents:")
    print(f"{name_header.ljust(name_width)}  {pages_header:>7}  {cost_header:>10}")
    print("-" * (name_width + 21))
    for name, pages, cost in rows:
        print(f"{name.ljust(name_width)}  {str(pages).rjust(7)}  {cost:10.4f}")
    print("-" * (name_width + 21))
    print(f"{'TOTAL'.ljust(name_width)}  {str(total_pages).rjust(7)}  {total_cost:10.4f}")
    return total_cost

def main():
    parser = argparse.ArgumentParser(description="Mistral OCR CLI App")
    parser.add_argument("input", nargs="?", default="input", help="Input folder, PDF, JPEG, or URL (default: input folder)")
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

    inputs = collect_inputs(args.input)
    if not inputs:
        print("No supported inputs found. Please provide a folder, PDF/JPEG file, or URL.")
        return

    for item in inputs:
        item["page_count"] = count_pages_for_item(item)
        item["cost"] = calculate_cost(item["page_count"])

    total_cost = print_cost_table(inputs)
    confirm = input("Proceed with OCR using the estimated costs above? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Operation cancelled.")
        return

    for item in inputs:
        output_dir = os.path.join(args.outputDir, derive_output_dir_name(item["source"]))
        if os.path.exists(output_dir):
            print(f"Output directory {output_dir} already exists. Skipping {item['name']}.")
            continue
        os.makedirs(output_dir, exist_ok=True)

        if item["type"] == "url":
            document_spec = {
                "type": "document_url",
                "document_url": item["source"],
            }
        else:
            document_spec = {
                "type": "document_url",
                "document_url": upload_document(item["source"], client),
            }

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document=document_spec,
            include_image_base64=args.loadImages,
        )

        create_markdown_file(ocr_response, os.path.join(output_dir, f"{derive_output_dir_name(item['source'])}.md"))

if __name__ == "__main__":
    main()