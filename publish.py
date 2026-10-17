#!/usr/bin/env python3
"""AIGenX autopost: posts the carousels in schedule.json to Instagram and a Facebook Page.

  python3 publish.py plan                  list every post, its time and its status
  python3 publish.py check                 validate schedule + media; with META_TOKEN set, also
                                           test the token, Page, Instagram account and image hosting
                                           (creates unpublished test media only, never posts)
  python3 publish.py run [--dry-run] [--now 2026-10-19T09:05+05:30]
                                           queue Facebook posts with Facebook's own scheduler and
                                           publish Instagram posts that are due

Environment: META_TOKEN (Page access token), FB_PAGE_ID, IG_USER_ID,
             MEDIA_BASE_URL (optional; default is this repo's raw.githubusercontent.com URL),
             GRAPH_VERSION (optional, default v23.0).
Standard library only, so GitHub Actions needs no installs.
"""
import json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCHEDULE = ROOT / "schedule.json"
STATE = ROOT / "state.json"
MEDIA = ROOT / "media"
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
FB_MIN_LEAD = timedelta(minutes=15)  # Facebook rejects scheduled posts less than 10 min ahead
FB_MAX_LEAD = timedelta(days=28)     # and more than ~30 days ahead
MAX_ATTEMPTS = 3
MAX_CAPTION = 2200
MAX_SLIDES = 10


class ApiError(Exception):
    pass


# ---------- schedule + state ----------

def tz_from(offset):
    sign = -1 if offset.startswith("-") else 1
    h, m = offset.lstrip("+-").split(":")
    return timezone(sign * timedelta(hours=int(h), minutes=int(m)))


def load_schedule():
    sched = json.loads(SCHEDULE.read_text())
    tz = tz_from(sched["utc_offset"])
    start = datetime.strptime(sched["start_date"], "%Y-%m-%d")
    posts = []
    for p in sched["posts"]:
        hh, mm = sched["slots"][p["slot"]].split(":")
        at = (start + timedelta(days=p["day"] - 1)).replace(hour=int(hh), minute=int(mm), tzinfo=tz)
        slides = sorted((MEDIA / p["id"]).glob("slide-*.jpg"), key=lambda f: int(f.stem.split("-")[1]))
        posts.append({**p, "at": at, "slides": [f.name for f in slides]})
    sched["posts"] = sorted(posts, key=lambda p: p["at"])
    sched["tz"] = tz
    return sched


def load_state():
    return json.loads(STATE.read_text()) if STATE.exists() else {}


def save_state(state):
    STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def media_base():
    if os.environ.get("MEDIA_BASE_URL"):
        return os.environ["MEDIA_BASE_URL"].rstrip("/")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        raise SystemExit("Set MEDIA_BASE_URL (or run inside GitHub Actions) so Meta can fetch the images.")
    branch = os.environ.get("GITHUB_REF_NAME", "main")
    return f"https://raw.githubusercontent.com/{repo}/{branch}/media"


def env(name):
    val = os.environ.get(name, "").strip()
    if not val:
        raise SystemExit(f"Missing {name}. Add it in GitHub: Settings → Secrets and variables → Actions.")
    return val


# ---------- Graph API ----------

def api(method, path, **params):
    params["access_token"] = env("META_TOKEN")
    body = urllib.parse.urlencode(params)
    url = f"{GRAPH}/{path}"
    req = (urllib.request.Request(f"{url}?{body}") if method == "GET"
           else urllib.request.Request(url, data=body.encode(), method="POST"))
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


def wait_ready(container_id):
    for _ in range(40):
        status = api("GET", container_id, fields="status_code").get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise ApiError(f"Instagram couldn't process media {container_id} ({status}). "
                           "Open the image URL in a browser to check it loads.")
        time.sleep(3)
    raise ApiError(f"Instagram media {container_id} still processing after 2 minutes")


def post_instagram(p, base):
    ig = env("IG_USER_ID")
    urls = [f"{base}/{p['id']}/{s}" for s in p["slides"]]
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


# ---------- commands ----------

def cmd_plan(sched, state, now):
    print(f"{'When':<18} {'Carousel':<28} {'Slides':>6}  {'Facebook':<12} {'Instagram':<12}")
    for p in sched["posts"]:
        st = state.get(p["id"], {})
        cell = lambda n: (st.get(n, {}).get("status") or ("due" if p["at"] <= now else "waiting"))
        print(f"{p['at'].strftime('%a %d %b %H:%M'):<18} {p['id']:<28} {len(p['slides']):>6}  "
              f"{cell('facebook'):<12} {cell('instagram'):<12}")
    return 0


