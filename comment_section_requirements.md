# Instagram-Style Comment Section — Refinement Requirements

**Intent:** Refine the comment section implementation based on feedback and reference examples (see attached screenshots showing real Instagram comment formatting: pinned comments, verified badges, "Liked by Author," author replies, threaded/indented replies, and like-count placement).

**Mode of operation:** As always, do not implement anything directly. First verify that my requirements below are correct and logically consistent, flag anything that seems contradictory or unclear, then provide a complete, step-by-step implementation for me to study, copy and apply.

---

## 1. Comment Placement (Correction)

The comment section is currently placed below the post itself. Instead, it needs to live **inside the "Replies" modal**.

When the user clicks the "Replies" button, a modal opens. Inside that modal, top to bottom, the layout should be:

1. The reply/tweet content (already implemented via `DICE/DICE/static/js/like_button.js`) — shown at the top of the modal, as it already is.
2. All comments for that post, displayed below it.
3. The text input field where the user types a new comment, at the bottom.

The visual appearance and CSS styling of individual comments is already correct and should not be changed — only the placement needs to move into the modal.

---

## 2. Additional Features

These require adding new columns/flags to the input CSV. For each comment, let **i** = the index of that comment on the post (e.g., `comment_0`, `comment_1`, …).

### Per-comment elements and layout

| Element | Position | CSV column | Type |
|---|---|---|---|
| Comment text | Main body | `comment_i` | String |
| Commenter photo | Left edge | `comment_image_i` | URL string |
| Commenter username | Top, next to photo | `comment_user_i` | String |
| Like count + heart icon | Right edge | *Not in CSV* — randomized 0–200 | — |
| Verified checkmark | Immediately right of username | `verified_user_comment_i` | Bool |
| Time since posted (e.g. "now", "2w", "3m", "1y") | Immediately right of verified checkmark | `comment_time_i` | String (no parsing needed) |
| "· Liked by Author" | Immediately right of the timestamp | `comment_liked_author_i` | Bool |
| "· Author" (when the commenter's username matches the post's author) | Immediately right of "· Liked by Author" | *No dedicated flag* — derived by comparing `comment_user_i` to the post's author username | — |
| "[pin symbol] Pinned by Author" | Own line, directly above the username | `pinned_comment_i` | Bool |
| Member comment (violet background), label directly above username (or immediately right of the "Pinned by Author" string if the comment is also pinned) | Above username | `member_comment_i` | Bool |

**Like/heart behavior:** the heart icon starts white/outlined. Clicking it increments that comment's like count. The heart turns red **only if the post's author has liked the comment** — this is directly tied to `comment_liked_author_i` (i.e., red heart ⇔ "· Liked by Author" is shown).

### Alignment rules

- The verified checkmark, timestamp, "· Liked by Author", and "· Author" must all sit **on the same horizontal line**, aligned with the comment's username and photo (username and photo are already correctly aligned).
- Each element appears **only if its corresponding CSV value is set**. If a value is missing (see fallback table below), the remaining elements should collapse leftward — keeping their relative order — right next to the username, with no gaps left by the missing element.
- **Exception:** the Pinned indicator. If `pinned_comment_i` is set, that comment is pulled to the top of the list (displayed first, above all other comments), and "[symbol] Pinned by Author" appears on its own line directly above the username, aligned with it.

---

## 3. Threaded replies — "View replies (N)" (IMPLEMENTED)

Each top-level comment that has replies shows a **"View replies (N)"** button below the comment,
left-aligned under the username. Clicking it expands the replies (indented to the right) and the
button toggles to **"Hide replies"**; clicking again collapses them.

- CSV column `subcomments_comment_i` — a list of comment references (e.g. `comment_1,comment_2`)
  naming the replies under comment *i*. **Delimiter: `,`** (the parser also accepts `&`).
- **One rule, applied in CSV order:** slots are read in ascending order (`comment_0`, `comment_1`, …).
  A comment that has **already been claimed** as a reply has its **own list ignored**; any other comment
  is top-level, and its list claims its replies. So each comment is exactly one of: a plain comment, a
  parent (has replies), or a reply. A reply may be listed by several parents and then appears under each.
