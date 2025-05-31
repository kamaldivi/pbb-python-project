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

    loader = PyPDFLoader("data/pdfs/Bhakti-Rasamrta-Sindhu-Bindu.pdf")
    pages = loader.load_and_split()

    print(f"\nTotal number of pages: {len(pages)}")
    """ print("\nPage Number | Page Label | Content Length")
    print("-" * 45)
    
    for i, page in enumerate(pages, 1):
        page_label = page.metadata.get('page_label', 'N/A')
        content_length = len(page.page_content)
        print(f"{i:^11} | {page_label:^10} | {content_length:^13}")
     """
    
    # Example: Print page 1
    #print("\nPrinting specific page:")
    print_page(pages, 227)

      
if __name__ == "__main__":
    main()