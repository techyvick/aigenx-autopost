#!/usr/bin/env python3
"""AIGenX autopost: posts what's in schedule.csv to Instagram and a Facebook Page.
Images (single or carousel) AND videos (Instagram Reels + Facebook Page videos).

schedule.csv columns: folder, date, time, caption, hashtags, platforms
  folder     a folder inside media/ holding EITHER 1–10 images (JPG or PNG; file names set the order)
             OR video: instagram.mp4 (9:16 → Instagram Reel) and optionally facebook.mp4
             (16:9 → Facebook video; without it Facebook gets instagram.mp4). Names containing
             "9x16" / "16x9" also work.
             If the caption cell is empty, the "## Caption" and "## Hashtags" sections of
             media/<folder>/caption.md are used instead.
  date       2026-11-06, 06-11-2026 or 06/11/2026
  time       09:00, 21:30 or 9:00 PM (IST unless TZ_OFFSET is set)
  hashtags   optional, added under the caption: "#diwali #ai" or "diwali, ai"
  platforms  both (default), facebook or instagram
  Start the folder cell with # to switch a row off without deleting it.

  python3 publish.py plan                  list every post, its time and its status
  python3 publish.py check                 validate schedule.csv + media; with META_TOKEN set, also
                                           test the token, Page, Instagram account and image hosting
                                           (creates unpublished test media only, never posts)
  python3 publish.py convert               turn PNGs in media/ into JPGs (needs Pillow; commits in Actions)
  python3 publish.py run [--dry-run] [--now 2026-10-19T09:05+05:30]
                                           queue Facebook posts in Facebook's own scheduler, publish
                                           Instagram posts that are due, and re-queue or cancel queued
                                           Facebook posts whose row was edited or deleted

Environment: META_TOKEN (Page access token), FB_PAGE_ID, IG_USER_ID,
             MEDIA_BASE_URL (optional; default is this repo's raw.githubusercontent.com URL),
             TZ_OFFSET (optional, default +05:30), GRAPH_VERSION (optional, default v23.0).
"""
import csv, hashlib, json, os, re, subprocess, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
SCHEDULE = ROOT / "schedule.csv"
STATE = ROOT / "state.json"
MEDIA = ROOT / "media"
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
FB_MIN_LEAD = timedelta(minutes=15)  # Facebook rejects scheduled posts less than 10 min ahead
FB_MAX_LEAD = timedelta(days=28)     # and more than ~30 days ahead
MAX_LATE = timedelta(hours=float(os.environ.get("MAX_LATE_HOURS", "6")))  # a post this overdue is skipped, not posted late
MAX_ATTEMPTS = 3
MAX_CAPTION = 2200
MAX_SLIDES = 10
IMAGES = {".jpg", ".jpeg", ".png"}
VIDEOS = {".mp4", ".mov"}
REEL_COVER_MS = int(os.environ.get("REEL_COVER_MS", "1600"))  # Reel cover frame (the hook) in ms
GRAPH_VIDEO = "https://graph-video.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
COLUMNS = {"folder": ("folder", "id", "post"), "date": ("date",), "time": ("time",),
           "caption": ("caption",), "hashtags": ("hashtags", "tags"), "platforms": ("platforms", "platform")}
DATE_FORMATS = ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y/%m/%d", "%d-%b-%Y", "%d %b %Y", "%d %B %Y")
TIME_FORMATS = ("%H:%M", "%H.%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p", "%I:%M%p", "%I %p", "%I%p")


class ApiError(Exception):
    pass


def needs_access(err):
    """Meta said the token isn't allowed to do this (missing permission, expired token):
    retried every run instead of counting as a failed attempt, so it posts once the token is fixed."""
    return any(c in str(err) for c in ("(#200)", "(#10)", "(#190)", "(#3)"))


# ---------- schedule + state ----------

