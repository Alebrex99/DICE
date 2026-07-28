# Handoff — DICE Instagram Comments Feature

**Date:** 2026-07-27
**Repo:** `c:\Users\Alessandro\VisualStudioCodeProjects\SocialNetworkClone\DICE` (branch `main`)
**Project type:** oTree 6.0.15 social-media feed simulator (Instagram focus), deployed to Heroku via oTree Hub.

---

## ⚠️ READ FIRST — operating constraints (do not violate)

These were set explicitly by the user and are the most important part of this handoff:

1. **CODE changes → PLAN ONLY.** For any change to `.py` / `.html` / `.js` / `.css` / `.csv`, give a **step-by-step "what to change, where, and why"**. **Do NOT apply code edits directly** — the user applies all code themselves. (They rejected direct code edits twice.)
2. **Markdown docs → apply directly.** `INSTRUCTIONS.md`, `COMMENTS_INSTRUCTIONS.md`, `comment_section_requirements.md`, `FUTURE_UPDATES.md` may be edited with the Edit/Write tools without asking.
3. **Language:** the user is Italian and frequently writes in Italian. **Match their language** in each reply (Italian when they write Italian).
4. **Never run `otree zip`** (or resetdb / devserver as a "verification") unless asked — the user builds/deploys the zip themselves. They rejected a zip attempt.
5. When verifying doc claims, **verify against the actual code** (full-project review), not from memory. The user repeatedly asked for this and several table inaccuracies were caught this way.

---

## Project map (do not re-derive)

- Cross-project map: [CLAUDE.md](c:\Users\Alessandro\VisualStudioCodeProjects\SocialNetworkClone\CLAUDE.md) (three sibling repos: DICE / DICE-lite / DICE-tiktok-fork).
- App-specific: [DICE/CLAUDE.md](c:\Users\Alessandro\VisualStudioCodeProjects\SocialNetworkClone\DICE\CLAUDE.md).
- **Work happens in the full `DICE/` folder.** oTree project root is `DICE/DICE/` (has `settings.py`); the app is `DICE/DICE/DICE/`.
- Run: `cd DICE\DICE && otree devserver` → http://localhost:8000 → Demo → pick Instagram session.

---

## What is DONE and applied (in code)

The Instagram **comments feature** and **threaded replies** are fully built and applied in code by the user. Data-driven entirely from the feed CSV — no runtime code change needed to author comments.

- **Comments** load from `comment_i` CSV slots into a `comments` list-of-dicts column, rendered inside the **Comments modal** (not below the post).
- Per comment: avatar (or Bootstrap person-icon fallback), username, blue ✓ verified, timestamp, "· Liked by Author", "· Author" (auto when commenter == post `username`), "📌 Pinned by Author", violet "Comment by Member", and a like heart (red **only** if `comment_liked_author_i` set; random 0–200 count; click changes only the number).
- **Threaded replies** via `subcomments_comment_i` (1-level cap). "View replies (N)" ⇄ "Hide replies" toggle.
- Renamed "creator" → **"Author"** everywhere. Italian booleans **VERO/FALSO** supported.

### Key code locations (reference — already correct in repo)

| File | What lives there |
|---|---|
| `DICE/DICE/DICE/__init__.py` | `to_bool()`, `highlight_entities()`, `preprocessing()`, **`build_comments()`** (threading resolver), `creating_session()`, `custom_export()` |
| `DICE/DICE/DICE/T_Item_Insta.html` | post + Comments modal; loops comments into the card partial |
| `DICE/DICE/DICE/T_Insta_Comment.html` | reusable comment card (used for comments AND replies via `{{ include … with c=sc }}`) |
| `DICE/DICE/DICE/static/js/insta_comments.js` | heart toggle (count only) + View-replies expand/collapse (frontend only) |
| `DICE/DICE/DICE/static/css/styles.css` | `.insta-comment*`, `.view-replies-btn`, `.insta-subcomments` |
| `DICE/DICE/settings.py` | `SESSION_CONFIGS` / defaults; `data_path` (line ~73 local CSV), `survey_link` (institutional Qualtrics — do not paste in outputs) |
| `DICE/DICE/DICE/static/data/sample_feed_comments.csv` | sample feed; 18 post columns + 9 columns per comment slot (`comment_0`..`comment_6`) |

### Threading model (current, agreed after 3 iterations)

Strict **"first-met wins in CSV order"**: slots read ascending; a comment already claimed as a reply has **its own subcomments list ignored** → each comment is exactly one of {plain, parent, reply}; hierarchy capped at 1 level; cycles safe. A 2-line **safety net** blanks a claimed reply's list (handles backward references, at the cost of orphaning the malformed target). **Good practice:** put replies at the end with the highest indices so every reference points forward. Full rule + 9 edge-case table already written in `COMMENTS_INSTRUCTIONS.md` §7 and `comment_section_requirements.md` §3.

