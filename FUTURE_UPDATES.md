# FUTURE_UPDATES.md

Pending improvements for the video and Instagram-comment features in the full DICE app.
Reference state: see **Current state** below. Video source is **GitHub raw URLs** (final decision).

---

## Current state (updated)

### Implemented and working

**Backend — `DICE/DICE/DICE/__init__.py` → `preprocessing()`**
Extension-based media classification:
```python
df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False)
video_ext = r'\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$'
df['is_video'] = df['media'].str.contains(video_ext, case=False, regex=True, na=False)
df['video_available'] = df['pic_available'] & df['is_video']
df['image_available'] = df['pic_available'] & ~df['is_video']
```

**Instagram feed — `T_Item_Insta.html` + `insta_video.js`**
- `{{ if i.video_available }}` renders `<video controls muted loop playsinline preload="auto">`
  (both organic and sponsored blocks); images fall through to `<img>`.
- Autoplay via `IntersectionObserver` (play when ≥50% visible, pause otherwise).
- All feed videos pause on tab-hide (`visibilitychange` → `hidden`); no auto-resume on return (by design).
- The in-post video pauses when an external/CTA link is clicked.

**Stories — `T_Item_Stories.html` + `stories.js` + `styles_stories.css`**
- Video slides use `<video class="stories-bg-video" muted loop>`; play/pause driven on slide activation.
- Global mute button (`storiesMuteBtn` / `toggleStoriesAudio`); last video stopped on the end slide.
- Video + progress timer pause on CTA click and on tab-hide; resume on tab return.
- **Progress bar lasts the video's own length for video slides** (`slideDurationMs`),
  `story_duration` for images.
- Sponsored stories have a clickable CTA (`.stories-cta`).

**Instagram comments — `T_Item_Insta.html` + `T_Insta_Comment.html` + `insta_comments.js`**
- Static comments per post come from the CSV (`comment_i`, `comment_user_i`, `comment_image_i`, plus
  `verified_user_comment_i`, `comment_time_i`, `comment_likes_count_i`, `comment_liked_author_i`,
  `pinned_comment_i`, `member_comment_i`, `subcomments_comment_i`). The slot count is **auto-detected**
  from the `comment_<n>` columns, so adding a slot needs no code change. Booleans accept `1/true/vero/yes/x`;
  `comment_likes_count_i` is a plain integer (empty → 0).
- Rendered inside the Replies modal, between the post text and the "Add a comment…" input.
  Pinned comments sort first.
- **Threaded replies (1 level):** `subcomments_comment_i` lists a comment's replies (delimiter `,`,
  `&` also accepted). Slots resolve in ascending CSV order with **one rule**: a comment already claimed
  as a reply has its **own list ignored**. That single rule gives the 1-level cap *and* makes cycles safe
  (`0→1`, `1→0` leaves comment_0 the parent). A comment named only by an ignored list is never claimed
  and renders as a normal top-level comment. A 2-line safety net empties every reply's own list so
  2 levels can never render — a no-op with well-formed data (see **UPDATE G**).
  **CSV convention:** put subcomments at the end of the row with the highest indices (forward refs only).
  "View replies (N)" expands them indented and toggles to "Hide replies".
- One reusable card partial (`T_Insta_Comment.html`) included recursively via
  `{{ include "DICE/T_Insta_Comment.html" with c=sc }}` — identical markup at both levels.
- The like heart is **white by default** and turns **red only when the participant clicks it** (count ±1,
  nothing saved). `comment_liked_author_i` shows a **static red heart** beside the "· Liked by Author" label
  (it no longer colours the like heart). Per-comment counts come from `comment_likes_count_i` (manual int).
- **Under-post comment preview:** the post-level flag `view_direct_comments` (bool via `to_bool`, placed right
  after `sequence`) renders comments **directly under the post using the SAME card as the modal** (identical
  style + interactions + working "View replies"/subcomments), in addition to the modal; empty/false keeps the
  modal-only behavior. A companion integer **`preview_comments`** sets how many **parent** comments show
  (N → first N, all if it exceeds the total; `0`/empty → none; `<0` → all). `preprocessing` derives
  `view_direct_comments`, `preview_comments` and `comments_preview`; the
  preview renders via `T_Insta_Comments_Preview.html`, which includes `T_Insta_Comment.html`. The card's
  `subreplies_*` ids are **namespaced** via an `ns` include variable (`"modal"` vs `"preview"`) so the two
  renderings don't clash. Known limit: the two copies are independent DOM nodes → their like/expand state is
  not synced.