def tz_from(offset):
    sign = -1 if offset.startswith("-") else 1
    h, m = offset.lstrip("+-").split(":")
    return timezone(sign * timedelta(hours=int(h), minutes=int(m)))


TZ_OFFSET = os.environ.get("TZ_OFFSET", "+05:30")
TZ = tz_from(TZ_OFFSET)


def images(folder):
    natural = lambda f: [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", f.name)]
    if not folder.is_dir():
        return []
    return sorted((f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in IMAGES), key=natural)


def videos(folder):
    """(vertical, landscape) video files in a folder, or (None, None)."""
    if not folder.is_dir():
        return None, None
    vids = sorted(f for f in folder.iterdir() if f.is_file() and f.suffix.lower() in VIDEOS)
    if not vids:
        return None, None
    v = next((f for f in vids if "instagram" in f.name.lower() or "9x16" in f.name.lower()), None)
    h = next((f for f in vids if "facebook" in f.name.lower() or "16x9" in f.name.lower()), None)
    v = v or next((f for f in vids if f is not h), None) or vids[0]
    return v, h or v


def md_caption(folder):
    """Caption + hashtags from media/<folder>/caption.md (## Caption / ## Hashtags sections)."""
    f = folder / "caption.md"
    if not f.exists():
        return "", ""
    text = f.read_text(encoding="utf-8")
    def section(name):
        m = re.search(rf"^##\s+{name}\s*$\n(.*?)(?=^##\s|^---\s*$|\Z)", text, re.S | re.M | re.I)
        return m.group(1).strip() if m else ""
    return section("Caption"), section("Hashtags")


def parse_when(date, clock):
    for df in DATE_FORMATS:
        try:
            d = datetime.strptime(date.strip(), df)
            break
        except ValueError:
            pass
    else:
        raise ValueError(f"date '{date}' not understood (use 2026-11-06)")
    for tf in TIME_FORMATS:
        try:
            t = datetime.strptime(clock.strip().upper(), tf)
            break
        except ValueError:
            pass
    else:
        raise ValueError(f"time '{clock}' not understood (use 09:00 or 9:00 PM)")
    return d.replace(hour=t.hour, minute=t.minute, tzinfo=TZ)


def hashtags(text):
    tags = [t if t.startswith("#") else "#" + t for t in re.split(r"[\s,]+", text.strip())
            if re.fullmatch(r"#?[\w\u0900-\u09FF]+", t)]   # letters/digits/_ + Devanagari/Bengali; drops "---" etc.
    return " ".join(tags)


def platforms(text):
    text = text.lower()
    nets = [n for n in ("facebook", "instagram") if n in text]
    return nets or ["facebook", "instagram"]


def fingerprint(p):
    raw = json.dumps([p["at"].isoformat(), p["caption"], p["slides"], p["platforms"]] + ([p["kind"]] if p.get("kind") == "video" else []), ensure_ascii=False)
    return hashlib.sha1(raw.encode()).hexdigest()[:16]


def load_schedule():
    """Returns (posts sorted by time, problems, listed). Bad rows are reported and left out;
    listed holds every folder named in an active row, valid or not."""
    if not SCHEDULE.exists():
        return [], ["schedule.csv is missing"], None
    rows = list(csv.reader(SCHEDULE.read_text(encoding="utf-8-sig").splitlines(keepends=True)))
    if not rows:
        return [], ["schedule.csv is empty"], None
    header = [h.strip().lower() for h in rows[0]]
    col = {}
    for key, names in COLUMNS.items():
        col[key] = next((header.index(n) for n in names if n in header), None)
    missing = [k for k in ("folder", "date", "time") if col[k] is None]
    if missing:
        return [], [f"schedule.csv header is missing: {', '.join(missing)}"], None

    posts, problems, seen = [], [], set()
    for line, row in enumerate(rows[1:], start=2):
        cell = lambda k: (row[col[k]].strip() if col[k] is not None and col[k] < len(row) else "")
        folder = cell("folder").strip("/")
        if not any(c.strip() for c in row) or folder.startswith("#"):
            continue
        where = f"row {line} ({folder or 'no folder'})"
        if not folder:
            problems.append(f"{where}: folder is empty")
            continue
        if folder in seen:
            problems.append(f"{where}: folder used twice; give each post its own folder")
            continue
        seen.add(folder)
        try:
            at = parse_when(cell("date"), cell("time"))
        except ValueError as e:
            problems.append(f"{where}: {e}")
            continue
        vert, land = videos(MEDIA / folder)
        files = [vert, land] if vert else images(MEDIA / folder)
        cap, tag_text = cell("caption"), cell("hashtags")
        if not cap:
            cap, md_tags = md_caption(MEDIA / folder)
            tag_text = tag_text or md_tags
        tags = hashtags(tag_text)
        caption = "\n\n".join(x for x in (cap, tags) if x)
        if not files:
            problems.append(f"{where}: no images or videos in media/{folder}/")
            continue
        if not vert and len(files) > MAX_SLIDES:
            problems.append(f"{where}: {len(files)} images, the limit is {MAX_SLIDES}")
            continue
        if len(caption) > MAX_CAPTION:
            problems.append(f"{where}: caption + hashtags is {len(caption)} characters (max {MAX_CAPTION})")
            continue
        if caption.count("#") > 30:
            problems.append(f"{where}: more than 30 hashtags (Instagram limit)")
            continue
        p = {"key": folder, "id": quote(folder), "at": at, "caption": caption, "kind": "video" if vert else "images",
             "files": files, "slides": [quote(f.name) for f in files], "platforms": platforms(cell("platforms"))}
        p["fp"] = fingerprint(p)
        posts.append(p)
    return sorted(posts, key=lambda p: p["at"]), problems, seen


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, cwd=ROOT).stdout.strip()


