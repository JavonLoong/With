# -*- coding: utf-8 -*-
"""
wx_db_export.py — 方法二：从解密后的本地数据库读取聊天记录，生成 HTML

用法：
  python wx_db_export.py <联系人名/备注名>
  python wx_db_export.py Aha
  python wx_db_export.py 赵宇欣

会自动搜索联系人、找到消息表、生成 HTML 文件。
HTML 格式与方法一（截图）输出的风格一致。
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime

DECRYPTED_DIR = r"d:\虚拟C盘\光\微信工具\数据库导出\wechat-decrypt\decrypted"
OUTPUT_DIR    = r"d:\虚拟C盘\光"
CONFIG_FILE   = r"d:\虚拟C盘\光\微信工具\数据库导出\wechat-decrypt\config.json"

# 消息 DB 文件列表（按顺序查找）
MSG_DBS = [
    os.path.join(DECRYPTED_DIR, "message", f"message_{i}.db")
    for i in range(10)
    if os.path.exists(os.path.join(DECRYPTED_DIR, "message", f"message_{i}.db"))
]

# ─────────────────── 联系人 ───────────────────

def load_contacts():
    """返回 {username: display_name}"""
    db = os.path.join(DECRYPTED_DIR, "contact", "contact.db")
    conn = sqlite3.connect(db)
    names = {}
    for username, nick, remark in conn.execute(
        "SELECT username, nick_name, remark FROM contact"
    ).fetchall():
        names[username] = remark or nick or username
    conn.close()
    return names


def find_contact(query, contacts):
    """模糊搜索联系人，返回 (username, display_name) 或 None"""
    q = query.lower()
    for uname, display in contacts.items():
        if q == display.lower() or q == uname.lower():
            return uname, display
    for uname, display in contacts.items():
        if q in display.lower() or q in uname.lower():
            return uname, display
    return None


# ─────────────────── 消息 ───────────────────

def find_msg_table(username):
    """在所有 message_N.db 中找包含该用户消息表的 (conn, table_name)"""
    table_name = "Msg_" + hashlib.md5(username.encode()).hexdigest()
    for db_path in MSG_DBS:
        conn = sqlite3.connect(db_path)
        exists = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        if exists:
            return conn, table_name
        conn.close()
    return None, None


def get_self_wxid():
    """从 config.json 的 db_dir 路径提取自己的 wxid"""
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            cfg = json.load(f)
        db_dir = cfg.get("db_dir", "")
        m = re.search(r"(wxid_[a-z0-9]+)", db_dir)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def get_self_sender_id(conn):
    """在 Name2Id 表中查找自己 wxid 对应的 rowid，用于判断消息发送方"""
    self_wxid = get_self_wxid()
    if not self_wxid:
        return None
    try:
        rows = conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()
        for rowid, uname in rows:
            if uname == self_wxid:
                return rowid
    except Exception:
        pass
    return None


def get_name2id(conn, table_name):
    """从同一DB里的 Name2Id 表获取 {rowid: username}"""
    try:
        rows = conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()
        return {rowid: uname for rowid, uname in rows}
    except Exception:
        return {}


def fetch_messages(conn, table_name):
    """返回所有消息，按时间升序"""
    rows = conn.execute(f"""
        SELECT local_id, local_type, create_time, real_sender_id, message_content,
               WCDB_CT_message_content
        FROM [{table_name}]
        ORDER BY create_time ASC
    """).fetchall()
    return rows


# ─────────────────── 消息格式化 ───────────────────

def decompress_content(content, ct):
    if ct == 4 and isinstance(content, bytes):
        try:
            import zstandard
            return zstandard.ZstdDecompressor().decompress(content).decode("utf-8", errors="replace")
        except Exception:
            pass
    if isinstance(content, bytes):
        return content.decode("utf-8", errors="replace")
    return content or ""


def parse_type(local_type):
    t = int(local_type) if local_type else 0
    if t > 0xFFFFFFFF:
        return t & 0xFFFFFFFF, t >> 32
    return t, 0


def format_content(local_type, content):
    base, _ = parse_type(local_type)
    if base == 1:
        return content, "text"
    if base == 3:
        return "[图片]", "meta"
    if base == 34:
        return "[语音消息]", "meta"
    if base == 43:
        return "[视频]", "meta"
    if base == 47:
        return "[表情包]", "meta"
    if base == 48:
        return "[位置]", "meta"
    if base == 49:
        # 尝试提取链接/文件标题
        if content and "<title>" in content:
            m = re.search(r"<title>(.*?)</title>", content, re.S)
            if m:
                title = m.group(1).strip()[:80]
                return f"[链接] {title}", "meta"
        return "[链接/文件]", "meta"
    if base == 50:
        return "[语音通话]", "meta"
    if base == 10000:
        return content or "[系统消息]", "system"
    if base == 10002:
        return "[撤回了一条消息]", "system"
    return content or f"[type={local_type}]", "meta"


# ─────────────────── HTML 生成 ───────────────────

HTML_HEAD = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>微信聊天记录 - {name}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:linear-gradient(180deg,#0f0c29 0%,#1a1a2e 50%,#16213e 100%);
     color:#eee;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;
     display:flex;flex-direction:column;align-items:center;padding:30px 20px;min-height:100vh}}
.header{{background:rgba(255,255,255,.05);backdrop-filter:blur(20px);
         padding:25px 40px;border-radius:20px;margin-bottom:30px;text-align:center;
         border:1px solid rgba(255,255,255,.1);box-shadow:0 8px 32px rgba(0,0,0,.4)}}
.header h1{{font-size:1.8em;font-weight:700;margin-bottom:8px;
            background:linear-gradient(135deg,#a8edea,#fed6e3);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.header p{{opacity:.7;font-size:.9em}}
.chat-container{{width:100%;max-width:800px}}
.date-divider{{text-align:center;margin:20px 0;color:rgba(255,255,255,.4);
               font-size:.78em;position:relative}}
.date-divider::before,.date-divider::after{{content:'';position:absolute;top:50%;
  width:30%;height:1px;background:rgba(255,255,255,.1)}}
.date-divider::before{{left:0}}.date-divider::after{{right:0}}
.msg{{display:flex;margin:8px 0;gap:10px}}
.msg.me{{flex-direction:row-reverse}}
.avatar{{width:38px;height:38px;border-radius:8px;background:linear-gradient(135deg,#667eea,#764ba2);
         display:flex;align-items:center;justify-content:center;font-size:.8em;
         font-weight:700;flex-shrink:0}}
.avatar.me{{background:linear-gradient(135deg,#43c6ac,#191654)}}
.bubble-wrap{{max-width:65%;display:flex;flex-direction:column}}
.msg.me .bubble-wrap{{align-items:flex-end}}
.sender-name{{font-size:.72em;color:rgba(255,255,255,.5);margin-bottom:3px;padding:0 4px}}
.bubble{{padding:10px 14px;border-radius:16px;font-size:.92em;line-height:1.5;
         word-break:break-word;white-space:pre-wrap}}
.bubble.them{{background:rgba(255,255,255,.1);border-radius:16px 16px 16px 4px}}
.bubble.me{{background:linear-gradient(135deg,#43c6ac,#191654);border-radius:16px 16px 4px 16px}}
.bubble.system{{background:transparent;color:rgba(255,255,255,.4);font-size:.8em;
                text-align:center;padding:4px 10px;font-style:italic}}
.bubble.meta{{opacity:.6;font-style:italic}}
.time{{font-size:.68em;color:rgba(255,255,255,.3);margin-top:4px;padding:0 4px}}
.stats{{margin-top:30px;background:rgba(255,255,255,.05);padding:16px 24px;
        border-radius:12px;font-size:.85em;opacity:.7;text-align:center;
        border:1px solid rgba(255,255,255,.08)}}
</style>
</head>
<body>
<div class="header">
  <h1>💬 {name}</h1>
  <p>聊天记录 · 共 {total} 条 · 由本地数据库导出</p>
</div>
<div class="chat-container">
"""

