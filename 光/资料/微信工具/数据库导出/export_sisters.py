# -*- coding: utf-8 -*-
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

DECRYPTED_DIR = r"d:\虚拟C盘\光\微信工具\数据库导出\wechat-decrypt\decrypted"
OUTPUT_DIR    = r"d:\虚拟C盘\光\姐姐妹妹聊天档案"
CONFIG_FILE   = r"d:\虚拟C盘\光\微信工具\数据库导出\wechat-decrypt\config.json"

MSG_DBS = [
    os.path.join(DECRYPTED_DIR, "message", f"message_{i}.db")
    for i in range(10)
    if os.path.exists(os.path.join(DECRYPTED_DIR, "message", f"message_{i}.db"))
]

def get_self_wxid():
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        db_dir = cfg.get("db_dir", "")
        m = re.search(r"(wxid_[a-z0-9]+)", db_dir)
        if m: return m.group(1)
    except: pass
    return None

def get_self_sender_id(conn):
    self_wxid = get_self_wxid()
    if not self_wxid: return None
    try:
        rows = conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()
        for rowid, uname in rows:
            if uname == self_wxid: return rowid
    except: pass
    return None

def find_msg_table(username):
    table_name = "Msg_" + hashlib.md5(username.encode()).hexdigest()
    for db_path in MSG_DBS:
        conn = sqlite3.connect(db_path)
        exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table_name,)).fetchone()
        if exists: return conn, table_name
        conn.close()
    return None, None

def decompress_content(content, ct):
    if ct == 4 and isinstance(content, bytes):
        try:
            import zstandard
            return zstandard.ZstdDecompressor().decompress(content).decode("utf-8", errors="replace")
        except: pass
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content or ""

def parse_type(local_type):
    t = int(local_type) if local_type else 0
    if t > 0xFFFFFFFF: return t & 0xFFFFFFFF, t >> 32
    return t, 0

def format_content(local_type, content):
    base, _ = parse_type(local_type)
    if base == 1: return content, "text"
    if base in (3, 34, 43, 47, 48, 50): return f"[{base}]", "meta"
    if base == 49: return "[链接/文件]", "meta"
    if base == 10000: return content or "[系统消息]", "system"
    if base == 10002: return "[撤回了一条消息]", "system"
    return content or f"[type={local_type}]", "meta"

HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>微信聊天记录 - {name}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:linear-gradient(180deg,#0f0c29 0%,#1a1a2e 50%,#16213e 100%);color:#eee;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;display:flex;flex-direction:column;align-items:center;padding:30px 20px;min-height:100vh}
.header{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);padding:25px 40px;border-radius:20px;margin-bottom:30px;text-align:center;border:1px solid rgba(255,255,255,.1);box-shadow:0 8px 32px rgba(0,0,0,.4)}
.header h1{font-size:1.8em;font-weight:700;margin-bottom:8px;background:linear-gradient(135deg,#a8edea,#fed6e3);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.header p{opacity:.7;font-size:.9em}
.chat-container{width:100%;max-width:800px}
.date-divider{text-align:center;margin:20px 0;color:rgba(255,255,255,.4);font-size:.78em;position:relative}
.date-divider::before,.date-divider::after{content:'';position:absolute;top:50%;width:30%;height:1px;background:rgba(255,255,255,.1)}
.date-divider::before{left:0}.date-divider::after{right:0}
.msg{display:flex;margin:8px 0;gap:10px}
.msg.me{flex-direction:row-reverse}
.avatar{width:38px;height:38px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);display:flex;align-items:center;justify-content:center;font-size:.8em;font-weight:700;flex-shrink:0}
.avatar.me{background:linear-gradient(135deg,#43c6ac,#191654)}
.bubble-wrap{max-width:65%;display:flex;flex-direction:column}
.msg.me .bubble-wrap{align-items:flex-end}
.bubble{padding:10px 14px;border-radius:16px;font-size:.92em;line-height:1.5;word-break:break-word;white-space:pre-wrap}
.bubble.them{background:rgba(255,255,255,.1);border-radius:16px 16px 16px 4px}
.bubble.me{background:linear-gradient(135deg,#43c6ac,#191654);border-radius:16px 16px 4px 16px}
.bubble.system{background:transparent;color:rgba(255,255,255,.4);font-size:.8em;text-align:center;padding:4px 10px;font-style:italic}
.bubble.meta{opacity:.6;font-style:italic}
.time{font-size:.68em;color:rgba(255,255,255,.3);margin-top:4px;padding:0 4px}
.stats{margin-top:30px;background:rgba(255,255,255,.05);padding:16px 24px;border-radius:12px;font-size:.85em;opacity:.7;text-align:center;border:1px solid rgba(255,255,255,.08)}
</style>
</head>
<body>
<div class="header">
  <h1>💬 {name}</h1>
  <p>聊天记录 · 共 {total} 条</p>
</div>
<div class="chat-container">
"""
HTML_TAIL = """</div>\n{stats}\n</body></html>"""

def _esc(s): return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def render_html(contact_name, messages_data, self_initial, them_initial):
    lines = []
    last_date = None
    for ts, is_me, text, msg_type in messages_data:
        dt = datetime.fromtimestamp(ts)
        date_str = dt.strftime("%Y年%m月%d日")
        time_str = dt.strftime("%H:%M")
        if date_str != last_date:
            lines.append(f'<div class="date-divider">{date_str}</div>')
            last_date = date_str
        side = "me" if is_me else "them"
        initial = self_initial if is_me else them_initial
        bubble_class = "me" if is_me else "them"
        if msg_type == "system":
            lines.append(f'<div class="msg"><div class="bubble-wrap" style="width:100%"><div class="bubble system">{_esc(text)}</div></div></div>')
            continue
        if msg_type == "meta": bubble_class += " meta"
        lines.append(f'<div class="msg {side}"><div class="avatar {side}">{initial}</div><div class="bubble-wrap"><div class="bubble {bubble_class}">{_esc(text)}</div><div class="time">{time_str}</div></div></div>')
    return "\n".join(lines)

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print("\n[=========================================]")
    print("[*] 微信海王检测仪：启动！")
    print("[*] 正在加载联系人...")
    contacts_info = {}
    hash_to_username = {}
    
    db = os.path.join(DECRYPTED_DIR, "contact", "contact.db")
    if not os.path.exists(db):
        print(f"[!] 找不到联系人库: {db}")
        return
        
    conn_c = sqlite3.connect(db)
    for username, nick, remark in conn_c.execute("SELECT username, nick_name, remark FROM contact").fetchall():
        contacts_info[username] = (nick or "", remark or "")
        table_name = "Msg_" + hashlib.md5(username.encode()).hexdigest()
        hash_to_username[table_name] = username
    conn_c.close()

    print(f"[*] 找到 {len(contacts_info)} 个联系人记录。正在搜索您发送过 '姐姐' 或 '妹妹' 的消息...")
    matched_usernames = set()
    
    for db_path in MSG_DBS:
        if not os.path.exists(db_path): continue
        print(f"    -> 扫描库分片: {os.path.basename(db_path)}...", flush=True)
        conn = sqlite3.connect(db_path)
        
        self_sid = None
        self_wxid = get_self_wxid()
        if self_wxid:
            try:
                rows = conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()
                for rowid, uname in rows:
                    if uname == self_wxid: self_sid = rowid
            except: pass
            
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'").fetchall()
        for (table_name,) in tables:
            username = hash_to_username.get(table_name)
            if not username or username in matched_usernames:
                continue
            
            # 排除群聊、公众号、企业微信
            if username.endswith("@chatroom") or username.startswith("gh_") or "@openim" in username:
                continue

            try:
                rows = conn.execute(f"SELECT local_type, real_sender_id, message_content, WCDB_CT_message_content FROM [{table_name}]").fetchall()
                for local_type, real_sender_id, content, ct in rows:
                    is_me = (real_sender_id == self_sid) if (self_sid is not None) else (real_sender_id == 0)
                    if is_me:
                        content_str = decompress_content(content, ct)
                        text, msg_type = format_content(local_type, content_str)
                        if msg_type == "text" and text and ("姐姐" in text or "妹妹" in text):
                            matched_usernames.add(username)
                            break
            except Exception as e:
                pass
        conn.close()

    print(f"\n[*] 搜索完成！共找到 {len(matched_usernames)} 个目标女孩（或兄弟）。开始导出记录...")
    if not matched_usernames:
        print("[!] 没有找到符合条件的聊天记录。您的海王指数为 0。")
        return

    for username in matched_usernames:
        nick, remark = contacts_info[username]
        display_name = remark or nick or username
        nick_safe = re.sub(r'[\\/:*?"<>|]', '_', nick)
        remark_safe = re.sub(r'[\\/:*?"<>|]', '_', remark)
        
        if remark_safe and nick_safe and remark_safe != nick_safe:
            file_name = f"{nick_safe}_{remark_safe}.html"
        else:
            file_name = f"{nick_safe or remark_safe or username}.html"
            
        out_path = os.path.join(OUTPUT_DIR, file_name)
        
        conn, table_name = find_msg_table(username)
        if not conn: continue
        self_sid = get_self_sender_id(conn)
        raw_rows = conn.execute(f"SELECT local_id, local_type, create_time, real_sender_id, message_content, WCDB_CT_message_content FROM [{table_name}] ORDER BY create_time ASC").fetchall()
        
        messages_data = []
        for local_id, local_type, create_time, real_sender_id, content, ct in raw_rows:
            content_str = decompress_content(content, ct)
            text, msg_type = format_content(local_type, content_str)
            is_me = (real_sender_id == self_sid) if (self_sid is not None) else (real_sender_id == 0)
            messages_data.append((create_time, is_me, text, msg_type))
        conn.close()
        
        self_initial = "我"
        them_initial = (display_name[0] if display_name else "?")
        body = render_html(display_name, messages_data, self_initial, them_initial)
        
        me_count = sum(1 for _, is_me, _, t in messages_data if is_me and t != "system")
        them_count = sum(1 for _, is_me, _, t in messages_data if not is_me and t != "system")
        first_dt = datetime.fromtimestamp(messages_data[0][0]).strftime("%Y-%m-%d") if messages_data else "—"
        last_dt = datetime.fromtimestamp(messages_data[-1][0]).strftime("%Y-%m-%d") if messages_data else "—"

        stats_html = f'<div class="stats">时间跨度: {first_dt} ~ {last_dt} &nbsp;|&nbsp; 我: {me_count} 条 &nbsp;|&nbsp; {display_name}: {them_count} 条</div>'
        html = HTML_HEAD.replace("{name}", display_name).replace("{total}", str(len(messages_data))) + body + HTML_TAIL.replace("{stats}", stats_html)
        
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
            
        print(f"  [+] 已导出: {file_name} (包含 {len(messages_data)} 条互动记录)")

if __name__ == "__main__":
    main()
