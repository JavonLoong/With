# -*- coding: utf-8 -*-
"""
WeChat chat export for 赵宇欣 - search, scroll to top, capture all pages.
"""
import ctypes
import ctypes.wintypes as wt
import time
import pyautogui
import os
import hashlib
import base64
from PIL import Image
import numpy as np

user32 = ctypes.windll.user32
pyautogui.PAUSE = 0.01
pyautogui.FAILSAFE = False

CONTACT_NAME = "赵宇欣"
SCREENSHOT_DIR = r"d:\虚拟C盘\光\chat_screenshots_zyx"
OUTPUT_HTML = r"d:\虚拟C盘\光\赵宇欣_聊天记录.html"
LOG_FILE = r"d:\虚拟C盘\光\gui_output.txt"

os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# Clean old screenshots
for f in os.listdir(SCREENSHOT_DIR):
    if f.endswith('.png'):
        os.remove(os.path.join(SCREENSHOT_DIR, f))

def log(msg):
    print(msg, flush=True)
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def get_screen_hash(region):
    img = pyautogui.screenshot(region=region)
    small = img.resize((80, 80))
    arr = np.array(small)
    return hashlib.md5(arr.tobytes()).hexdigest(), img


def detect_input_box_top(left, right, bottom, top_limit):
    """自动检测微信输入框上边界：从底部向上扫描，找到颜色突变（输入框→聊天区）的位置"""
    cx = (left + right) // 2
    scan_width = 200
    scan_left = cx - scan_width // 2
    scan_region = (scan_left, top_limit, scan_width, bottom - top_limit)
    img = pyautogui.screenshot(region=scan_region)
    arr = np.array(img)

    h = arr.shape[0]
    for y in range(h - 1, max(h - 300, 0), -1):
        row_mean = arr[y, :, :3].mean()
        if row_mean < 200:
            input_box_height = h - y
            return bottom - input_box_height
    return None


