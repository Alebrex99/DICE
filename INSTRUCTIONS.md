# DICE — Video Feature: Instructions

---

## 1. Feed data

The feed is driven by a CSV file. The active path is set in:

```
DICE/DICE/settings.py  →  data_path = "DICE/static/data/sample_feed.csv"
```

You can also point `data_path` to a GitHub raw URL or a Google Sheets export URL. Delimiter is `;` by default.

> **After every CSV or `settings.py` change: run `otree resetdb`, create a new session, and hard-refresh the browser (Ctrl+Shift+R).**

---

## 2. Adding a video post

Put a video URL in the `media` column of the CSV. Supported formats: any direct URL ending in `.mp4`, `.webm`, `.ogg`, `.mov`, `.m4v`.

**Recommended source:** GitHub raw URL from a public repository:
```
https://raw.githubusercontent.com/<user>/<repo>/<branch>/<file>.mp4
```
Files up to ~100 MB work reliably. Autoplay is fully supported (video is muted).

The backend (`preprocessing()` in `__init__.py`) automatically computes:
- `is_video` — True when the URL has a video extension
- `video_available` — True when the post has a playable video
- `image_available` — True when the post has an image (not a video)

Do not add these columns manually.

---

## 3. Instagram feed — video behaviour

**Files:** [T_Item_Insta.html](DICE/DICE/DICE/T_Item_Insta.html), [insta_video.js](DICE/DICE/DICE/static/js/insta_video.js)

`insta_video.js` uses an `IntersectionObserver` (threshold 0.5) watching all `<video data-doc-id>` elements. When a video reaches 50% visibility it calls `play()`; when it leaves, `pause()`. Muted videos always autoplay reliably.

The template renders:
- **Video post** → `<video muted loop playsinline controls>`
- **Image post** → `<img>`

---

## 4. Stories simulation — video behaviour

**Files:** [T_Item_Stories.html](DICE/DICE/DICE/T_Item_Stories.html), [stories.js](DICE/DICE/DICE/static/js/stories.js), [styles_stories.css](DICE/DICE/DICE/static/css/styles_stories.css)

Stories are slide-based: all slides are in the DOM, only the `.active` one is visible. Navigation is by tapping left/right tap-zones or waiting for the timer.

On slide activation (`activateSlide()`), `stories.js` calls `playCurrentSlideVideo()` which finds `video.stories-bg-video` in the active slide and calls `play()`. On deactivation the outgoing video is paused and reset to `currentTime = 0`.

**First slide:** activated with `startTimer = false`. A `MutationObserver` watches for the loading screen to disappear, then starts the video and progress bar.

**Audio:** all videos start muted. The speaker button (top-right) toggles audio for all `<video>` elements at once.

**Story duration:** controlled by `story_duration` in `settings.py` (seconds). The timer always uses this value regardless of video length — shorter videos loop, longer videos are cut off.

```python
# SESSION_CONFIG_DEFAULTS
story_duration = 7

# per-session override
dict(name='Stories', channel_type='Stories', story_duration=20)
```

The template renders:
- **Video post** → `<video class="stories-bg-video" muted playsinline loop>` filling the slide
- **Image post** → blurred background + sharp foreground `<img>`

---

## 5. Step-by-step: adding a video post

1. Upload your `.mp4` to a public GitHub repo and copy the raw URL.
2. Edit the CSV (`DICE/DICE/DICE/static/data/sample_feed.csv`). Set the `media` column to the raw URL.
3. Run `otree resetdb` from `DICE/DICE/` and create a new session.
4. Hard-refresh the browser and open **Instagram** or **Stories** from the Demo page.

---

## 6. Key file map

| What | File |
|---|---|
| CSV feed data (default) | `DICE/DICE/DICE/static/data/sample_feed.csv` |
| Feed path + story duration config | `DICE/DICE/settings.py` |
| Video preprocessing (Python) | `DICE/DICE/DICE/__init__.py` → `preprocessing()` |
| Instagram post template | `DICE/DICE/DICE/T_Item_Insta.html` |
| Instagram autoplay JS | `DICE/DICE/DICE/static/js/insta_video.js` |
| Stories slide template | `DICE/DICE/DICE/T_Item_Stories.html` |
| Stories feed template | `DICE/DICE/DICE/T_Feed_Stories.html` |
| Stories JS (navigation + video) | `DICE/DICE/DICE/static/js/stories.js` |
| Stories CSS | `DICE/DICE/DICE/static/css/styles_stories.css` |
