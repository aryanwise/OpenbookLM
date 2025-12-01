import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import (
    DocumentLoader, DocumentManager, ExtractLink, ExtractText
)


if __name__ == "__main__":
    # url extraction
    url_extraction = ExtractLink()
    url_text = url_extraction.url_extraction("https://developer.nvidia.com/discover/artificial-neural-network")
    # text extraction 
    extract_text = ExtractText()
    text = extract_text.extract_text("Aryan Mishra")
    
    # Save the output as .txt 
    save_text = DocumentManager()
    save_text.set_storage_location("/Users/aryanmishra/Documents") # Set a temporary storage location
    save_text.create_load_project("test_project_for_saving") # Create or load a project
    save_text.save_text_to_project(text_content=str(url_text), file_name="Sample") # Convert url_text to string
    save_text.save_text_to_project(text_content=text, file_name="Name") 