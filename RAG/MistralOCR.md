# Mistral OCR CLI App

This is a command-line interface (CLI) application for processing documents using Mistral's OCR (Optical Character Recognition) service. The app supports processing PDF, JPEG, and JPG files, as well as URLs pointing to PDFs.

## Features

- Process multiple documents at once by providing a directory.
- Estimate costs before processing.
- Save extracted text in Markdown format.
- Save images from the documents.

## Requirements

- Python 3.6 or higher
- Mistral API Key

## Installation

1. Clone the repository:

```bash

```

2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

1. Set your Mistral API Key as an environment variable or provide it via the `--MistralApiKey` argument.

2. Run the app with the desired input:

```bash
python MistralOCR3.py input --outputDir output --MistralApiKey your_api_key
```

Replace `input` with the path to your input file or directory, `output` with your desired output directory, and `your_api_key` with your Mistral API Key.

## Arguments

- `input`: Input folder, PDF, JPEG, or URL (default: input folder)
- `--outputDir`: Output directory (default: output)
- `--MistralApiKey`: Mistral API Key (optional if set as environment variable)
- `--loadImages`: Load images (default: True)

## Example

```bash
python MistralOCR3.py documents --outputDir results --MistralApiKey your_api_key
```

This will process all supported files in the `documents` directory and save the results in the `results` directory.