import os

try:
    import pytesseract
    print("pytesseract is installed!")
except ImportError:
    print("pytesseract is NOT installed!")

try:
    import easyocr
    print("easyocr is installed!")
except ImportError:
    print("easyocr is NOT installed!")
