# How to post: AIGenX Autopost

**One folder, one CSV.** Static posts and reels work the same way:
**the content sits in `media/`, one row in `schedule.csv` says when, and GitHub posts it** to Instagram + Facebook.

```
AIGenX-Autopost/                 ← on your Mac: ~/OptimityFX/Claude/AIGenX-Autopost
├── schedule.csv                 ← 1 row = 1 post (what, when, caption). Opens in Google Sheets.
├── media/                       ← one folder per post
│   ├── 2026-10-20_50_Camera_Moves/   reel: instagram.mp4 + facebook.mp4 + caption.md
│   ├── 2026-10-21_Raw_to_Graded/     static: slide-1.jpg … slide-N.jpg + caption.md
│   └── _posted/                      already published (kept for reference, never posted again)
├── post-now/                    ← drop images here to post IMMEDIATELY (skips the CSV)
└── publish.py, .github/         ← the robot. Don't edit.
```

## The plan (starts tonight)

**45 posts, 20 Oct → 11 Nov 2026: 16 static + 29 reels, mixed.**
Two slots a day, **1:00 PM and 8:00 PM IST**. The first post is **tonight, Tue 20 Oct, 8:00 PM** (Reel 01, *50 Camera Moves*).
A reel always comes first, and there are never two statics in a row. The *AIGenX Starter Kit* reel closes the series on 11 Nov at 8 PM.
Reel 13 (*Free OptimityFX LUT*) is in the CSV but switched **off** (`#`) until the real LUT is ready.

The full list is at the bottom of this page.

---

## Part A · Open and edit the schedule in Google Sheets

1. Open **sheets.new** (a blank Google Sheet).
2. **File → Import → Upload** → choose `schedule.csv` from `~/OptimityFX/Claude/AIGenX-Autopost`.
3. In the import box:
   - **Import location:** *Replace spreadsheet*
   - **Separator type:** *Comma*
   - **Untick "Convert text to numbers, dates and formulas"** (this keeps `2026-10-20` and `20:00` exactly as written)
   - Click **Import data**.
4. Edit what you like: change a `time`, rewrite a `caption`, or put `#` in front of a `folder` to skip that post.
   **Don't rename the header row** (`folder, date, time, type, caption, hashtags, platforms`) or the folder names.
5. **File → Download → Comma-separated values (.csv)**.
6. The download is called something like `schedule - Sheet1.csv`. **Rename it to `schedule.csv`** and use it to replace the one in the folder.

| Column | What it means | Example |
|---|---|---|
| `folder` | the folder in `media/` | `2026-10-20_50_Camera_Moves` |
| `date` | posting date | `2026-10-20` |
| `time` | posting time, **IST**, 24-hour | `20:00` (= 8 PM) |
| `type` | a label for you | `reel` or `static` |
| `caption` | the caption (line breaks are fine) | |
| `hashtags` | added under the caption | `#aivideo #aiprompts` |
| `platforms` | `both`, `instagram` or `facebook` | `both` |

If `caption` and `hashtags` are left empty, the post uses the `## Caption` and `## Hashtags` sections of that folder's `caption.md`.

---

## Part B · Upload to GitHub, using the website (step by step)

The GitHub website takes **up to 100 files and 25 MB per file in one upload**. So the files are already split into small batches for you in:

```
~/OptimityFX/Claude/AIGenX-Web-Upload/
├── Step-2-media-upload-1 … Step-2-media-upload-8   ← 6–7 post folders each, about 90 MB
├── Step-3-root-files                               ← schedule.csv, publish.py, 2 guides
└── Step-4-workflow                                 ← autopost.yml
```

Use **Chrome** on your Mac (you need to drag folders in). Start **by 7:00 PM tonight**: 8 uploads of about 90 MB each take roughly 20–40 minutes.
The repo: **github.com/techyvick/aigenx-autopost**

### Step 1 · Pause the robot while you upload (1 minute)
1. In the repo, open **Settings** (top tab) → left menu **Secrets and variables → Actions** → **Variables** tab.
2. If `AUTOPOST_PAUSED` is listed, click ✏️ and set it to `true`. If not, click **New repository variable**: **Name** `AUTOPOST_PAUSED`, **Value** `true` → **Add variable**.