### Not yet implemented (sections below)
- **A** — Video height cap (CSS)
- **B** — Per-video watch-time tracking (`watch_time_data`)  ← main data-collection gap
- **C** — Pause-aware dwell time (exclude hidden-tab time)
- **D** — Move video hosting off the repo (production reliability)
- **E** — Purge the committed videos from git history (depends on D)
- **F** — Comment/reply interaction logging (comment feature is display-only)
- **G** — Stronger cleanup for malformed comment references (nothing gets orphaned)

### Google Drive: abandoned
Drive was tried and dropped. The `uc?id=` endpoint does not serve the headers a native `<video>`
needs (no `Content-Range`/byte-range requests, often `Content-Disposition: attachment`, inconsistent
`Content-Type`/CORS) and shows an HTML virus-scan interstitial for files > ~25 MB. The `/preview`
iframe works but cannot be controlled by JS (no scroll-autoplay/pause/mute, cross-origin).
**Decision: keep GitHub raw URLs.** For large files use GitHub Releases (`/releases/download/...`)
or a CDN (UPDATE D). The commented Drive scaffolding left in `__init__.py`, the templates and the JS
can be deleted whenever convenient — it is no longer a planned direction.

---

## UPDATE A — Video height cap (CSS)

### Why
A tall portrait video (9:16) can dominate the feed and push content off-screen. Instagram caps
in-feed media height at roughly 585 px.

### File to change
**`DICE/DICE/DICE/static/css/styles.css`** — add at the end:
```css
.insta-post video {
    max-height: 585px;
    background: #000;  /* letterbox bars for landscape video */
}
```
No template or backend change needed.

---

## UPDATE B — Per-video watch-time tracking (`watch_time_data`)

