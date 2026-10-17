# AIGenX Autopost: free setup guide

This folder posts all 21 Week 1 carousels to **Instagram and your Facebook Page** automatically, for ₹0.

- **Facebook:** the first run queues every post in Facebook's own scheduler. They show up in **Meta Business Suite → Planner**, and you can edit or delete them there.
- **Instagram:** the Instagram API can't schedule ahead, so a free GitHub timer checks every 15 minutes and publishes each carousel once its slot has passed. Expect each post to go live **0–30 minutes after** 9 AM, 1 PM or 8 PM, because GitHub's timer runs late at busy times.
- Your Mac **doesn't** need to be on.

Setup takes about 30 minutes, once.

> 🔒 **Never paste your access token into a chat, an email or a file.** The only place it goes is GitHub's secret storage (Part D).

---

## Part A: Check your accounts (2 min)

1. Instagram must be a **Professional account** (Business or Creator). In Instagram, go to **Settings → Account type and tools**.
2. Instagram must be **linked to your Facebook Page**. On the Page, go to **Settings → Linked accounts → Instagram** (or use **Accounts Center**).
3. You must be an **admin of the Page** (full control).

## Part B: Set up your Meta app (15 min)

You've already created the app in your business portfolio, so start at **B1**. If you haven't made one yet, do **B0** first.

> **Two Meta websites, two jobs:**
> - **business.facebook.com** is your business portfolio, where your Page, Instagram and people live.
> - **developers.facebook.com** is where apps are configured.
>
> Even an app you created from your business portfolio is set up on **developers.facebook.com**. Everything below happens there unless it says otherwise.

### B0. Create the app (skip if you already have one)

1. Open **https://developers.facebook.com/apps/creation/** and log in with the Facebook account that is **admin of your Page**.
   - If you see **Get started**, click it and finish developer registration (verify your email or phone, then pick a role such as "Developer"). It's free.
2. **App details** screen: type the **App name** `AIGenX Autopost` and your **App contact email**. Click **Next**.
3. **Use cases** screen: tick **Manage everything on your Page**. Then also tick **Manage messaging & content on Instagram**. If Meta greys it out because the two can't be combined, leave it and add it later in B3. Click **Next**.
4. **Business** screen: choose **your business portfolio** (the one that owns your Page). Click **Next**.
5. **Requirements** screen: just read it and click **Next**. You don't need App Review, because you're only posting to your own accounts.
6. **Overview** screen: click **Go to dashboard**.

### B1. Open your app

1. Go to **https://developers.facebook.com/apps**.
2. Click your app's name, for example `AIGenX Autopost`.
   - Don't see it? Check you're logged in as the same Facebook account that created it. Otherwise, ask the person who created it to add you: in the app, go to **App roles → Roles → Add People → Administrator**.
3. You're now on the app **Dashboard**, with a menu down the left side.

### B2. Check which use cases the app has

1. In the left menu, click **Use cases**.
2. Look at the list of use cases. You need these two:
   - ✅ **Manage everything on your Page**
   - ✅ **Manage messaging & content on Instagram**
3. If both are there, go to **B4**. If one or both are missing, do **B3**.

### B3. Add a missing use case

1. On the **Use cases** page, click **Add use cases** (top right).
2. Tick the missing one(s) and click **Save** or **Add**.
3. **If the option is greyed out** ("incompatible"), your app was created with a use case that can't be combined with these. The quickest fix is to create a fresh app with **B0** and pick the two use cases there. It takes 3 minutes, and you can ignore the old app.

### B4. Add the Facebook Page permissions

1. On the **Use cases** page, find **Manage everything on your Page** and click **Customize**.
2. You'll see a list of **Permissions** with an **Add** button next to each. Click **Add** for each of these (skip any that already say **Ready for testing** or **Added**):
   - `pages_show_list`
   - `pages_read_engagement`
   - `pages_manage_posts`
   - `business_management`
3. Click **Use cases** in the left menu to go back.

### B5. Add the Instagram permissions

