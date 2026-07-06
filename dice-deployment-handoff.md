# Handoff — DICE (oTree social-media simulator): video feature + Heroku deployment

**Status:** Video feature is built and mostly reviewed. The user is now **mid-deployment** to Heroku via **oTree Hub**. Next session most likely continues the deploy (add-ons → dyno plan → upload zip → Reset DB → verify) and/or the last small code cleanups.

**Workspace:** `c:\Users\Alessandro\VisualStudioCodeProjects\SocialNetworkClone\DICE`
Git repo root = that folder (it **is** the GitHub repo `Alebrex99/DICE`, branch `main`).
oTree project root (where `settings.py` lives) = `DICE\DICE\`. App = `DICE\DICE\DICE\`. Run `otree` commands from the **middle** `DICE\DICE`.

Read first (do NOT duplicate here):
- `CLAUDE.md` (root) and `DICE/CLAUDE.md` — project map. NOTE: they say "oTree 5.x" but the venv/deploy now use **oTree 6.0.15**.
- `INSTRUCTIONS.md` — how the video feature works (Insta + Stories).
- `FUTURE_UPDATES.md` — parked improvements (see below).

---

## Environment facts
- Local `.venv` at **repo root** (`...\DICE\.venv`), Python **3.11**, oTree **6.0.15** installed. It's gitignored and outside the project root, so it's excluded from `otree zip` and never deployed. Nothing to do with it except activate it to run `otree`.
- `runtime.txt` = `python-3.11.9` (governs Heroku). `.python-version` = `3.12` (stale/cosmetic; Heroku ignores it).
- `Procfile` = `web: otree prodserver1of2` + `worker: otree prodserver2of2` → **2 dynos** required.

---

## Code state (video feature)

### Done & reviewed (working)
- Backend `DICE/DICE/DICE/__init__.py` `preprocessing()`: media classification (`is_video`, `video_available`, `image_available`) via `video_ext` regex.
- Instagram: `T_Item_Insta.html` `{{ if i.video_available }}` → `<video controls muted loop playsinline preload="auto">`; `static/js/insta_video.js` = IntersectionObserver autoplay (≥50% visible) + pause-on-tab-hide (no resume by design) + pause-on-CTA-click. `visibleVideos` Set removed/cleaned.
- Stories: `T_Item_Stories.html`, `static/js/stories.js`, `static/css/styles_stories.css`. Video slides, global mute button, stop-on-end-slide, CTA button for sponsored.
- `stories.js` fixes APPLIED and verified: focus→pause video, blur→resume only if tab visible, visibilitychange resume skips if reply input focused, `slideDurationMs()` makes the progress bar last the video's real length (image slides still use `story_duration`).
- `data_path` in `DICE/DICE/settings.py:71` already switched to a **GitHub-raw URL** (good for changing the feed without redeploy).

### Outstanding / decisions
- **Broken-video handling (bug #1):** the `error`-fallback fix was **reverted** — current `startProgressAnimation` only waits for `loadedmetadata` (+ a leftover `console.log`). A 404/broken video URL → progress bar never starts → story stuck (manual tap still works). **User decided to ACCEPT this for now** ("makes the problem more evident, shouldn't happen"). If revisited: the `error` event fires on the `<source>` child, not `<video>`, so listen on `v.querySelector('source')` + a `setTimeout` fallback + a `started` flag. Also remove the `console.log` at ~`stories.js:380`.
- **No video watch-time collected** (no Player field / not in `get_form_fields` / not in `custom_export`). Parked as FUTURE_UPDATES **UPDATE B**. User = future work.
- **Dwell inflated on tab-hide** (`recordViewTime` wall-clock, pre-existing). Parked as FUTURE_UPDATES **UPDATE C**. User = leave it.
- Minor/edge items (double `loadedmetadata` listener, resume-before-metadata fallback, controls-vs-observer, CTA-in-background-tab, `video_ext` `$`-anchor): all reviewed and judged **not worth fixing** for the controlled setup.
- **requirements.txt** (`DICE/DICE/requirements.txt`): currently `otree>=5.11.0,<=6.0.15`. Works (installs 6.0.15). To satisfy the oTree-Hub security notice cleanly, tighten to `otree>=6.0.14,<=6.0.15` or pin `otree==6.0.15`. **User has NOT decided/applied yet** — offered repeatedly. Keep line 1 `# oTree-may-not-overwrite-this-file`.
- **Git hygiene:** `db.sqlite3` staged-deleted + gitignored (done). `.pyc` files still **tracked** → run `git rm -r --cached DICE/DICE/__pycache__ DICE/__pycache__`. `.gitignore` already updated.

---

