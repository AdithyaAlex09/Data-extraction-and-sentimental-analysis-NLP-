from setuptools import setup, find_packages

# Function to read the requirements.txt file
def parse_requirements(filename):
    with open(filename, 'r') as file:
        return file.read().splitlines()

setup(
    name='text_extraction_and_sentiment_analysis',
    version='0.1',
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),
    entry_points={
        'console_scripts': [
            'scrape=src.main:main',
        ],
    },
)

