import logging
import os

def setup_logging(log_file, level=logging.INFO):
    logging.basicConfig(
        filename=log_file,
        filemode='a',
        format='%(asctime)s - %(levelname)s - %(message)s',
        level=level
    )

def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
