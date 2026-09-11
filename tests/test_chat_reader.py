"""Tests for the QQ reader's OneBot message parsing."""
from datetime import datetime

import pytest

from src.chat_reader.qq_reader import QQReader
from src.storage.models import ChatMessage


@pytest.fixture
def reader() -> QQReader:
    return QQReader(base_url="http://127.0.0.1:3000/")


class TestParseMsg:
    def test_plain_text_message(self, reader):
        raw = {
            "message_id": 1,
            "time": 1700000000,
            "message": "你好世界",
            "sender": {"nickname": "小明", "user_id": 10001},
        }
        msg = reader._parse_msg(raw)
        assert isinstance(msg, ChatMessage)
        assert msg.platform == "qq"
        assert msg.content == "你好世界"
        assert msg.sender == "小明"
        assert msg.group_name == ""

    def test_segment_message_mixed(self, reader):
        raw = {
            "message": [
                {"type": "text", "data": {"text": "看这个 "}},
                {"type": "image", "data": {"file": "a.jpg"}},
                {"type": "face", "data": {"id": "1"}},
                {"type": "record", "data": {}},
                {"type": "video", "data": {}},
                {"type": "at", "data": {"qq": "10002"}},
            ],
            "sender": {"nickname": "A"},
        }
        msg = reader._parse_msg(raw)
        assert msg.content == "看这个 [图片][表情][语音][视频]@10002"

    def test_sender_prefers_card_over_nickname(self, reader):
        raw = {
            "message": "hi",
            "sender": {"card": "群名片", "nickname": "昵称"},
        }
        msg = reader._parse_msg(raw)
        assert msg.sender == "群名片"

    def test_sender_falls_back_to_user_id(self, reader):
        raw = {
            "message": "hi",
            "sender": {"user_id": 424242},
        }
        msg = reader._parse_msg(raw)
        assert msg.sender == "424242"

    def test_group_id_becomes_group_name(self, reader):
        raw = {
            "message": "hi",
            "group_id": 123456,
            "sender": {"nickname": "A"},
        }
        msg = reader._parse_msg(raw)
        assert msg.group_name == "123456"

    def test_timestamp_converted(self, reader):
        raw = {"message": "hi", "time": 1700000000, "sender": {}}
        msg = reader._parse_msg(raw)
        expected = datetime.fromtimestamp(1700000000)
        assert msg.created_at == expected

    def test_bad_timestamp_falls_back_to_now(self, reader):
        raw = {"message": "hi", "time": 0, "sender": {}}
        msg = reader._parse_msg(raw)
        assert isinstance(msg.created_at, datetime)
        # Should be "now", not the epoch
        assert msg.created_at.year >= 2025


class TestLifecycle:
    def test_base_url_trailing_slash_stripped(self, reader):
        assert reader.base_url == "http://127.0.0.1:3000"

    def test_not_polling_after_init(self, reader):
        assert reader._polling is False
