import os
import fitz

pdf_sub = r'd:\虚拟C盘\学习\流体力学\期末六页A4速查表\新建文件夹\期末六页A4速查表_重整版四_公式重排版.pdf'
artifact_dir = r'C:\Users\15410\.gemini\antigravity\brain\d7a3129b-a055-473f-8391-d61281f1f488'

doc = fitz.open(pdf_sub)
page = doc.load_page(0)

# Search for the text "泵吸水高度"
rects = page.search_for("泵吸水高度")
if rects:
    print(f"Found search rects: {rects}")
    rect = rects[0]
    
    # We want a larger area around it to see the context
    # PyMuPDF coords are in points (1/72 inch). 
    # Let's crop it: 
    # x ranges from column 1 to column 2
    # Let's set crop box:
    # x0 = 10, y0 = rect.y0 - 20, x1 = 400, y1 = rect.y1 + 100
    crop_rect = fitz.Rect(10, rect.y0 - 10, 420, rect.y1 + 50)
    
    # Get pixmap of this crop rect
    pix = page.get_pixmap(clip=crop_rect, dpi=200)
    out_path = os.path.join(artifact_dir, 'cropped_pump.png')
    pix.save(out_path)
    print(f"Saved cropped region to {out_path}")
else:
    print("Could not find text '泵吸水高度' on page 1!")
