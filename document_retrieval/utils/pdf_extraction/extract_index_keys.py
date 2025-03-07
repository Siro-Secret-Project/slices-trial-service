import re
import PyPDF2

#Extraction Process Start
def extract_index_keys(index_pdf_path):
    """
    Reads all pages of the index PDF and extracts section titles with their corresponding start page numbers.
    Expects each line in the index to be in the format:
        Section Title ... PageNumber
    The section title is cleaned to remove periods and any numbers.
    """
    keys = {}
    with open(index_pdf_path, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        num_pages = len(pdf.pages)
        print(f"Index PDF has {num_pages} pages.")
        for page_number in range(num_pages):
            text = pdf.pages[page_number].extract_text()
            for line in text.splitlines():
                # This pattern expects the line to end with a number (the page number)
                match = re.match(r"^(.*?)\s+(\d+)$", line.strip())
                if match:
                    section, page = match.groups()
                    # Remove periods and digits from the section title
                    clean_section = section.replace('.', '')
                    clean_section = re.sub(r'\d+', '', clean_section).strip()
                    # Convert the page number to 0-index (assuming PDF pages start at 1)
                    keys[clean_section] = int(page) - 1
    return keys