HTML_TAIL = """</div>
{stats}
</body></html>"""


def render_html(contact_name, messages_data, self_initial, them_initial):
    """messages_data: [(ts, is_me, text, msg_type)] """
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
            lines.append(
                f'<div class="msg"><div class="bubble-wrap" style="width:100%">'
                f'<div class="bubble system">{_esc(text)}</div></div></div>'
            )
            continue

        if msg_type == "meta":
            bubble_class += " meta"

        lines.append(
            f'<div class="msg {side}">'
            f'<div class="avatar {side}">{initial}</div>'
            f'<div class="bubble-wrap">'
            f'<div class="bubble {bubble_class}">{_esc(text)}</div>'
            f'<div class="time">{time_str}</div>'
            f'</div></div>'
        )

    return "\n".join(lines)


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ─────────────────── 主流程 ───────────────────

def main():
    if len(sys.argv) < 2:
        print("用法: python wx_db_export.py <联系人名/备注名>")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    print(f"[*] 搜索联系人: {query}")

    contacts = load_contacts()
    result = find_contact(query, contacts)
    if not result:
        # 列出包含关键词的联系人供参考
        q = query.lower()
        candidates = [(u, d) for u, d in contacts.items()
                      if q in d.lower() or q in u.lower()]
        if candidates:
            print(f"[!] 未找到精确匹配。相似联系人：")
            for u, d in candidates[:10]:
                print(f"    {d}  ({u})")
        else:
            print("[!] 未找到任何匹配的联系人")
        sys.exit(1)

    username, display_name = result
    print(f"[+] 找到联系人: {display_name} ({username})")

    conn, table_name = find_msg_table(username)
    if not conn:
        print(f"[!] 未找到该联系人的消息表 (Msg_{hashlib.md5(username.encode()).hexdigest()})")
        print("    可能从未聊过天，或消息在其他 message_N.db 分片中")
        sys.exit(1)

    print(f"[+] 消息表: {table_name}")
    name2id = get_name2id(conn, table_name)

    # 查找自己的 sender_id
    self_sid = get_self_sender_id(conn)
    if self_sid:
        print(f"[+] 自己的 sender_id: {self_sid}")
    else:
        print("[!] 警告: 无法确定自己的 sender_id，将使用启发式判断")

    raw_rows = fetch_messages(conn, table_name)
    conn.close()

    print(f"[+] 共 {len(raw_rows)} 条消息，正在处理...")

    messages_data = []
    for local_id, local_type, create_time, real_sender_id, content, ct in raw_rows:
        content = decompress_content(content, ct)
        text, msg_type = format_content(local_type, content)

        # 通过 Name2Id 的 rowid 判断发送方
        is_me = (real_sender_id == self_sid) if self_sid else (real_sender_id == 0)

        messages_data.append((create_time, is_me, text, msg_type))

    # 取首字作为头像缩写
    self_initial = "我"
    them_initial = (display_name[0] if display_name else "?")

    body = render_html(display_name, messages_data, self_initial, them_initial)

    # 统计
    me_count   = sum(1 for _, is_me, _, t in messages_data if is_me and t != "system")
    them_count = sum(1 for _, is_me, _, t in messages_data if not is_me and t != "system")
    if messages_data:
        first_dt = datetime.fromtimestamp(messages_data[0][0]).strftime("%Y-%m-%d")
        last_dt  = datetime.fromtimestamp(messages_data[-1][0]).strftime("%Y-%m-%d")
    else:
        first_dt = last_dt = "—"

    stats_html = (
        f'<div class="stats">'
        f'时间跨度: {first_dt} ~ {last_dt} &nbsp;|&nbsp; '
        f'我: {me_count} 条 &nbsp;|&nbsp; {display_name}: {them_count} 条'
        f'</div>'
    )

    html = HTML_HEAD.format(name=display_name, total=len(messages_data)) + body + HTML_TAIL.format(stats=stats_html)

    # 输出文件名（清理非法字符）
    safe_name = re.sub(r'[\\/:*?"<>|]', '_', display_name)
    out_path = os.path.join(OUTPUT_DIR, f"{safe_name}_聊天记录_db.html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[+] 导出完成: {out_path}")
    print(f"    共 {len(messages_data)} 条消息，时间范围 {first_dt} ~ {last_dt}")


if __name__ == "__main__":
    main()
