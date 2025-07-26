def print_page(pages, page_number):
    """
    Print content and metadata for a specific page.
    
    Args:
        pages: List of document pages
        page_number: Page number to print (1-based indexing)
    """
    if page_number < 1 or page_number > len(pages):
        print(f"Error: Page number must be between 1 and {len(pages)}")
        return
        
    page = pages[page_number - 1]
    print(f"\nPage {page_number}:")
    print("-" * 50)
    print("Content:")
    print(page.page_content)
    print("\nMetadata:")
    print(page.metadata)
    print("-" * 50)

def main():
    print("Hello from Python in WSL!")
    
    # Test numpy
    
    import os

    from langchain.document_loaders import PyPDFLoader

    import fitz  # PyMuPDF
    from typing import Optional, List, Dict
    from unidecode import unidecode
    from sanskrit_char_mapper import char_map

    doc = fitz.open("data/pdfs/Gaudiya Kanthahara.pdf")
    print(f"\nTotal number of pages: {doc.page_count}")

    """ outline = doc.outline
    print(f"\nOutline entries found: {len(outline)}")
    if len(outline) == 0:
        print("Warning: No outline found in the PDF")
    else:
        print("\nOutline:")
        for level, title, page_num in outline:
            print(f"Level: {level}, Title: {title}, Page: {page_num}") """

    toc = doc.get_toc()
    print(f"\nTOC entries found: {len(toc)}")
    if len(toc) == 0:
        print("Warning: No table of contents found in the PDF")
    else:
        print("\nTable of Contents:")
        for level, title, page_num in toc:
            print(f"Level: {level}, Title: {title}, Page: {page_num}")

     
    # Open file for writing
    with open("page_content.txt", "w", encoding="utf-8") as f:
        for i in range(doc.page_count):
            page = doc[i]
            
            page_label = page.get_label()
            if page_label and "250" <= page_label <= "260":
                f.write(f"\nPage {i+1} (Label: {page_label}) Text:\n")
                f.write("-" * 50 + "\n")
                #f.write(char_map(page.get_text()))
                f.write(page.get_text())
                f.write("\n" + "-" * 50 + "\n")
    
    print("Content has been written to page_content.txt")

    # Close the document
    doc.close()

    
    """ print("\nPage Number | Page Label | Content Length")
    print("-" * 45)
    
    for i, page in enumerate(pages, 1):
        page_label = page.metadata.get('page_label', 'N/A')
        content_length = len(page.page_content)
        print(f"{i:^11} | {page_label:^10} | {content_length:^13}")
     """
    
    # Example: Print page 1
    #print("\nPrinting specific page:")
   # print_page(pages, 227)

      
if __name__ == "__main__":
    main()