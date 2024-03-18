import sys
import io
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

def extract_text_from_pdf(pdf_path):
    resource_manager = PDFResourceManager()
    fake_file_handle = io.StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    with open(pdf_path, 'rb') as fh:
        for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
            page_interpreter.process_page(page)

    text = fake_file_handle.getvalue()
    converter.close()
    fake_file_handle.close()

    return text

def format_text(text):
    # Remove extra whitespace and newline characters
    formatted_text = ' '.join(text.split())

    # Add proper punctuation and capitalization
    formatted_text = formatted_text.replace(' .', '.')
    formatted_text = formatted_text.replace(' ,', ',')
    formatted_text = formatted_text.replace(' ?', '?')
    formatted_text = formatted_text.replace(' !', '!')
    formatted_text = formatted_text.replace('( ', '(')
    formatted_text = formatted_text.replace(' )', ')')
    formatted_text = formatted_text.replace(' - ', '-')

    return formatted_text

def main(pdf_path):
    # Extract text from the PDF
    text = extract_text_from_pdf(pdf_path)

    # Format the extracted text
    formatted_text = format_text(text)

    # Save the formatted text
    txt_path = pdf_path.rsplit('.', 1)[0] + '.txt'
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(formatted_text)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python pdf2txt.py <pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    main(pdf_path)