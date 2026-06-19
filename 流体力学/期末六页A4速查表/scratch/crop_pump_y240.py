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
    
    # We want a larger area around the first match
    rect = rects[0]
    crop_rect = fitz.Rect(10, rect.y0 - 20, 420, rect.y1 + 100)
    
    # Get pixmap of this crop rect
    pix = page.get_pixmap(clip=crop_rect, dpi=200)
    out_path = os.path.join(artifact_dir, 'cropped_pump_y240.png')
    pix.save(out_path)
    print(f"Saved y240 cropped region to {out_path}")
else:
    print("Could not find text '泵吸水高度' on page 1!")
