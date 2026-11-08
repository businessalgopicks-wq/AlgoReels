#!/usr/bin/env python3
"""Search Openverse, download open media and keep an attribution ledger. Standard library only.

  openverse.py search {images,audio} QUERY [filters]
  openverse.py get {images,audio} ID
  openverse.py download {images,audio} ID --out DIR
  openverse.py credits DIR
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

API = "https://api.openverse.org/v1"
USER_AGENT = "algoreel-openverse/1.0"
DEFAULT_LICENSES = "cc0,pdm,by"
MAX_BYTES = 200 * 1024 * 1024
ID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
LEDGER = "credits.jsonl"


def fail(message):
    print(f"openverse: {message}", file=sys.stderr)
    sys.exit(1)


def request(url, accept="application/json"):
    headers = {"User-Agent": USER_AGENT, "Accept": accept}
    token = os.environ.get("OPENVERSE_TOKEN")
    if token and url.startswith(API):
        headers["Authorization"] = f"Bearer {token}"
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=45)


def api_get(path, params=None):
    url = f"{API}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    try:
        with request(url) as response:
            left = [
                f"{name.split('available-')[1]}={value}"
                for name, value in response.headers.items()
                if name.lower().startswith("x-ratelimit-available-")
            ]
            if left:
                print("rate limit left: " + ", ".join(left), file=sys.stderr)
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            fail(f"rate limited. Retry after {error.headers.get('Retry-After', 'a while')} seconds.")
        body = error.read(400).decode("utf-8", "replace")
        fail(f"HTTP {error.code} for {url}: {body}")
    except urllib.error.URLError as error:
        fail(f"could not reach the API: {error.reason}")


def licence_label(item):
    version = item.get("license_version")
    return item["license"] + (f" {version}" if version and version != "N/A" else "")


def shape(item, kind):
    if kind == "images":
        if item.get("width") and item.get("height"):
            return f"{item['width']}x{item['height']}"
        return "?"
    duration = item.get("duration")
    return f"{duration / 1000:.1f}s" if duration else "?"


def cmd_search(args):
    params = {"q": args.query, "filter_dead": "true", "page": args.page, "page_size": args.page_size}
    if args.license_type:
        params["license_type"] = args.license_type
    else:
        params["license"] = args.license
    optional = {
        "source": args.source,
        "extension": args.extension,
        "creator": args.creator,
        "category": args.category,
        "aspect_ratio": args.aspect,
        "size": args.size,
        "length": args.length,
    }
    if args.creator:
        # The API refuses creator alongside q, so a creator search is creator-only.
        params.pop("q")
    params.update({key: value for key, value in optional.items() if value})
    data = api_get(f"/{args.kind}/", params)
    if args.json:
        print(json.dumps(data, indent=1))
        return
    print(f"{data.get('result_count', 0)} results, page {data.get('page')} of {data.get('page_count')}")
    for item in data.get("results", []):
        title = (item.get("title") or "untitled")[:60]
        creator = (item.get("creator") or "unknown")[:28]
        print(
            f"{item['id']}  {licence_label(item):11s} {item.get('source', '?'):16s} "
            f"{shape(item, args.kind):>11s}  {title} by {creator}"
        )


def get_item(kind, item_id):
    if not ID_RE.match(item_id):
        fail(f"not an Openverse id: {item_id!r}")
    return api_get(f"/{kind}/{item_id}/")


def cmd_get(args):
    print(json.dumps(get_item(args.kind, args.id), indent=1))


def safe_slug(text):
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "untitled").lower()).strip("-")
    return slug[:48] or "untitled"


def extension_of(item):
    candidate = item.get("filetype") or Path(urllib.parse.urlparse(item["url"]).path).suffix.lstrip(".")
    candidate = (candidate or "bin").lower()
    return candidate if re.fullmatch(r"[a-z0-9]{1,5}", candidate) else "bin"


def read_ledger(directory):
    path = directory / LEDGER
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cmd_download(args):
    item = get_item(args.kind, args.id)
    url = item.get("url") or ""
    if urllib.parse.urlparse(url).scheme not in ("http", "https"):
        fail(f"unexpected media URL: {url!r}")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    target = out / f"{safe_slug(item.get('title'))}-{item['id'][:8]}.{extension_of(item)}"

    partial = target.with_name(target.name + ".part")
    written = 0
    try:
        with request(url, accept="*/*") as response, open(partial, "wb") as handle:
            while chunk := response.read(1 << 16):
                written += len(chunk)
                if written > MAX_BYTES:
                    handle.close()
                    partial.unlink()
                    fail(f"refusing a file over {MAX_BYTES // (1024 * 1024)} MB: {url}")
                handle.write(chunk)
    except urllib.error.HTTPError as error:
        partial.unlink(missing_ok=True)
        fail(f"HTTP {error.code} downloading {url}. Try the landing page: {item.get('foreign_landing_url')}")
    except urllib.error.URLError as error:
        partial.unlink(missing_ok=True)
        fail(f"could not download {url}: {error.reason}")
    partial.replace(target)

    entries = [entry for entry in read_ledger(out) if entry["id"] != item["id"]]
    entries.append(
        {
            "id": item["id"],
            "kind": args.kind,
            "file": target.name,
            "title": item.get("title"),
            "creator": item.get("creator"),
            "creator_url": item.get("creator_url"),
            "license": item.get("license"),
            "license_version": item.get("license_version"),
            "license_url": item.get("license_url"),
            "source": item.get("source"),
            "landing_page": item.get("foreign_landing_url"),
            "attribution": item.get("attribution"),
            "media_url": url,
            "downloaded": date.today().isoformat(),
        }
    )
    (out / LEDGER).write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries), encoding="utf-8")
    print(f"{target}  ({written / 1024:.0f} KB, {licence_label(item)})")
    print(f"confirm the licence on the source page before publishing: {item.get('foreign_landing_url')}")


def cmd_credits(args):
    directory = Path(args.dir)
    entries = read_ledger(directory)
    if not entries:
        fail(f"no {LEDGER} in {directory}")
    required = [e for e in entries if e.get("license") not in ("cc0", "pdm")]
    free = [e for e in entries if e.get("license") in ("cc0", "pdm")]
    lines = ["# Credits", "", f"Open media found through Openverse ({len(entries)} files).", ""]
    if required:
        lines += ["## Attribution required", ""]
        lines += [f"- {e['attribution']} Source: {e['landing_page']}" for e in required]
        lines.append("")
    if free:
        lines += ["## No attribution required (recorded for provenance)", ""]
        lines += [f"- {e['attribution']} Source: {e['landing_page']}" for e in free]
        lines.append("")
    target = directory / "CREDITS.md"
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f"{target}  ({len(required)} need attribution, {len(free)} do not)")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search", help="search images or audio")
    search.add_argument("kind", choices=["images", "audio"])
    search.add_argument("query")
    search.add_argument("--license", default=DEFAULT_LICENSES, help=f"comma list, default {DEFAULT_LICENSES}")
    search.add_argument("--license-type", help="commercial, modification, all-cc, all; replaces --license")
    search.add_argument("--category")
    search.add_argument("--source")
    search.add_argument("--extension")
    search.add_argument("--creator", help="search this creator instead of the query")
    search.add_argument("--aspect", choices=["tall", "wide", "square"], help="images only")
    search.add_argument("--size", choices=["small", "medium", "large"], help="images only")
    search.add_argument("--length", choices=["shortest", "short", "medium", "long"], help="audio only")
    search.add_argument("--page", type=int, default=1)
    search.add_argument("--page-size", type=int, default=10)
    search.add_argument("--json", action="store_true")
    search.set_defaults(run=cmd_search)

    get = commands.add_parser("get", help="print one record")
    get.add_argument("kind", choices=["images", "audio"])
    get.add_argument("id")
    get.set_defaults(run=cmd_get)

    download = commands.add_parser("download", help="save the file and record its attribution")
    download.add_argument("kind", choices=["images", "audio"])
    download.add_argument("id")
    download.add_argument("--out", required=True)
    download.set_defaults(run=cmd_download)

    credits = commands.add_parser("credits", help="write CREDITS.md from a folder's ledger")
    credits.add_argument("dir")
    credits.set_defaults(run=cmd_credits)
    return parser


if __name__ == "__main__":
    arguments = build_parser().parse_args()
    arguments.run(arguments)
