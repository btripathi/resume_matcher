import pypdf
import docx
import io
import pytesseract
import json
from PIL import Image

# Removed streamlit import to keep this module UI-agnostic

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

def extract_text_from_docx(file_bytes):
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error reading DOCX: {e}"

def extract_text_from_pdf(file_bytes, use_ocr=False, log_callback=None):
    """
    Extracts text from PDF with optional OCR fallback.
    log_callback: A function that accepts a string message (e.g. logger.log)
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    try:
        log("Attempting native PDF extraction...")

        pdf_reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for i, page in enumerate(pdf_reader.pages):
            content = page.extract_text()
            if content:
                text += content + "\n"

        text_len = len(text.strip())
        log(f"Extracted {text_len} chars via native method.")

        # OCR Fallback
        if text_len < 50 and use_ocr:
            log("Text sparse (<50 chars). Triggering OCR fallback...")

            if PDF2IMAGE_AVAILABLE:
                try:
                    images = convert_from_bytes(file_bytes)
                    log(f"Converted PDF to {len(images)} images. Running Tesseract...")

                    ocr_text = ""
                    for i, img in enumerate(images):
                        page_text = pytesseract.image_to_string(img)
                        ocr_text += page_text + "\n"
                        log(f"OCR Page {i+1} done ({len(page_text)} chars)")

                    return ocr_text if ocr_text.strip() else "[OCR Failed: No text found]"
                except Exception as e:
                    err = f"[OCR Error: {e}]"
                    log(err)
                    return err
            else:
                msg = "[OCR Needed but pdf2image/poppler missing]"
                log(msg)
                return msg

        return text
    except Exception as e:
        return f"Error reading PDF: {e}"

def clean_json_response(text):
    """Robust extraction of JSON from LLM markdown response."""
    try:
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            json_str = text[start:end+1]
            return json.loads(json_str)
        return None
    except json.JSONDecodeError:
        return None