1. Find **Manage messaging & content on Instagram** and click **Customize**.
2. It offers two setups. Choose **API setup with Facebook login**, not "Instagram login". This app posts using your Facebook Page connection.
3. Under **Permissions** (or "Add required permissions"), click **Add** for:
   - `instagram_basic`
   - `instagram_content_publish`
4. Go back to **Use cases**.

### B6. Check the app is in Development mode

1. At the top of the dashboard there's an **App Mode** toggle. It should show **Development**. Leave it that way for now.
2. Development mode works for accounts that have a role on the app, which includes you. Part F, step 3 explains when you might switch to **Live**.

✅ **Part B done.** You don't need App Review or business verification for this.

## Part C: Get your Page token and IDs (10 min)

You'll collect three values here. Keep them in a temporary note on your Mac for 10 minutes, and **never paste them into a chat.**

### C1. Open Graph API Explorer

1. Go to **https://developers.facebook.com/tools/explorer**.
2. On the right side there's a panel:
   - **Meta App**: pick your app, `AIGenX Autopost`.
   - **User or Page**: pick **Get User Access Token** (it may show as **User Token**).

### C2. Pick the permissions

1. In the same right panel, find **Permissions** and the **Add a Permission** box.
2. Type each of these and click it to add (each one appears as a chip):
   `pages_show_list` · `pages_read_engagement` · `pages_manage_posts` · `business_management` · `instagram_basic` · `instagram_content_publish`
   - If one doesn't show up in the search, it wasn't added in B4/B5. Go back and **Add** it there.

### C3. Generate the token

1. Click the blue **Generate Access Token** button.
2. A Facebook pop-up opens:
   - **"Continue as [your name]"**: click it.
   - **Choose the businesses / Pages**: tick **your Page**. If you see **"Opt in to all current and future Pages"**, either option is fine, as long as your Page is ticked.
   - **Choose Instagram accounts**: tick **your Instagram account**.
   - Review the permissions screen and leave everything **on**. Click **Save** or **Done**, then **OK**.
3. The **Access Token** box at the top of Explorer now contains a long string starting with `EAA…`. This is a short-lived token that lasts about 1 hour.

### C4. Make it long-lived (so the final Page token never expires)

1. Click the small **ⓘ** (info) icon at the left end of the Access Token box, then click **Open in Access Token Tool**.
   - Or copy the token, go to **https://developers.facebook.com/tools/debug/accesstoken**, paste it and click **Debug**.
2. Scroll to the bottom of the Access Token Debugger and click **Extend Access Token**. If asked, re-enter your Facebook password. That's Facebook's own login page, so typing it there is fine.
3. A new token appears under **"This new long-lived access token will expire on…"**. Click **Debug** next to it if you want to check it, then **copy this new token**.

### C5. Get your Page ID, Instagram ID and Page token

1. Go back to the **Graph API Explorer** tab.
2. **Paste the long-lived token** from C4 into the **Access Token** box at the top, replacing what was there.
3. Next to the **GET** dropdown there's a text box with something like `me?fields=id,name`. Replace it with exactly:
   ```
   me/accounts?fields=id,name,access_token,instagram_business_account{id,username}
   ```
4. Click **Submit**.
5. The result looks like this (your values will differ):
   ```
   {
     "data": [
       {
         "id": "1234567890",                        ← FB_PAGE_ID
         "name": "AIGenX",
         "access_token": "EAAG...very long...",     ← META_TOKEN
         "instagram_business_account": {
           "id": "17841400000000000",               ← IG_USER_ID
           "username": "aigenx"
         }
       }
     ]
   }
   ```
6. Copy these three values into your temporary note:
   | From the result | Name in GitHub |
   |---|---|
   | the Page's `"id"` (the first one, **not** the one inside `instagram_business_account`) | `FB_PAGE_ID` |
   | `"id"` inside `instagram_business_account` (usually starts with `1784…`) | `IG_USER_ID` |
   | the Page's `"access_token"` | `META_TOKEN` |

**If the result looks wrong:**
- **`"data": []` (empty):** the token didn't get access to your Page. Redo C3 and make sure your Page is ticked in the pop-up. Also check that you're an admin of the Page in your business portfolio: on **business.facebook.com**, go to **Settings → Accounts → Pages → your Page → People**.
- **No `instagram_business_account` in the result:** Instagram isn't linked to this Page (Part A, step 2), or you didn't tick your Instagram account in C3.
- **Several Pages listed:** use the block whose `"name"` is your AIGenX Page.

