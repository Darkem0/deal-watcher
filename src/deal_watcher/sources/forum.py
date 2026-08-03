from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit, urlunsplit

from selectolax.parser import HTMLParser, Node

from deal_watcher.models.domain import ForumTopic, ParseResult


class ForumParseError(ValueError):
    pass


def _text(node: Node, selector: str) -> str | None:
    child = node.css_first(selector)
    if child is None:
        return None
    value = child.text(strip=True)
    return value or None


def _parse_int(value: str | None) -> int:
    if not value:
        return 0
    normalized = value.strip().lower()
    multiplier = 1000 if normalized.endswith("k") else 1
    if multiplier == 1000:
        normalized = normalized[:-1].replace(",", ".")
    else:
        normalized = normalized.replace(".", "").replace(",", ".")
    try:
        return int(float(normalized) * multiplier)
    except ValueError as exc:
        raise ForumParseError(f"invalid numeric field: {value!r}") from exc


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ForumParseError(f"invalid datetime field: {value!r}") from exc


def _canonical_url(base_url: str, href: str) -> str:
    parts = urlsplit(urljoin(base_url, href))
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


class DonanimArsiviForumParser:
    """Parser for topic-list HTML; all source selectors live in this adapter."""

    row_selector = "article.topic-row, div.structItem--thread"

    def parse(self, html: str, base_url: str) -> ParseResult:
        tree = HTMLParser(html)
        topics: list[ForumTopic] = []
        errors: list[str] = []
        for index, row in enumerate(tree.css(self.row_selector), start=1):
            try:
                topics.append(self._parse_row(row, base_url))
            except ForumParseError as exc:
                errors.append(f"row {index}: {exc}")
        if not topics and not errors:
            errors.append(f"no rows matched selector {self.row_selector!r}")
        return ParseResult(tuple(topics), tuple(errors))

    def _parse_row(self, row: Node, base_url: str) -> ForumTopic:
        link = row.css_first("a.topic-title, .structItem-title > a[data-tp-primary]")
        if link is None:
            raise ForumParseError("missing topic title link")
        href = link.attributes.get("href")
        title = link.text(strip=True)
        topic_id = row.attributes.get("data-topic-id")
        if not topic_id:
            match = re.search(r"js-threadListItem-(\d+)", row.attributes.get("class", ""))
            topic_id = match.group(1) if match else None
        if not href or not title or not topic_id:
            raise ForumParseError("topic_id, title and href are required")
        prefixes = tuple(
            node.text(strip=True)
            for node in row.css(".topic-prefix, .structItem-title .label, .structItem .label")
            if node.text(strip=True)
        )
        return ForumTopic(
            topic_id=topic_id,
            canonical_topic_url=_canonical_url(base_url, href),
            title=title,
            prefix_labels=prefixes,
            author=_text(row, ".topic-author") or row.attributes.get("data-author"),
            created_at=_parse_datetime(row.attributes.get("data-created-at")),
            last_activity_at=_parse_datetime(row.attributes.get("data-last-activity-at")),
            last_activity_user=_text(row, ".last-activity-user"),
            reply_count=_parse_int(_text(row, ".reply-count")),
            view_count=_parse_int(_text(row, ".view-count")),
            page_count=max(1, _parse_int(_text(row, ".page-count"))),
            is_locked=row.attributes.get("data-locked", "false").lower() == "true",
            is_sticky=row.attributes.get("data-sticky", "false").lower() == "true",
        )


_AMOUNT = r"\d{1,3}(?:\.\d{3})*(?:,\d{1,2})?|\d+(?:[,.]\d{1,2})?"
_PRICE_PATTERN = re.compile(
    rf"(?<![\w])(?:(?:₺|TL|TRY)\s*({_AMOUNT})|({_AMOUNT})\s*(?:TL|TRY|₺)|({_AMOUNT})\s*[Kk])",
    re.IGNORECASE,
)


def extract_price_kurus(text: str) -> list[int]:
    """Extract explicit Turkish-currency amounts, excluding bare hardware specifications."""
    prices: list[int] = []
    for match in _PRICE_PATTERN.finditer(text):
        raw = match.group(1) or match.group(2) or match.group(3)
        assert raw is not None
        if match.group(3):
            raw = raw.replace(",", ".")
            prices.append(round(float(raw) * 100_000))
            continue
        value = raw.replace(".", "").replace(",", ".")
        prices.append(round(float(value) * 100))
    return prices
