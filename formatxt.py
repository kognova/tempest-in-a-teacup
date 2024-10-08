import sys
import base64
from io import BytesIO
from pdf2image import convert_from_path
from PIL import Image
from dotenv import load_dotenv
import os
from PyPDF2 import PdfReader
import anthropic
import time
import traceback
import streamlit as st
import fitz  # PyMuPDF
import logging

load_dotenv()
client = anthropic.Anthropic(api_key=st.secrets['api_keys']['anthropic'])

logging.basicConfig(level=logging.INFO)

def read_text_file(file_path):
    """Reads a text file and returns its content."""
    with open(file_path, 'r') as file:
        return file.read()

prompt = read_text_file(os.path.join(os.path.dirname(os.path.realpath(__file__)), "formatxt.txt"))

def resize_and_encode_image(image, max_size=2048):
    # Resize image, maintaining aspect ratio
    ratio = min(max_size / image.size[0], max_size / image.size[1])
    new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
    resized_image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Encode image to base64
    buffered = BytesIO()
    resized_image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def convert_with_pymupdf(pdf_path):
    try:
        logging.info(f"Attempting to open PDF with PyMuPDF: {pdf_path}")
        doc = fitz.open(pdf_path)
        logging.info(f"PDF opened successfully. Number of pages: {len(doc)}")
        
        encoded_images = []
        for page_num, page in enumerate(doc):
            logging.info(f"Processing page {page_num + 1}")
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')
            encoded_images.append(encoded)
            logging.info(f"Page {page_num + 1} processed successfully")
        
        logging.info("PDF conversion completed successfully")
        return encoded_images
    except Exception as e:
        logging.error(f"Error in convert_with_pymupdf: {str(e)}")
        return None

def convert_and_encode_pdf(pdf_path):
    try:
        logging.info(f"Attempting PDF conversion: {pdf_path}")
        # Try PyMuPDF first
        encoded_images = convert_with_pymupdf(pdf_path)
        if encoded_images is not None:
            return encoded_images
        
        # Fallback to pdf2image if PyMuPDF fails
        logging.info("Falling back to pdf2image")
        images = convert_from_path(pdf_path, 300)
        encoded = []
        for image in images:
            encoded.append(resize_and_encode_image(image))
        return encoded
    except Exception as e:
        logging.error(f"Error converting PDF: {str(e)}")
        raise

def send_request(encoded_image, max_retries=3, retry_delay=10):
    retry_count = 0
    while retry_count < max_retries:
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=4000,
                temperature=0,
                system=prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": encoded_image
                                }
                            },
                            {
                                "type": "text",
                                "text": f"Transcribe the text from this image and preserve all formatting. Only output the text and nothing else."
                            }
                        ]
                    }
                ]
            )
            if message.content[0].text.find("<formatted_clean_text>") > -1:
                return message.content[0].text.split("<formatted_clean_text>")[1].split("</formatted_clean_text>")[0]
            else:
                print(f"Error: Unexpected response format. Full response: {message.content}")
                return "Error: Unexpected response format"
        except Exception as e:
            retry_count += 1
            print(f"Request failed. Error: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            if retry_count < max_retries:
                print(f"Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Request failed after {max_retries} retries.")
                return f"Request failed: {str(e)}"

def format_text_from_pdf(pdf_path, start_page=None, stop_page=None):
    encoded_images = convert_and_encode_pdf(pdf_path)
    responses = []
    for i, encoded_image in enumerate(encoded_images, start=1):
        if start_page and i < start_page:
            continue
        if stop_page and i > stop_page:
            break
        if start_page:
            print(f"\n<<<Processing page {i} of {len(encoded_images)}>>>")
        response = send_request(encoded_image)
        response = response.rstrip()
        print(response)
        responses.append(response)
    return responses

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <PDF-file-path> [start stop]")
    else:
        pdf_path = sys.argv[1]
        start_page = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        stop_page = int(sys.argv[3]) if len(sys.argv) > 3 else 100
        format_text_from_pdf(pdf_path, start_page, stop_page)