### C6. Confirm the Page token never expires

1. Copy the Page `access_token` from C5.
2. Paste it into **https://developers.facebook.com/tools/debug/accesstoken** and click **Debug**.
3. Check two lines:
   - **Type:** `Page`
   - **Expires:** `Never`
   - If **Expires** shows a date instead, you used the short token in C5. Redo C4 and C5.
4. Also check **Scopes** lists `pages_manage_posts` and `instagram_content_publish`.

✅ **Part C done.** You now have `FB_PAGE_ID`, `IG_USER_ID` and `META_TOKEN`. Delete the temporary note after Part D.

## Part D: Put it on GitHub (15 min)

The images have to be on a **public** link for Meta to fetch them, so this repo must be **public**. That means anyone with the link could see your slides and captions before they go live.

You can do all of this on the **GitHub website**, with nothing to install. The website has two quirks, and the steps below work around both:
- It uploads **at most 100 files at a time**, and you have 119 slides, so the slides go up in two batches.
- Mac Finder hides the `.github` folder (names starting with a dot are hidden), so you'll create that one file by pasting it in instead.

### D1. Create the repo

1. Sign up or log in at **https://github.com** (free).
2. Click **+** (top right) → **New repository**.
3. **Repository name:** `aigenx-autopost`. Choose **Public**. Leave "Add a README" **unticked**. Click **Create repository**.

### D2. Upload the main files

1. On the new empty repo page, click the **uploading an existing file** link.
2. In Finder, open the `autopost` folder and select these 3 files: `publish.py`, `schedule.json`, `SETUP-GUIDE.md`. Drag them onto the browser page.
3. Scroll down and click **Commit changes**.

### D3. Create the `media` folder and upload the slides (2 batches)

1. In the repo, click **Add file → Create new file**.
2. In the name box, type `media/README.md` (typing the `/` creates the folder). In the big box, type `Slides for autopost`. Click **Commit changes…**, then **Commit changes**.
3. Click into the **media** folder, then **Add file → Upload files**.
4. **Batch 1:** in Finder, open `autopost/media`, select the folders **`d1-…` through `d4-…`** (12 folders, 68 slides) and drag them onto the browser. Wait until every file shows in the list, then click **Commit changes**.
5. Inside **media** again, click **Add file → Upload files**.
6. **Batch 2:** drag the folders **`d5-…` through `d7-…`** (9 folders, 51 slides). Click **Commit changes**.
7. Check: the **media** folder should list 21 folders. Open one; it should contain `slide-1.jpg`, `slide-2.jpg` and so on, **not** a nested `media` folder.

### D4. Create the timer file (workflow)

1. Go back to the repo's main page and click **Add file → Create new file**.
2. In the name box, type exactly: `.github/workflows/autopost.yml`
3. On your Mac, open `autopost/.github/workflows/autopost.yml`. In Finder, press **⌘ Shift .** (Command, Shift, full stop) to show hidden folders, then open the file with **TextEdit**. Select all (**⌘ A**), copy (**⌘ C**), and paste it into the big box on GitHub.
4. Click **Commit changes…**, then **Commit changes**.

### D5. Add your token and IDs

1. In the repo, go to **Settings** (top tab) → **Secrets and variables** (left menu) → **Actions**.
2. **Secrets** tab → **New repository secret**: Name `META_TOKEN`, Secret = the Page access token. Click **Add secret**.
3. **Variables** tab → **New repository variable**: Name `FB_PAGE_ID`, Value = Page id. Click **Add variable**.
4. **Variables** tab → **New repository variable**: Name `IG_USER_ID`, Value = Instagram id. Click **Add variable**.

### D6. Let the timer save its progress

1. Go to **Settings → Actions → General**.
2. Scroll to **Workflow permissions**, choose **Read and write permissions**, and click **Save**.