- **That single rule gives both guarantees:** the **1-level cap** (a reply's list is dead, so replies
  never nest) **and cycle safety** — with `comment_0 → comment_1` and `comment_1 → comment_0`, comment_1
  is already a reply when we reach it, so its list is ignored and comment_0 stays the parent.
- **An ignored list has no effect at all.** With `comment_0 → comment_3` and `comment_3 → comment_4`,
  comment_3 is a reply of comment_0 and comment_4 is simply **never claimed** — so it renders as a
  **normal top-level comment**. Nothing is lost; it only loses the link to comment_3.
- ✅ **Good practice: put all subcomments at the END of the row, with the HIGHEST indices**, so a parent
  always cites a *higher* index than its own (`comment_0 → comment_5,comment_6`). With this convention
  every reference points forward and the model resolves correctly in a single pass.
- ⚠️ **Backward references are malformed data.** If a comment cites an *earlier* slot already processed
  as a parent (`comment_0 → comment_1` **and** `comment_2 → comment_0`), comment_0 would become a reply
  that still carries a reply = 2 levels. A safety net in `build_comments` empties every reply's own list,
  so **2 levels can never render**; the cost in that malformed case is that comment_1 is orphaned and not
  shown. See `FUTURE_UPDATES.md` → **UPDATE G** for the stronger variant that restores it.
- A `pinned` flag on a reply has no effect (replies never enter the top-level ordering).

Example: on a post row, `subcomments_comment_0 = comment_5,comment_6` renders comment_0 at top level
with a "View replies (2)" button; comment_5 and comment_6 appear **only** indented under it.

---

## 4. CSV Structure and Fallbacks (per comment index i)

| Column | Type | Fallback if empty |
|---|---|---|
| `comment_i` | String (comment text) | Rendered as empty string `""` |
| `comment_user_i` | String | Replaced with `"unknown"` |
| `comment_image_i` | URL string | Use the existing Bootstrap person-icon fallback |
| `verified_user_comment_i` | Bool | No checkmark shown |
| `comment_time_i` | String | No timestamp shown |
| `comment_liked_author_i` | Bool | "· Liked by Author" not shown |
| `pinned_comment_i` | Bool | Comment is not pinned |
| `member_comment_i` | Bool | Not treated as a member comment |
| `subcomments_comment_i` | String (e.g. `comment_1,comment_2,comment_3`) | Comment has no subcomments |

**General fallback rule:** if `comment_i`, `comment_user_i`, and `comment_image_i` are all empty, that comment slot is skipped entirely (treated as unused for that post).

**Note:** the number of filled comment columns does not need to match the post's "replies" count — that will be checked manually at data-entry time.

---

## 5. Direct comment preview under the post — `view_direct_comments` (IMPLEMENTED)

A **post-level** CSV column (one value per row), placed **right after `sequence`** and **before** the comment
slots, boolean via the usual truthy values (`1`/`true`/`vero`/`yes`/`x`).

- **TRUE** → besides the 💬 modal, the post renders comments **directly under the post using the exact same
  cards as the modal** — identical style **and** interactions (avatars, badges, "· Liked by Author",
  click-to-like heart, and working "View replies"/subcomments) — preceded by a "View all N comments" line that
  opens the modal for the rest. How many **parent** comments appear is set by the companion integer column
  **`preview_comments`**: **N>0** → first N (all if N exceeds the total); **0 or empty** → none; **<0** → all.
- **Empty / false (`view_direct_comments`)** → unchanged: comments appear **only** in the modal.
- Backend: `preprocessing` converts `view_direct_comments` via `to_bool` and `preview_comments` via `to_int`,
  then derives `comments_preview` (the chosen count of `comments`). Rendered by `T_Insta_Comments_Preview.html` (included in
  both post branches of `T_Item_Insta.html`), which reuses `T_Insta_Comment.html`. The card's `subreplies_*`
  ids are namespaced via an `ns` include variable (`"modal"` vs `"preview"`) so preview and modal don't clash.
  Known limit: the two copies are independent DOM nodes, so their like/expand state is not synced.