def cmd_check(sched, state, now):
    problems = []
    ids = [p["id"] for p in sched["posts"]]
    if len(ids) != len(set(ids)):
        problems.append("Duplicate carousel ids in schedule.json")
    for p in sched["posts"]:
        n = len(p["slides"])
        if n == 0:
            problems.append(f"{p['id']}: no JPEGs in media/{p['id']}/ (run prepare.py)")
        elif n > MAX_SLIDES:
            problems.append(f"{p['id']}: {n} slides, the API allows {MAX_SLIDES}")
        if len(p["caption"]) > MAX_CAPTION:
            problems.append(f"{p['id']}: caption is {len(p['caption'])} chars (max {MAX_CAPTION})")
        if p["caption"].count("#") > 30:
            problems.append(f"{p['id']}: more than 30 hashtags")
    first, last = sched["posts"][0]["at"], sched["posts"][-1]["at"]
    print(f"{len(ids)} carousels, {sum(len(p['slides']) for p in sched['posts'])} slides, "
          f"{first:%a %d %b %H:%M} → {last:%a %d %b %H:%M} (UTC{sched['utc_offset']})")
    if last < now:
        problems.append("Every post time is in the past: update start_date in schedule.json")

    if os.environ.get("META_TOKEN"):
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
            test = sched["posts"][0]
            url = f"{media_base()}/{test['id']}/{test['slides'][0]}"
            print(f"Test image: {url}")
            c = api("POST", f"{env('IG_USER_ID')}/media", image_url=url, is_carousel_item="true")["id"]
            wait_ready(c)
            print("Instagram can fetch the images ✓ (unpublished test container, expires on its own)")
            api("POST", f"{env('FB_PAGE_ID')}/photos", url=url, published="false", temporary="true")
            print("Facebook can fetch the images ✓ (unpublished test photo)")
        except ApiError as e:
            problems.append(str(e))
    else:
        print("META_TOKEN not set: skipped the account checks")

    for msg in problems:
        print("✗", msg)
    print("All good ✓" if not problems else f"{len(problems)} problem(s)")
    return 1 if problems else 0


def cmd_run(sched, state, now, dry):
    late = timedelta(hours=sched.get("max_late_hours", 3))
    base = media_base() if not dry else os.environ.get("MEDIA_BASE_URL", "<media-url>")
    failures = 0
    for p in sched["posts"]:
        for net in sched["platforms"]:
            s = state.setdefault(p["id"], {}).setdefault(net, {})
            if s.get("status") in ("posted", "scheduled", "missed", "failed"):
                continue
            due = p["at"] <= now
            if now - p["at"] > late:
                print(f"skip  {net:<9} {p['id']}: more than {late} late, marked missed")
                if not dry:
                    s.update(status="missed")
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
            print(f"{'(dry) ' if dry else ''}{action:<8} {net:<9} {p['id']} ({len(p['slides'])} slides) {when}")
            if dry:
                continue
            try:
                if net == "instagram":
                    post_id = post_instagram(p, base)
                else:
                    post_id = post_facebook(p, base, None if due else p["at"])
                s.clear()
                s.update(status="posted" if action == "publish" else "scheduled", id=post_id,
                         at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
                print(f"   ✓ {post_id}")
            except ApiError as e:
                failures += 1
                s["attempts"] = s.get("attempts", 0) + 1
                s["error"] = str(e)
                if s["attempts"] >= MAX_ATTEMPTS:
                    s["status"] = "failed"
                print(f"   ✗ attempt {s['attempts']}/{MAX_ATTEMPTS}: {e}")
            save_state(state)
    return 1 if failures else 0


def main(argv):
    if not argv or argv[0] not in ("plan", "check", "run"):
        print(__doc__)
        return 2
    sched, state = load_schedule(), load_state()
    now = datetime.now(timezone.utc)
    if "--now" in argv:
        now = datetime.fromisoformat(argv[argv.index("--now") + 1])
    now = now.astimezone(sched["tz"])
    if argv[0] == "plan":
        return cmd_plan(sched, state, now)
    if argv[0] == "check":
        return cmd_check(sched, state, now)
    return cmd_run(sched, state, now, dry="--dry-run" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