---

## Documentation files (in-repo; edit these directly)

Do **not** duplicate their content into new files — extend them.

- **INSTRUCTIONS.md** — comprehensive project guide: §1 feed data + **complete per-column CSV reference table** + highlight table, §2 media, §3 comments summary (+ `replies` callout), §4 config layers, §5 pre-deployment checklist, §6 deployment + DEMO-vs-STUDY access model, §7 study/teardown, §8 billing, §9 file map.
- **COMMENTS_INSTRUCTIONS.md** — standalone comment-authoring guide (§1–9). Full content was read this session; see the file directly.
- **comment_section_requirements.md** — the input spec; §3 holds the order-resolved strict threading model.
- **FUTURE_UPDATES.md** — deferred work: **UPDATE F** = comment-interaction logging (JS→hidden input→Player LongStringField→get_form_fields); **UPDATE G** = stronger 5-line malformed-reference cleanup (superset of the current 2-line safety net); Instagram-comments block.

### Last completed task (this session)

Added the **`replies` rule** (comment counter is decoupled from actual comments — read from the post's `replies` integer column, must be set manually; a display total like "View all 128 comments", not a live count) to **INSTRUCTIONS.md §3** and **COMMENTS_INSTRUCTIONS.md §2**; fixed the highlight cell in **COMMENTS_INSTRUCTIONS.md §3** to list all 4 highlighted types (`#hashtag` `@mention` `$cashtag` + `http/https/ftp` links). A full §1–9 review of COMMENTS_INSTRUCTIONS.md confirmed everything else matches the code. **This request is complete.**

---

## Pending / optional (offered, NOT yet confirmed by user)

Start these only if the user asks:

1. **Parity pass:** replicate the full column-reference corrections (complete boolean value set `1/true/vero/yes/x`; 4-type highlight list) into COMMENTS_INSTRUCTIONS.md's §3 table so the two doc files stay identical on details.
2. **`data_path` coherence in settings.py:** line ~73 uses a local CSV path while the commented raw-URL (line ~72) still points at the OLD `sample_feed.csv`. Offer to align the raw URL to the comments CSV: `https://raw.githubusercontent.com/Alebrex99/DICE/main/DICE/DICE/static/data/sample_feed_comments.csv` — **code change → plan only.**
3. **Cross-consistency check** between INSTRUCTIONS.md and COMMENTS_INSTRUCTIONS.md.

---

## Deployment context (for accuracy when advising)

- Heroku: web (`prodserver1of2`) + worker (`prodserver2of2`) dynos; Postgres Essential-0; Key-Value/Redis Mini. Procfile already targets this.
- oTree Hub **Public** project ⇒ must use `OTREE_AUTH_LEVEL=DEMO` (Public forbids STUDY). Participants necessarily know the base URL (embedded in start links); mitigate leakage with Prolific-only distribution + `PROLIFIC_PID` filtering via `url_param`.
- Boolean handling differs by column: the **4 comment bools** (verified/liked_author/pinned/member) use `to_bool` (accept `1/true/vero/yes/x`); **post-level** `sponsored` and `commented_post` do **not** — they need numeric `1/0` (`commented_post` uses `== 1`). `commented_post` on Instagram would break (no `T_Feed_Insta_Replies.html` exists). Empty `media` ⇒ whole post skipped (`pic_available` gate).

---

## Suggested skills for the next session

- **`/code-review`** — if asked to re-verify docs against code or audit the comments/threading logic, this runs a structured multi-file review. (`/code-review ultra` = billed cloud review of the branch; user-triggered only — you cannot launch it.)
- **`context7` MCP** (`resolve-library-id` → `query-docs`) — for authoritative oTree / pandas / Heroku behaviour instead of guessing, when a doc claim needs verification.
- **`Explore` / `general-purpose` agent** — only if the user explicitly asks to spawn a subagent for a broad code sweep; otherwise handle searches inline with Grep/Glob/Read (do not spawn agents unprompted).

> Check the live user-invocable skills list at session start; names above are the ones known to exist in this project.

---

## Gotchas

- CSV files are frequently open in Excel → edits can hit `EPERM` locks; retry.
- The "image goes full-screen" report was a stale browser CSS cache, not a code bug (hard-refresh fixes it).
- oTree templates are ibis-based (not Django): `{{ if }}/{{ elif }}/{{ endif }}`, `{{ for }}`, and parameterized `{{ include "path" with var=expr }}` (multiple bindings separated by `&`). No autoescaping.
- Do not include the user's email or the institutional survey URL verbatim in deliverables.
