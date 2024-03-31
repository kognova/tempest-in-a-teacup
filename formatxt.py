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

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

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

def convert_and_encode_pdf(pdf_path):
    encoded = []
    images = convert_from_path(pdf_path, 300)
    for image in images:
        encoded.append(resize_and_encode_image(image))
    return encoded

def send_request(encoded_image, max_retries=3, retry_delay=10):
    retry_count = 0
    while retry_count < max_retries:
        try:
            message = client.messages.create(
                #model="claude-3-opus-20240229",
                model="claude-3-sonnet-20240229",
                #model="claude-3-haiku-20240307",
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
                print(f"Error: {message.content}")
                return "Error"
        except Exception as e:
            retry_count += 1
            if retry_count < max_retries:
                print(f"Request failed. Retrying in {retry_delay} seconds... (Attempt {retry_count}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Request failed after {max_retries} retries. Error: {str(e)}")
                return "Request Timeout"


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