def media_base():
    if os.environ.get("MEDIA_BASE_URL"):
        return os.environ["MEDIA_BASE_URL"].rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("Set MEDIA_BASE_URL (or run inside GitHub Actions) so Meta can fetch the images.")
    # Pin to the exact commit: raw.githubusercontent.com caches branch URLs for a few minutes
    try:
        ref = git("rev-parse", "HEAD")
    except Exception:
        ref = os.environ.get("GITHUB_SHA") or os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{ref}/media"


def env(name):
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(f"Missing {name}. Add it in GitHub: Settings → Secrets and variables → Actions.")
    return val


# ---------- Graph API ----------

def api(method, path, host=None, **params):
    params["access_token"] = env("META_TOKEN")
    body = urllib.parse.urlencode(params)
    url = f"{host or GRAPH}/{path}"
    if method in ("GET", "DELETE"):
        req = urllib.request.Request(f"{url}?{body}", method=method)
    else:
        req = urllib.request.Request(url, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raw = e.read().decode(errors="replace")
        try:
            err = json.loads(raw)["error"]
            msg = err.get("error_user_msg") or err.get("message")
        except Exception:
            msg = raw[:300]
        raise ApiError(f"{method} {path.split('?')[0]} → {msg}") from None
    except urllib.error.URLError as e:
        raise ApiError(f"{method} {path} → network error: {e.reason}") from None


def wait_ready(container_id, tries=40, every=3):
    for _ in range(tries):
        status = api("GET", container_id, fields="status_code,status").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            detail = api("GET", container_id, fields="status").get("status", "")
            raise ApiError(f"Instagram couldn't process media {container_id} ({status}{': ' + detail if detail else ''}). "
                           "Open the media URL in a browser to check it loads.")
        time.sleep(every)
    raise ApiError(f"Instagram media {container_id} still processing after {tries * every // 60} minutes")


def post_instagram(p, base):
    ig = env("IG_USER_ID")
    urls = [f"{base}/{p['id']}/{s}" for s in p["slides"]]
    if p.get("kind") == "video":   # 9:16 file -> Reel (also shown in the main feed)
        container = api("POST", f"{ig}/media", media_type="REELS", video_url=urls[0], caption=p["caption"],
                        share_to_feed="true", thumb_offset=str(REEL_COVER_MS))["id"]
        wait_ready(container, tries=60, every=10)   # videos take longer than images
        return api("POST", f"{ig}/media_publish", creation_id=container)["id"]
    if len(urls) == 1:
        container = api("POST", f"{ig}/media", image_url=urls[0], caption=p["caption"])["id"]
    else:
        children = [api("POST", f"{ig}/media", image_url=u, is_carousel_item="true")["id"] for u in urls]
        for c in children:
            wait_ready(c)
        container = api("POST", f"{ig}/media", media_type="CAROUSEL",
                        children=",".join(children), caption=p["caption"])["id"]
    wait_ready(container)
    return api("POST", f"{ig}/media_publish", creation_id=container)["id"]


def post_facebook(p, base, schedule_at=None):
    page = env("FB_PAGE_ID")
    if p.get("kind") == "video":   # 16:9 file -> Page video (Facebook's own scheduler holds it)
        params = {"file_url": f"{base}/{p['id']}/{p['slides'][1]}", "description": p["caption"]}
        if schedule_at:
            params.update(published="false", scheduled_publish_time=str(int(schedule_at.timestamp())))
        return api("POST", f"{page}/videos", host=GRAPH_VIDEO, **params)["id"]
    photo_ids = []
    for s in p["slides"]:
        extra = {"temporary": "true"} if schedule_at else {}
        photo_ids.append(api("POST", f"{page}/photos", url=f"{base}/{p['id']}/{s}",
                             published="false", **extra)["id"])
    params = {"message": p["caption"]}
    for i, pid in enumerate(photo_ids):
        params[f"attached_media[{i}]"] = json.dumps({"media_fbid": pid})
    if schedule_at:
        params.update(published="false", scheduled_publish_time=str(int(schedule_at.timestamp())))
    return api("POST", f"{page}/feed", **params)["id"]


def unschedule_facebook(post_id, kind="images"):
    """Delete a queued Facebook post or video. Returns False if it had already gone out."""
    field = "published" if kind == "video" else "is_published"
    if api("GET", post_id, fields=field).get(field):
        return False
    api("DELETE", post_id)
    return True


# ---------- commands ----------

def cmd_plan(posts, problems, state, now):
    print(f"{'When':<18} {'Folder':<34} {'Media':>5}  {'Facebook':<12} {'Instagram':<12}")
    for p in posts:
        st = state.get(p["key"], {})
        def cell(n):
            if n not in p["platforms"]:
                return "-"
            return st.get(n, {}).get("status") or ("due" if p["at"] <= now else "waiting")
        media = "video" if p.get("kind") == "video" else str(len(p["slides"]))
        print(f"{p['at'].strftime('%a %d %b %H:%M'):<18} {p['key'][:34]:<34} {media:>5}  "
              f"{cell('facebook'):<12} {cell('instagram'):<12}")
    for msg in problems:
        print("✗", msg)
    return 0


def cmd_check(posts, problems, state, now):
    problems = list(problems)
    if posts:
        nv = sum(1 for p in posts if p.get("kind") == "video")
        print(f"{len(posts)} posts ({nv} video, {len(posts) - nv} image), "
              f"{posts[0]['at']:%a %d %b %H:%M} → {posts[-1]['at']:%a %d %b %H:%M} (UTC{TZ_OFFSET})")
        upcoming = [p for p in posts if now - p["at"] <= MAX_LATE]
        if not upcoming:
            problems.append("Every post time is in the past: add rows with future dates to schedule.csv")
        pngs = sum(1 for p in posts for f in p["files"] if f.suffix.lower() == ".png")
        if pngs:
            print(f"{pngs} PNG image(s) will be converted to JPG on the next run")
    else:
        problems.append("No valid rows in schedule.csv")

    if os.environ.get("META_TOKEN") and posts:
        try:
            page = api("GET", env("FB_PAGE_ID"), fields="name,instagram_business_account{id,username}")
            print(f"Facebook Page: {page['name']}")
            ig = page.get("instagram_business_account")
            if not ig:
                problems.append("This Page has no linked Instagram professional account")
            elif ig["id"] != env("IG_USER_ID"):
                problems.append(f"IG_USER_ID doesn't match the Page's Instagram account (@{ig['username']}, {ig['id']})")
            else:
                print(f"Instagram: @{ig['username']}")
            vtest = next((p for p in posts if p.get("kind") == "video"), None)
            if vtest:
                url = f"{media_base()}/{vtest['id']}/{vtest['slides'][0]}"
                print(f"Test video: {url}")
                c = api("POST", f"{env('IG_USER_ID')}/media", media_type="REELS", video_url=url,
                        share_to_feed="false")["id"]
                wait_ready(c, tries=60, every=10)
                print("Instagram can fetch the videos ✓ (unpublished test Reel container, expires on its own)")
            test = next((p for p in posts if p.get("kind") != "video" and not p["slides"][0].lower().endswith(".png")), None)
            if test:
                url = f"{media_base()}/{test['id']}/{test['slides'][0]}"
                print(f"Test image: {url}")
                c = api("POST", f"{env('IG_USER_ID')}/media", image_url=url, is_carousel_item="true")["id"]
                wait_ready(c)
                print("Instagram can fetch the images ✓ (unpublished test container, expires on its own)")
                api("POST", f"{env('FB_PAGE_ID')}/photos", url=url, published="false", temporary="true")
                print("Facebook can fetch the images ✓ (unpublished test photo)")
        except ApiError as e:
            problems.append(str(e))
    elif not os.environ.get("META_TOKEN"):
        print("META_TOKEN not set: skipped the account checks")

    for msg in problems:
        print("✗", msg)
    print("All good ✓" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_convert():
    pngs = [f for f in MEDIA.rglob("*") if f.is_file() and f.suffix.lower() == ".png"]
    if not pngs:
        print("No PNGs to convert.")
        return 0
    from PIL import Image
    for f in pngs:
        out = f.with_suffix(".jpg")
        Image.open(f).convert("RGB").save(out, "JPEG", quality=92)
        f.unlink()
        print(f"{f.relative_to(ROOT)} → {out.name}")
    if os.environ.get("GITHUB_ACTIONS"):
        git("config", "user.name", "autopost-bot")
        git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        git("add", "-A", "media")
        git("commit", "-m", f"autopost: convert {len(pngs)} PNG to JPG")
        git("pull", "--rebase")
        git("push")
    return 0


def reconcile(posts, listed, state, now, dry):
    """Handle rows that were edited or deleted after their Facebook post was queued.
    A row that's present but invalid (typo, missing images) is left alone, never cancelled."""
    by_key = {p["key"]: p for p in posts}
    for key, nets in state.items():
        p = by_key.get(key)
        if p is None and (listed is None or key in listed):
            continue
        fb = nets.get("facebook", {})
        if fb.get("status") == "scheduled" and fb.get("id"):
            if p is None:
                why = "row deleted"
            elif fb.get("fp") is None:
                fb["fp"] = p["fp"]          # queued by an older version: start tracking from here
                if not dry:
                    save_state(state)
                continue
            elif fb["fp"] != p["fp"]:
                why = "row changed"
            else:
                continue
            print(f"{'(dry) ' if dry else ''}update   facebook  {key}: {why}, removing the queued post")
            if dry:
                continue
            try:
                if unschedule_facebook(fb["id"], fb.get("kind", "images")):
                    nets["facebook"] = {"status": "cancelled", "id": fb["id"]} if p is None else {}
                    print("   ✓ removed" + ("" if p is None else ", will queue the new version"))
                else:
                    fb.update(status="posted", fp=fb.get("fp"))
                    print("   already published, left as it is")
            except ApiError as e:
                print(f"   ✗ couldn't remove it: {e}")
            save_state(state)
        # A missed or failed post whose row was edited gets another go
        if p is not None:
            for net in ("facebook", "instagram"):
                s = nets.get(net, {})
                if s.get("status") in ("missed", "failed") and s.get("fp") and s["fp"] != p["fp"]:
                    print(f"retry    {net:<9} {key}: row changed after it was {s['status']}")
                    if not dry:
                        nets[net] = {}
                        save_state(state)


def cmd_run(posts, problems, listed, state, now, dry):
    for msg in problems:
        print("⚠", msg, "(skipped)")
    reconcile(posts, listed, state, now, dry)
    base = media_base() if not dry else os.environ.get("MEDIA_BASE_URL", "<media-url>")
    failures = 0
    for p in posts:
        if any(f.suffix.lower() == ".png" for f in p["files"]):
            print(f"skip     {p['key']}: has PNGs, run 'convert' first")
            continue
        for net in p["platforms"]:
            s = state.setdefault(p["key"], {}).setdefault(net, {})
            if s.get("status") == "failed" and needs_access(s.get("error", "")):
                s.pop("status")                      # blocked by a permission, not by the post: try again
            if s.get("status") in ("posted", "scheduled", "missed", "failed", "cancelled"):
                continue
            due = p["at"] <= now
            if now - p["at"] > MAX_LATE:
                print(f"skip     {net:<9} {p['key']}: more than {MAX_LATE} late, marked missed")
                if not dry:
                    s.update(status="missed", fp=p["fp"])
                    save_state(state)
                continue
            if net == "facebook":
                if not due and not (FB_MIN_LEAD <= p["at"] - now <= FB_MAX_LEAD):
                    continue
                action = "publish" if due else "schedule"
            else:
                if not due:
                    continue
                action = "publish"
            when = "now" if action == "publish" else f"for {p['at']:%a %d %b %H:%M}"
            what = ("Reel 9:16" if net == "instagram" else "video 16:9") if p.get("kind") == "video" else f"{len(p['slides'])} images"
            print(f"{'(dry) ' if dry else ''}{action:<8} {net:<9} {p['key']} ({what}) {when}")
            if dry:
                continue
            try:
                if net == "instagram":
                    post_id = post_instagram(p, base)
                else:
                    post_id = post_facebook(p, base, None if due else p["at"])
                s.clear()
                s.update(status="posted" if action == "publish" else "scheduled", id=post_id, fp=p["fp"],
                         kind=p.get("kind", "images"), at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                print(f"   ✓ {post_id}")
            except ApiError as e:
                failures += 1
                s["error"] = str(e)
                s["fp"] = p["fp"]
                if needs_access(e):
                    print(f"   ✗ Meta permission problem, will retry every run until it's fixed: {e}")
                else:
                    s["attempts"] = s.get("attempts", 0) + 1
                    if s["attempts"] >= MAX_ATTEMPTS:
                        s["status"] = "failed"
                    print(f"   ✗ attempt {s['attempts']}/{MAX_ATTEMPTS}: {e}")
            save_state(state)
    return 1 if failures else 0


def main(argv):
    if not argv or argv[0] not in ("plan", "check", "run", "convert"):
        print(__doc__)
        return 2
    if argv[0] == "convert":
        return cmd_convert()
    posts, problems, listed = load_schedule()
    state = load_state()
    now = datetime.now(timezone.utc)
    if "--now" in argv:
        now = datetime.fromisoformat(argv[argv.index("--now") + 1])
    now = now.astimezone(TZ)
    if argv[0] == "plan":
        return cmd_plan(posts, problems, state, now)
    if argv[0] == "check":
        return cmd_check(posts, problems, state, now)
    return cmd_run(posts, problems, listed, state, now, dry="--dry-run" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
