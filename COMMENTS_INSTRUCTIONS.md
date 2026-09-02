# DICE — Instagram Comments: Authoring Guide

How to add and control the comment section of Instagram-style posts **entirely from the feed CSV**.
Applies to the `Insta` channel. No code changes are needed — comments are data-driven.

This file is a standalone reference. For pending/optional work see `FUTURE_UPDATES.md`
(UPDATE F = comment interaction logging, UPDATE G = stronger malformed-reference cleanup).

---

## 1. Where comments appear

Comments live inside the **Comments modal** that opens when a participant clicks the 💬 button on a
post. Top to bottom, the modal shows:

1. the post text being commented,
2. the list of comments for that post (from the CSV),
3. the "Add a comment…" input.

**Optional — the comments repeated directly under the post (`view_direct_comments`).** This is a **post-level**
column (one value per row, placed right after `sequence`, *before* the comment slots), boolean via the usual
values (`1`/`true`/`vero`/`yes`/`x`). When it is **true**, the post renders comments **directly under it using
the exact same cards as the modal** — identical style **and** interactions (avatars, badges, "· Liked by
Author", the click-to-like heart, and working **"View replies"/subcomments**) — preceded by a "View all N
comments" line that opens the modal for the rest. When **empty/false**, nothing changes: comments appear
**only** in the 💬 modal.

**How many are shown — `preview_comments`** (a companion **post-level** integer column, right after
`view_direct_comments`). It counts **parent (top-level) comments only** — subcomments travel nested under their
shown parent and are not counted:
- **N > 0** → the first N parents (pinned first); if N exceeds the total, **all** are shown;
- **0 or empty/invalid** → **no** preview (even if `view_direct_comments` is true) — the default is `0`;
- **< 0** → **all** parents.

> ℹ️ The same comment is rendered **twice** (preview + modal) as two independent DOM nodes, so liking/expanding
> in the preview is **not** synced with the modal copy (and vice-versa). Under the hood, the shared card's
> `subreplies_*` ids are namespaced via an `ns` include variable (`"modal"` vs `"preview"`) so the two never
> clash.

---

## 2. How comment slots work

- One post = one CSV **row**. A post can hold several comments in fixed **slots** numbered from 0:
  `comment_0`, `comment_1`, …
- The number of slots is **auto-detected** from the `comment_<n>` columns present in the header, so
  adding a slot = adding its 10-column block to the CSV (no code change).
- A slot is **used** when any of its three core fields — `comment_i`, `comment_user_i`,
  `comment_image_i` — is non-empty. If all three are empty, the slot is skipped (treated as unused).

> ⚠️ **The comment counter is separate from the comments (`replies` rule).** The number shown on a post's
> 💬 button is read from the post's **`replies`** column (an integer) and is **completely independent** of
> how many `comment_i` slots you fill. Adding comments does **not** update it automatically:
> - `replies = 0` + 3 comments added → the button shows **0**, but the 3 comments still appear in the modal;
> - set `replies` **manually** to the number you want displayed — it may equal the number of comments you
>   added, or be higher (like Instagram's "View all 128 comments", where the shown total exceeds the loaded
>   comments). It is a **display total**, not a live count of rendered comments.

---

## 3. CSV columns per slot — in the exact order they appear

For each slot `i`, the CSV contains these **10 columns, in this order**, appended after the post columns
(`…;condition;sequence`):

| # | Column | Type | Effect | Fallback if empty |
|---|--------|------|--------|-------------------|
| 1 | `comment_i`               | string | comment text — `#hashtag` `@mention` `$cashtag` + `http/https/ftp` links auto-highlighted blue | empty text `""` |
| 2 | `comment_user_i`          | string | commenter username | `"unknown"` |
| 3 | `comment_image_i`         | URL    | commenter avatar photo | Bootstrap person icon |
| 4 | `verified_user_comment_i` | bool   | blue ✓ right of the username | no checkmark |
| 5 | `comment_time_i`          | string | timestamp text, e.g. `now`, `2w`, `3m`, `1y` (shown as-is) | no timestamp |
| 6 | `comment_likes_count_i`   | int    | number shown next to the like heart (set manually per comment) | `0` |
| 7 | `comment_liked_author_i`  | bool   | "· Liked by Author" label **+ a static red heart** beside it (does **not** colour the clickable like heart) | no label, no red heart |
| 8 | `pinned_comment_i`        | bool   | "📌 Pinned by Author" line + comment hoisted to the top | not pinned |
| 9 | `member_comment_i`        | bool   | violet background + "Comment by Member" label | normal comment |
| 10 | `subcomments_comment_i`   | list   | replies nested under this comment (see §7). ⚠️ **only the digits are read** — `xyz_5` / `ninvuinviunv_5` are parsed as `comment_5`; a value with no digit is ignored | no replies |

**Header block for slot 0** (slots 1, 2, … repeat the same 9 with `_1`, `_2`, …):

```
comment_0;comment_user_0;comment_image_0;verified_user_comment_0;comment_time_0;comment_likes_count_0;comment_liked_author_0;pinned_comment_0;member_comment_0;subcomments_comment_0
```

**Full row column order** (post columns + first comment block):

```
doc_id;datetime;text;media;alt_text;likes;reposts;replies;username;handle;user_description;user_image;user_followers;commented_post;sponsored;target;condition;sequence;comment_0;comment_user_0;comment_image_0;verified_user_comment_0;comment_time_0;comment_likes_count_0;comment_liked_author_0;pinned_comment_0;member_comment_0;subcomments_comment_0;comment_1;…
```

---

## 4. Boolean values

For every bool column, **TRUE** = one of `1`, `true`, `vero`, `yes`, `x` (case-insensitive).
Anything else — including empty, `0`, `false`, `falso` — is **FALSE**.
(`vero`/`falso` support is there so Italian-locale Excel exports work directly.)

---

## 5. Derived elements (no CSV column)

- **"· Author"** — shown automatically when `comment_user_i` equals the post's `username` (i.e. the
  commenter is the post's author).
- **Like count** — read from `comment_likes_count_i` (a plain integer you set per comment; empty → `0`).
  The like heart starts **white**; clicking it toggles it **red ↔ white** and changes the count **+1 / −1**
  (frontend only, not saved). The red heart beside "· Liked by Author" is a **separate static decoration**
  set by `comment_liked_author_i`, unrelated to the clickable like heart.

---

## 6. Layout & alignment of a comment

```
[📌 Pinned by Author]  [· Comment by Member]        ← own line, only if pinned/member
[avatar]  username  ✓  2w  · Liked by Author ❤  · Author        ♡ 128
          comment text …
          View replies (N)                                    ← only if it has replies
```

- The meta items (**✓ verified**, **timestamp**, **· Liked by Author ❤**, **· Author**) sit on the **same
  line** as the username, to its right. Each appears only if set, and missing ones **collapse leftward**
  (no gaps) so the rest stay next to the username.
- The **like heart** on the right starts white (♡); it turns red (❤) **only when the participant clicks it**.
  The red heart inside "· Liked by Author" is a separate, static badge and is never affected by clicks.
- **Pinned** and **Member** labels go on their **own line above** the username. If a comment is both, the
  "Comment by Member" label follows the "Pinned by Author" text on that same top line.
- A **pinned** comment is **hoisted to the top** of the comment list (before all non-pinned comments).

---

## 7. Threaded replies — "View replies (N)"

`subcomments_comment_i` lists the comments that are **replies** under comment *i*, e.g.
`comment_5,comment_6`. **Delimiter: `,`** (the parser also accepts `&`; references may be written as
`comment_5` or just `5`). A comment that has replies shows a **"View replies (N)"** button below it;
clicking expands the replies (indented to the right) and toggles the label to **"Hide replies"**.

> ⚠️ **The reference format is lenient — a typo silently points to the wrong reply.** The parser does **not**
> match the literal string `comment_N`. For each item (split on `,` / `&`) it grabs the **first run of digits**
> and uses that as the slot number, ignoring every other character. So `comment_5`, `5`, and even a garbage
> value like `ninvuinviunv_5` are **all read as `comment_5`** — no error is raised. A token with **no digit at
> all** (e.g. `abc`) is silently **skipped** (no reply added). Always write clean `comment_N` values so a
> mistyped cell can't attach the wrong reply.

### The one rule (and why it is enough)

Slots are read in ascending order (`comment_0`, `comment_1`, …). **A comment that has already been
claimed as a reply has its own subcomments list ignored.** From this single rule:

- each comment is exactly one of: a **plain comment**, a **parent** (has replies), or a **reply**;
- replies never nest → **hierarchy is capped at 1 level**;
- reference **cycles are safe**.

### ✅ Good practice

Put all replies **at the end of the row, with the highest indices**, so a parent always references a
*higher* index than itself: `comment_0 → comment_5,comment_6`. With this convention every reference
points "forward" and the model resolves correctly in one pass.

### Edge cases

| Case | Example | Result | Status |
|---|---|---|---|
| Normal replies (forward) | `comment_0 → comment_5,comment_6` | comment_0 is the parent; 5 and 6 appear **only** nested | ✅ works |
| Reply of a reply | `comment_0 → comment_3` and `comment_3 → comment_4` | 3 nests under 0; **comment_4 becomes a normal top-level comment** (3's list is ignored) | ✅ resolved |
| Cycle | `comment_0 → comment_1` and `comment_1 → comment_0` | comment_0 stays the parent, comment_1 its reply; nothing hangs | ✅ resolved |
| Self-reference | `comment_0 → comment_0` | ignored; comment_0 is a plain comment | ✅ guarded |
| Missing / empty target | `comment_0 → comment_9` (slot 9 unused) | reference skipped | ✅ guarded |
| Shared reply (N parents) | `comment_0 → comment_5` and `comment_1 → comment_5` | comment_5 appears nested under **both** | ✅ works |
| Duplicate in one list | `comment_0 → comment_5,comment_5` | comment_5 shown **twice** under 0 | ⚠️ avoid |
| Pinned on a reply | comment_5 is pinned **and** referenced | no ordering effect, but the pin **badge still draws** on the nested reply | ⚠️ don't pin replies |
| Backward reference | `comment_0 → comment_1` and `comment_2 → comment_0` | 2 levels are **prevented**; comment_0 becomes comment_2's reply; **comment_1 is orphaned and not shown** | ⚠️ malformed — follow the good practice |

The last three only occur with malformed data and are all avoided by the good-practice ordering.

---

## 8. Minimal authoring example

A post with **2 top-level comments**, the second of which has **2 replies**:

- `comment_0` = "Amazing shot!", `comment_user_0` = giulia, `comment_image_0` = <url>,
  `verified_user_comment_0` = VERO, `comment_time_0` = 2w, `comment_likes_count_0` = 210
- `comment_1` = "Where is this?", `comment_user_1` = marco, `comment_image_1` = <url>,
  `subcomments_comment_1` = `comment_4,comment_5`
- `comment_4` = "Yosemite!", `comment_user_4` = giulia, `comment_image_4` = <url>,
  `comment_liked_author_4` = VERO, `comment_likes_count_4` = 87
- `comment_5` = "Bucket list ✅", `comment_user_5` = luca, `comment_image_5` = <url>

Renders as: comment_0 (verified, "2w") and comment_1 at the top level; comment_1 shows
**"View replies (2)"** → comment_4 ("· Liked by Author" + red heart, 87 likes) and comment_5, indented.

---

## 9. Related files (for maintainers)

| File | Role |
|---|---|
| `DICE/DICE/__init__.py` → `build_comments()` / `preprocessing()` | Parses the CSV into the comment model + resolves threading; `preprocessing` also derives `view_direct_comments` (bool), `preview_comments` (int) and `comments_preview` (the chosen count). |
| `DICE/DICE/T_Insta_Comment.html` | The reusable comment card (used for both comments and replies). |
| `DICE/DICE/T_Item_Insta.html` | Includes the card list inside the Comments modal, and the under-post preview. |
| `DICE/DICE/T_Insta_Comments_Preview.html` | Under-post preview: the **same** comment cards as the modal (count = `preview_comments`, via `ns="preview"`), shown when `view_direct_comments` is set. |
| `DICE/DICE/static/js/insta_comments.js` | Heart toggle + "View replies" expand/collapse (frontend only). |
| `DICE/DICE/static/css/styles.css` | Comment / badge / reply styling (`.insta-comment*`, `.view-replies-btn`). |