Nothing posts while it's `true`, so a half-finished upload can't post anything by mistake.

### Step 2 · Upload the post folders (8 times)
1. In the repo, click the **`media`** folder. Check that the address bar ends in **`/tree/main/media`**.
2. Click **Add file → Upload files**.
3. In Finder, open **`Step-2-media-upload-1`**, select all the folders inside (**⌘ A**), and **drag them** onto the GitHub page.
   Drag the folders *inside* the batch, not the batch folder itself.
4. Wait until every file shows in the list and the progress bars are gone.
5. Under **Commit changes**, write `Media batch 1`. Keep **Commit directly to the main branch** selected → **Commit changes**.
6. Wait for the page to finish (it goes back to the `media` folder). Then repeat 1–5 with **upload-2**, **upload-3** … **upload-8**.

**Check:** the `media` folder now shows 46 new folders whose names start with a date (`2026-10-20_…` to `2026-11-12_…`), next to the old `d1-1-…` folders. Leave the old ones; they won't post again.

### Step 3 · Upload the schedule and the robot
1. Go to the repo's **main page** (click **aigenx-autopost** at the top).
2. **Add file → Upload files** → drag the 4 files from **`Step-3-root-files`**: `schedule.csv`, `publish.py`, `HOW-TO-POST.md`, `CRON-JOB-ORG-SETUP.md`.
   It replaces the old `publish.py`. That's what you want.
3. Commit message `New mixed schedule from 20 Oct 8 PM` → **Commit changes**.

### Step 4 · Replace the workflow file
1. On the main page, click **`.github`** → **`workflows`**. The address bar should end in **`/tree/main/.github/workflows`**.
2. **Add file → Upload files** → drag **`autopost.yml`** from **`Step-4-workflow`** → **Commit changes**.
   It replaces the old one. Leave `post-now.yml` as it is: it hasn't changed.

### Step 5 · Delete the old schedule file
1. On the main page, click **`schedule.json`** → the **⋯** button (top right of the file) → **Delete file** → **Commit changes**.
2. **Don't touch `state.json`.** It remembers what's already posted, so nothing posts twice.

### Step 6 · Test it (posts nothing)
1. Go back to **Settings → Secrets and variables → Actions → Variables**, click ✏️ on `AUTOPOST_PAUSED`, set it to **`false`** → **Update variable**.
2. Open **Actions** (top tab) → **Autopost** (left) → **Run workflow** → keep **dry run ticked** → green **Run workflow**.
3. Refresh after about a minute and open the run. The **check** step should end with **All good ✓**.
   The **plan** step lists all 45 posts; tonight's reel shows as *waiting*.
4. If you see a red **✗**, send me a screenshot.

### Step 7 · Make it post on time
- **Tonight, at 8:00 PM or just after:** Actions → Autopost → **Run workflow** → **untick dry run** → **Run workflow**.
  Reel 01 goes to Instagram and Facebook, and the rest are queued in Facebook's scheduler.
- **From tomorrow, automatically:** set up the free 15-minute trigger in `CRON-JOB-ORG-SETUP.md` (about 5 minutes). Without it, GitHub's own timer runs too, but it can be hours late, and Instagram skips a post that's more than 6 hours late.

---

## What happens on the first real run

- **Reel 01** posts to Instagram (Reel) and Facebook (16:9 video).
- **All other posts are queued in Facebook's own scheduler.** Facebook then posts them exactly on time, even if GitHub is late.
- **Old Facebook posts queued under the old folder names are removed** (21 of them), so nothing posts twice.
  The 5 that already went out (*Prompt Formula*, *Three Tools*, *Tutorials*, *AI Faces*, *Real or AI*) are left alone.
- **Instagram** posts each one when a run happens after its time. It's within 15 minutes if the cron-job.org trigger is on.

**Note:** 4 of the 5 old static posts (*Prompt Formula*, *Three Tools*, *Tutorials*, *AI Faces*) reached Facebook but were **missed on Instagram** earlier. On your Mac they're in `media/_posted/` (on GitHub they're the old `d1-1-…` folders). To post one on Instagram later, copy its folder into `media/` with a new name (e.g. `2026-11-13_Prompt_Formula`), then add a row with `platforms` = `instagram`.

