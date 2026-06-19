import os
import easyocr

image_dir = r"C:\Users\15410\.gemini\antigravity\brain\d7a3129b-a055-473f-8391-d61281f1f488"
out_dir = r"d:\虚拟C盘\学习\流体力学\期末六页A4速查表\scratch"

images = [
    ("mid_wbz_p1.png", "ocr_mid_wbz.txt"),
    ("final_wbz_p1.png", "ocr_final_wbz.txt")
]

# Initialize reader with Chinese and English
try:
    print("Initializing EasyOCR reader...")
    reader = easyocr.Reader(['ch_sim', 'en'])
    print("EasyOCR reader initialized successfully!")
    
    for img_name, txt_name in images:
        img_path = os.path.join(image_dir, img_name)
        txt_path = os.path.join(out_dir, txt_name)
        if os.path.exists(img_path):
            print(f"Running OCR on {img_name}...")
            result = reader.readtext(img_path, detail=0)
            text = "\n".join(result)
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"Saved OCR results to {txt_path} (size: {os.path.getsize(txt_path)} bytes)")
        else:
            print(f"Image not found: {img_path}")
            
except Exception as e:
    print(f"EasyOCR failed: {e}")
    
    # Try pytesseract as fallback
    print("Trying pytesseract as fallback...")
    try:
        import pytesseract
        from PIL import Image
        
        # Check if tesseract is available
        # pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe' # common path
        for img_name, txt_name in images:
            img_path = os.path.join(image_dir, img_name)
            txt_path = os.path.join(out_dir, txt_name)
            if os.path.exists(img_path):
                print(f"Running pytesseract on {img_name}...")
                img = Image.open(img_path)
                text = pytesseract.image_to_string(img, lang='chi_sim+eng')
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Saved pytesseract results to {txt_path} (size: {os.path.getsize(txt_path)} bytes)")
    except Exception as ex:
        print(f"Pytesseract also failed: {ex}")
