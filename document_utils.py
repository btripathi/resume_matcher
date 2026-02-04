import pypdf
import docx
import io
import pytesseract
import json
import re
import ast
from PIL import Image

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False

def extract_text_from_docx(file_bytes):
    """
    Extracts text from DOCX files, robustly handling both standard paragraphs
    and text hidden inside tables (common in resume layouts).
    """
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        full_text = []

        # 1. Extract text from standard paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text)

        # 2. Extract text from tables (Crucial for resumes with sidebars/grid layouts)
        for table in doc.tables:
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    for para in cell.paragraphs:
                        if para.text.strip():
                            row_text.append(para.text)
                # Join cell content with pipe to maintain some structure
                if row_text:
                    full_text.append(" | ".join(row_text))

        text = "\n".join(full_text)
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
        # Increased threshold to 200 to catch PDFs that only have minimal metadata text
        if text_len < 200 and use_ocr:
            log("Text sparse (<200 chars). Triggering OCR fallback...")

            if PDF2IMAGE_AVAILABLE:
                try:
                    images = convert_from_bytes(file_bytes)
                    log(f"Converted PDF to {len(images)} images. Running Tesseract...")

                    ocr_text = ""
                    for i, img in enumerate(images):
                        # Use simple config to handle layout analysis
                        page_text = pytesseract.image_to_string(img, config='--psm 6')
                        ocr_text += page_text + "\n"
                        log(f"OCR Page {i+1} done ({len(page_text)} chars)")

                    if not ocr_text.strip():
                         return "[OCR Failed: No text found in images]"

                    return ocr_text
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
    """
    Robust extraction of JSON from LLM markdown response.
    Uses hex escape sequences for backticks to prevent display truncation.
    """
    if not text or not isinstance(text, str):
        return None

    text_content = None

    try:
        # Backticks using hex escape (0x60)
        backticks = "\x60\x60\x60"
        pattern = rf"{backticks}\s*(?:json)?\s*(.*?)\s*{backticks}"

        # 1. Extract fenced JSON
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            text_content = match.group(1).strip()
        else:
            # 2. Fallback: outermost braces
            start = text.find('{')
            end = text.rfind('}')
            if start == -1 or end == -1 or end <= start:
                # Fallback 2.1: Try finding list brackets if object failed
                start_list = text.find('[')
                end_list = text.rfind(']')
                if start_list != -1 and end_list != -1 and end_list > start_list:
                    text_content = text[start_list:end_list+1].strip()
                else:
                    return None
            else:
                text_content = text[start:end+1].strip()

        # Normalize smart quotes (common LLM issue)
        text_content = text_content.replace("\u2019", "'")

        # 3. Strict JSON first
        return json.loads(text_content)

    except json.JSONDecodeError:
        # 4. Python literal fallback
        try:
            return ast.literal_eval(text_content)
        except Exception:
            return None
    except Exception:
        return None