def main():
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.write('')

    log("=" * 60)
    log(f"  WeChat Chat Screenshot Export - {CONTACT_NAME}")
    log("=" * 60)

    # Find WeChat
    hwnd = user32.FindWindowW("WeChatMainWndForPC", "微信")
    if not hwnd:
        hwnd = user32.FindWindowW("Qt51514QWindowIcon", "微信")
    if not hwnd:
        hwnd = user32.FindWindowW(None, "微信")
    if not hwnd:
        log("ERROR: WeChat window not found!")
        return

    # Bring to foreground and position
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)
    user32.MoveWindow(hwnd, 50, 50, 1400, 1000, True)
    time.sleep(0.3)
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.5)

    rect = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom
    width = right - left
    height = bottom - top
    log(f"Window: ({left},{top}) size={width}x{height}")

    # ============================================
    # PHASE 0: Search for contact
    # ============================================
    log(f"\n[Step 0] Searching for {CONTACT_NAME}...")

    # Click search box (Ctrl+F to open search)
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.5)

    # Type contact name
    import pyperclip
    pyperclip.copy(CONTACT_NAME)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(1.5)

    # Press Enter to select the first result
    pyautogui.press('enter')
    time.sleep(1.5)

    # Re-get window rect after search
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    left, top, right, bottom = rect.left, rect.top, rect.right, rect.bottom

    # Chat area bounds — 自动检测输入框上边界
    chat_left = left + 410
    chat_top = top + 70
    chat_right = right - 10

    detected_top = detect_input_box_top(chat_left, chat_right, bottom, bottom - 300)
    if detected_top and (bottom - detected_top) > 50:
        chat_bottom = detected_top - 5  # 留 5px 安全边距
        log(f"Auto-detected input box top at y={detected_top}, input height={bottom - detected_top}px")
    else:
        chat_bottom = bottom - 170  # 保守回退值（原值80太小）
        log(f"Using fallback bottom offset: 170px")

    chat_width = chat_right - chat_left
    chat_height = chat_bottom - chat_top
    log(f"Chat area: ({chat_left},{chat_top}) to ({chat_right},{chat_bottom})")

    cx = (chat_left + chat_right) // 2
    cy = (chat_top + chat_bottom) // 2
    chat_region = (chat_left, chat_top, chat_width, chat_height)

    # Click chat area to ensure focus
    pyautogui.click(cx, cy)
    time.sleep(0.3)

    # ============================================
    # PHASE 1: Scroll to top FAST
    # ============================================
    log("\n[Step 1] Scrolling to top...")

    pyautogui.click(cx, cy)
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'Home')
    time.sleep(1)

    MAX_SCROLL_BATCHES = 150
    stable_count = 0
    scroll_count = 0
    prev_hash = None

    while stable_count < 3 and scroll_count < MAX_SCROLL_BATCHES:
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.01)
        pyautogui.click(cx, cy)
        time.sleep(0.01)

        for _ in range(30):
            pyautogui.scroll(20, cx, cy)
            time.sleep(0.005)

        scroll_count += 1
        time.sleep(0.15)

        curr_hash, _ = get_screen_hash(chat_region)
        if curr_hash == prev_hash:
            stable_count += 1
        else:
            stable_count = 0
        prev_hash = curr_hash

        if scroll_count % 20 == 0:
            log(f"  Scrolling up... {scroll_count}/{MAX_SCROLL_BATCHES} batches, stable={stable_count}/3")

    if scroll_count >= MAX_SCROLL_BATCHES:
        log(f"  Reached max scroll limit ({MAX_SCROLL_BATCHES}), proceeding...")
    else:
        log(f"  Reached top after {scroll_count} scroll batches!")
    time.sleep(0.3)

    # ============================================
    # PHASE 2: Capture screenshots going DOWN
    # ============================================
    log("\n[Step 2] Taking screenshots page by page...")

    page = 0
    stable_count = 0
    prev_hash = None

    while stable_count < 3:
        user32.SetForegroundWindow(hwnd)
        time.sleep(0.05)

        curr_hash, screenshot = get_screen_hash(chat_region)

        if curr_hash == prev_hash:
            stable_count += 1
        else:
            stable_count = 0
            filepath = os.path.join(SCREENSHOT_DIR, f"page_{page:04d}.png")
            screenshot.save(filepath)
            if page % 10 == 0:
                log(f"  Page {page} saved")
            page += 1

        prev_hash = curr_hash

        pyautogui.click(cx, cy)
        time.sleep(0.01)
        pyautogui.press('pagedown')
        time.sleep(0.15)

    log(f"  Last page: {page - 1}")
    log(f"\nTotal pages captured: {page}")
    log(f"Screenshots saved to: {SCREENSHOT_DIR}")

    # ============================================
    # PHASE 3: Generate HTML
    # ============================================
    log("\n[Step 3] Generating HTML...")

    files = sorted([f for f in os.listdir(SCREENSHOT_DIR) if f.startswith('page_') and f.endswith('.png')])

    if not files:
        log("ERROR: No screenshots found!")
        return

    html_parts = [f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>微信聊天记录 - {CONTACT_NAME}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: linear-gradient(180deg, #0f0c29 0%, #1a1a2e 50%, #16213e 100%);
            color: #eee;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Microsoft YaHei', sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 30px 20px;
            min-height: 100vh;
        }}
        .header {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(20px);
            padding: 30px 50px;
            border-radius: 20px;
            margin-bottom: 30px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
        }}
        .header h1 {{
            font-size: 28px;
            background: linear-gradient(90deg, #07f49e, #42d3ff);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .header p {{ color: #8899aa; font-size: 14px; }}
        .page-container {{
            margin: 4px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.05);
            position: relative;
            max-width: 800px;
        }}
        .page-container img {{ display: block; width: 100%; height: auto; }}
        .page-label {{
            position: absolute;
            top: 8px;
            right: 8px;
            background: rgba(0,0,0,0.6);
            color: #fff;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            backdrop-filter: blur(4px);
        }}
        .footer {{
            margin-top: 30px;
            padding: 20px;
            color: #445;
            font-size: 12px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💬 微信聊天记录 — {CONTACT_NAME}（完整版）</h1>
        <p>完整聊天记录 · 共 {len(files)} 页 · 导出时间: 2026-03-22</p>
    </div>
"""]

    for i, f in enumerate(files):
        path = os.path.join(SCREENSHOT_DIR, f)
        with open(path, 'rb') as img_file:
            img_b64 = base64.b64encode(img_file.read()).decode()
        html_parts.append(f"""
    <div class="page-container">
        <span class="page-label">第 {i+1}/{len(files)} 页</span>
        <img src="data:image/png;base64,{img_b64}" alt="第{i+1}页">
    </div>
""")

    html_parts.append("""
    <div class="footer">
        <p>本聊天记录通过截图方式从微信客户端完整导出</p>
    </div>
</body>
</html>
""")

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(''.join(html_parts))

    file_size = os.path.getsize(OUTPUT_HTML) / 1024 / 1024
    log(f"\nHTML saved: {OUTPUT_HTML}")
    log(f"Size: {file_size:.1f} MB, Pages: {len(files)}")
    log("DONE!")

if __name__ == '__main__':
    main()
