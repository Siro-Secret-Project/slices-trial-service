import PyPDF2

def clean_text(text):
    """
    Cleans the text by removing newlines, tabs, and extra spaces,
    resulting in a single continuous string.
    """
    return " ".join(text.split())

def extract_sections(pdf_path, index_keys):
    """
    Splits the Main PDF into sections based on the page numbers extracted from the index.
    For each section, text is extracted from the starting page to just before the next section starts.
    After extraction, the text is cleaned to remove newline, tab, and extra whitespace characters.
    Sections with a starting page that exceeds the number of pages in the document are skipped.
    """
    section_text = {}
    with open(pdf_path, "rb") as f:
        pdf = PyPDF2.PdfReader(f)
        num_pages = len(pdf.pages)
        # Sort sections by the starting page number
        sections = sorted(index_keys.items(), key=lambda x: x[1])

        # Filter out sections that start beyond the number of pages
        valid_sections = []
        for section, start_page in sections:
            if start_page < num_pages:
                valid_sections.append((section, start_page))
            else:
                print(f"Warning: Section '{section}' with start page {start_page+1} is out of range (Total pages: {num_pages}). Skipping.")

        for i, (section, start_page) in enumerate(valid_sections):
            # Determine the end page for the current section:
            if i < len(valid_sections) - 1:
                # End at one page before the next section starts.
                end_page = valid_sections[i+1][1] - 1
            else:
                # Last section goes to the end of the document.
                end_page = num_pages - 1

            text = ""
            # Extract text while ensuring we do not exceed page limits.
            for p in range(start_page, min(end_page + 1, num_pages)):
                page_text = pdf.pages[p].extract_text()
                if page_text:
                    text += page_text + " "
            # Clean the extracted text.
            section_text[section] = clean_text(text)
    return section_text