# DICE — Video Feature: Instructions

This document explains how video support works in the current version of DICE, and how to add videos to a feed for the **Instagram** and **Stories** simulations.

---

## 1. Where the feed data comes from

The feed is driven by a CSV file. The active path is configured in:

```
DICE/DICE/settings.py  →  data_path = "DICE/static/data/sample_feed.csv"
```

The default CSV is:

```
DICE/DICE/DICE/static/data/sample_feed.csv
```

You can point `data_path` to a different local file or a remote URL (GitHub raw, Google Sheets export, Google Drive). The delimiter is `;` by default.

> **After every change to the CSV or to `settings.py`, run `otree resetdb` and create a new session. The preprocessing runs once at session creation — old sessions retain the old data.**

---

## 2. How to add a video to a post

In the CSV, the `media` column controls what appears as the post's visual content. To show a video instead of an image, put a video URL in that column.

### Supported video sources

| Source | URL format in `media` column | Notes |
|---|---|---|
| **GitHub raw** (recommended) | `https://raw.githubusercontent.com/<user>/<repo>/<branch>/<path>.mp4` | Full autoplay + pause control. Repo must be public. 100 MB soft limit per file. |
| **Google Drive** | `https://drive.google.com/file/d/<FILE_ID>/view` or `https://drive.google.com/file/d/<FILE_ID>/preview` or `https://drive.google.com/uc?id=<FILE_ID>` | See limitations below. File **must** be shared as "Anyone with the link → Viewer". |
| **Other direct URL** | Any URL ending in `.mp4`, `.webm`, `.ogg`, `.mov`, `.m4v` | Treated as native video (same as GitHub raw). |

### What the backend does automatically (`__init__.py` preprocessing)

When the session is created, `preprocessing()` reads the `media` column and adds these columns to the feed:

- `pic_available` — `True` if `media` contains any URL
- `is_video` — `True` if the URL ends with a video extension (`.mp4`, `.webm`, etc.)
- `is_drive` — `True` if the URL contains `drive.google.com`
- `drive_embed` — the `/preview` embed URL built from the Drive file ID (used for the iframe `src`)
- `video_available` — `True` if the post has a playable video (either extension-detected or Drive)
- `image_available` — `True` if the post has an image (not a video)

You do **not** need to add these columns yourself — they are computed from `media` automatically.

---

## 3. Instagram feed — video behaviour

**Relevant files:**
- Template: `DICE/DICE/DICE/T_Item_Insta.html`
- JS autoplay: `DICE/DICE/DICE/static/js/insta_video.js`

### How it works

`insta_video.js` uses an `IntersectionObserver` to watch all video/iframe elements in the feed. When an element reaches **50% visibility** in the scroll container, the observer fires:

| Element type | On enter (≥ 50% visible) | On exit (< 50% visible) |
|---|---|---|
| `<video>` (GitHub/CDN) | `video.play()` — starts muted | `video.pause()` |
| `<iframe>` (Drive) | injects `src` from `data-drive-src` → Drive loads | removes `src` → Drive stops |

The observer uses `root: null` (the browser viewport) as the scroll root.

### What the template renders

- **GitHub/CDN video** → native `<video>` element with `muted loop playsinline controls`. Autoplay is reliable because the video is muted.
- **Google Drive video** → `<iframe data-drive-src="...?autoplay=1">` without an initial `src`. The observer injects the `src` when the post scrolls into view.
- **Image** → standard `<img>` tag.

### Google Drive limitations in Instagram

- **Autoplay is not guaranteed.** Browsers allow autoplay only after a user gesture (click/tap). Scroll is not a gesture. If the user has not clicked anything before reaching the Drive post, Drive may not autostart.
- **The video is clickable** (no tap-zones cover it, unlike Stories), so the user can manually press play.
- **File must be public:** share the file as "Anyone with the link → Viewer" on Google Drive. If not public, Drive redirects to its homepage and the iframe shows a CSP error.

**Recommendation: use GitHub-raw `.mp4` for reliable autoplay in Instagram.**

---

## 4. Stories simulation — video behaviour

**Relevant files:**
- Template: `DICE/DICE/DICE/T_Item_Stories.html`
- Feed template: `DICE/DICE/DICE/T_Feed_Stories.html`
- JS: `DICE/DICE/DICE/static/js/stories.js`
- CSS: `DICE/DICE/DICE/static/css/styles_stories.css`

### How it works

Stories use a **slide-based navigation**: all slides are in the DOM at load time, only one has the `.active` class and is visible. There is no scroll — navigation is by tapping the left/right tap-zones or waiting for the progress timer.

