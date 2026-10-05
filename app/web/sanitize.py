"""Allow-list HTML sanitizer for the rich-text description (standard library only).

Keeps a few formatting tags, drops every attribute, and drops <script>/<style>/etc. together
with their content. Everything else is escaped text.
"""
from __future__ import annotations

from html import escape
from html.parser import HTMLParser

ALLOWED = {"b", "strong", "i", "em", "u", "p", "br", "ul", "ol", "li", "div"}
VOID = {"br"}
DROP_WITH_CONTENT = {"script", "style", "iframe", "object", "embed", "template", "noscript", "svg", "math",
                     "textarea", "select", "title", "head"}
MAX_LEN = 4000  # characters of visible text


class _Clean(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out: list[str] = []
        self.stack: list[str] = []
        self.skip = 0
        self.text_len = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self.skip += 1
            return
        if self.skip or tag not in ALLOWED:
            return
        if tag == "div":
            tag = "p"  # contenteditable produces <div> per line
        if tag in VOID:
            self.out.append("<br>")
            return
        self.out.append(f"<{tag}>")
        self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        if tag in VOID and not self.skip:
            self.out.append("<br>")

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT:
            self.skip = max(0, self.skip - 1)
            return
        if self.skip:
            return
        if tag == "div":
            tag = "p"
        if tag in self.stack:
            while self.stack:
                t = self.stack.pop()
                self.out.append(f"</{t}>")
                if t == tag:
                    break

    def handle_data(self, data):
        if self.skip or self.text_len >= MAX_LEN:
            return
        data = data[: MAX_LEN - self.text_len]
        self.text_len += len(data)
        self.out.append(escape(data, quote=False))

    def result(self) -> str:
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")
        return "".join(self.out).strip()


def clean_html(raw: str | None) -> str:
    if not raw:
        return ""
    p = _Clean()
    p.feed(raw[: MAX_LEN * 10])
    p.close()
    html = p.result()
    return "" if html in ("<p></p>", "<p><br></p>", "<br>") else html
