"""Photo guard shared by the pre-commit and pre-push hooks (RELEASE.md).

Refuses a notebook with outputs or attachments (nbformat 4 cells and nbformat 3 worksheets), a
non-Markdown file under data/, a copy of an original from data/raw/ or data/external/, an image or
video outside .images_readme/, a .images_readme/ image without its <stem>.md sidecar or within
difference-hash distance NEAR of an original, a Git LFS pointer, a .gitattributes that sets a
filter, a data:image or data:video URI and an archive.

  python3 photo_guard.py pre-commit          checks the staged blobs
  python3 photo_guard.py pre-push <remote>   checks the blobs of the pushed commits (refs on stdin)
"""

import hashlib
import io
import json
import os
import pickle
import re
import subprocess
import sys

NEAR = 10  # Hamming distance of the 64-bit difference hash at or below which an image is a copy
VENV_PYTHON = ".venv/bin/python"
# a URI needs the ; or , after the subtype, so prose naming the scheme passes
DATA_URI = re.compile(rb"data:(?:image|video)/[\w.+-]*[;,]", re.IGNORECASE)
OUTPUTS_ADVICE = {
    "pre-commit": ("staged", "clear them (RELEASE.md), stage again and commit"),
    "pre-push": ("in the pushed commits", "clear them (RELEASE.md), amend the commits and push"),
}


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def media_type(b):
    if b[:3] == b"\xff\xd8\xff":
        return "JPEG image"
    if b[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG image"
    if b[:6] in (b"GIF87a", b"GIF89a"):
        return "GIF image"
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP":
        return "WebP image"
    if b[:4] in (b"II*\0", b"MM\0*"):
        return "TIFF image"
    if b[:2] == b"BM" and b[6:10] == bytes(4):
        return "BMP image"  # reserved zeros keep "BM..." text out
    if b[:4] == b"\x1a\x45\xdf\xa3":
        return "WebM/MKV video"
    if b[4:8] == b"ftyp":
        brand = b[8:12]
        if brand in (b"heic", b"heix", b"hevc", b"hevx", b"heim", b"heis", b"mif1", b"msf1"):
            return "HEIC/HEIF image"
        if brand in (b"avif", b"avis"):
            return "AVIF image"
        if brand == b"qt  ":
            return "MOV video"
        return "MP4/M4V video (ftyp " + brand.decode("latin-1").strip() + ")"
    return None


def archive_type(b):
    if b[:4] in (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"):
        return "zip"
    if b[:3] == b"\x1f\x8b\x08":
        return "gzip"
    if b[257:262] == b"ustar":
        return "tar"
    if b[:6] == b"7z\xbc\xaf\x27\x1c":
        return "7z"
    if b[:6] == b"Rar!\x1a\x07":
        return "rar"
    if re.match(rb"BZh[1-9]", b):
        return "bzip2"
    if b[:6] == b"\xfd7zXZ\x00":
        return "xz"
    return None


def is_image(b):
    return (media_type(b) or "").endswith(" image")


def notebook_cells(b):
    """Cells of a notebook blob: nbformat 4 top-level cells and nbformat 3 worksheet cells."""
    nb = json.loads(b)
    return nb.get("cells", []) + [c for w in nb.get("worksheets", []) for c in w.get("cells", [])]


def staged():
    """(label, path, blob, tracked paths) of every staged added, copied, modified, renamed or
    type-changed file; tracked paths are the index."""
    names = git("diff", "--cached", "--name-only", "-z", "--diff-filter=ACMRT")
    index = set(os.fsdecode(git("ls-files", "-z")).split("\0"))
    return [
        (p, p, git("cat-file", "blob", ":0:" + p), index)
        for p in os.fsdecode(names).split("\0")
        if p
    ]


def pushed(remote, ref_lines):
    """(label, path, blob, tracked paths) of every blob each pushed commit adds or changes, for the
    commits not already on a remote-tracking ref of the remote; tracked paths are the commit tree."""
    entries = []
    for line in ref_lines:
        local_sha = line.split()[1]
        if set(local_sha) == {"0"}:  # a deleted ref pushes no commit
            continue
        commits = git("rev-list", local_sha, "--not", "--remotes=" + remote)
        for commit in os.fsdecode(commits).split():
            tree = {}  # path -> (object type, sha)
            for record in os.fsdecode(git("ls-tree", "-r", "-z", commit)).split("\0"):
                if record:
                    meta, _, path = record.partition("\t")
                    tree[path] = meta.split()[1:3]
            names = git(
                "diff-tree",
                "-r",
                "--root",
                "-m",
                "--no-commit-id",
                "--name-only",
                "-z",
                "--diff-filter=ACMRT",
                commit,
            )
            for p in sorted({p for p in os.fsdecode(names).split("\0") if p}):
                kind, sha = tree[p]
                if kind == "blob":  # a submodule gitlink holds no blob
                    entries.append((commit[:12] + ":" + p, p, git("cat-file", "blob", sha), tree))
    return entries


def tracked_originals():
    """(label, size, blob sha) of every non-.md blob HEAD records under data/raw/ or data/external/
    outside .ipynb_checkpoints, so a git mv of an original committed with --no-verify is still
    compared; none before the first commit."""
    head = ["git", "rev-parse", "-q", "--verify", "HEAD"]
    if subprocess.run(head, capture_output=True, check=False).returncode:
        return []
    found = []
    tree = git("ls-tree", "-r", "-l", "-z", "HEAD", "--", "data/raw", "data/external")
    for record in os.fsdecode(tree).split("\0"):
        if record:
            meta, _, path = record.partition("\t")
            _, kind, sha, size = meta.split()
            skip = path.endswith(".md") or ".ipynb_checkpoints" in path.split("/")
            if kind == "blob" and not skip:
                found.append(("HEAD:" + path, int(size), sha))
    return found


def read(label, blob, n=-1):
    """The first n bytes, or all, of an original: the git blob with sha blob, else the file at
    path label."""
    if blob:  # rare, since the data/ rule refuses a commit that adds one, so read whole
        b = git("cat-file", "blob", blob)
        return b if n < 0 else b[:n]
    with open(label, "rb") as fh:
        return fh.read(n)


def dhash(item):
    """64-bit difference hash (9x8 greyscale) of a file path or blob bytes, or None if undecodable."""
    from PIL import Image, ImageOps

    try:
        im = Image.open(item if isinstance(item, str) else io.BytesIO(item))
        im.draft("L", (288, 256))  # JPEG decodes at a reduced scale, much faster
        im = ImageOps.exif_transpose(im).convert("L").resize((9, 8), Image.Resampling.LANCZOS)
    except Exception:  # noqa: BLE001 - Pillow raises many types for a truncated or unsupported file
        return None
    px = im.tobytes()
    return sum(
        1 << (r * 8 + c) for r in range(8) for c in range(8) if px[r * 9 + c] > px[r * 9 + c + 1]
    )


def dhash_all(items):
    """Difference hashes of items through the project venv's Pillow, or the reason they failed."""
    if not os.access(VENV_PYTHON, os.X_OK):
        return f"the near-copy check needs Pillow in {VENV_PYTHON}, which is missing"
    run = subprocess.run(
        [VENV_PYTHON, "-I", os.path.abspath(__file__), "dhash"],
        input=pickle.dumps(items),
        capture_output=True,
        check=False,
    )
    if run.returncode:
        last = (run.stderr.decode(errors="replace").strip().splitlines() or ["no error text"])[-1]
        return f"the near-copy check failed in {VENV_PYTHON}: {last}"
    return json.loads(run.stdout)


def near_copies(readme, originals):
    """Refusals of readme images [(label, blob)] within NEAR of an original image's hash."""
    images = [(label, blob) for label, _, blob in originals if is_image(read(label, blob, 16))]
    if not images:
        return []
    cache_path = os.fsdecode(git("rev-parse", "--git-path", "photo-guard-cache.json")).strip()
    try:
        with open(cache_path) as fh:
            cache = json.load(fh)  # sha256 of an original -> its difference hash or null
    except (OSError, ValueError):
        cache = {}
    shas = {label: hashlib.sha256(read(label, blob)).hexdigest() for label, blob in images}
    missing = [(p, blob) for p, blob in images if shas[p] not in cache]
    # a file goes to the decoder by its path, a git blob by its bytes
    items = [p if blob is None else read(p, blob) for p, blob in missing]
    hashes = dhash_all([b for _, b in readme] + items)
    if isinstance(hashes, str):
        return [(label, hashes) for label, _ in readme]
    if missing:
        cache.update({shas[p]: h for (p, _), h in zip(missing, hashes[len(readme) :])})
        with open(cache_path, "w") as fh:
            json.dump(cache, fh)
    # shortcut: an original Pillow cannot decode (cached as null) is not compared; fix by a plugin
    known = [(cache[shas[p]], p) for p, _ in images if cache[shas[p]] is not None]
    refusals = []
    for (label, _), h in zip(readme, hashes):
        if h is None:
            refusals.append((label, "image cannot be decoded for the near-copy check"))
            continue
        distance, original = min((((h ^ o).bit_count(), p) for o, p in known), default=(64, ""))
        if distance <= NEAR:
            reason = f"near-copy of the original {original} (difference-hash distance {distance})"
            refusals.append((label, reason))
    return refusals


def check(entries, hook):
    """Print the refusals of entries [(label, path, blob, tracked paths)]; return 1 on any."""
    # originals [(label, size, blob sha or None)] indexed by size first, so only same-size ones
    # are hashed
    originals = []
    for top in ("data/raw", "data/external"):
        for root, dirs, files in os.walk(top):
            dirs[:] = [d for d in dirs if d != ".ipynb_checkpoints"]
            for f in files:
                path = os.path.join(root, f)
                if not f.endswith(".md") and os.path.isfile(path):
                    originals.append((path, os.path.getsize(path), None))
    if hook == "pre-commit":  # at push, the data/ rule refuses the pushed commit that added one
        originals += tracked_originals()
    sizes = {len(b) for _, _, b, _ in entries}
    by_sha = {}
    for label, size, blob in originals:
        if size in sizes:
            by_sha.setdefault(hashlib.sha256(read(label, blob)).hexdigest(), label)

    refusals, with_outputs, readme = [], [], []
    for label, p, b, tracked in entries:
        if p.startswith("data/") and not (p.endswith(".md") or os.path.basename(p) == ".gitkeep"):
            refusals.append((label, "only .md and .gitkeep files may be committed under data/"))
        original = by_sha.get(hashlib.sha256(b).hexdigest())
        if original:
            refusals.append((label, "byte-equal to the original " + original))
        kind = media_type(b)
        if kind and not p.startswith(".images_readme/"):
            refusals.append((label, kind + " outside .images_readme/"))
        sidecar = os.path.splitext(p)[0] + ".md"
        if kind and p.startswith(".images_readme/") and sidecar not in tracked:
            refusals.append((label, "no sidecar " + sidecar + " staged or tracked"))
        if p.startswith(".images_readme/") and is_image(b):
            readme.append((label, b))
        if p.endswith(".ipynb"):
            try:
                cells = notebook_cells(b)
                if any(c.get("attachments") for c in cells):
                    refusals.append((label, "notebook cell carries attachments"))
                if any(c.get("outputs") for c in cells):
                    with_outputs.append(label)
            except (ValueError, AttributeError, TypeError):
                with_outputs.append(label)  # a notebook that cannot be read is refused as before
        if b.startswith(b"version https://git-lfs.github.com/spec/v1"):
            refusals.append((label, "Git LFS pointer; content filters are refused"))
        if os.path.basename(p) == ".gitattributes" and b"filter=" in b:
            refusals.append((label, "sets a filter= attribute; content filters are refused"))
        if DATA_URI.search(b):
            refusals.append((label, "holds a data:image or data:video URI"))
        if archive_type(b):
            refusals.append((label, archive_type(b) + " archive"))
    if readme:
        refusals += near_copies(readme, originals)

    if refusals:
        print(f"{hook}: refused:", file=sys.stderr)
        for label, reason in refusals:
            print(f"  {label}: {reason}", file=sys.stderr)
    if with_outputs:
        where, advice = OUTPUTS_ADVICE[hook]
        print(f"{hook}: notebooks with outputs are {where}:", file=sys.stderr)
        for label in with_outputs:
            print(f"  {label}", file=sys.stderr)
        print(advice, file=sys.stderr)
    return int(bool(refusals or with_outputs))


if __name__ == "__main__":
    if sys.argv[1] == "dhash":
        print(json.dumps([dhash(item) for item in pickle.load(sys.stdin.buffer)]))
    elif sys.argv[1] == "pre-commit":
        sys.exit(check(staged(), "pre-commit"))
    else:
        sys.exit(check(pushed(sys.argv[2], sys.stdin.read().splitlines()), "pre-push"))