### Why
This is the **main data gap**: there is currently **no video-specific data**. `dwell.js` /
`viewport_data` records how long a post was *visible* (paused/scrolled-past time included), not how
many seconds of video actually **played**. For video research you want real play seconds
(equivalent to DICE-tiktok's `watch_time_seconds`).

### Files to change (4 coordinated edits — missing any one silently drops the data)

**1. `__init__.py` — add a Player field (inside `class Player`, after the other LongStringFields)**
```python
watch_time_data = models.LongStringField(doc='per-video play seconds for Instagram videos.', blank=True)
```

**2. `__init__.py` — include it in `C_Feed.get_form_fields()`**
```python
# current:
fields = ['likes_data', 'replies_data', 'promoted_post_clicks', 'touch_capability', 'device_type', 'screen_resolution']
# add 'watch_time_data':
fields = ['likes_data', 'replies_data', 'promoted_post_clicks', 'touch_capability', 'device_type', 'screen_resolution', 'watch_time_data']
```

**3. `T_Feed_Insta.html` — add a hidden input next to the other hidden fields**
```html
<input type="hidden" name="watch_time_data" id="watch_time_data" value="">
```

**4. `insta_video.js` — accumulate play time from the video's own play/pause events**
Add inside the existing `DOMContentLoaded` listener. Note: because the observer and the tab-hide
handler already call `play()`/`pause()`, the `play`/`pause` events below fire automatically — so
**no extra `visibilitychange` block is needed** for watch-time; it is captured for free.
```javascript
    // Per-video play-time accumulation
    var playData = {}; // { docId: { totalSeconds, playStartTime } }

    function onVideoPlay(docId) {
        if (!playData[docId]) playData[docId] = { totalSeconds: 0, playStartTime: null };
        playData[docId].playStartTime = Date.now();
    }
    function onVideoPause(docId) {
        var d = playData[docId];
        if (!d || d.playStartTime === null) return;
        d.totalSeconds += (Date.now() - d.playStartTime) / 1000;
        d.playStartTime = null;
    }
    function flushPlayData() {
        var now = Date.now();
        Object.keys(playData).forEach(function (docId) {
            var d = playData[docId];
            if (d.playStartTime !== null) { d.totalSeconds += (now - d.playStartTime) / 1000; d.playStartTime = null; }
        });
        var result = Object.keys(playData).map(function (docId) {
            return { doc_id: parseInt(docId), duration: Number(playData[docId].totalSeconds.toFixed(3)) };
        });
        var field = document.getElementById('watch_time_data');
        if (field) field.value = JSON.stringify(result);
    }

    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        var docId = parseInt(v.dataset.docId);
        v.addEventListener('play',  function () { onVideoPlay(docId); });
        v.addEventListener('pause', function () { onVideoPause(docId); });
        v.addEventListener('ended', function () { onVideoPause(docId); });
    });

    // Persist before the oTree form submits / page unloads
    window.addEventListener('beforeunload', flushPlayData);
    document.querySelectorAll('form').forEach(function (f) {
        f.addEventListener('submit', flushPlayData);
    });
```

**5. (optional) `__init__.py` — add `watch_time_data` to `custom_export()`**
Append `'watch_time_data'` to the header `yield [...]` and `p.watch_time_data` to the data row `yield [...]`.

### Data format
JSON list, one entry per video the participant actually played (videos never played are absent):
```json
[ {"doc_id": 10, "duration": 12.450}, {"doc_id": 11, "duration": 4.100} ]
```

> **Caveat:** verify the persistence trigger on your oTree version. Writing the input on `form submit`
> and `beforeunload` is the safest combination; if a value ever arrives empty, write it on the oTree
> Next-button click instead.

---

## UPDATE C — Pause-aware dwell time (Stories)

### Why / priority
`recordViewTime()` measures pure wall-clock (`Date.now() - slideStartTime`), so time spent with the
tab hidden is counted as view time. **Low priority and pre-existing:** the original DICE behaviour is
identical, and it affects image stories the same way — the video feature did not introduce it. Apply
only if you need dwell to reflect active on-screen time.

### Files to change (`stories.js`, 4 small edits)
**a)** New global near `slideStartTime`:
```js
var dwellAccumulatedMs = 0; // active-watch ms accumulated, paused intervals excluded
```
**b)** In `activateSlide`, right after `slideStartTime = Date.now();`:
```js
dwellAccumulatedMs = 0; // reset per slide
```
**c)** In the `visibilitychange` handler, one line per branch:
```js
// hidden branch:
if (slideStartTime) { dwellAccumulatedMs += Date.now() - slideStartTime; slideStartTime = null; }
// visible branch:
slideStartTime = Date.now();
```
**d)** In `recordViewTime`, compute from the accumulator and reset it:
```js
var activeMs = dwellAccumulatedMs + (slideStartTime ? Date.now() - slideStartTime : 0);
var dur = activeMs / 1000;
// ... and set  dwellAccumulatedMs = 0;  alongside  slideStartTime = null;
```

---

## UPDATE D — Move video hosting off the repo (production reliability)

### Why
Videos are served from `raw.githubusercontent.com/Alebrex99/DICE/main/...`. GitHub's raw endpoint is
**not a CDN**: it is bandwidth-throttled, per-IP rate-limited (HTTP 429), has no streaming/Range
guarantees, and requires the repo to stay **public and pushed**. With many concurrent participants
streaming the same clips this stalls playback and silently degrades dwell/watch-time data — a single
point of failure outside oTree's control.

### Options (no code change beyond the CSV `media` URL — the `video_ext` regex already matches them)
- **GitHub Releases** — `https://github.com/<user>/<repo>/releases/download/<tag>/<file>.mp4`.
  Same hosting, but keeps large binaries out of the working tree; soft 100 MB/file limit lifts to 2 GB.
- **Object storage / CDN** — AWS S3 / Cloudflare R2 / Google Cloud Storage / Bunny / Backblaze B2.
  Direct `https://<bucket>.../<key>.mp4`; proper `Content-Range`, CORS and `Content-Type`. Recommended
  for a real study.
- **oTree `{{ static }}`** — serve the committed files locally instead of over the network. Removes the
  external dependency but bloats the `.otreezip` (see UPDATE E). Requires a template change to
  `{{ if i.video_is_url }}{{ i.media }}{{ else }}{{ static i.media }}{{ endif }}` plus a `video_is_url`
  flag in `preprocessing()`.

---

## UPDATE E — Purge the committed videos from git history

### Why
`DICE/DICE/static/videos/` holds ~70 MB of `.mp4` (incl. `Interstellar.mp4` at 36 MB). Every clone/
fetch carries them and `Interstellar.mp4` trips GitHub's 50 MB push warning and permanently bloats
history.

