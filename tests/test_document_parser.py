"""Tests for Document Parser."""
import pytest
from src.document.parser import DocumentParser


def test_parser_exists():
    parser = DocumentParser()
    assert parser is not None
