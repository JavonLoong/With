import os

try:
    import fitz # PyMuPDF
    print("fitz is installed!")
except ImportError:
    print("fitz is NOT installed!")

try:
    from pdf2image import convert_from_path
    print("pdf2image is installed!")
except ImportError:
    print("pdf2image is NOT installed!")