When a slide is activated (`activateSlide()`), `stories.js` calls:

- `playCurrentSlideVideo()` — finds `video.stories-bg-video` in the active slide and calls `video.play()`. If the video is not yet buffered, retries on the `canplay` event.
- `activateDriveIframe()` — finds `iframe[data-drive-src]` in the active slide and sets its `src`.

When a slide is deactivated:

- The outgoing `<video>` is paused and reset to `currentTime = 0`.
- The outgoing `<iframe>` has its `src` cleared (stops Drive playback).

### First slide special case

The first slide is activated with `startTimer = false` (timer and video are not started yet because the loading screen is still showing). A `MutationObserver` watches for the loading screen to receive the `d-none` class (hidden). When it fires:

1. `playCurrentSlideVideo()` is called for the first slide.
2. `activateDriveIframe()` is called.
3. `startProgressAnimation()` starts the progress bar.

### Audio

All videos start **muted** (browser autoplay policy requires this). A speaker button (top-right of the author row) toggles audio for all native `<video>` elements at once. Toggling audio on an iframe Drive is **not possible** (cross-origin restriction).

### Story duration

Controlled by `story_duration` in `settings.py`:

```python
# Default for all sessions (SESSION_CONFIG_DEFAULTS):
story_duration = 7   # seconds

# Per-session override (inside a SESSION_CONFIGS dict):
dict(
    name='Stories',
    channel_type='Stories',
    story_duration=20,   # overrides the default for this session only
)
```

The timer always uses `story_duration` regardless of actual video length. A video shorter than `story_duration` will loop; a longer one will be cut off.

### What the template renders

- **GitHub/CDN video** → `<video class="stories-bg-video" muted playsinline loop>`. Fills the slide with `object-fit: contain` and a black background. Controlled by `stories.js`.
- **Google Drive video** → `<iframe data-drive-src="...?autoplay=1">` (no initial `src`). Filled to the full slide with inline styles. `stories.js` injects the `src` on slide activation.
- **Image** → two `<img>` tags: a blurred background fill and a sharp foreground image.

### Google Drive in Stories

Drive autoplay works in Stories because **navigating to the slide requires a tap** (the tap-zones), and a tap is a valid user gesture that unlocks autoplay. The browser authorises autoplay for the iframe loaded immediately after that tap.

However:
- The tap-zones (z-index 9) cover the entire slide including the iframe (z-index 1). The user **cannot click** the Drive player's internal controls.
- The mute button does not affect Drive iframes (cross-origin).

---

## 5. Quick reference: adding a video post step by step

1. **Prepare the video URL.**
   - GitHub: upload to a public repo, use the raw URL: `https://raw.githubusercontent.com/<user>/<repo>/main/<file>.mp4`
   - Drive: share as "Anyone with the link → Viewer", copy the file URL in any supported format.

2. **Edit the CSV** (`DICE/DICE/DICE/static/data/sample_feed.csv` or your custom file). Add or edit a row, setting `media` to the video URL. Leave `alt_text` descriptive. Example row:

   ```
   10;01.06.25 10:00;Check out this clip!;https://raw.githubusercontent.com/user/repo/main/clip.mp4;A short demo clip.;0;0;0;DemoUser;@DemoUser;Demo account.;https://...profile.jpg;1000;0;0;;A;10
   ```

3. **Run `otree resetdb`** from the `DICE/DICE/` directory and start a new session.

4. **Hard-refresh the browser** (Ctrl+Shift+R) to bypass cached JS/CSS.

5. Open the **Demo page** (`http://localhost:8000`) and pick **Instagram** or **Stories**.

---

## 6. Key file map

| What | File |
|---|---|
| CSV feed data (default) | `DICE/DICE/DICE/static/data/sample_feed.csv` |
| Feed path config | `DICE/DICE/settings.py` → `data_path` |
| Story duration config | `DICE/DICE/settings.py` → `story_duration` |
| Video preprocessing (Python) | `DICE/DICE/DICE/__init__.py` → `preprocessing()` |
| Instagram post template | `DICE/DICE/DICE/T_Item_Insta.html` |
| Instagram autoplay JS | `DICE/DICE/DICE/static/js/insta_video.js` |
| Stories slide template | `DICE/DICE/DICE/T_Item_Stories.html` |
| Stories feed template | `DICE/DICE/DICE/T_Feed_Stories.html` |
| Stories JS (navigation + video) | `DICE/DICE/DICE/static/js/stories.js` |
| Stories CSS | `DICE/DICE/DICE/static/css/styles_stories.css` |
