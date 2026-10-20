# Fix: posts not publishing (reliable 15-minute trigger)

**What went wrong:** GitHub ran the `*/15` schedule only 12 times in 2 days, with gaps of 2–7 hours. Any Instagram post more than 3 hours late is skipped, so d1-1 and d1-2 were marked **missed**. Facebook posts were already queued in Facebook's own scheduler, so they weren't affected.

**The fix:** an outside clock (cron-job.org, free) pings GitHub every 15 minutes. GitHub's own schedule stays on as a backup, and the late window goes from 3 to 6 hours.

---

## 1 · Create a GitHub token (for cron-job.org)

1. Go to **github.com/settings/personal-access-tokens/new** (fine-grained token).
2. **Token name:** `cron-job tick` · **Expiration:** Custom → **31 Dec 2026**.
3. **Resource owner:** techyvick · **Repository access:** *Only select repositories* → **aigenx-autopost** .
4. **Repository permissions → Contents → Read and write.** That's the only permission it needs (Metadata: read is added automatically).
5. **Generate token** and copy it. You won't see it again.

This token can only change files and trigger workflows in the repos you picked. Keep it private, and delete it after the campaign.

## 2 · cron-job.org (free, about 3 minutes)

1. Sign up at **cron-job.org** → **Cronjobs → Create cronjob**.
2. **Common tab**
   - **Title:** `AIGenX autopost tick`
   - **URL:** `https://api.github.com/repos/techyvick/aigenx-autopost/dispatches`
   - **Execution schedule:** *Every 15 minutes*
   - **Notifications:** tick *"execution of the cronjob fails"*
3. **Advanced tab**
   - **Request method:** `POST`
   - **Headers** (add 4):
     | Key | Value |
     |---|---|
     | `Accept` | `application/vnd.github+json` |
     | `Authorization` | `Bearer YOUR_TOKEN_FROM_PART_B` |
     | `X-GitHub-Api-Version` | `2022-11-28` |
     | `Content-Type` | `application/json` |
   - **Request body:** `{"event_type":"tick"}`
4. **Save**, then click **Test run**. You should see **HTTP 204** (204 = success, no content).
5. On GitHub → **Actions**: within about a minute a new **Autopost** run appears, marked *repository_dispatch*. It's a **real** run (not a dry run) and posts whatever is due.

**If the test run shows…**
- **401 / 403:** the token is wrong or lacks *Contents: Read and write* on this repo.
- **404:** the repo name in the URL is wrong, or the token doesn't include this repo.
- **422:** the request body isn't exactly `{"event_type":"tick"}`.

Don't use the **"Run workflow"** button as the trigger: it defaults to *dry run* and only previews.

## How it behaves now
- A post goes out within **about 15 minutes** of its scheduled time.
- If something still runs late, posts up to **6 hours** late are published; anything later is marked *missed*, so a morning post never lands at midnight.
- Two runs never overlap, and each one reads the latest `state.json`, so nothing posts twice.
- **Pause everything:** on GitHub → *Settings → Secrets and variables → Actions → Variables* → `AUTOPOST_PAUSED` = `true` (or pause the cronjob).

## Bring back the 2 missed Instagram posts (optional)
The fix doesn't retry posts already marked *missed*. To post d1-1 and d1-2 on Instagram:
- **Quickest:** upload their slides and caption into `post-now/`. Your *Post now* workflow publishes immediately.
- **Or schedule them:** in `schedule.json`, move them to a free future slot (e.g. a new `"day"`), and in `state.json` delete their `"instagram": {"status": "missed"}` lines. Do both, or they'll be marked missed again. Leave their Facebook entries alone: those already went out.