---

## Change or cancel later
- **Change a time or caption:** edit the CSV (Part A), then on github.com use **Add file → Upload files** on the main page to replace `schedule.csv`. Or open `schedule.csv` on github.com → ✏️ → edit → **Commit changes**. A Facebook post that's already queued is re-queued automatically.
- **Cancel a post:** put `#` in front of its folder name.
- **Add a post:** make a new folder (slides `slide-1.jpg`…, or `instagram.mp4` + `facebook.mp4`, plus `caption.md`), drag it into `media/` on github.com (Add file → Upload files), then add its row to `schedule.csv`.
- **Pause everything:** GitHub → Settings → Secrets and variables → Actions → Variables → `AUTOPOST_PAUSED` = `true`.

## Rules the robot follows
- **Instagram:** posts at the time, give or take 15 minutes. If it can't post within **6 hours**, it skips that post rather than posting at a strange hour.
- **Facebook:** queued up to 28 days ahead in Facebook's scheduler, so it's always on time. Posts more than 28 days away are queued on a later run.
- **Limits:** up to 10 images a post, a caption of up to 2,200 characters, and 30 hashtags.
- Every folder is posted **once**. To post it again, copy it to a new folder name.
- **Secrets** (`META_TOKEN`, `FB_PAGE_ID`, `IG_USER_ID`) are already in the repo. Nothing new is needed.
- **Video note:** if the check says Instagram couldn't process a video, turn on **GitHub Pages** (Settings → Pages → main). Then add a variable `MEDIA_BASE_URL` = `https://techyvick.github.io/aigenx-autopost/media`.
- **Only use this one repo.** Don't upload the old `github-reels` as a second repo, or reels will post twice.

## Before each reel goes live: SuperProfile
Each reel asks people to comment a keyword. Make sure that keyword has an auto-DM in SuperProfile, especially the new ones: **CITY** (Reel 14, 30 Oct) and **FESTIVAL** (Reel 26, 25 Oct).
The keyword and DM text are in each folder's `caption.md`.

---

## Full schedule

