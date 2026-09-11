"""WeChat Reader Test Script

Usage:
  python test_wechat_reader.py

Prerequisites:
  1. pip install wechatauto-replica
  2. 微信 PC 版已登录并保持运行
  3. 不要锁屏

This script tests:
  - WeChatDB initialization
  - Session list retrieval
  - Message reading from a specific chat
  - Contact search
"""

import sys
import time
from datetime import datetime


def test_wechat_reader():
    print("=" * 60)
    print("WeChat Reader Test")
    print("=" * 60)

    # Step 1: Import and initialize
    print("\n[1] 初始化 WeChatDB...")
    try:
        from wechatauto import WeChatDB
        db = WeChatDB()
        print("    ✅ WeChatDB 初始化成功")
    except ImportError:
        print("    ❌ wechatauto-replica 未安装")
        print("    请运行: pip install wechatauto-replica")
        return
    except Exception as e:
        print(f"    ❌ 初始化失败: {e}")
        print("    请确保微信 PC 版已登录")
        return

    # Step 2: Get self info
    print("\n[2] 获取当前账号信息...")
    try:
        info = db.get_self_info()
        if info:
            print(f"    昵称: {info.get('nickname', '未知')}")
            print(f"    微信号: {info.get('username', '未知')}")
        else:
            print("    ⚠️ 无法获取账号信息")
    except Exception as e:
        print(f"    ⚠️ 获取账号信息失败: {e}")

    # Step 3: Get sessions
    print("\n[3] 获取会话列表（最近 10 个）...")
    try:
        sessions = db.get_sessions(limit=10)
        if sessions:
            print(f"    找到 {len(sessions)} 个会话:")
            for i, s in enumerate(sessions, 1):
                username = s.get("username", "")
                nickname = db.get_nickname(username) or username
                unread = s.get("unread", 0)
                digest = s.get("digest", "")[:30]
                print(f"    {i:2d}. {nickname:<20} [未读:{unread}] {digest}")
        else:
            print("    ⚠️ 未找到会话")
    except Exception as e:
        print(f"    ❌ 获取会话列表失败: {e}")
        sessions = []

    # Step 4: Read messages from first chat
    if sessions:
        first_chat = sessions[0].get("username", "")
        first_nickname = db.get_nickname(first_chat) or first_chat
        print(f"\n[4] 读取 [{first_nickname}] 的最近 5 条消息...")
        try:
            messages = db.get_messages(first_chat, limit=5)
            if messages:
                print(f"    找到 {len(messages)} 条消息:")
                for m in messages:
                    create_time = m.get("create_time", 0)
                    if isinstance(create_time, (int, float)) and create_time > 0:
                        dt = datetime.fromtimestamp(create_time).strftime("%H:%M:%S")
                    else:
                        dt = "??:??:??"

                    sender_id = m.get("sender_id", "")
                    content = m.get("content", "")
                    if isinstance(content, bytes):
                        content = content.decode("utf-8", errors="ignore")
                    content = str(content)[:50]

                    if str(sender_id) == "2":
                        sender = "我"
                    else:
                        sender = db.get_nickname(str(sender_id)) or str(sender_id)

                    print(f"    [{dt}] {sender}: {content}")
            else:
                print("    ⚠️ 未找到消息")
        except Exception as e:
            print(f"    ❌ 读取消息失败: {e}")

    # Step 5: Search contact
    print("\n[5] 搜索联系人（搜索 '文件传输助手'）...")
    try:
        hits = db.search_contact("文件传输助手")
        if hits:
            print(f"    找到 {len(hits)} 个结果:")
            for h in hits[:3]:
                print(f"    - {h.get('nickname', '未知')} ({h.get('username', '未知')})")
        else:
            print("    ⚠️ 未找到匹配的联系人")
    except Exception as e:
        print(f"    ❌ 搜索联系人失败: {e}")

    # Step 6: Test listener (optional)
    print("\n[6] 测试 Listener（3秒）...")
    try:
        from wechatauto import Listener

        listener = Listener(db)
        received = []

        def on_message(msg):
            content = msg.get("content", "")
            if isinstance(content, bytes):
                content = content.decode("utf-8", errors="ignore")
            received.append(f"  收到: {str(content)[:50]}")
            print(f"    📩 新消息: {str(content)[:50]}")

        # Listen to file helper if available
        if sessions:
            listener.add(sessions[0].get("username", ""))
            listener.start(callback=on_message)
            print("    Listener 已启动，等待 3 秒...")
            time.sleep(3)
            listener.stop()
            print(f"    Listener 停止，共收到 {len(received)} 条消息")
        else:
            print("    ⚠️ 跳过（无可用会话）")
    except Exception as e:
        print(f"    ⚠️ Listener 测试跳过: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_wechat_reader()
