import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from data_loader import url_extraction


if __name__ == "__main__":
    url_extraction(url="https://developer.nvidia.com/discover/artificial-neural-network")
