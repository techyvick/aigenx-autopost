#!/usr/bin/env python3
"""Post-now inbox: upload images into the post-now/ folder on GitHub and they're posted right away.

- Images directly inside post-now/ = one post. Each subfolder of post-now/ = one post.
- JPG or PNG, 1–10 images (2 or more = carousel), in file-name order (slide-1, slide-2, …).
- Optional caption.txt = the caption.
- Optional platforms.txt = facebook, instagram or both (default: both).
- After posting, the files are removed and a line is added to post-now/log.txt.
  If only one platform worked, platforms.txt is rewritten to the one that failed, so a retry
  (Actions → Post now → Run workflow) never double-posts.

Runs in GitHub Actions (post-now.yml) and reuses the posting code in publish.py.
"""
import os, re, shutil, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import publish

INBOX = publish.ROOT / "post-now"
IMAGES = {".jpg", ".jpeg", ".png"}
EXTRAS = ("caption.txt", "platforms.txt")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout.strip()


def push(message):
    git("add", "-A", "post-now")
    if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode == 0:
        return
    git("commit", "-m", message)
    git("pull", "--rebase")
    git("push")


def images(folder):
    natural = lambda f: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", f.name)]
    return sorted((f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGES), key=natural)


def find_posts():
    posts = [INBOX] if images(INBOX) else []
    return posts + sorted(d for d in INBOX.iterdir() if d.is_dir() and images(d))


def to_jpeg(folder):
    pngs = [f for f in images(folder) if f.suffix.lower() == ".png"]
    if pngs:
        from PIL import Image
        for f in pngs:
            Image.open(f).convert("RGB").save(f.with_suffix(".jpg"), "JPEG", quality=92)
            f.unlink()
    return bool(pngs)


def read(folder, name):
    f = folder / name
    return f.read_text(encoding="utf-8").strip() if f.exists() else ""


def platforms(text):
    text = text.lower()
    nets = [n for n in ("facebook", "instagram") if n in text]
    return nets or ["facebook", "instagram"]


def clear(folder):
    if folder == INBOX:
        for f in images(folder) + [folder / n for n in EXTRAS]:
            f.unlink(missing_ok=True)
    else:
        shutil.rmtree(folder)


def main():
    if not INBOX.is_dir():
        print("No post-now/ folder.")
        return 0
    posts = find_posts()
    if not posts:
        print("post-now/ has no images, nothing to post.")
        return 0

    git("config", "user.name", "autopost-bot")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    if True in [to_jpeg(p) for p in posts]:
        push("post-now: convert PNG to JPG")
    # Pin image URLs to this exact commit so they keep working after the files are removed
    raw = f"https://raw.githubusercontent.com/{os.environ['GITHUB_REPOSITORY']}/{git('rev-parse', 'HEAD')}"

    log, failures = [], 0
    for folder in posts:
        rel = folder.relative_to(publish.ROOT)
        name = "post-now/" if folder == INBOX else rel.name
        files = images(folder)
        nets = platforms(read(folder, "platforms.txt"))
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        if len(files) > publish.MAX_SLIDES:
            print(f"✗ {name}: {len(files)} images, the limit is {publish.MAX_SLIDES}")
            log.append(f"{stamp} | {name} | ✗ too many images ({len(files)}, max {publish.MAX_SLIDES})")
            failures += 1
            continue
        base = raw if str(rel.parent) == "." else f"{raw}/{quote(str(rel.parent))}"
        p = {"id": quote(rel.name), "slides": [quote(f.name) for f in files], "caption": read(folder, "caption.txt")}
        print(f"{name}: {len(files)} image(s) → {', '.join(nets)}")
        done, failed = [], []
        for net in nets:
            try:
                post_id = publish.post_instagram(p, base) if net == "instagram" else publish.post_facebook(p, base)
                print(f"   ✓ {net}: posted ({post_id})")
                done.append(f"{net} ✓ {post_id}")
            except publish.ApiError as e:
                print(f"   ✗ {net}: {e}")
                done.append(f"{net} ✗ {e}")
                failed.append(net)
        log.append(f"{stamp} | {name} | {len(files)} image(s) | " + " | ".join(done))
        if failed:
            failures += 1
            (folder / "platforms.txt").write_text(" ".join(failed) + "\n")
        else:
            clear(folder)

    with open(INBOX / "log.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")
    push("post-now: posted" if not failures else "post-now: some posts failed (see log.txt)")
    if failures:
        print("\nFix the problem above, then go to Actions → Post now → Run workflow to retry.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
