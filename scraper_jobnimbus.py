import csv
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse


BASE_URL = "https://www.jobnimbus.com/thank-you-for-signing-up?submissionGuid=c83b4069-5145-4a75-b1c0-209e1025aa70"


class TopNavParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_header = False
        self.header_depth = 0
        self.in_footer = False
        self.footer_depth = 0
        self.in_anchor = False
        self.anchor_href = None
        self.anchor_text_parts = []
        self.anchor_attrs = {}
        self.collected = []
        self._class_stack = []

        self._void_tags = {
            "area",
            "base",
            "br",
            "col",
            "embed",
            "hr",
            "img",
            "input",
            "link",
            "meta",
            "param",
            "source",
            "track",
            "wbr",
        }
        self._exclude_text_classes = {"sr-only"}

    def _class_list(self, attrs):
        classes = attrs.get("class", "")
        return classes.split()

    def _should_enter_header(self, tag, attrs) -> bool:
        if tag not in ("div", "header", "nav"):
            return False
        class_list = self._class_list(attrs)
        if any(
            cls in class_list
            for cls in ("nav_fixed", "navbar_component", "navbar_component_taller")
        ):
            return True
        if attrs.get("role") == "banner":
            return True
        return False

    def _should_enter_footer(self, tag, attrs) -> bool:
        if tag != "footer":
            return False
        class_list = self._class_list(attrs)
        return "footer" in class_list or not class_list

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if not self.in_header and self._should_enter_header(tag, attrs):
            self.in_header = True
            self.header_depth = 1
        elif self.in_header and tag not in self._void_tags:
            self.header_depth += 1

        if not self.in_footer and self._should_enter_footer(tag, attrs):
            self.in_footer = True
            self.footer_depth = 1
        elif self.in_footer and tag not in self._void_tags:
            self.footer_depth += 1

        if (self.in_header or self.in_footer) and tag == "a":
            self.in_anchor = True
            self.anchor_href = attrs.get("href")
            self.anchor_text_parts = []
            self.anchor_attrs = attrs

        if self.in_anchor and tag not in self._void_tags:
            self._class_stack.append(self._class_list(attrs))

    def handle_endtag(self, tag):
        if self.in_anchor and tag == "a":
            text = " ".join("".join(self.anchor_text_parts).split())
            self.collected.append((text, self.anchor_href, self.anchor_attrs))
            self.in_anchor = False
            self.anchor_href = None
            self.anchor_text_parts = []
            self.anchor_attrs = {}
            self._class_stack = []
        elif self.in_anchor and tag not in self._void_tags and self._class_stack:
            self._class_stack.pop()

        if self.in_header and tag not in self._void_tags:
            self.header_depth -= 1
            if self.header_depth <= 0:
                self.in_header = False
                self.header_depth = 0

        if self.in_footer and tag not in self._void_tags:
            self.footer_depth -= 1
            if self.footer_depth <= 0:
                self.in_footer = False
                self.footer_depth = 0

    def handle_data(self, data):
        if (self.in_header or self.in_footer) and self.in_anchor:
            if any(
                cls in self._exclude_text_classes
                for class_list in self._class_stack
                for cls in class_list
            ):
                return
            self.anchor_text_parts.append(data)


def is_jobnimbus_domain(url: str) -> bool:
    parsed = urlparse(url)
    if not parsed.netloc:
        return False
    return parsed.netloc.lower().endswith("jobnimbus.com")


def normalize_link(href: str) -> str:
    return urljoin(BASE_URL, href)


def should_skip_link(text: str, href: str, attrs: dict) -> bool:
    if not href or not href.strip():
        return True
    href = href.strip()
    if href.startswith("#"):
        return True
    if href.startswith(("mailto:", "tel:", "javascript:")):
        return True
    if not text:
        return True
    class_list = attrs.get("class", "").split()
    if any(
        cls in class_list
        for cls in (
            "navbar_brand",
            "w-nav-brand",
            "footer_top-download-item",
            "footer_bot-social-link",
        )
    ):
        return True
    return False


def extract_top_nav_links(html_text: str):
    parser = TopNavParser()
    parser.feed(html_text)
    results = []
    seen_urls = set()

    for text, href, attrs in parser.collected:
        if should_skip_link(text, href, attrs):
            continue
        full_url = normalize_link(href)
        if not is_jobnimbus_domain(full_url):
            continue
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        results.append((text, full_url))

    return results


def main() -> None:
    with open("jobnimbus.html", "r", encoding="utf-8") as handle:
        html_text = handle.read()

    links = extract_top_nav_links(html_text)

    with open("navigation_links_jobnimbus.csv", "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["link_text", "full_url"])
        writer.writerows(links)


if __name__ == "__main__":
    main()
