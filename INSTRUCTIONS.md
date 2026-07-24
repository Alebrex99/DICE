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
| `https://…` | blue link `<a>` | not clickable away by default |
| `VERO` / `1` / `true` / `yes` / `x` | boolean **TRUE** | for every bool column; anything else (incl. `FALSO`, `0`, empty) = FALSE |

> After **any** CSV or `settings.py` change in local dev: `otree resetdb`, create a new session, and
> **hard-refresh** the browser (`Ctrl+Shift+R`) — the browser caches CSS/JS aggressively.

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

### The 9 columns per slot `i` (exact CSV order) → effect → what is shown

| # | Column | Effect | Fallback if empty |
|---|---|---|---|
| 1 | `comment_i` | comment text (auto-highlighted) | empty text |
| 2 | `comment_user_i` | username | `"unknown"` |
| 3 | `comment_image_i` | avatar photo (URL) | person icon |
| 4 | `verified_user_comment_i` | blue ✓ after username | no ✓ |
| 5 | `comment_time_i` | timestamp text (`2w`, `now`…) | no timestamp |
| 6 | `comment_liked_author_i` | **red heart** + "· Liked by Author" | white heart |
| 7 | `pinned_comment_i` | "📌 Pinned by Author" + hoisted to top | not pinned |
| 8 | `member_comment_i` | violet background + "Comment by Member" | normal |
| 9 | `subcomments_comment_i` | replies nested under this comment (`comment_5,comment_6`) | no replies |

Derived (no column): **"· Author"** when `comment_user_i` == post `username`; **like count** random 0–200
(display only — clicking changes the number, never the colour; red comes only from column 6).

### Layout of one comment

```
[📌 Pinned by Author]  [· Comment by Member]              ← own line, only if set
[avatar]  username ✓  2w  · Liked by Author  · Author        ♥ 128
          comment text …
          View replies (N)                                   ← only if it has replies
```
Meta items (✓ · time · Liked by Author · Author) sit on the username line and collapse left if missing.
Pinned comments jump to the top of the list.

### Threading rule (1 level) + good practice
`subcomments_comment_i` lists the replies. **One rule:** read in ascending order, a comment already
claimed as a reply has its own list ignored → gives the 1-level cap *and* cycle safety.
✅ **Good practice: put replies at the END of the row with the HIGHEST indices** (`comment_0 → comment_5,comment_6`)
so references point forward. ⚠️ A **backward** reference (`comment_2 → comment_0`) is malformed data and can
drop a comment — see `COMMENTS_INSTRUCTIONS.md` §7.

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

### Access model — what you get, and DEMO vs STUDY (important)

After deploy you get **one base URL** (`https://dice-custom-app-<hash>.herokuapp.com/`). Everything lives on it:

| Path | What |
|---|---|
| `/admin` | admin interface — **password-protected**; you create sessions & participant links here |
| `/demo` | Demo page (spins up throwaway preview sessions) |
| `/InitializeParticipant/<code>` | a participant **start link** (one seat in your real session) |

**Start link vs demo link — the key difference:**
- A **start link** is a pre-assigned seat in a **session you created** (Admin → Sessions). The person's
  data goes into **your study** (what you export). Works at **any** auth level.
- A **demo link** spins up a **throwaway demo session** from the Demo page → **separate** data, uses the
  `settings.py` defaults, **not** your study results. Exists **only** under `DEMO`.

**The catch — the base URL is inside every start link**, so participants necessarily know it:
```
https://dice-custom-app-<hash>.herokuapp.com/InitializeParticipant/o34uxfur
        └───────────────── base URL ──────────────────┘
```
Under `DEMO`, a participant can **trim** their link to `…/demo` and reach the Demo page (replay a demo,
possibly hit the survey redirect again). Under `STUDY`, trimming leads nowhere — only their unique start
link works.

| | `DEMO` (required for a **Public** project) | `STUDY` (Private / paid only) |
|---|---|---|
| Who can reach `/demo` | your participants (they can trim their link) + anyone the URL leaks to — but **not** the anonymous internet (random hash + `robots.txt`, not indexed by Google) | **nobody** (Demo disabled) |
| Join your real study session | only via a start link (unguessable code) | only via a start link |
| Admin / data / export | password-protected | password-protected |

**So `DEMO` vs `STUDY` protects you from your own participants, not from the anonymous internet.** Because
Public forces `DEMO`, mitigate the one real risk (a participant replaying through to the survey) by:
- distributing the app URL **only via Prolific** (never link it publicly), and
- **filtering Qualtrics / Prolific by `PROLIFIC_PID`** — a demo playthrough passes a random participant
  code, not a valid Prolific PID, so those responses are easy to discard.

For a hard lock (nobody can even open the demo): use **Private + `STUDY`** (paid oTree Hub Pro), or a
**Room with a participant-label whitelist** (free, stays on `DEMO`, but only pre-listed labels can enter).

---

## 7. Running a study & teardown

- **Run:** Admin → **Sessions** → *Create new session* → (optionally override `data_path`/`survey_link`/…) →
  use the generated **start links** for participants. Launch from **Sessions**, never Demo.
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
