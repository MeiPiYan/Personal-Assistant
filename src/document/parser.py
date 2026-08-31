from __future__ import annotations

from pathlib import Path


class DocumentParser:
    """Multi-format document parser (PDF/DOCX/TXT/MD/HTML)."""

    def parse(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            return ""

        suffix = path.suffix.lower()
        try:
            if suffix == ".pdf":
                return self._parse_pdf(path)
            elif suffix in (".docx", ".doc"):
                return self._parse_docx(path)
            elif suffix in (".txt", ".md", ".markdown"):
                return path.read_text(encoding="utf-8")
            elif suffix in (".html", ".htm"):
                return self._parse_html(path)
            else:
                return path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return f"[解析错误: {e}]"

    def _parse_pdf(self, path: Path) -> str:
        import fitz
        doc = fitz.open(str(path))
        texts = []
        for page in doc:
            texts.append(page.get_text())
        doc.close()
        return "\n".join(texts)

    def _parse_docx(self, path: Path) -> str:
        from docx import Document
        doc = Document(str(path))
        return "\n".join(p.text for p in doc.paragraphs if p.text.strip())

    def _parse_html(self, path: Path) -> str:
        import trafilatura
        html = path.read_text(encoding="utf-8", errors="ignore")
        return trafilatura.extract(html) or html[:5000]

    def parse_url(self, url: str) -> str:
        import trafilatura
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            return trafilatura.extract(downloaded) or ""
        return ""
