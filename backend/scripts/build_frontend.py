import argparse
import json
import shutil
from pathlib import Path


TEXT_EXTENSIONS = {".html", ".css", ".js"}
JSON_EXTENSIONS = {".json"}
SKIP_DIRS = {"__pycache__"}


def normalize_text(text: str) -> str:
    ends_with_newline = text.endswith(("\n", "\r\n", "\r"))
    normalized = "\n".join(line.rstrip() for line in text.splitlines())
    if ends_with_newline:
        normalized += "\n"
    return normalized


def should_skip(path: Path) -> bool:
    return any(part in SKIP_DIRS for part in path.parts)


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    ensure_dir(path)
    path.write_text(text, encoding="utf-8", newline="\n")


def compile_json(src: Path, dst: Path) -> None:
    try:
        data = json.loads(src.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON: {src}") from exc
    write_text(dst, json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n")


def compile_text(src: Path, dst: Path) -> None:
    text = src.read_text(encoding="utf-8")
    write_text(dst, normalize_text(text))


def copy_binary(src: Path, dst: Path) -> None:
    ensure_dir(dst)
    shutil.copy2(src, dst)


def compile_tree(src_root: Path, dst_root: Path) -> dict:
    counts = {"json": 0, "text": 0, "binary": 0}
    for src in src_root.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(src_root)
        if should_skip(rel):
            continue
        dst = dst_root / rel
        suffix = src.suffix.lower()
        if suffix in JSON_EXTENSIONS:
            compile_json(src, dst)
            counts["json"] += 1
        elif suffix in TEXT_EXTENSIONS:
            compile_text(src, dst)
            counts["text"] += 1
        else:
            copy_binary(src, dst)
            counts["binary"] += 1
    return counts


def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build frontend assets into a dist folder.")
    parser.add_argument(
        "--out",
        default="dist/frontend",
        help="Output directory (relative to backend/).",
    )
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--templates-only",
        action="store_true",
        help="Only compile templates into dist/templates.",
    )
    scope_group.add_argument(
        "--static-only",
        action="store_true",
        help="Only compile static assets into dist/static.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove the output directory and exit.",
    )
    args = parser.parse_args()

    backend_root = Path(__file__).resolve().parents[1]
    out_dir = backend_root / args.out

    if args.clean:
        clean_dir(out_dir)
        return

    templates_src = backend_root / "templates"
    static_src = backend_root / "static"

    counts = {"json": 0, "text": 0, "binary": 0}

    if args.templates_only:
        clean_dir(out_dir / "templates")
        if templates_src.exists():
            result = compile_tree(templates_src, out_dir / "templates")
            for key in counts:
                counts[key] += result[key]
        summary = (
            f"Built frontend templates to {out_dir} "
            f"(json={counts['json']}, text={counts['text']}, binary={counts['binary']})."
        )
        print(summary)
        return

    if args.static_only:
        clean_dir(out_dir / "static")
        if static_src.exists():
            result = compile_tree(static_src, out_dir / "static")
            for key in counts:
                counts[key] += result[key]
        summary = (
            f"Built frontend static assets to {out_dir} "
            f"(json={counts['json']}, text={counts['text']}, binary={counts['binary']})."
        )
        print(summary)
        return

    clean_dir(out_dir)

    if templates_src.exists():
        result = compile_tree(templates_src, out_dir / "templates")
        for key in counts:
            counts[key] += result[key]

    if static_src.exists():
        result = compile_tree(static_src, out_dir / "static")
        for key in counts:
            counts[key] += result[key]

    summary = (
        f"Built frontend assets to {out_dir} "
        f"(json={counts['json']}, text={counts['text']}, binary={counts['binary']})."
    )
    print(summary)


if __name__ == "__main__":
    main()
