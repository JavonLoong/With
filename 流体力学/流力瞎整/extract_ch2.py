import fitz
import os

doc = fitz.open(r'd:\虚拟C盘\流体力学\流体力学 张兆顺 第三版.pdf')

# Chapter 2 is pages 29-68 (0-indexed based on TOC)
# Let's extract the last ~15 pages of chapter 2 as images for exercise identification
output_dir = r'd:\虚拟C盘\流体力学\ch2_pages'
os.makedirs(output_dir, exist_ok=True)

# First, let's search for exercise pages by looking at text content
print("Searching for exercise pages in Chapter 2...")
for i in range(29, 69):
    text = doc[i].get_text()
    # Print page info
    if len(text.strip()) > 0:
        print(f"Page {i}: {len(text)} chars, first 100: {text[:100].replace(chr(10), ' ')}")

print("\n\nNow rendering last pages of chapter 2 as images...")
# Render pages 58-68 as images (likely where exercises are)
for i in range(56, 69):
    page = doc[i]
    mat = fitz.Matrix(2, 2)  # 2x zoom for readability
    pix = page.get_pixmap(matrix=mat)
    output_path = os.path.join(output_dir, f'page_{i:03d}.png')
    pix.save(output_path)
    print(f"Saved page {i} to {output_path}")

doc.close()
print("Done!")
