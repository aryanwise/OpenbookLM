import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import url_extraction, extract_text, save_txt


if __name__ == "__main__":
    # url_extraction(url="https://developer.nvidia.com/discover/artificial-neural-network")
    doc = extract_text("Aryan Mishra")
    save_txt(doc=doc)