### ⚠️ Dependency
These files **are** what the current raw URLs serve (this repo *is* `Alebrex99/DICE`). **Do NOT purge
them while the CSV still points at `raw.githubusercontent.com/.../static/videos/...`** or every video
404s. Do UPDATE D first (move hosting to Releases/CDN and update the CSV URLs), then purge.

### Steps (after hosting is moved)
```bash
# preferred: git-filter-repo
pip install git-filter-repo
git filter-repo --path DICE/DICE/static/videos/ --invert-paths

# or BFG
# bfg --delete-folders videos

git push --force        # coordinate: every collaborator must re-clone afterwards
```
Then add `DICE/DICE/static/videos/` (or `*.mp4`) to `.gitignore` if the files are no longer needed
in the tree.

---

## UPDATE F — Comment / reply interaction logging

### Why
The Instagram comment section (static comments + threaded replies from the CSV) is fully rendered,
but every interaction is **frontend-only** — nothing is recorded:
- comment/reply heart clicks (`insta_comments.js`, `.comment-like-button`) move the visible count only;
- "View replies (N)" expand/collapse clicks (`.view-replies-btn`) are not tracked;
- there is no per-comment "seen" measurement.

If comment engagement is a study variable, add a collection layer (same 3-part pattern as likes/replies).

### Files to change (3 coordinated edits — missing any one silently drops the data)
1. `T_Feed_Insta.html` — hidden input, e.g. `<input type="hidden" name="comment_likes_data" id="comment_likes_data">`.
2. `insta_comments.js` — give each `.comment-like-button` a `data-doc-id` + comment `idx`, and collect
   `{doc_id, comment_idx, liked}` (optionally reply-expand events) into the hidden input on form submit.
3. `__init__.py` — `comment_likes_data = models.LongStringField(blank=True)` on `Player`, add it to
   `C_Feed.get_form_fields()`, and optionally to `custom_export()`.

### Note
The per-comment `like_count` now comes from `comment_likes_count_i` (a manual integer, fixed per comment —
no longer randomized). The seed itself carries no behavioural signal; only the participant's click deltas
(which comments they liked/unliked) would be meaningful if collected.

---

## UPDATE G — Stronger cleanup for malformed comment references

### Why
`build_comments()` resolves threaded replies in one sequential pass, then runs a 2-line safety net that
empties every reply's own `subcomments` list. That makes the 1-level cap a **guarantee** (2 levels can
never render), but in one malformed case it silently drops a comment.

**The case — a "backward" reference:** `comment_0 → comment_1` **and** `comment_2 → comment_0`.
At `j=0` comment_0 has not been claimed yet (comment_2 is read later), so it is treated as a parent and
claims comment_1. At `j=2`, comment_2 claims comment_0. Now comment_0 is a reply that still carries
comment_1 → 2 levels. The safety net empties comment_0's list, so the render is correct
(comment_2 → comment_0, flat), but **comment_1 stays marked as a reply while no parent holds it any more
→ it is not rendered anywhere.**

This cannot happen when subcomments are placed at the END of the row with the HIGHEST indices (the
documented CSV convention), because then every reference points forward. UPDATE G is only worth applying
if hand-entered data cannot be trusted to follow that convention.

### The fix — replace the 2-line net with these ~5 lines
Derive `replies` from what is **actually rendered**, instead of trusting the earlier marking:
```python
        # 1) a reply cannot carry replies of its own
        for j in replies:
            all_comments[j]['subcomments'] = []

        # 2) a comment is a reply only if a surviving top-level parent still holds it
        held = set()
        for j in comment_slot_ids:
            if j in all_comments and j not in replies:
                held.update(sc['idx'] for sc in all_comments[j]['subcomments'])
        replies = held
```

### Result
On the malformed case: comment_2 → comment_0 (flat, 1 level) **and comment_1 is restored as a normal
top-level comment** instead of disappearing. On well-formed data both versions are identical no-ops.

### Known limit
With *chained* backward references (`comment_0 → comment_1`, `comment_2 → comment_0`,
`comment_3 → comment_2`) some parent→reply links are still dropped — all comments stay visible, they just
lose their nesting. Fully resolving an arbitrary reference graph would require a fixpoint computation
(which can oscillate on cycles) and is not worth the complexity for hand-entered stimuli.
