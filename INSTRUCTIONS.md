# DICE — Full Project Instructions

General guide that collects **everything implemented so far** (feed data, images, videos, comments) and
the **complete pre-deployment + deployment procedure** for the full DICE app (Instagram focus).

- Comment authoring detail → `COMMENTS_INSTRUCTIONS.md`
- Parked/optional improvements → `FUTURE_UPDATES.md`
- oTree project root (where `settings.py` lives) = **`DICE/DICE/`** — run every `otree` command from there.

---

## 1. Feed data (CSV) — the single source of truth

The whole feed (posts, media, comments) comes from one CSV, set in
[settings.py](DICE/DICE/settings.py) → `data_path`. Delimiter is `;`.

### Where the CSV can live (`data_path` formats)

| Format | Example | When to use | Caveat |
|---|---|---|---|
| **Local path** (relative to `DICE/DICE/`) | `DICE/static/data/sample_feed_comments.csv` | Feed is final and shipped inside the app | The file **must be bundled in the `.otreezip`**. If it isn't, `read_feed()` raises `FileNotFoundError` and the session **crashes**. |
| **GitHub raw URL** | `https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/<PATH>/file.csv` | You want to change the feed **without redeploying** | Repo must be **public and pushed**; a network problem at session creation fails the session. |
| **Google Sheets export URL** | `https://docs.google.com/spreadsheets/d/<id>/export?format=csv` | Non-developers edit the feed in Sheets | Sheet must be shared/public. |

> **Current state & the exact URL to use:** `settings.py` line 73 currently uses the **local** comments CSV;
> the commented raw URL on line 72 still points to the *old* `sample_feed.csv` (no comments). If you deploy
> with a raw URL, use the **comments** CSV (already pushed to GitHub) — copy-paste into `data_path`:
>
> ```
> https://raw.githubusercontent.com/Alebrex99/DICE/main/DICE/DICE/static/data/sample_feed_comments.csv
> ```
>
> **Convert any GitHub file page into a raw URL** — remove `blob/`:
> ```
> https://github.com/<USER>/<REPO>/blob/<BRANCH>/<PATH>/file.csv          ← GitHub page
> https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/<PATH>/file.csv  ← raw (use in data_path)
> ```

### Automatic text highlighting (applied to post text **and** comment text)

`preprocessing()` rewrites text before rendering — you just type plain text in the CSV:

| You write | Rendered as | Note |
|---|---|---|
| `#Yosemite` | blue hashtag | `\B#word` |
| `@9GAG` | blue mention | `\B@word` |
| `$AAPL` | blue cashtag | `\B$word` |
| `http(s)://` or `ftp://` link | blue link `<a>` | not clickable (no `href`) |
| `VERO` / `1` / `true` / `yes` / `x` | boolean **TRUE** | for the **4 comment** bool columns; anything else (incl. `FALSO`, `0`, empty) = FALSE. **Post flags `sponsored` / `commented_post` need numeric `1` / `0`** |

> After **any** CSV or `settings.py` change in local dev: `otree resetdb`, create a new session, and
> **hard-refresh** the browser (`Ctrl+Shift+R`) — the browser caches CSS/JS aggressively.

### Complete CSV column reference (every column)

One row per CSV column, in the exact order they appear. **Two kinds of booleans:** the **4 comment flags**
(`verified_user_comment_i`, `comment_liked_author_i`, `pinned_comment_i`, `member_comment_i`) go through
`to_bool` → accept `VERO` / `1` / `true` / `yes` / `x` (anything else = false). The **2 post flags**
(`sponsored`, `commented_post`) are **not** converted → they need a plain **numeric `1` / `0`** — `VERO`
does **not** work for these. The **comment block** (9 columns) repeats identically for each slot `i` = `0`…`5`.