> **Prefer an app?** GitHub Desktop (https://desktop.github.com) uploads the whole folder in one go, with no 100-file limit or hidden-folder issue. Use **File → Add Local Repository** on the `autopost` folder, then **Publish repository** (untick "Keep this code private"). Then do D5 and D6.

## Part E: Test, then go live (5 min)

1. Open the **Actions** tab. If asked, click **I understand my workflows, enable them**.
2. Click **Autopost → Run workflow**. Leave **Dry run** ticked and click **Run workflow**.
3. Open the run and read the log:
   - **Check setup** should end with `All good ✓`. It shows your Page name and `@instagram` handle, and confirms Instagram and Facebook can fetch your images. This only creates **unpublished** test media and never posts.
   - **Post what's due** lists what it *would* post.
4. **That's it, you're live.** Within 15 minutes the timer runs for real:
   - All upcoming Facebook posts appear in **Business Suite → Planner** as scheduled.
   - Each Instagram carousel posts shortly after its slot.
   - GitHub emails you if a post fails.

Week 1 runs **Mon 19 Oct → Sun 25 Oct 2026**. To change the dates, edit `start_date` in `schedule.json` before you upload it, or later on github.com (pencil icon → **Commit changes**).

---

## Part F: Before the first post goes out

1. ⚠️ **Day 1 "3 tools" carousel:** swap the stand-in `tools-1/2/3` images for your real outputs, re-render (`./render-week.sh d1-2`), run `python3 prepare.py`. Then on github.com open `media/d1-2-three-tools`, click **Add file → Upload files**, drag in the new `slide-*.jpg` files (same names replace the old ones) and click **Commit changes**.
2. **ManyChat:** set up each keyword's automation and DM giveaway before its post goes live. ManyChat works separately from this script.
3. **Check the first post is public:** open it from a logged-out browser or a friend's phone. If the Facebook post isn't visible to others, switch the app to **Live**: in the app dashboard, go to **App settings → Basic**, add a **Privacy Policy URL** (any public page you own, such as a public Notion page) and pick a category, then flip the **App Mode** toggle to **Live**.

## Everyday use

| I want to… | Do this |
|---|---|
| See what's posted and what's waiting | Open any run in the **Actions** tab and look at the **Show status** step, or run `python3 publish.py plan` on your Mac |
| Pause everything | Settings → Variables → add `AUTOPOST_PAUSED` = `true` (delete it to resume). Facebook posts that are already queued still go out, so pause those in Business Suite. |
| Change a Facebook caption | Edit it in **Business Suite → Planner** (it's already queued there) |
| Change an Instagram caption | On github.com, open `schedule.json`, click the ✏️ pencil, edit the caption and click **Commit changes**, before that post's slot |
| Retry a failed post | It retries 3 times on its own. After that, delete that carousel's `"instagram"` (or `"facebook"`) entry in `state.json` on github.com (pencil icon → **Commit changes**). |
| Post a new week | Render the new week, put the new ids, captions and `start_date` in `schedule.json`, run `python3 prepare.py`. Then on github.com, edit `schedule.json` (pencil icon) and upload the new `media` folders the same way as D3 |

**Safety rules built in:**
- It never posts the same carousel twice. Progress is saved in `state.json`.
- If a slot is more than 3 hours overdue (for example, you set this up late), that post is skipped and marked `missed` instead of being dumped out late. You can change this with `max_late_hours`.

## Troubleshooting

| Error in the log | Fix |
|---|---|
| `Missing META_TOKEN` / `FB_PAGE_ID` / `IG_USER_ID` | Part D, step 5. Names must match exactly. |
| `Error validating access token` / `session has expired` | Redo Part C, steps 4–7, then update the `META_TOKEN` secret |
| `(#200) ... permission` | A permission from Part C, step 3 is missing. Generate the token again with all of them. |
| `couldn't process media` / `Only photo or video can be accepted` | Instagram couldn't load the image. Open the test image URL from the log in a browser. If it doesn't load, check the repo is public and the `media/` folder was uploaded (D3). |
| `Permission denied` when saving state | Part D, step 6 (Read and write permissions) |
| Posts didn't run on time | GitHub's timer can run late at busy times. Click **Run workflow** with Dry run **unticked** to post what's due right away. |