| # | When (IST) | Type | Folder |
|---|---|---|---|
| 1 | Tue 20 Oct · 08:00 PM | 🎬 Reel | `2026-10-20_50_Camera_Moves` |
| 2 | Wed 21 Oct · 01:00 PM | 🎬 Reel | `2026-10-21_5_Sora_Replacements` |
| 3 | Wed 21 Oct · 08:00 PM | 🖼 Static | `2026-10-21_Raw_to_Graded` |
| 4 | Thu 22 Oct · 01:00 PM | 🎬 Reel | `2026-10-22_Character_Consistency_Kit` |
| 5 | Thu 22 Oct · 08:00 PM | 🎬 Reel | `2026-10-22_AI_Music_Video_Workflow` |
| 6 | Fri 23 Oct · 01:00 PM | 🖼 Static | `2026-10-23_8_Camera_Moves` |
| 7 | Fri 23 Oct · 08:00 PM | 🎬 Reel | `2026-10-23_Which_AI_Tools_Are_Free` |
| 8 | Sat 24 Oct · 01:00 PM | 🖼 Static | `2026-10-24_Your_Festival_in_AI` |
| 9 | Sat 24 Oct · 08:00 PM | 🎬 Reel | `2026-10-24_Seedance_25_Template` |
| 10 | Sun 25 Oct · 01:00 PM | 🎬 Reel | `2026-10-25_Festival_AI_Prompt_Pack` |
| 11 | Sun 25 Oct · 08:00 PM | 🖼 Static | `2026-10-25_Zero_Rupee_Cart` |
| 12 | Mon 26 Oct · 01:00 PM | 🎬 Reel | `2026-10-26_Same_Prompt_4_Tools` |
| 13 | Mon 26 Oct · 08:00 PM | 🎬 Reel | `2026-10-26_10_Product_Ad_Prompts` |
| 14 | Tue 27 Oct · 01:00 PM | 🖼 Static | `2026-10-27_5_Prompt_Mistakes` |
| 15 | Tue 27 Oct · 08:00 PM | 🎬 Reel | `2026-10-27_Client_Pitch_Templates` |
| 16 | Wed 28 Oct · 01:00 PM | 🎬 Reel | `2026-10-28_AI_Video_Pricing_Sheet` |
| 17 | Wed 28 Oct · 08:00 PM | 🖼 Static | `2026-10-28_Same_Shot_4_Grades` |
| 18 | Thu 29 Oct · 01:00 PM | 🎬 Reel | `2026-10-29_100_Reel_Hooks` |
| 19 | Thu 29 Oct · 08:00 PM | 🎬 Reel | `2026-10-29_Nano_Banana_Portraits` |
| 20 | Fri 30 Oct · 01:00 PM | 🖼 Static | `2026-10-30_Music_Video_Maths` |
| 21 | Fri 30 Oct · 08:00 PM | 🎬 Reel | `2026-10-30_Your_City_in_AI` |
| 22 | Sat 31 Oct · 01:00 PM | 🖼 Static | `2026-10-31_Same_Face_Every_Shot` |
| 23 | Sat 31 Oct · 08:00 PM | 🎬 Reel | `2026-10-31_60-Second_Script_Template` |
| 24 | Sun 01 Nov · 01:00 PM | 🎬 Reel | `2026-11-01_Shot_List_and_Storyboard` |
| 25 | Sun 01 Nov · 08:00 PM | 🖼 Static | `2026-11-01_Your_City_2080` |
| 26 | Mon 02 Nov · 01:00 PM | 🎬 Reel | `2026-11-02_AI_Video_Fix-It_List` |
| 27 | Mon 02 Nov · 08:00 PM | 🎬 Reel | `2026-11-02_AI_Lip-Sync_Guide` |
| 28 | Tue 03 Nov · 01:00 PM | 🖼 Static | `2026-11-03_How_to_Join` |
| 29 | Tue 03 Nov · 08:00 PM | 🎬 Reel | `2026-11-03_25_Faceless_AI_Niches` |
| 30 | Wed 04 Nov · 01:00 PM | 🎬 Reel | `2026-11-04_30-Day_Content_Calendar` |
| 31 | Wed 04 Nov · 08:00 PM | 🖼 Static | `2026-11-04_Your_First_AI_Video` |
| 32 | Thu 05 Nov · 01:00 PM | 🎬 Reel | `2026-11-05_Follower_to_Client_DMs` |
| 33 | Thu 05 Nov · 08:00 PM | 🎬 Reel | `2026-11-05_AI_Influencer_Sheet` |
| 34 | Fri 06 Nov · 01:00 PM | 🖼 Static | `2026-11-06_4_Types_of_Creators` |
| 35 | Fri 06 Nov · 08:00 PM | 🎬 Reel | `2026-11-06_Quality_Booster_List` |
| 36 | Sat 07 Nov · 01:00 PM | 🎬 Reel | `2026-11-07_Free_Music_and_SFX_Guide` |
| 37 | Sat 07 Nov · 08:00 PM | 🖼 Static | `2026-11-07_AI_Changes_Weekly` |
| 38 | Sun 08 Nov · 01:00 PM | 🎬 Reel | `2026-11-08_Portfolio_Checklist` |
| 39 | Sun 08 Nov · 08:00 PM | 🖼 Static | `2026-11-08_Prompt_of_the_Week` |
| 40 | Mon 09 Nov · 01:00 PM | 🎬 Reel | `2026-11-09_AI_Invite_Video_Prompts` |
| 41 | Mon 09 Nov · 08:00 PM | 🎬 Reel | `2026-11-09_ElevenLabs_Voice_Settings` |
| 42 | Tue 10 Nov · 01:00 PM | 🖼 Static | `2026-11-10_Teach_Next` |
| 43 | Tue 10 Nov · 08:00 PM | 🎬 Reel | `2026-11-10_1-Page_Prompt_Formula` |
| 44 | Wed 11 Nov · 01:00 PM | 🖼 Static | `2026-11-11_Meet_Your_Mentor` |
| 45 | Wed 11 Nov · 08:00 PM | 🎬 Reel | `2026-11-11_AIGenX_Starter_Kit` |
| 46 | Thu 12 Nov · 08:00 PM | 🎬 Reel | `#2026-11-12_Free_OptimityFX_LUT` · **off** (draft LUT) |