| # | CSV column | What to write (format / example) | Type | What it shows / does | Position | Fallback if empty |
|---|---|---|---|---|---|---|
| 1 | `doc_id` | unique integer, e.g. `0` | int (required) | internal post ID; keys JS tracking, ordering & references | not shown (used in element ids) | **required, must be unique** |
| 2 | `datetime` | `01.03.22 06:00` (`dd.mm.yy HH:MM`, or any pandas-parseable date) | string date | post date, shown as `1. Mar` (CSS-uppercased) | post date line | today's date if unparseable |
| 3 | `text` | free text; `#hashtag` `@mention` `$cashtag` + `http/https/ftp` links auto-highlighted blue | string | post caption / body | caption under the media | empty caption |
| 4 | `media` | ONE **http(s)** image or video URL (local paths don't work) | URL | the post media — video if URL ends `.mp4/.webm/.ogg/.ogv/.mov/.m4v`, else image | main post media | ⚠️ **whole post is skipped in Instagram** — a post requires media (`pic_available` = the URL contains `http`) |
| 5 | `alt_text` | short description | string | image accessibility text (`<img alt>`) | not shown (screen readers) | empty |
| 6 | `likes` | integer, e.g. `15` | int | like counter | ♥ row under post | `0` |
| 7 | `reposts` | integer | int | share / repost counter | share icon under post | `0` |
| 8 | `replies` | integer | int | comment counter on the 💬 button — **set manually to match how many comments you added** | comment icon under post | `0` |
| 9 | `username` | e.g. `NatureFanatic` | string (required) | poster display name; also used to derive a comment's "· Author" | post header + caption prefix | **required** |
| 10 | `handle` | e.g. `NatureFanatic88` | string | poster @handle | sponsored CTA (Instagram); under name on other platforms | empty |
| 11 | `user_description` | bio text | string | bio inside the profile tooltip | hover tooltip on the avatar | blank (quotes stripped) |
| 12 | `user_image` | avatar URL | URL | poster avatar photo | round avatar in post header | colored initials icon (first 2 letters of `username`) |
| 13 | `user_followers` | integer, e.g. `4523` | int | follower count, formatted `4.523` | profile tooltip ("X Followers") | — |
| 14 | `commented_post` | numeric `1` on exactly one row (**not** `VERO`) | bool (numeric, `== 1`) | **Twitter-Replies feature**: pins that row to position 1 and switches the feed to a `_Replies` layout. ⚠️ On **Instagram** there is **no `T_Feed_Insta_Replies.html`** → it **errors**; leave `0`/empty for Instagram | feed layout + order | `0` (not commented) |
| 15 | `sponsored` | numeric `1` / `0` (**not** `VERO`) | bool (numeric truthiness) | renders the post as a **promoted / ad** post (with a "Learn more" CTA) | whole-post styling | **write `0` explicitly** — an empty cell becomes `NaN` and may be misread as sponsored |
| 16 | `target` | URL | URL | click-through link of a sponsored post's CTA & media | "Learn more" button + media link | — (used only if `sponsored`) |
| 17 | `condition` | e.g. `A` / `B` | string | between-subjects A/B label — filters which posts a participant sees (column name set by `condition_col`) | not shown (assignment) | post shown to everyone |
| 18 | `sequence` | integer, e.g. `1` | int | pins the post to a fixed feed position; the rest are shuffled around it | feed order | random position |
| | **— COMMENT BLOCK — repeats for each slot `i` = `0`…`5` (in the Comments modal) —** | | | | | |
| 19 | `comment_i` | free text; **same highlighting as post `text`** — `#hashtag` `@mention` `$cashtag` + links | string | comment text | comment body | empty text `""` |
| 20 | `comment_user_i` | e.g. `giulia` | string | commenter username | top of comment, next to avatar | `"unknown"` |
| 21 | `comment_image_i` | avatar URL | URL | commenter avatar photo | left edge of the comment | Bootstrap person icon |
| 22 | `verified_user_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | blue verified ✓ | right of the username | no ✓ |
| 23 | `comment_time_i` | `2w`, `now`, `3m`, `1y` | string | timestamp (shown as-is, no parsing) | username line, right of ✓ | no timestamp |
| 24 | `comment_likes_count_i` | integer, e.g. `128` | int | number shown next to the like heart (set manually per comment) | under the heart, right of the comment | `0` |
| 25 | `comment_liked_author_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | "· Liked by Author" **+ a static red heart** next to the label (does **not** colour the clickable like heart) | on the username line, after the timestamp | no label, no red heart |
| 26 | `pinned_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | "📌 Pinned by Author" + comment hoisted to the top of the list | own line above username; list order | not pinned |
| 27 | `member_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | violet background + "Comment by Member" | whole-comment tint + label above username | normal comment |
| 28 | `subcomments_comment_i` | `comment_5,comment_6` or just `5,6` (**forward refs**; separator `,` or `&`). ⚠️ **Only the digits are read** — any text wrapped around a number (e.g. `xyz_5`, `ninvuinviunv_5`) is still parsed as `comment_5`; a value with no digit is silently ignored | list | the replies nested under this comment → "View replies (N)" | expandable block indented under the comment | no replies |
| | **— DERIVED (no CSV column — computed automatically) —** | | | | | |
| D1 | *(· Author)* | — | derived | "· Author" label | username line, right of "Liked by Author" | shown when `comment_user_i` == post `username` |
| D2 | *(like-heart click)* | — | derived | clicking the like heart toggles it **red↔white** and changes the count **±1** (frontend only, not saved) | the like heart | starts white; count from `comment_likes_count_i` |

> **Do NOT add these auto-computed columns** — `preprocessing()` creates them and would overwrite yours:
> `pic_available`, `is_video`, `video_available`, `image_available`, `profile_pic_available`, `icon`,
> `color_class`, `date`, `formatted_datetime`, `comments`.

---

## 2. Media — images & videos (the `media` column)

Put **one URL** in `media`. The backend auto-classifies it (do **not** add these columns by hand):
- `video_available` — URL ends in `.mp4 .webm .ogg .ogv .mov .m4v`
- `image_available` — any other `http…` URL

### Video sources

| Source | Example | Notes |
|---|---|---|
| **GitHub raw** (recommended) | `https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/<PATH>/clip.mp4` | Repo public & pushed; ≤ ~100 MB/file. Autoplay works (videos are muted). |
| GitHub Releases | `https://github.com/<USER>/<REPO>/releases/download/<TAG>/clip.mp4` | For files > 100 MB (see FUTURE_UPDATES D). |
| CDN / object storage | `https://<bucket>/…/clip.mp4` | Best for a real study. |

**Behaviour** — Instagram feed ([insta_video.js](DICE/DICE/DICE/static/js/insta_video.js)): `IntersectionObserver`
plays a video at ≥50% visibility, pauses otherwise; pauses on tab-hide (no auto-resume) and on CTA click.
**Stories** ([stories.js](DICE/DICE/DICE/static/js/stories.js)): video slides last the video's own length
(`slideDurationMs`), images last `story_duration`; global mute button; pause on tab-hide/CTA.

> ⚠️ **Local `.mp4` files are NOT read by the app** — only the GitHub URLs in `media` are. The local
> `static/videos/` files exist only to be *served from GitHub*. They must stay **committed & pushed**, but
> should be **removed from the ZIP** (see §5) to keep it slim.

---

## 3. Comments (summary)

Comments render inside the **Comments modal** (💬 button): post text → comments → "Add a comment…" input.
Each post row carries comments in fixed slots (`comment_0`, `comment_1`, …), auto-detected from the header.
Full authoring detail is in **`COMMENTS_INSTRUCTIONS.md`**; summary below.

> ⚠️ **The comment counter is NOT the number of comments you added.** The number on a post's 💬 button is
> read from the post's **`replies`** column (an integer) and is **completely independent** of how many
> `comment_i` slots you fill — adding comments does **not** update it. You must set `replies` **manually**
> to the number you want shown (it may equal the comments you added, or be higher, like Instagram's
> "View all 128 comments"). Leaving `replies = 0` while adding comments shows **0** on the button even
> though the comments still appear in the modal.

### The 9 columns per slot `i` (exact CSV order) → effect → what is shown

| # | Column | Effect | Fallback if empty |
|---|---|---|---|
| 1 | `comment_i` | comment text (auto-highlighted) | empty text |
| 2 | `comment_user_i` | username | `"unknown"` |
| 3 | `comment_image_i` | avatar photo (URL) | person icon |
| 4 | `verified_user_comment_i` | blue ✓ after username | no ✓ |
| 5 | `comment_time_i` | timestamp text (`2w`, `now`…) | no timestamp |
| 6 | `comment_likes_count_i` | number shown next to the like heart (manual) | `0` |
| 7 | `comment_liked_author_i` | "· Liked by Author" + static red heart by the label (not the like button) | no label |
| 8 | `pinned_comment_i` | "📌 Pinned by Author" + hoisted to top | not pinned |
| 9 | `member_comment_i` | violet background + "Comment by Member" | normal |
| 10 | `subcomments_comment_i` | replies nested under this comment (`comment_5,comment_6`) | no replies |

Derived (no column): **"· Author"** when `comment_user_i` == post `username`. The **like count** comes from
`comment_likes_count_i` (manual; default 0); clicking the like heart toggles it **red↔white** and the count
**±1** (frontend only, not saved). The red heart beside "· Liked by Author" is a **separate static decoration**.

### Layout of one comment

```
[📌 Pinned by Author]  [· Comment by Member]              ← own line, only if set
[avatar]  username ✓  2w  · Liked by Author ❤  · Author        ♡ 128
          comment text …
          View replies (N)                                   ← only if it has replies
```
Meta items (✓ · time · Liked by Author ❤ · Author) sit on the username line and collapse left if missing.
The like heart on the right starts white (♡) and turns red (❤) only when the participant clicks it.
Pinned comments jump to the top of the list.

### Threading rule (1 level) + good practice
`subcomments_comment_i` lists the replies. **One rule:** read in ascending order, a comment already
claimed as a reply has its own list ignored → gives the 1-level cap *and* cycle safety.
✅ **Good practice: put replies at the END of the row with the HIGHEST indices** (`comment_0 → comment_5,comment_6`)
so references point forward. ⚠️ A **backward** reference (`comment_2 → comment_0`) is malformed data and can
drop a comment — see `COMMENTS_INSTRUCTIONS.md` §7.

> ⚠️ **The reference format is lenient — a typo silently points to the wrong reply.** The parser does **not**
> match the literal string `comment_N`: for each item (split on `,` / `&`) it grabs the **first run of digits**
> and uses it as the slot number, ignoring every other character. So `comment_5`, `5`, and even a garbage value
> like `ninvuinviunv_5` are **all read as `comment_5`** — no error is raised. A token with **no digit at all**
> (e.g. `abc`) is silently **skipped** (no reply added). Always write clean `comment_N` values so a mistyped
> cell can't attach the wrong reply.

---

## 4. Configuration: what is editable, and what happens without a session

Three layers — know which is which before deploying:

| Layer | Where it lives | Editable live after deploy? |
|---|---|---|
| **Default value** | `settings.py` (baked into the `.otreezip`) | ❌ No — requires re-`otree zip` + redeploy |
| **Per-session override** | Admin → **Sessions** → *Create new session* form | ✅ Yes — string/number/bool keys only, that session only |
| **Deploy env vars** (`OTREE_ADMIN_PASSWORD`, `OTREE_PRODUCTION`, `OTREE_AUTH_LEVEL`) | Heroku → **Config Vars** | ✅ Yes — no redeploy |

**Editable per session (no redeploy):** `survey_link`, `data_path`, `story_duration`, `dwell_threshold`,
`skip_intro`, … — any config whose value is a string/number/boolean. (List/dict configs need a redeploy.)

**Be specific about the Demo vs Sessions distinction:**
- Editing is available **only** under **Sessions / Rooms** — **not** the **Demo** section.
- **Demo always uses the hard-coded `settings.py` defaults.** So for a **real study, launch from Sessions, not Demo.**
- Overrides are **per-session and not persistent**: the next session starts again from the `settings.py`
  default. To make a value the permanent default for every session, change `settings.py` and redeploy.

**What happens if you don't create a session:** nothing runs for participants. The Sessions list is empty,
no participant **start links** exist, and no data is collected — the deployed URL only shows the landing/demo.
A real run **requires** creating a session under **Sessions** (or a Room) to generate the participant links.

> Practical consequence: you don't strictly need the final `survey_link`/`data_path` baked in before
> deploying — you can set them at session-creation time. (You already baked your Polimi Qualtrics link on
> line 63, which is convenient: it pre-fills, and you can still override per session.)

---

## 5. PRE-DEPLOYMENT — do / check / verify, then ZIP (in order)

Everything below happens **before** `otree zip`. Each step says **why** it matters at that point.

1. **Decide `data_path`** ([settings.py:73](DICE/DICE/settings.py#L73)).
   *Why here:* it's baked into the zip. **Local path** → the CSV must be inside the zip (do **not** delete it,
   step 4). **Raw URL** → the CSV must be pushed to GitHub and the URL must point to `sample_feed_comments.csv`
   (not the old `sample_feed.csv`).

2. **Check `survey_link`** ([settings.py:63](DICE/DICE/settings.py#L63)) — currently your Polimi Qualtrics
   `SV_eeS0tFcikR5hSrs`. *Why:* it's the baked default; `''` would show the built-in debrief instead.

3. **Comments — update the `replies` count manually** for each post.
   *Why:* the number shown on the post's 💬 counter comes from the `replies` column, **not** auto-computed from
   how many comments you added. Set it to match, per your data-entry convention.

4. **Comments — format subcomment references FORWARD only.**
   *Why:* a parent must reference **higher** indices than itself (put replies last, highest indices). A backward
   reference (`comment_0 → comment_1` **and** `comment_2 → comment_0`) is the one malformed case: the cleanup
   prevents 2 levels but **loses** `comment_1`.

5. **Do NOT delete the config CSV.**
   *Why:* with a **local** `data_path`, if the CSV isn't bundled, `read_feed()` raises `FileNotFoundError` and
   the session crashes on creation.

6. **Videos — remove the local `.mp4` from `DICE/DICE/static/videos/` BEFORE zipping, then restore them AFTER.**
   *Why:* the app streams videos from the **GitHub URLs**, not from the zip — the local files only bloat the
   `.otreezip` (~70 MB). They must stay **committed/pushed** (GitHub keeps serving them), so after zipping
   restore them (e.g. `git checkout -- DICE/DICE/static/videos/`) and **never commit their deletion**.

7. **`requirements.txt`** ([DICE/requirements.txt](DICE/requirements.txt)) — currently `otree>=5.11.0,<=6.0.15`
   (installs 6.0.15). *Why:* Heroku installs from this file; keep line 1 `# oTree-may-not-overwrite-this-file`.

8. **Static cache sanity** — not a zip step, but after any CSS/JS change test with `Ctrl+Shift+R`.
   *Why:* stale cached `styles.css` once made the comment avatar render full-screen.

9. **ZIP** — from the middle folder that contains `settings.py`:
   ```
   cd DICE/DICE
   otree zip          # → produces DICE.otreezip
   ```
   *Why here:* `otree zip` must run from the oTree project root; it packages the current source, so any edit
   made **after** zipping is invisible until you re-zip.

---

## 6. DEPLOYMENT — oTree Hub + Heroku (step by step)

Reference pages: **oTree Hub Dashboard** (`otreehub.com/my_projects`) and **Heroku Dashboard**
(`dashboard.heroku.com/apps`). The app is `dice-custom-app`.

1. **Create the Heroku app.** In oTree Hub → *Heroku server deployment*, follow the link to log into Heroku
   and create a **New app** (`dice-custom-app`). One Heroku "app" = the whole oTree project. Then return to
   oTree Hub. *(Don't do the Deploy on Heroku directly — you deploy from oTree Hub.)*

2. **oTree Hub → Register the project.** Choose **Public** (free; Private needs the paid Pro plan).
   🚩 A **Public** project **must NOT** use `OTREE_AUTH_LEVEL=STUDY` (oTree Hub requires it playable in demo).
   → use `OTREE_AUTH_LEVEL=DEMO` in step 4.

3. **Heroku → Resources → Add-ons.** Add both (they set `DATABASE_URL` / `REDIS_URL` automatically):
   - **Heroku Postgres — Essential-0** (~$5/mo) → persistent data storage (without it you lose all data).
   - **Heroku Key-Value Store — Mini** (~$3/mo) → the `prodserver`'s internal messaging (without it it won't run).
   *Why:* `otree devserver` uses SQLite + in-memory; the Procfile `prodserver1of2`/`2of2` **requires** real
   Postgres + Redis.

4. **Heroku → Settings → Config Vars:**
   - `OTREE_PRODUCTION=1`
   - `OTREE_AUTH_LEVEL=DEMO`  ← (not STUDY, see step 2)
   - `OTREE_ADMIN_PASSWORD=<your password>`
   *(Admin username is `admin`. Per the oTree docs, if you later change the admin username or password you
   must **reset the database**. `DEMO` = anybody can play the demo but the full admin interface stays
   password-protected; `STUDY` = only visitors with a start link can play — but `STUDY` is disallowed on a
   Public oTree Hub project.)*

5. **oTree Hub → Deploy tab.** *Choose file* → upload `DICE.otreezip` → wait for the build to succeed.
   *Why:* the build reads the **Procfile**, which is what makes Heroku create the `web` and `worker` processes
   — they only appear **after** this first deploy.

6. **Heroku → Resources → Dyno formation.** Now `web` and `worker` exist. Set **both to Basic** and switch
   **both ON** (web = 1, worker = 1). ⚠️ It's **2 dynos**. (Basic ≈ $0.01/h each.)

7. **oTree Hub → Configure.** Verify DB + Redis are OK, then **Reset DB** (Postgres must already exist).

8. **Open the app** (`https://dice-custom-app-<hash>.herokuapp.com/`) and verify: create an **Instagram**
   session from **Sessions**, confirm the feed, videos, and comments render (videos load from the GitHub URLs).

### Public vs Private — the choice you make when registering

Setup order (mechanics in steps 1–5 above): first you **create the Heroku app** (the real server), then you
**register it on oTree Hub** and deploy the `.otreezip` to it. At registration you choose the project type:

| | **Public** (free) | **Private** (paid — oTree Hub Pro) |
|---|---|---|
| Cost | free | subscription |
| Source code | must be **open** / playable as a demo | can stay closed |
| `OTREE_AUTH_LEVEL` allowed | **`DEMO` only** (`STUDY` is refused) | `DEMO` **or** `STUDY` |
| Best for | most academic studies on a budget | studies that must fully lock the demo page |

You are on **Public**, so `OTREE_AUTH_LEVEL=DEMO` — what that changes for your links is the **last** subsection here.

### After deployment: your app URL

The deploy gives you **one base URL** — your live application, served by Heroku 24/7:
```
https://dice-custom-app-<hash>.herokuapp.com/
```
This base URL is **not** a participant link — it is the app itself. Everything hangs off it:

| Path | What it is |
|---|---|
| `…/` | landing page |
| `…/admin` | **admin** — password-protected; here you create sessions and copy the participant links |
| `…/demo` | Demo page — throwaway preview runs (uses `settings.py` defaults; **separate** data, not your results) |
| `…/room/<name>/` , `…/InitializeParticipant/<code>` | **participant links** — see next |

To run a real study you **generate participant links in `/admin`**; you never hand out the bare base URL.

### Participant links — the formats, and how they behave across browsers

A participant link opens **straight into the experiment** (Intro → Feed → survey redirect), never the admin.
The three formats, as **complete URLs** (`<hash>` = your app's unique Heroku suffix):

```
Individual link     https://dice-custom-app-<hash>.herokuapp.com/InitializeParticipant/gjgq80vp
Session-wide link   https://dice-custom-app-<hash>.herokuapp.com/join/8kd2mfp3
Room link           https://dice-custom-app-<hash>.herokuapp.com/room/dice
```

| Format (route) | Bound to | One link for many people? |
|---|---|---|
| **Individual link** (`/InitializeParticipant/<code>`) | a **specific participant seat** | ❌ one link = one seat; you'd send N different links |
| **Session-wide link** (`/join/<code>`) | a **specific session** | ✅ same link for everyone in **that** session |
| **Room link** (`/room/<name>`) | **the room** (session-agnostic) | ✅ same **permanent** link, reused across sessions |

**How "one link → many participants" actually works** — oTree tells people apart by the **browser**, not by
the link:
- **Different browsers / devices** (your real experiment: each participant on their own phone/PC) → each is a
  **new, independent participant** with their own seat, own randomized feed, own data. The shared link is
  exactly right. ✅
- **Same browser** (e.g. *you* testing) → re-opening the link **resumes the same participant** (a cookie
  remembers them); you do **not** get a second seat. To simulate several participants on one machine, open the
  link in **different browsers or Incognito/private windows**.

So during the study — every participant on their own device — the single shared link gives each their own
version automatically.

### One link for everyone: Room vs session-wide link

Your experiment needs **exactly one link**, embedded in a Qualtrics/Prolific page, that all participants click.
Both the **session-wide link** and the **Room link** provide that; the difference:

| | Session-wide link | Room link |
|---|---|---|
| Bound to | one **specific session** | the **room** (whichever session is open in it) |
| Setup cost | none (no code change) | one line in `settings.py` + one redeploy |
| URL stability | **changes** with every new session | **permanent** — never changes |
| Known in advance | only **after** you create the session | **yes** — exists before any session; paste in Qualtrics once |
| URL readability | random code (`/join/8kd2mfp3`) | clean (`/room/dice`) |
| **If that session is deleted / DB reset** | link **dies** → visitor sees *"This participant does not exist in the database. Maybe the database was reset."* | link **survives** → visitor sees a neutral **waiting page** (keeps polling) until you open a new session |
| Monitor who's participating | **Session Monitor** — same for both | **Session Monitor** — same (+ an optional label-attendance view, only useful with a whitelist) |
| Labels / access whitelist | ❌ | ✅ (optional — see below) |

**The one difference that actually matters:** a session-wide (or individual) link has a session/participant
**code baked in**, so if you delete that session or reset the database the link is **dead** — everyone holding
it hits *"This participant does not exist in the database…"* and you must redistribute a new link. A **Room link
is session-agnostic**: delete the session and the same `https://dice-custom-app-<hash>.herokuapp.com/room/dice`
still works — a visitor just waits on the polling page until you open the next session. That resilience — **not**
"attendance monitoring", which is the **same Session Monitor** for both — is the real reason to prefer a Room for
a link you embed **once** in Qualtrics.

**Recommendation for you:** the **Room** — set the Qualtrics link **once** and never touch it again, even across
reruns. The session-wide link is only simpler if you run a **single** one-off (una tantum) session.

Add the Room in `settings.py` (code → you apply it), then redeploy:
```python
ROOMS = [dict(name='dice', display_name='DICE Instagram study')]   # link: https://dice-custom-app-<hash>.herokuapp.com/room/dice
```
**Room lifecycle** — the link `https://dice-custom-app-<hash>.herokuapp.com/room/dice` is a permanent *door*; clicking it does **not** auto-create a
session. Before each data collection you **open a session for the room** (Admin → **Rooms** → *Create session
for this room* → Instagram config + N seats). Someone who clicks **before** you open the session sees a
**waiting page** (not an error) and is admitted **automatically** once you open it.

> **Seat capacity:** a session reserves **N** seats; once N have entered, the link is **full**. Set **N a bit
> higher than expected recruits** (recruit 100 → set ~120); unused seats are harmless, a full session blocks latecomers.

### Optional add-ons: the Prolific PID and participant labels

**What is a Prolific PID?** When you recruit on **Prolific**, it assigns every participant a unique identifier —
the **`PROLIFIC_PID`** — and appends it to your study URL as `?PROLIFIC_PID=<id>`. It tells you *which* Prolific
person did the study (so you can pay them and match their data). In `settings.py`, `url_param = 'PROLIFIC_PID'`
makes DICE carry that ID through to the final `survey_link` redirect (`…/survey?PROLIFIC_PID=<id>`), linking
oTree ↔ Qualtrics ↔ Prolific by the same ID.

**Participant labels are optional — the simple version does NOT need them.** A plain open room
(`https://dice-custom-app-<hash>.herokuapp.com/room/dice`, nothing appended) already gives each visitor their
own independent run. A **label** (`?participant_label=<x>`)
only *adds*, optionally:
- a **readable ID** in your data (e.g. the Prolific PID) instead of a random participant code;
- **anti-double-participation** — the same label re-entering resumes the same run instead of starting a new one
  (blocks the "open in two browsers to play twice" trick);
- with a **whitelist file**, access control — only pre-listed labels can enter.

To tag each entrant with their Prolific ID from Qualtrics:
`https://dice-custom-app-<hash>.herokuapp.com/room/dice?participant_label=${e://Field/PROLIFIC_PID}`
(Qualtrics substitutes the real PID at click time). Skip this if you just want the bare link.

### `OTREE_AUTH_LEVEL`: DEMO vs STUDY — and its effect on your links

Set in **Heroku → Config Vars** (step 4). Because you registered **Public**, you must use **`DEMO`** (`STUDY`
is allowed only on Private). What the level changes — and, crucially, what it does **not**:

| | `DEMO` (Public — your case) | `STUDY` (Private only) |
|---|---|---|
| `/admin`, data, export | password-protected | password-protected |
| `/demo` page | reachable by anyone who **has** the base URL | **disabled** (nobody) |
| **Participant links** (individual / session-wide / **room**) | **open** — work for anyone with the link | **open** — same |

**Key point for your links:** participant links are **never password-protected, at either level** — that's how
participants get in. So **`DEMO` does not expose your room / session-wide / individual link any more than
`STUDY` would.** The *only* thing `DEMO` leaves open that `STUDY` closes is the `/demo` page (and anyone holding
a participant link knows the base URL, so they could manually visit `…/demo`).

`DEMO` is therefore fine for you, as long as the link isn't posted publicly. Avoiding "**a random person clicks a
stray link and loads my server**":
- the base URL carries a **random hash** + `robots.txt` → **not indexed / not discoverable**; distribute it
  **only** via Prolific/Qualtrics and it never floats around in public;
- the **seat cap `N`** (limite max posti) bounds (limita) how many can ever enter a session;
- demo/junk entries carry **no valid `PROLIFIC_PID`**, so they are trivial to discard at analysis;
- for a guarantee **even if the link becomes public**, use a **Room + participant-label whitelist**
  (`participant_label_file` + `use_secure_urls`) → a stray plain link then admits **nobody**, and this stays
  free on `DEMO`.

### The app runs on Heroku, not your computer

After deploy, the app **and** its Postgres DB run on **Heroku's servers 24/7** — **no local PC needs to stay
on**, and the participant links work independently (`otree devserver` is for local testing only). Dyno note:
**Basic** dynos never sleep (use these during data collection); **Eco** dynos sleep after 30 min idle and
cold-start in a few seconds on the next visit — still no PC required.

---

## 7. Running a study & teardown

- **Run:** Admin → **Sessions** → *Create new session* → (optionally override `data_path`/`survey_link`/…) →
  hand out participant links (per-participant, the **session-wide link**, or a **Room** link — see §6).
  Launch from **Sessions**, never Demo.
- **Teardown (stop all costs), in order:**
  1. **Export data FIRST** — Admin → **Data → Plain** → save the CSV locally. *(Deleting Postgres deletes the DB.)*
  2. **Scale dynos to 0** — Heroku → Resources → Dyno formation → web = 0, worker = 0.
  3. **Delete the add-ons** — Heroku → Resources → Postgres / Key-Value Store → *Delete Add-on* (confirm with the app name).
  - A stopped app shows an error page — that's normal. **Don't delete the Heroku site** (oTree Hub registration
    keys aren't reusable) — keep it and redeploy for the next study.

---

## 8. Billing (quick reference)

| Component | Plan | Cost |
|---|---|---|
| Dynos (web + worker) | **Basic** | ~$7/mo **each** → $14/mo for 2 |
| Dynos (web + worker) | **Eco** | $5/mo **flat for the account** (shared 1000 h) — 2 eco dynos = $5 total |
| Database | Postgres Essential-0 | ~$5/mo (~$0.007/h) |
| Redis | Key-Value Store Mini | ~$3/mo (~$0.004/h) |
| **All on (Basic)** | | **≈ $22/mo** |

- Dynos bill while **scaled ≥1** (stop by scaling to 0). Add-ons bill while they **exist** (stop by deleting).
- Pro-rated: a study torn down the same day costs a fraction (e.g. ~$0.22 for ~7 h all-in on Basic).
- **GitHub Student Pack** → Heroku **$13/mo credit for 24 months** (covers Eco dynos + both add-ons) —
  redeem at education.github.com/pack. Effectively free for a small study.

---

## 9. Key file map

| What | File |
|---|---|
| Feed path + config defaults | `DICE/DICE/settings.py` |
| Backend logic (preprocessing, comments, video classification) | `DICE/DICE/DICE/__init__.py` |
| CSV feed (with comments) | `DICE/DICE/DICE/static/data/sample_feed_comments.csv` |
| Instagram post template | `DICE/DICE/DICE/T_Item_Insta.html` |
| Instagram feed shell | `DICE/DICE/DICE/T_Feed_Insta.html` |
| Reusable comment card (comments + replies) | `DICE/DICE/DICE/T_Insta_Comment.html` |
| Instagram autoplay JS | `DICE/DICE/DICE/static/js/insta_video.js` |
| Comment likes + "View replies" JS | `DICE/DICE/DICE/static/js/insta_comments.js` |
| Like/reply capture JS | `DICE/DICE/DICE/static/js/like_button.js` |
| Comment / badge / reply CSS | `DICE/DICE/DICE/static/css/styles.css` |
| Stories template / JS / CSS | `T_Item_Stories.html` · `static/js/stories.js` · `static/css/styles_stories.css` |
| Deploy | `DICE/Procfile` (2 dynos) · `DICE/requirements.txt` |

---

## Sources (auth/billing facts verified against official docs)

- oTree — Admin & `OTREE_AUTH_LEVEL` (DEMO/STUDY), admin password, Data export: <https://otree.readthedocs.io/en/latest/admin.html>
- oTree — configurable session parameters, Demo not configurable: <https://otree.readthedocs.io/en/latest/treatments.html>
- Heroku — dyno & add-on pricing, proration, scaling to 0: <https://devcenter.heroku.com/articles/usage-and-billing>
