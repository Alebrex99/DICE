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

## 3. Future Feature (design for it now, but do not implement yet)

**"View previous replies" button** — collects subcomments (threaded replies) under a specific comment.

- Each top-level comment gets a "View previous replies" button, positioned below the comment text, left-aligned in line with the comment's username.
- Clicking it expands a subcomments section showing all replies to that comment, indented slightly to the right.
- **Hierarchy is limited to 1 level**: a subcomment cannot itself have subcomments, and a comment that appears as a subcomment of another comment cannot simultaneously exist as a top-level comment.

Example:
```
Comment_0
  ○ subcomment: comment_1
  ○ subcomment: comment_2
```

- CSV column: `subcomments_comment_i` — a delimited list of column references pointing to the subcomments (e.g., `comment_1,comment_2`). Suggest evaluating whether `,` or `&` is the more robust delimiter given other data in the CSV.
- Any comment referenced inside a `subcomments_comment_i` list must not have its own `subcomments_comment_i` — it is only ever a subcomment.

I don't need the implementation steps for this yet — just make sure the CSV schema and comment data model accommodate it. I'll ask for the implementation plan separately later.

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
