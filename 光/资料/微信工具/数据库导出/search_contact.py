import sqlite3, hashlib, os

# Msg_4a2e287e967fc41ef0c3fb830594c963 里有人叫闫智波
# 反查 Name2Id 获取 username
conn = sqlite3.connect(r"d:\虚拟C盘\光\wechat-decrypt\decrypted\message\message_0.db")
name2id = {rowid: u for rowid, u in conn.execute("SELECT rowid, user_name FROM Name2Id").fetchall()}
conn.close()

# 找到 Msg_4a2e287e967fc41ef0c3fb830594c963 对应的 username (MD5反查)
target_hash = "4a2e287e967fc41ef0c3fb830594c963"
contact_conn = sqlite3.connect(r"d:\虚拟C盘\光\wechat-decrypt\decrypted\contact\contact.db")
all_contacts = contact_conn.execute("SELECT username, nick_name, remark FROM contact").fetchall()
contact_conn.close()

print("反查Msg_4a2e...对应的username:")
for username, nick, remark in all_contacts:
    h = hashlib.md5(username.encode()).hexdigest()
    if h == target_hash:
        print(f"  {username} | {nick} | {remark}")

# 也搜索含"智波"的所有联系人
print("\n联系人中name2id里的闫智波相关 uid:")
conn2 = sqlite3.connect(r"d:\虚拟C盘\光\wechat-decrypt\decrypted\message\message_1.db")
name2id2 = {rowid: u for rowid, u in conn2.execute("SELECT rowid, user_name FROM Name2Id").fetchall()}
conn2.close()

# 在 message_0 里的 Msg_4a2e 群里，找 sid 对应的用户
conn3 = sqlite3.connect(r"d:\虚拟C盘\光\wechat-decrypt\decrypted\message\message_0.db")
# 找包含 闫智波 的消息的 sid
rows = conn3.execute(
    "SELECT DISTINCT real_sender_id FROM [Msg_4a2e287e967fc41ef0c3fb830594c963] WHERE message_content LIKE '%闫智波%'"
).fetchall()
print("群里提到闫智波的sender_id:", rows)
for (sid,) in rows:
    uname = name2id.get(sid, "?")
    print(f"  sid={sid} -> {uname}")

# 找"闫智波"在 Name2Id 中的 rowid
all_names = conn3.execute("SELECT rowid, user_name FROM Name2Id WHERE user_name LIKE '%yan%'").fetchall()
print("\nName2Id里含yan的:", all_names[:10])
conn3.close()


