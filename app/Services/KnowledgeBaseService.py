from pathlib import Path

DEFAULT_KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent.parent / "data" / "knowledge_base.md"


class KnowledgeBaseService:
    def __init__(self, path=None, text=None):
        self._path = Path(path) if path else DEFAULT_KNOWLEDGE_BASE_PATH
        self._text = text
        self._sections = None

    def sections(self):
        if self._sections is None:
            source = self._text if self._text is not None else self._read_file()
            self._sections = self._parse(source)
        return self._sections

    def _read_file(self):
        try:
            return self._path.read_text(encoding="utf-8")
        except OSError:
            return ""

    def _parse(self, markdown):
        sections = []
        current = None
        alias_lines = []
        localized = {}
        for raw_line in (markdown or "").splitlines():
            line = raw_line.rstrip()
            if line.startswith("## "):
                if current is not None:
                    sections.append(self._build(current, alias_lines, localized))
                current = {"heading": line[3:].strip(), "lines": []}
                alias_lines = []
                localized = {}
            elif current is not None:
                lowered = line.lower()
                if lowered.startswith("aliases:"):
                    alias_lines.append(line)
                elif lowered.startswith("key:"):
                    current["key"] = line.split(":", 1)[1].strip().lower()
                elif lowered.startswith("heading-") or lowered.startswith("body-") or lowered.startswith("aliases-"):
                    self._parse_localized(localized, line)
                else:
                    current["lines"].append(line)
        if current is not None:
            sections.append(self._build(current, alias_lines, localized))
        return sections

    def _parse_localized(self, localized, line):
        field, _, rest = line.partition("-")
        locale, _, value = rest.partition(":")
        field = field.lower()
        locale = locale.strip()
        value = value.strip()
        if not locale:
            return
        entry = localized.setdefault(locale, {})
        if field == "heading":
            entry["heading"] = value
        elif field == "body":
            entry["body"] = value
        elif field == "aliases":
            aliases = entry.setdefault("aliases", [])
            for alias in value.split(","):
                alias = alias.strip().lower()
                if alias:
                    aliases.append(alias)

    def _build(self, current, alias_lines, localized):
        aliases = []
        for line in alias_lines:
            _, _, rest = line.partition(":")
            for alias in rest.split(","):
                alias = alias.strip().lower()
                if alias:
                    aliases.append(alias)
        body = "\n".join(item for item in current["lines"] if item.strip()).strip()
        return {
            "heading": current["heading"],
            "key": current.get("key"),
            "aliases": aliases,
            "body": body,
            "localized": localized,
        }