import os
import json
import zipfile
import argparse
import datetime
import logging
from tqdm import tqdm
import document_utils
from ai_engine import AIEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def process_zip(zip_path, output_json, base_url, api_key):
    """
    Extracts resumes from a ZIP file, parses text, and uses LLM to generate JSON profiles.
    Saves the result as a list of objects compatible with the Resume Matcher App.
    """

    # Initialize AI Engine
    client = AIEngine(base_url, api_key)

    processed_data = []

    if not os.path.exists(zip_path):
        logging.error(f"Input file not found: {zip_path}")
        return

    try:
        with zipfile.ZipFile(zip_path, 'r') as z:
            # Filter out macOS hidden files and directories
            file_list = [f for f in z.namelist() if not f.startswith('__MACOSX') and not f.startswith('.') and not f.endswith('/')]

            print(f"\n📂 Found {len(file_list)} files in {zip_path}")

            for filename in tqdm(file_list, desc="Processing Resumes"):
                try:
                    # Read file content
                    with z.open(filename) as f:
                        file_bytes = f.read()

                    # Determine file type
                    clean_filename = os.path.basename(filename)
                    file_ext = clean_filename.lower().split('.')[-1]
                    text = ""

                    # Extract Text
                    if file_ext == 'pdf':
                        # Force OCR for offline batch to be safe
                        text = document_utils.extract_text_from_pdf(file_bytes, use_ocr=True)
                    elif file_ext == 'docx':
                        text = document_utils.extract_text_from_docx(file_bytes)
                    elif file_ext in ['txt', 'md']:
                        text = str(file_bytes, 'utf-8', errors='ignore')
                    else:
                        logging.warning(f"Skipping unsupported file type: {clean_filename}")
                        continue

                    # Skip empty text or failed OCR
                    if not text or len(text.strip()) < 50 or text.startswith("[OCR Failed"):
                        logging.warning(f"Skipping {clean_filename}: Text extraction failed or empty.")
                        continue

                    # AI Analysis
                    # We use the existing analyze_resume function which returns the profile dict
                    profile = client.analyze_resume(text)

                    # Structure for App Import
                    record = {
                        "filename": clean_filename,
                        "content": text,
                        "profile": profile, # This is the JSON dict from LLM
                        "upload_date": datetime.datetime.now().isoformat(),
                        "tags": None # Default to no tags, user can add in app
                    }

                    processed_data.append(record)

                except Exception as e:
                    logging.error(f"Failed to process {filename}: {e}")
                    continue

        # Save to Output File
        with open(output_json, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, indent=2)

        print(f"\n✅ Successfully processed {len(processed_data)} resumes.")
        print(f"📁 Output saved to: {output_json}")

    except zipfile.BadZipFile:
        logging.error("The input file is not a valid ZIP archive.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TalentScout Offline Resume Processor")
    parser.add_argument("--input", required=True, help="Path to input ZIP file containing resumes")
    parser.add_argument("--output", default="processed_resumes.json", help="Path to output JSON file")
    parser.add_argument("--url", default="http://localhost:1234/v1", help="Local LLM Base URL")
    parser.add_argument("--key", default="lm-studio", help="API Key")

    args = parser.parse_args()

    process_zip(args.input, args.output, args.url, args.key)
