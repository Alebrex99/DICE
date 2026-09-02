# DICE — Full Project Instructions (complete app)

General guide that collects **everything implemented so far** (feed data, images, videos, comments) and
the **complete pre-deployment + deployment procedure** for the **full DICE app** (Instagram focus).

- Comment authoring detail → `COMMENTS_INSTRUCTIONS.md`
- Parked/optional improvements → `FUTURE_UPDATES.md`
- For the stripped-down **"Simple Viewer"** build (no survey button, fixed timer) → `INSTRUCTIONS.md`

---

## The project at a glance — stack, repositories, how to get the code

### What this is
DICE is a **social-media feed simulator for behavioural research**, built on:
- **[oTree](https://www.otree.org/)** (v5/v6) — the Python experiment framework that renders the pages,
  assigns participants and stores data. Docs: <https://otree.readthedocs.io/en/latest/>
- **[Heroku](https://www.heroku.com/)** — the cloud host where the app is deployed and runs 24/7.
- **[oTree Hub](https://www.otreehub.com/home/)** — the middle layer that packages/uploads your app to Heroku.
- Project site & official docs: <https://www.dice-app.org/> ·
  [stimuli/CSV](https://www.dice-app.org/docs/stimuli.html) ·
  [deployment](https://www.dice-app.org/docs/deployment.html)

### Which repository do I take?

| Purpose | Repository | Notes |
|---|---|---|
| **Media content** (images/videos for the CSV) | <https://github.com/analyticspeg/202609_ITA_Exp_Content> | ⚠️ **All media raw links must come from here**, in every app/version |
| **Full DICE — experiment org** | <https://github.com/analyticspeg/GENERAL_DICE> | `data_path` → `https://raw.githubusercontent.com/analyticspeg/GENERAL_DICE/refs/heads/main/DICE/DICE/static/data/sample_feed_comments.csv` |
| **Full DICE — developer** | <https://github.com/Alebrex99/DICE> | the maintained source the org repo is forked from |
| **Full TikTok — experiment org** | <https://github.com/analyticspeg/DICE-tiktok> | fork of <https://github.com/Howquez/DICE-tiktok> |
| Instagram **Simple Viewer** (see `INSTRUCTIONS.md`) | <https://github.com/analyticspeg/DICE_EXP_SEPT2026> · dev: <https://github.com/Alebrex99/DICE_v2> | `data_path` → `…/DICE_EXP_SEPT2026/refs/heads/main/DICE/DICE/static/data/sample_feed.csv` |
| TikTok **Simple Viewer** | <https://github.com/analyticspeg/DICE-tiktok_EXP_SEPT2026> · dev: <https://github.com/Alebrex99/DICE-tiktok-fork> | `data_path` → `…/DICE-tiktok_EXP_SEPT2026/refs/heads/main/DICE/static/data/sample_exp.csv` — **note: one folder level less** than DICE |
| Upstream / reference | <https://github.com/Howquez/DICE-lite> · <https://github.com/Alebrex99/DICE-lite> · [prebuilt upstream .otreezip](https://github.com/Howquez/DICE/blob/main/software/DICE/DICE.otreezip) | Twitter-only variant + ready-made zip |

> The **`analyticspeg`** repos (<https://github.com/analyticspeg>) are **forks** of the developer repos, which is
> why the names differ. Every correct CSV on `analyticspeg` also exists in the developer repos — you only need to
> adjust the relative **path** in `settings.py`. **Media files, however, are always linked from
> [202609_ITA_Exp_Content](https://github.com/analyticspeg/202609_ITA_Exp_Content).**

### First time? Clone the repo
Pick the repo above, then get it locally so you can edit it:
```bash
git clone https://github.com/Alebrex99/DICE.git      # ← or the repo you need
cd DICE
```
You now have the full source and can change the CSV, templates, `settings.py`, etc. Installing oTree and
packaging come later, in **§5 PRE-DEPLOYMENT**.

### Folder structure (what matters)
```
<repo-root>/                    ← what `git clone` creates
└── DICE/                       ← oTree PROJECT root — settings.py lives here
    │                             ⚠️ run every `otree …` command FROM HERE
    ├── settings.py             ← SESSION_CONFIGS, SESSION_CONFIG_DEFAULTS, ROOMS, data_path
    ├── requirements.txt        ← what Heroku installs (otree, pandas, numpy…)
    ├── Procfile                ← declares the Heroku processes: web + worker
    ├── _static/global/         ← project-level static files
    ├── _templates/global/      ← base Page.html
    └── DICE/                   ← the oTree APP
        ├── __init__.py         ← ALL Python logic (models, creating_session, pages, export)
        ├── A_Intro.html  B_Briefing.html  C_Feed.html  D_Redirect.html  D_Debrief.html
        ├── T_Feed_*.html       ← one feed shell per channel (Insta, Twitter, Stories, …)
        ├── T_Item_*.html       ← one post template per channel
        ├── T_Insta_Comment.html← reusable comment card (comments + replies)
        └── static/
            ├── data/*.csv      ← feed CSVs
            ├── js/             ← dwell.js, insta_video.js, insta_comments.js, …
            ├── css/            ← styles.css, preloader_*.css
            └── videos/         ← local .mp4 (served FROM GitHub, not from the zip — see §2)
```

---

## 1. Feed data (CSV) — the single source of truth

The whole feed (posts, media, comments) comes from one CSV, set in
[settings.py](DICE/DICE/settings.py) → `data_path`. Delimiter is `;`.

### Where the CSV can live (`data_path` formats)

| Format | Example | When to use | Caveat |
|---|---|---|---|
| **Local path** (relative to `DICE/DICE/`) | `DICE/static/data/sample_feed_comments.csv` | Feed is final and shipped inside the app | The file **must be bundled in the `.otreezip`**. If it isn't, `read_feed()` raises `FileNotFoundError` and the session **crashes**. |
| **GitHub raw URL** | `https://raw.githubusercontent.com/<USER>/<REPO>/refs/heads/<BRANCH>/<PATH>/file.csv` | You want to change the feed **without redeploying** | Repo must be **public and pushed**; a network problem *or a 404 (wrong/renamed path, unpushed file)* at session creation **fails the session** — see the callout below. |
| **Google Sheets export URL** | `https://docs.google.com/spreadsheets/d/<id>/export?format=csv` | Non-developers edit the feed in Sheets | Sheet must be shared/public. |

> **The URL to use for the full DICE app** (org repo [GENERAL_DICE](https://github.com/analyticspeg/GENERAL_DICE)):
> ```
> https://raw.githubusercontent.com/analyticspeg/GENERAL_DICE/refs/heads/main/DICE/DICE/static/data/sample_feed_comments.csv
> ```
> The same CSV also lives in the developer repo <https://github.com/Alebrex99/DICE> — only the relative path changes.
>
> **Convert any GitHub file page into a raw URL** — open the file on GitHub, click **Raw**, and copy the URL
> it gives you (GitHub now generates the `refs/heads/` form):
> ```
> https://github.com/<USER>/<REPO>/blob/<BRANCH>/<PATH>/file.csv                     ← GitHub file page
> https://raw.githubusercontent.com/<USER>/<REPO>/refs/heads/<BRANCH>/<PATH>/file.csv ← raw (use in data_path) — current GitHub format
> https://raw.githubusercontent.com/<USER>/<REPO>/<BRANCH>/<PATH>/file.csv            ← older short form — still resolves, but not what GitHub's Raw button gives you today
> ```
> Manual shortcut: on the file page, remove `blob/` and add `refs/heads/` right before the branch name.
>
> ⚠️ **A 404 at this URL crashes session creation** (exact traceback:
> `pandas…urlopen…HTTPError: HTTP Error 404: Not Found`, raised from `read_feed()` around the
> `pd.read_csv(path, …)` call). Causes: the file was never **pushed**; the path/branch doesn't match the repo;
> or the deployed `.otreezip` was built from a **different `settings.py`** (e.g. an old example URL was still
> active when it was zipped). **Fix without redeploying:** Admin → *Create session* → override `data_path` with
> a URL you verified returns `200` (`curl -I <url>`). **Fix definitively:** correct `settings.py` and re-zip from
> the right folder, or switch to a **local** `data_path` (bundled in the zip → no network fetch, no 404 possible).

> 🔗 **Authoring helpers:** official stimuli/CSV documentation <https://www.dice-app.org/docs/stimuli.html> ·
> DICE preprocessing web tool <https://dice-app.shinyapps.io/DICE-Preprocessing/>

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
does **not** work for these. (The post flag `view_direct_comments` **does** use `to_bool`, so `VERO`/`1`/… work.)
The **comment block** (10 columns) repeats identically for each slot `i` = `0`…`5`.

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
| 19 | `view_direct_comments` | `VERO`/`1`/`true`/`yes`/`x` (post-level flag; **uses `to_bool`**, unlike `sponsored`/`commented_post`) | bool | when TRUE, renders comments **directly under the post using the exact same cards as the modal** (avatars, badges, like button, working "View replies"/subcomments) + a "View all N comments" line, **in addition to** the 💬 modal — how many are shown is set by `preview_comments` | below the caption/timestamp, inside the post card | **empty/false → current behavior**: comments only via the 💬 modal, no preview |
| 20 | `preview_comments` | integer (post-level; used only when `view_direct_comments` is TRUE) | int | **how many parent (top-level) comments** the preview shows: **N > 0** → first N (all if N exceeds the total); **0 or empty/invalid** → none; **< 0** → all. Subcomments aren't counted (they travel nested under their shown parent) | sets the preview count | **empty/absent → none (0)** |
| | **— COMMENT BLOCK — repeats for each slot `i` = `0`…`5` (in the Comments modal) —** | | | | | |
| 21 | `comment_i` | free text; **same highlighting as post `text`** — `#hashtag` `@mention` `$cashtag` + links | string | comment text | comment body | empty text `""` |
| 22 | `comment_user_i` | e.g. `giulia` | string | commenter username | top of comment, next to avatar | `"unknown"` |
| 23 | `comment_image_i` | avatar URL | URL | commenter avatar photo | left edge of the comment | Bootstrap person icon |
| 24 | `verified_user_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | blue verified ✓ | right of the username | no ✓ |
| 25 | `comment_time_i` | `2w`, `now`, `3m`, `1y` | string | timestamp (shown as-is, no parsing) | username line, right of ✓ | no timestamp |
| 26 | `comment_likes_count_i` | integer, e.g. `128` | int | number shown next to the like heart (set manually per comment) | under the heart, right of the comment | `0` |
| 27 | `comment_liked_author_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | "· Liked by Author" **+ a static red heart** next to the label (does **not** colour the clickable like heart) | on the username line, after the timestamp | no label, no red heart |
| 28 | `pinned_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | "📌 Pinned by Author" + comment hoisted to the top of the list | own line above username; list order | not pinned |
| 29 | `member_comment_i` | `VERO`/`1`/`true`/`yes`/`x` | bool | violet background + "Comment by Member" | whole-comment tint + label above username | normal comment |
| 30 | `subcomments_comment_i` | `comment_5,comment_6` or just `5,6` (**forward refs**; separator `,` or `&`). ⚠️ **Only the digits are read** — any text wrapped around a number (e.g. `xyz_5`, `ninvuinviunv_5`) is still parsed as `comment_5`; a value with no digit is silently ignored | list | the replies nested under this comment → "View replies (N)" | expandable block indented under the comment | no replies |
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
| **GitHub raw** | `https://raw.githubusercontent.com/<USER>/<REPO>/refs/heads/<BRANCH>/<PATH>/clip.mp4` | Repo public & pushed; ≤ ~100 MB/file. Autoplay works (videos are muted). Fine for pilots; for a large study (hundreds+ participants) prefer a CDN — GitHub raw has no SLA and may throttle/hotlink-block at scale. |
| GitHub Releases | `https://github.com/<USER>/<REPO>/releases/download/<TAG>/clip.mp4` | For files > 100 MB (see FUTURE_UPDATES D). |
| **jsDelivr** (CDN in front of GitHub) | `https://cdn.jsdelivr.net/gh/<USER>/<REPO>@<BRANCH>/<PATH>/clip.mp4` | <https://www.jsdelivr.com/> — free CDN that serves public GitHub files; better caching than raw. |
| CDN / object storage | `https://<bucket>/…/clip.mp4` | Best for a real study (Cloudflare R2, Bunny, S3…). |

> 📦 **Where the media lives:** all images/videos for the experiments are in
> <https://github.com/analyticspeg/202609_ITA_Exp_Content> — take the raw links from there and paste them into
> the CSV `media` column, whichever app version you are running.

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
Set the post-level flag **`view_direct_comments`** (`VERO`/`1`/…) to also render comments **directly under the
post using the exact same cards as the modal** (same style, like button, and working "View replies"/subcomments)
+ a "View all N comments" line. The companion integer **`preview_comments`** sets how many **parent** comments
appear (**N** → first N, all if it exceeds the total; **0/empty** → none; **<0** → all). Flag off → comments only in the modal.
Full authoring detail is in **`COMMENTS_INSTRUCTIONS.md`**; summary below.

> ⚠️ **The comment counter is NOT the number of comments you added.** The number on a post's 💬 button is
> read from the post's **`replies`** column (an integer) and is **completely independent** of how many
> `comment_i` slots you fill — adding comments does **not** update it. You must set `replies` **manually**
> to the number you want shown (it may equal the comments you added, or be higher, like Instagram's
> "View all 128 comments"). Leaving `replies = 0` while adding comments shows **0** on the button even
> though the comments still appear in the modal.

### The 10 columns per slot `i` (exact CSV order) → effect → what is shown

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

A setting can live in three different places, and *where* it lives decides whether you can still change it once
the app is online. Knowing which is which saves you a lot of pointless redeploys:

| Layer | Where it lives | Editable live after deploy? |
|---|---|---|
| **Default value** | `settings.py` (baked into the `.otreezip`) | ❌ No — requires re-`otree zip` + redeploy |
| **Per-session override** | Admin → **Sessions** → *Create new session* form | ✅ Yes — string/number/bool keys only, that session only |
| **Deploy env vars** (`OTREE_ADMIN_PASSWORD`, `OTREE_PRODUCTION`, `OTREE_AUTH_LEVEL`) | Heroku → **Config Vars** | ✅ Yes — no redeploy |

**Editable per session (no redeploy):** `survey_link`, `data_path`, `story_duration`, `dwell_threshold`,
`skip_intro`, … — any config whose value is a string/number/boolean. (List/dict configs need a redeploy.)

**Demo vs Sessions — an important distinction.** The override form only exists under **Sessions / Rooms**; the
**Demo** section has no such form and always runs with the hard-coded `settings.py` defaults. That is why a real
study must always be launched from **Sessions** (or a Room), never from Demo. Also keep in mind that an override
applies to **that session only** and is not remembered: the next session you create starts again from the
`settings.py` value. If you want a new value to become the permanent default, you have to edit `settings.py`,
re-zip and redeploy.

**What happens if you don't create a session:** nothing runs for participants. The Sessions list is empty,
no participant **start links** exist, and no data is collected — the deployed URL only shows the landing/demo.
A real run **requires** creating a session under **Sessions** (or a Room) to generate the participant links.

> Practical consequence: you don't strictly need the final `survey_link`/`data_path` baked in before
> deploying — you can set them at session-creation time. (Baking the Qualtrics link in `settings.py` is
> convenient: it pre-fills the form, and you can still override it per session.)

> 🔗 oTree docs — session configs & treatments: <https://otree.readthedocs.io/en/latest/treatments.html> ·
> passing values from Python to JavaScript (`js_vars`):
> <https://otree.readthedocs.io/en/latest/templates.html#passing-data-from-python-to-javascript-js-vars>

---

## 5. PRE-DEPLOYMENT — do / check / verify, then ZIP (in order)

Everything below happens **before** `otree zip`. Each step says **why** it matters at that point.

1. **Decide `data_path`** ([settings.py](DICE/settings.py)) — the feed the app will read.
   *Why now:* this value is baked into the zip, so getting it wrong means a failed session later. If you use a
   **local path**, the CSV has to travel inside the zip (so don't delete it — step 5). If you use a **raw URL**,
   the file must already be **pushed** to GitHub and the URL must be the one you actually want (for the full app:
   the **comments** CSV, `sample_feed_comments.csv`). Check it returns `200` before zipping — a 404 here crashes
   session creation (see §1).

2. **Check `survey_link`** ([settings.py](DICE/settings.py)) — the Qualtrics (or other survey) URL participants
   are sent to when they finish the feed. *Why now:* it's the default baked into the zip. Leaving it empty
   (`''`) is legitimate — the app then shows its built-in debrief page instead of redirecting — but if you do
   want the redirect, make sure the URL is the right one. You can still override it per session later.

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

9. **Get the code + an environment that has `otree`** (do this once per machine).

   **a) Clone the repo you need** (see the repository table at the top):
   ```bash
   git clone https://github.com/Alebrex99/DICE.git
   cd DICE
   ```

   **b) Install oTree** — two options, either is fine:
   ```bash
   # OPTION 1 — virtual environment (recommended: isolated, no clashes with other projects)
   python -m venv .venv
   .venv\Scripts\activate           # Windows      (macOS/Linux: source .venv/bin/activate)
   pip install otree

   # OPTION 2 — global install (only if `pip` is on your PATH / system env variables)
   pip install otree
   ```
   *Why:* `otree zip` only needs the **`otree` package** itself — it does **not** import your app, pandas or
   numpy (those are installed on Heroku from `requirements.txt`). If `pip` isn't recognised in the terminal,
   either add Python/pip to the PATH environment variables or just use the `.venv` route.
   💡 Install a **6.x** oTree (matching `requirements.txt`, currently `otree>=5.11.0,<=6.0.15`).

10. **ZIP** — from the folder that contains `settings.py`:
    ```bash
    cd <repo-root>/DICE      # the oTree project root
    otree zip                # → produces DICE.otreezip
    ```
    *Why here:* `otree zip` must run from the oTree project root; it packages the current source, so any edit
    made **after** zipping is invisible until you re-zip. *(A `.venv` folder in the project is automatically
    excluded from the archive, so it never bloats the zip.)*

---

## 6. DEPLOYMENT — oTree Hub + Heroku (step by step)

Reference pages: **oTree Hub** <https://www.otreehub.com/my_projects/> · **Heroku Dashboard**
<https://dashboard.heroku.com/apps> · official DICE deployment guide
<https://www.dice-app.org/docs/deployment.html> · oTree server docs
<https://otree.readthedocs.io/en/latest/server/intro.html>

**0. Create the two accounts** (once, before anything else):
   - **Heroku** — sign up / log in: <https://www.heroku.com/> · <https://www2.heroku.com/auth/login>.
     💰 **If you have the GitHub Student Developer Pack, redeem the free credit first:**
     <https://www.heroku.com/github-students/> (via <https://education.github.com/pack>) →
     **$13/month for 24 months** (≈ $312), valid on Dynos, Postgres and Key-Value Store. A valid
     credit/debit card and age 18+ are required; unused monthly credit does **not** roll over, and the offer
     doesn't apply to Team accounts. This covers a whole single-app setup (see §8).
   - **oTree Hub** — sign up / log in: <https://www.otreehub.com/home/> → your projects live at
     <https://www.otreehub.com/my_projects/>. *(Examples of published Hub projects:
     <https://www.otreehub.com/projects/ibt-hsg/> · <https://www.otreehub.com/otai/jr/>.)*

1. **Create the Heroku app.** In oTree Hub → *Heroku server deployment*, follow the link to log into Heroku
   and create a **New app** (`dice-custom-app`). One Heroku "app" = the whole oTree project. Then return to
   oTree Hub. *(Don't do the Deploy on Heroku directly — you deploy from oTree Hub.)*

2. **oTree Hub → Register the project.** Choose **Public** (free; Private needs the paid Pro plan).
   🚩 A **Public** project **must NOT** use `OTREE_AUTH_LEVEL=STUDY` (oTree Hub requires it playable in demo).
   → use `OTREE_AUTH_LEVEL=DEMO` in step 4. ⚠️ Registering **consumes a Hub key** — read
   *"oTree Hub keys"* below **before** registering a second/third app.

3. **Add-ons — you *add* these from the Heroku `Resources` tab.** Open the app's **Resources** page
   (e.g. <https://dashboard.heroku.com/apps/dice-app/resources>), type a name into the **"Add-ons"** search
   box, select it, choose the plan and **Submit** to provision it. You add **one** and deliberately skip the other:

   **➕ Add — [Heroku Postgres](https://elements.heroku.com/addons/heroku-postgresql) — Essential-0** (~$5/mo)
   → **recommended.** Sets `DATABASE_URL` automatically.

   *What if you skip it (no DB add-on)?* The app still boots — oTree falls back to a local **SQLite** file.
   But a Heroku dyno's filesystem is **ephemeral**: *"Any files written get discarded the moment the dyno stops
   or restarts, including automatic restarts"* ([Heroku — Ephemeral filesystem](https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem)),
   and Heroku **cycles dynos automatically** — at least once a day, plus on every deploy, config change or crash
   ([Heroku — Dyno restarts](https://devcenter.heroku.com/articles/dyno-restarts)). So the SQLite DB (sessions,
   participants **and all collected data**) is periodically **wiped**. For the full DICE app — which *does*
   collect behavioural data — this means **losing your study results**: Postgres is effectively mandatory here.
   Consequence for links: a **room** link (`…/room/dice`) survives (it lives in `settings.py`) but shows the
   *"waiting for your session to begin"* page until you re-create the session; a **session-wide**
   (`/join/<code>`) or individual link **hard-breaks** with *"This participant does not exist in the database"*.

   **⛔ Do NOT add — [Heroku Key-Value Store (Redis)](https://elements.heroku.com/addons/heroku-key-value-store).**
   The Key-Value Store is *"an in-memory key-value data store … provisioned and managed as an add-on"* that sets
   a `REDIS_URL` ([docs](https://devcenter.heroku.com/articles/heroku-redis)). It's the classic cache /
   **message broker** many web apps — and **oTree 5** — used to connect a web process with a separate worker
   process. **oTree 6 does not use Redis at all**, so provisioning it only wastes ~$3/mo. (Full explanation in
   *"Dynos & the Procfile"* below.)

4. **Heroku → Settings → Config Vars:**
   - `OTREE_PRODUCTION=1`
   - `OTREE_AUTH_LEVEL=DEMO`  ← (not STUDY, see step 2)
   - `OTREE_ADMIN_PASSWORD=<your password>`
   *(Admin username is `admin`. Per the [oTree admin docs](https://otree.readthedocs.io/en/latest/admin.html),
   if you later change the admin username or password you must **reset the database**. `DEMO` = anybody can play
   the demo but the full admin interface stays password-protected; `STUDY` = only visitors with a start link can
   play — but `STUDY` is disallowed on a Public oTree Hub project.)*

5. **oTree Hub → Deploy tab.** *Choose file* → upload `DICE.otreezip` → wait for the build to succeed.
   *Why:* the build reads the **Procfile**, which is what makes Heroku create the `web` and `worker` processes
   — they only appear **after** this first deploy.

6. **Heroku → `Resources` → Dyno formation.** Set **web = 1 (Basic, ON)** and **worker = 0 (OFF)** — on
   oTree 6 you run a **single** dyno. Full reasoning and the oTree 5-vs-6 difference in *"Dynos & the Procfile"*
   below. Scaling docs: <https://devcenter.heroku.com/articles/scaling> ·
   <https://devcenter.heroku.com/categories/dynos>

7. **oTree Hub → Configure.** Verify the DB is OK (there is no Redis to check), then **Reset DB** to create the
   tables (with Postgres it must already be provisioned; with SQLite the file is created automatically).

8. **Open the app** (`https://dice-custom-app-<hash>.herokuapp.com/`) and verify: create an **Instagram**
   session from **Sessions**, confirm the feed, videos, and comments render (videos load from the GitHub URLs).

### Dynos & the Procfile — oTree 6 (current) vs oTree 5 (previous)

A **dyno** is one running container (one process) that Heroku bills while it is switched on
(<https://devcenter.heroku.com/categories/dynos>). *Which* processes can exist is declared in the **`Procfile`**:

```
web:    otree prodserver1of2
worker: otree prodserver2of2
```

Each line is one dyno **type** that you turn on/off in **Resources → Dyno formation**.

**`web` dyno (`prodserver1of2`) — always required:**
- serves every HTTP page and the websockets — i.e. the actual experiment the participant sees;
- binds Heroku's `$PORT`;
- in **oTree 6** it *also* spawns the timeout sub-process (`otree timeoutsubprocess`) **inside itself**.

**`worker` dyno (`prodserver2of2`):**
- **oTree 5 (previous):** a **required** 2nd process. It ran the *timeout worker* (page timeouts, bot workers)
  and communicated with `web` **through Redis** as the message broker. Turning it off — or skipping Redis —
  broke timed pages.
- **oTree 6 (current):** a **no-op**. Its own source says *"doesn't do anything since we moved timeoutworker
  into main dyno"* — the body is literally `while True: sleep(10)`. The timeout work moved into the `web` dyno
  and Redis was removed, so this dyno does nothing.

**What each version actually needs:**

| | oTree 5 (previous) | oTree 6.0.15 (what you deploy) |
|---|---|---|
| `web` dyno | ✅ needed | ✅ needed |
| `worker` dyno | ✅ needed (timeout worker) | ❌ no-op → **switch OFF (0)** |
| Redis / Key-Value Store | ✅ needed (broker between web ↔ worker) | ❌ not used at all |
| Cross-process channel layer | Redis | in-process (single dyno, in-memory) |

**Bottom line (oTree 6):** run **web = 1, worker = 0, no Redis**. Leaving the `worker` line in the Procfile is
harmless — you just never scale it above 0. ⚠️ Keep **web = 1** (don't scale to 2+): the in-memory channel layer
isn't shared across dynos.

### oTree Hub keys & multiple accounts — how registration really works (tested)

**On the free (Public) plan you get exactly 2 registration keys** → max **2 registered projects per oTree Hub
account**. Keys are **consumed permanently**: they are never given back.

**How `CONNECT` behaves**
- Pressing **CONNECT** in oTree Hub links the Hub to your **Heroku** account: it authenticates and
  **automatically detects the apps already present on Heroku**.
- ⭐ **The SAME Heroku account can be connected to several different oTree Hub accounts** — this is exactly what
  makes the multi-account strategy below possible, and it works.
- The Heroku apps always follow the **currently connected** Hub account: log out, log into another Hub account,
  press Connect → the same Heroku apps now appear *there*. The link is "current", not permanent per account.

**Registration — the step that burns a key**
- **Register** on a specific Heroku app **consumes one key** on the account you are logged into.
- **An app can be registered on only ONE oTree Hub account at a time.**
- After switching account and reconnecting, the apps show up **unregistered**. If you then register an app that
  was **already registered on the other account**, the app moves to the current account — the other account
  **loses the registration but its key stays consumed and unrecoverable**.
- ✅ You may keep **many *unregistered* apps** connected at once — that costs nothing. **Only *Register* burns a key.**

> ⚠️ **Worst case:** registering on a second account the same Heroku apps you had already registered on the
> first leaves you with **an account with zero keys AND zero registered apps.**

**Rules to follow**
- 🚫 **Never register the same Heroku app on two different oTree Hub accounts** — the key is wasted for good.
- 📋 **Plan the split up front.** For 4 apps (DICE full, DICE Simple Viewer, TikTok full, TikTok Simple Viewer):
  **2 registered on account 1 + 2 registered on account 2** — each app registered once, on one account only.
- 🔄 **To update an app, never delete/re-register it:** upload a new `NOME_APP.otreezip` to the **same** Hub
  project → *Deploy*, then redo the deployment steps. Redeploys are unlimited and consume **no** key; you can
  even change the URL name — there is no need to create a new site.
- 💳 **Keep ONE Heroku account** (the GitHub Student credit is per-account and can't be re-applied after the
  24 months) and connect it to as many Hub accounts as you need.

> 💸 **Cost reality check:** each *live* app needs its own dyno + Postgres (≈ $12/mo). Three apps running at once
> ≈ $36/mo, well above the $13/mo student credit — so keep only the app you're actually collecting on scaled up,
> and scale the others to **0** (and delete their Postgres) — see §7 teardown and §8.

### ⚠️ The `web` dyno can switch itself back ON after you set it to 0

Setting `web = 0` is **not a permanent off switch**. The dyno can come back up by itself, and every second it
runs is billed — so after a study you have to check that it really stayed off.

**Why it happens.** Heroku never restarts a process that you scaled to 0 on its own
([dyno restarts](https://devcenter.heroku.com/articles/dyno-restarts)). What brings it back is **oTree Hub**:
when you press *Connect* you hand it your Heroku credentials, and from then on the Hub can turn your app back on
whenever it talks to Heroku.

**The situations that switch it back on:**
- you open or reload your project on **oTree Hub** — above all if you press **Connect** again;
- you run any Hub action on that app: **Deploy**, **Configure**, **Reset DB**;
- anything that creates a new Heroku release: a **deploy**, a change in **Config Vars**, adding or removing an
  **add-on**.

**What NOT to do after the study — and why:**
- ❌ **Don't go back to oTree Hub / press Connect "just to check"** on an app you shut down — that is the single
  most common way to wake it up again.
- ❌ **Don't leave Postgres attached** thinking `web = 0` is enough — an add-on bills just by **existing**, even
  with every dyno off.
- ❌ **Don't use `heroku maintenance:on` as an off switch** — it shows a maintenance page but keeps billing.
- ❌ **Don't delete the Heroku app** to feel safe — that also **burns your oTree Hub key**, which you never get
  back (see the section above).

**What to do instead:** export your data → delete the Postgres add-on → set `web = 0` → stay out of the Hub for
that app → **check Resources again a day later**.

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

Add the Room in `settings.py` (official docs: <https://otree.readthedocs.io/en/latest/rooms.html#rooms>),
then redeploy:
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
  2. **Delete the add-on** — Heroku → **Resources** → **Heroku Postgres** → *Delete Add-on* (confirm with the
     app name). *(On oTree 6 there is no Key-Value Store to delete — you never added it.)* Do this **before**
     scaling down: add-ons bill while they merely **exist**.
  3. **Scale dynos to 0** — Heroku → **Resources** → Dyno formation → web = 0 (worker is already 0).
  4. **Then stay out of oTree Hub for that app** — and **re-check the dyno formation a day later**: opening the
     Hub / pressing *Connect* can silently scale `web` back to 1 (see the ⚠️ subsection at the end of §6).
  - A stopped app shows an error page — that's normal. **Don't delete the Heroku site, and don't delete the
    oTree Hub project** — Hub registration keys are **not reusable and are never refunded** (see *"oTree Hub keys"*
    in §6). Keep both and simply upload a new `.otreezip` for the next study.

---

## 8. Billing (quick reference)

Costs differ by oTree version, because **v6 drops the worker dyno and Redis** (see *Dynos & the Procfile*, §6).
Pricing reference: <https://devcenter.heroku.com/articles/usage-and-billing#dyno-usage-and-costs>

**oTree 6.0.15 — what you deploy today (per app):**

| Component | Plan | Cost |
|---|---|---|
| `web` dyno (only) | **Basic** | ~$7/mo (≈ $0.01/h) |
| `worker` dyno | — (OFF) | **$0** |
| Database | [Postgres Essential-0](https://elements.heroku.com/addons/heroku-postgresql) | ~$5/mo (~$0.007/h) |
| Key-Value Store / Redis | — (not used) | **$0** |
| **Total — Basic web + Postgres** | | **≈ $12/mo** |
| *cheaper:* `web` on **Eco** + Postgres | Eco ($5 flat/account, 1000 h shared) | **≈ $10/mo** |

**oTree 5 — previous version, for reference (what the old guide assumed):**

| Component | Plan | Cost |
|---|---|---|
| `web` + `worker` dynos | **Basic** | ~$7/mo **each** → $14/mo for 2 |
| Database | Postgres Essential-0 | ~$5/mo |
| Redis | [Key-Value Store Mini](https://elements.heroku.com/addons/heroku-key-value-store) | ~$3/mo |
| **Total — all on (Basic)** | | **≈ $22/mo** |

- Dynos bill while **scaled ≥ 1** (stop by scaling to 0). Add-ons bill while they **exist** (stop by deleting).
- Pro-rated to the second: a study torn down the same day costs a fraction (e.g. ~$0.12 for ~7 h all-in on the
  v6 Basic + Postgres setup).
- **GitHub Student Pack** → Heroku **$13/mo for 24 months** (≈ $312), valid on Dynos, Postgres and Key-Value
  Store — redeem at <https://www.heroku.com/github-students/> (via <https://education.github.com/pack>).
  On **v6 that covers a whole ≈ $12/mo single-app setup**. ⚠️ Credit is **per month, no roll-over**, needs a card
  on file, and is **not** valid for Team accounts — so **N apps live at once ≈ N × $12** and will exceed it.

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
| Deploy | `DICE/Procfile` (declares web + worker; on oTree 6 run **web only**) · `DICE/requirements.txt` |

---

## Sources & reference links (all in one place)

### Project — DICE
- DICE project site: <https://www.dice-app.org/>
- Stimuli / CSV documentation: <https://www.dice-app.org/docs/stimuli.html>
- Deployment documentation: <https://www.dice-app.org/docs/deployment.html>
- CSV preprocessing web tool: <https://dice-app.shinyapps.io/DICE-Preprocessing/>
- Upstream prebuilt archive: <https://github.com/Howquez/DICE/blob/main/software/DICE/DICE.otreezip>

### Repositories
**Experiment org — [analyticspeg](https://github.com/analyticspeg)**
- Media content (images/videos for every CSV): <https://github.com/analyticspeg/202609_ITA_Exp_Content>
- Full DICE: <https://github.com/analyticspeg/GENERAL_DICE>
  → `data_path = "https://raw.githubusercontent.com/analyticspeg/GENERAL_DICE/refs/heads/main/DICE/DICE/static/data/sample_feed_comments.csv"`
- Full TikTok: <https://github.com/analyticspeg/DICE-tiktok>
- Instagram Simple Viewer: <https://github.com/analyticspeg/DICE_EXP_SEPT2026>
  → `data_path = "https://raw.githubusercontent.com/analyticspeg/DICE_EXP_SEPT2026/refs/heads/main/DICE/DICE/static/data/sample_feed.csv"`
- TikTok Simple Viewer: <https://github.com/analyticspeg/DICE-tiktok_EXP_SEPT2026>
  → `data_path = "https://raw.githubusercontent.com/analyticspeg/DICE-tiktok_EXP_SEPT2026/refs/heads/main/DICE/static/data/sample_exp.csv"`

**Developer — Alebrex99**
- Full DICE: <https://github.com/Alebrex99/DICE> · DICE-lite: <https://github.com/Alebrex99/DICE-lite>
- Instagram Simple Viewer: <https://github.com/Alebrex99/DICE_v2>
- TikTok Simple Viewer: <https://github.com/Alebrex99/DICE-tiktok-fork>

**Upstream (Howquez)**
- TikTok: <https://github.com/Howquez/DICE-tiktok> · DICE-lite: <https://github.com/Howquez/DICE-lite>

### oTree
- Home: <https://www.otree.org/> · Docs: <https://otree.readthedocs.io/en/latest/>
- Server / deployment overview: <https://otree.readthedocs.io/en/latest/server/intro.html>
- Admin & `OTREE_AUTH_LEVEL` (DEMO/STUDY), admin password, Data export: <https://otree.readthedocs.io/en/latest/admin.html>
- Rooms (permanent participant links): <https://otree.readthedocs.io/en/latest/rooms.html#rooms>
- Session configs / treatments: <https://otree.readthedocs.io/en/latest/treatments.html>
- Python → JavaScript (`js_vars`): <https://otree.readthedocs.io/en/latest/templates.html#passing-data-from-python-to-javascript-js-vars>

### oTree Hub
- Home: <https://www.otreehub.com/home/> · My projects: <https://www.otreehub.com/my_projects/>
- Example projects: <https://www.otreehub.com/projects/ibt-hsg/> · <https://www.otreehub.com/otai/jr/>

### Heroku
- Home / login: <https://www.heroku.com/> · <https://www2.heroku.com/auth/login>
- Apps dashboard: <https://dashboard.heroku.com/apps> · app Resources tab example: <https://dashboard.heroku.com/apps/dice-app/resources>
- **GitHub Students offer** ($13/mo × 24 months): <https://www.heroku.com/github-students/> · <https://education.github.com/pack>
- Add-on — Postgres: <https://elements.heroku.com/addons/heroku-postgresql>
- Add-on — Key-Value Store (Redis, **not needed on oTree 6**): <https://elements.heroku.com/addons/heroku-key-value-store> · <https://devcenter.heroku.com/articles/heroku-redis>
- Dynos (concepts): <https://devcenter.heroku.com/categories/dynos> · Scaling: <https://devcenter.heroku.com/articles/scaling>
- Billing & dyno costs: <https://devcenter.heroku.com/articles/usage-and-billing> · <https://devcenter.heroku.com/articles/usage-and-billing#dyno-usage-and-costs>
- Ephemeral filesystem (SQLite gets wiped): <https://devcenter.heroku.com/articles/dynos#ephemeral-filesystem>
- Automatic dyno restarts: <https://devcenter.heroku.com/articles/dyno-restarts>

### Media hosting alternatives
- jsDelivr (free CDN in front of GitHub): <https://www.jsdelivr.com/>