## ⚠️ Critical footgun — videos & CSV are served FROM GitHub
The CSV (`sample_feed.csv`) and all `.mp4`s are fetched at runtime from `raw.githubusercontent.com/Alebrex99/DICE/main/...`. The user **deleted the local `static/videos/*.mp4` from disk** (unstaged deletion) to keep the `.otreezip` slim — which is fine — BUT the files must **stay in the GitHub repo** (they're still in HEAD = on GitHub) or the URLs 404 in production.
- **DO NOT let the video/CSV deletions get committed & pushed.** Stage files explicitly (`git add <file>`), never `git add -A`.
- Long-term robust fix = move videos to GitHub Releases / CDN (FUTURE_UPDATES D/E), then safe to purge.

---

## Deployment state & next steps
- oTree Hub project: **`dice-custom-app`** (chosen **Public project** = free; private needs paid oTree sub).
- Heroku app `dice-custom-app` created, **billing card added**, but **no dynos, no add-ons yet** (Resources tab shows "no process types yet" — expected, because process types only appear AFTER the first deploy reads the Procfile).
- App URL: `https://dice-custom-app-<hash>.herokuapp.com/`.

**Decided plan: use BASIC dynos** (user wants lowest cost for short one-off studies; Basic is per-second-prorated, Eco is a flat $5/mo). Correct order:
1. (Add-ons can be added now, before deploy) Resources tab → add **Heroku Postgres (Essential-0, $5/mo)** + **Heroku Key-Value Store (Mini, $3/mo)**.
2. Settings → Config Vars: `OTREE_PRODUCTION=1`, `OTREE_AUTH_LEVEL=STUDY`, `OTREE_ADMIN_PASSWORD=<redacted — user sets their own>`.
3. Pin `otree==6.0.15` (recommended), then `cd DICE/DICE && otree zip`.
4. Upload `DICE.otreezip` on the oTree Hub **Deploy** page → wait for build.
5. Now the `web`/`worker` dynos appear in Heroku Resources → set both to **Basic** and ensure both are **ON (=1)**.
6. oTree Hub → **Configure** (verify DB+Redis) → **Reset DB**.
7. Open `/admin` (user `admin` + their password) → create a **Stories/Instagram** session → **confirm videos actually play from the GitHub URLs**.
8. Also: change `survey_link` in `settings.py:62` (currently a **UNISG Qualtrics** URL) to the user's own survey, or `''` for the built-in debrief.

### Billing model (already explained to user — confirmed facts)
- Dyno bills while **scaled ≥1** (even with zero visits) → stop by scaling to **0**. Add-ons bill while they **exist** (independent of dynos/visits) → stop by **deleting** them.
- **Basic** = $7/mo **per dyno** → 2 dynos = $14/mo. **Eco** = $5/mo **flat for the whole account** (shared 1,000-hr pool), so 2 eco dynos = **$5 total (not $10)**.
- Teardown after a study: **export data (admin→Data→Plain) FIRST**, then scale dynos to 0, then delete Postgres+Redis add-ons.
- Cost calc example the user cares about (sequential: 30-min session + 15-min wait between 10 participants = `10×30 + 9×15 = 435 min ≈ 7.25 h`): Basic all-in ≈ **$0.22** if torn down same day.
- **Heroku for GitHub Students** = **$13/mo credit for 24 months** — redeem at https://education.github.com/pack/redeem/heroku (user has the GitHub Student Pack but must redeem the Heroku offer specifically & link the Heroku account). Covers the whole minimal stack → effectively free.

---

## Suggested skills for the next session
- **`git-guardrails-claude-code`** — genuinely useful here: set a hook to block `git add -A`/broad commits so the video/CSV deletions can't be accidentally committed & pushed (the critical footgun above).
- **`diagnosing-bugs`** — if the Heroku build fails or videos don't play in production (e.g. 404s, missing add-on, psycopg2 build).
- **`/code-review`** (command the user relied on repeatedly) — for any further code edits before packaging.
- **`claude-md-management:revise-claude-md`** — optional: update `CLAUDE.md` to reflect oTree **6.0.15** (docs currently say 5.x).

## Language / working-style notes
- User is Italian; many replies were in Italian. Match the language of their message.
- User applies most code edits **themselves** and prefers precise "what to change + why" instructions over auto-applied edits. Confirm before applying. They dislike wrong/over-eager edits.
- "learning" output style was active for part of the session (educational insights). Not required.

## Redacted
- `OTREE_ADMIN_PASSWORD` (env var, user-chosen — not in repo). `SECRET_KEY` is hardcoded in `settings.py` (pre-existing; consider moving to env, low priority — value not reproduced here).
