# FUTURE_UPDATES.md

Pending improvements for the Instagram video feature in the full DICE app.
All changes assume the current working state described in the **Current state** section below.

---

## Current state (as of last review)

### What is already implemented

**Backend — `DICE/DICE/DICE/__init__.py` inside `preprocessing()`**
```python
df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False)
video_ext = r'\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$'
df['is_video'] = df['media'].str.contains(video_ext, case=False, regex=True, na=False)
df['video_available'] = df['pic_available'] & df['is_video']
df['image_available'] = df['pic_available'] & ~df['is_video']
```

**Template — `DICE/DICE/DICE/T_Item_Insta.html`**
Both the organic post block and sponsored post block have the `{{ if i.video_available }}` branch
that renders a `<video>` tag with `controls muted loop playsinline preload="auto"`.
Images fall through to the original `<img>` tag.

**JavaScript — `DICE/DICE/DICE/static/js/insta_video.js`** (loaded in `C_Feed.html` under the Insta branch)
```javascript
document.addEventListener('DOMContentLoaded', function () {
    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            var video = entry.target;
            if (entry.isIntersecting) {
                video.play().catch(function () {});
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        observer.observe(v);
    });
});
```

### What is NOT yet implemented
- Mute/unmute overlay button on videos
- Google Drive URL support
- Video height cap in CSS
- Per-video play-time tracking (watch_time_data)

---

## UPDATE A — Mute/unmute overlay button

### Why
Videos currently autoplay muted and there is no way for the participant to hear the audio.
This adds an Instagram-style speaker icon overlaid on each video (bottom-right corner).
Tapping it toggles audio globally — once a user unmutes, all subsequent auto-played videos
also play with audio, which matches real Instagram behavior.

### Files to change

#### 1. `DICE/DICE/DICE/T_Item_Insta.html` — organic post block

Find the current organic video block (around line 138):
```html
                {{ if i.video_available }}
                <!--<video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                       data-doc-id="{{ i.doc_id }}"
                       controls playsinline preload="metadata">-->
                <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                       data-doc-id="{{ i.doc_id }}"
                       controls muted loop playsinline preload="auto">
                    <source src="{{ i.media }}" type="video/mp4">
                    Your browser does not support video playback.
                </video>
```
Replace with (remove `controls`, wrap in `position-relative` div, add mute button):
```html
                {{ if i.video_available }}
                <div class="position-relative">
                    <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                           data-doc-id="{{ i.doc_id }}"
                           muted loop playsinline preload="auto">
                        <source src="{{ i.media }}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>
                    <button class="insta-mute-btn" type="button" aria-label="Toggle mute">
                        <i class="bi bi-volume-mute-fill"></i>
                    </button>
                </div>
```

#### 2. `DICE/DICE/DICE/T_Item_Insta.html` — sponsored post block

Find the current sponsored video block (around line 39):
```html
                        {{ if i.video_available }}
                        <!--<video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                               data-doc-id="{{ i.doc_id }}"
                               controls playsinline preload="metadata">-->
                        <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                               data-doc-id="{{ i.doc_id }}"
                               controls muted loop playsinline preload="auto">
                            <source src="{{ i.media }}" type="video/mp4">
                        </video>
```
Replace with:
```html
                        {{ if i.video_available }}
                        <div class="position-relative">
                            <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                                   data-doc-id="{{ i.doc_id }}"
                                   muted loop playsinline preload="auto">
                                <source src="{{ i.media }}" type="video/mp4">
                            </video>
                            <button class="insta-mute-btn" type="button" aria-label="Toggle mute">
                                <i class="bi bi-volume-mute-fill"></i>
                            </button>
                        </div>
```

> **Note on sponsored videos:** the sponsored block has an `<a href="{{i.target}}">` wrapper around
> the media. With `controls` removed, tapping the video area will navigate to the ad target URL
> instead of toggling play. If sponsored videos should be playable clips rather than clickable ads,
> remove that `<a>` wrapper. If they should be ads, keep it — the mute button uses
> `e.stopPropagation()` (see JS below) so tapping the speaker won't trigger the link.

#### 3. `DICE/DICE/DICE/static/css/styles.css` — add mute button style

Add anywhere at the end of the file:
```css
.insta-mute-btn {
    position: absolute;
    bottom: 12px;
    right: 12px;
    background: rgba(0, 0, 0, 0.55);
    border: none;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;
    font-size: 14px;
    cursor: pointer;
    z-index: 10;
}
```

#### 4. `DICE/DICE/DICE/static/js/insta_video.js` — full replacement

Replace the entire current file content with:
```javascript
var audioEnabled = false; // starts muted, matching the <video muted> attribute

document.addEventListener('DOMContentLoaded', function () {

    // Play when ≥50% visible, pause when not. Respects current mute state.
    var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            var video = entry.target;
            if (entry.isIntersecting) {
                video.muted = !audioEnabled;
                video.play().catch(function () {});
            } else {
                video.pause();
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        observer.observe(v);
    });

    // Global mute toggle: clicking any mute button flips state for all videos
    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.insta-mute-btn');
        if (!btn) return;
        e.stopPropagation(); // prevent triggering <a> wrapper on sponsored posts

        audioEnabled = !audioEnabled;

        document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
            v.muted = !audioEnabled;
        });

        document.querySelectorAll('.insta-mute-btn i').forEach(function (icon) {
            icon.className = audioEnabled ? 'bi bi-volume-up-fill' : 'bi bi-volume-mute-fill';
        });
    });

});
```

**No change needed to `C_Feed.html`** — `insta_video.js` is already registered there.

---

## UPDATE B — Google Drive video support

### Why
GitHub raw URLs work because they end in `.mp4` and the extension detection in `preprocessing()`
classifies them as video. Google Drive share links (`drive.google.com/file/d/.../view` or
`/uc?id=...`) carry **no file extension**, so the current regex misses them and they render
as broken `<img>` tags instead of video.

### Constraint
Drive serves an HTML virus-scan interstitial for files **larger than ~25 MB**, which breaks
the `<video>` tag entirely. Keep Drive videos **under 25 MB**, or use GitHub / a CDN for anything larger.
Drive also cannot be embedded in a `<video>` element directly — it must use an `<iframe>` with
the `/preview` embed URL. This means Drive videos have slightly different rendering
(iframe with Drive's own player) compared to GitHub raw videos (native browser `<video>`).

### Files to change

#### 1. `DICE/DICE/DICE/__init__.py` — extend the media classification block

Find the current VIDEO MODE block in `preprocessing()`:
```python
    # NEW
    df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
    df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False)
    video_ext = r'\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$'
    df['is_video'] = df['media'].str.contains(video_ext, case=False, regex=True, na=False)
    df['video_available'] = df['pic_available'] & df['is_video']
    df['image_available'] = df['pic_available'] & ~df['is_video']
```
Replace with:
```python
    df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
    df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False)

    # Extension-based video detection (GitHub raw, CDNs)
    video_ext = r'\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$'
    df['is_video'] = df['media'].str.contains(video_ext, case=False, regex=True, na=False)

    # Google Drive detection — no file extension, must use iframe /preview
    df['is_drive'] = df['media'].str.contains('drive.google.com', na=False)

    # Build the Drive /preview embed URL for each Drive row
    def drive_preview(url):
        if 'drive.google.com' not in str(url):
            return ''
        file_id = ''
        if '/file/d/' in url:
            file_id = url.split('/file/d/')[1].split('/')[0]
        elif 'id=' in url:
            file_id = url.split('id=')[1].split('&')[0]
        return f'https://drive.google.com/file/d/{file_id}/preview' if file_id else ''

    df['drive_embed'] = df['media'].apply(drive_preview)

    # video_available = has a playable URL (either extension-detected or Drive)
    df['video_available'] = df['pic_available'] & (df['is_video'] | df['is_drive'])
    df['image_available'] = df['pic_available'] & ~df['is_video'] & ~df['is_drive']
```

#### 2. `DICE/DICE/DICE/T_Item_Insta.html` — extend the video branch in both post blocks

In both the **organic** and **sponsored** blocks, find the existing video branch:
```html
                    <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                           data-doc-id="{{ i.doc_id }}"
                           muted loop playsinline preload="auto">
                        <source src="{{ i.media }}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>
```
Replace with (adds a Drive `<iframe>` sub-branch):
```html
                    {{ if i.is_drive }}
                    <div class="ratio ratio-1x1 mt-2">
                        <iframe src="{{ i.drive_embed }}"
                                allow="autoplay"
                                allowfullscreen
                                style="border:0; width:100%;">
                        </iframe>
                    </div>
                    {{ else }}
                    <video class="w-100 img-fluid mt-2" style="object-fit: cover;"
                           data-doc-id="{{ i.doc_id }}"
                           muted loop playsinline preload="auto">
                        <source src="{{ i.media }}" type="video/mp4">
                        Your browser does not support video playback.
                    </video>
                    {{ endif }}
```

> **Mute button note:** the mute button (UPDATE A) only applies to native `<video>` elements.
> Drive iframes have their own internal player controls; the `insta-mute-btn` button should
> be omitted (or hidden via CSS) when `i.is_drive` is true. Adjust the wrapper accordingly.

#### CSV usage
Both URL formats work in the `media` column:
```
# Share link — auto-converted to /preview
https://drive.google.com/file/d/1AbCdEfGhIjKlMnOpQrStUvWxYz/view?usp=sharing

# Direct download link — also detected as Drive
https://drive.google.com/uc?id=1AbCdEfGhIjKlMnOpQrStUvWxYz
```

---

## UPDATE C — Video height cap (CSS)

### Why
A tall portrait video (e.g. 9:16 aspect ratio) can dominate the feed and push content far
off-screen. Instagram caps in-feed media height at roughly 585 px for portrait content.

### File to change

**`DICE/DICE/DICE/static/css/styles.css`** — add alongside the `.insta-mute-btn` rule from UPDATE A:
```css
.insta-post video {
    max-height: 585px;
    background: #000;  /* letterbox bars for landscape video */
}
```

No template or backend changes needed.

---

## UPDATE D — Per-video play-time tracking (watch_time_data)

### Why
The existing `dwell.js` + `viewport_data` field records how long each post was *visible* in
the viewport (including paused / scrolled-past time). For video research you may want the
actual **play seconds** (paused time excluded), equivalent to DICE-tiktok's `watch_time_seconds`.

### Files to change (5 coordinated edits — all 5 required, missing any one silently drops data)

#### 1. `DICE/DICE/DICE/__init__.py` — add a Player field (after line 53, inside `class Player`)
```python
    watch_time_data = models.LongStringField(doc='per-video play seconds for Instagram videos.', blank=True)
```

#### 2. `DICE/DICE/DICE/__init__.py` — include the field in `C_Feed.get_form_fields()`

Find:
```python
        fields =  ['likes_data', 'replies_data', 'promoted_post_clicks', 'touch_capability', 'device_type', 'screen_resolution']
```
Replace with:
```python
        fields =  ['likes_data', 'replies_data', 'promoted_post_clicks', 'touch_capability', 'device_type', 'screen_resolution', 'watch_time_data']
```

#### 3. `DICE/DICE/DICE/T_Feed_Insta.html` — add a hidden input (alongside the other hidden fields, lines 4–13)
```html
<input type="hidden" name="watch_time_data" id="watch_time_data" value="">
```

#### 4. `DICE/DICE/DICE/static/js/insta_video.js` — add play-time tracking

Extend the file (if UPDATE A is also applied, add this inside the existing
`DOMContentLoaded` listener, after the `observer` setup block):
```javascript
    // Play-time tracking per video
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
            if (d.playStartTime !== null) {
                d.totalSeconds += (now - d.playStartTime) / 1000;
                d.playStartTime = null;
            }
        });
    }

    // Attach play/pause listeners to every video
    document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
        var docId = parseInt(v.dataset.docId);
        v.addEventListener('play',  function () { onVideoPlay(docId); });
        v.addEventListener('pause', function () { onVideoPause(docId); });
        v.addEventListener('ended', function () { onVideoPause(docId); });
    });

    // Pause timing when tab is hidden
    document.addEventListener('visibilitychange', function () {
        if (document.hidden) {
            flushPlayData();
        } else {
            document.querySelectorAll('video[data-doc-id]').forEach(function (v) {
                if (!v.paused) {
                    onVideoPlay(parseInt(v.dataset.docId));
                }
            });
        }
    });

    // Serialize and write to hidden field on submit
    document.querySelectorAll('button[type="submit"]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            flushPlayData();
            var result = Object.keys(playData).map(function (docId) {
                return { doc_id: parseInt(docId), duration: Number(playData[docId].totalSeconds.toFixed(3)) };
            });
            var field = document.getElementById('watch_time_data');
            if (field) field.value = JSON.stringify(result);
        });
    });
```

#### 5. `DICE/DICE/DICE/__init__.py` — include `watch_time_data` in `custom_export()` (optional)

Find the header row yield:
```python
    yield ['session', 'participant_code', 'participant_label', 'participant_in_session', 'condition', 'item_sequence',
           'scroll_sequence', 'item_dwell_time', 'likes', 'replies']
```
Replace with:
```python
    yield ['session', 'participant_code', 'participant_label', 'participant_in_session', 'condition', 'item_sequence',
           'scroll_sequence', 'item_dwell_time', 'likes', 'replies', 'watch_time_data']
```
And in the data row yield, add `p.watch_time_data` at the end.

### Data format collected
`watch_time_data` is stored as JSON on the Player. Each entry is one video:
```json
[
  {"doc_id": 0, "duration": 12.450},
  {"doc_id": 3, "duration": 4.100}
]
```
Only videos the participant actually played appear. Videos scrolled past without interaction
are absent (duration = 0 is not written, unlike DICE-tiktok which writes a row for every video).

---

## UPDATE E — Uniform `<video>` tag for Drive (ATTEMPTED — REVERTED)

### What was attempted and why

The goal was to make Google Drive videos behave identically to GitHub raw videos: autoplay
on scroll via the `IntersectionObserver` in `insta_video.js`. The iframe approach (current
working state from UPDATE B) cannot be controlled by JavaScript due to the browser's
same-origin policy — the Drive player runs on `drive.google.com` and exposes no postMessage
API for play/pause/mute.

The attempt had two parts:

**`__init__.py`** — replaced `drive_preview()` with a `drive_direct()` function that
normalised Drive sharing URLs to the direct-download format and wrote them back into the
`media` column:
```python
def drive_direct(url):
    if 'drive.google.com' not in str(url):
        return url
    if '/file/d/' in url:
        file_id = url.split('/file/d/')[1].split('/')[0]
        return f'https://drive.google.com/uc?id={file_id}'
    if 'id=' in url:
        file_id = url.split('id=')[1].split('&')[0]
        return f'https://drive.google.com/uc?id={file_id}'
    return url
df.loc[df['is_drive'], 'media'] = df.loc[df['is_drive'], 'media'].apply(drive_direct)
```

**`T_Item_Insta.html`** — removed the `{{if i.is_drive}}` iframe sub-branch so all
`video_available` items (GitHub and Drive alike) rendered through the same `<video>` tag:
```html
{{ if i.video_available }}
<video class="w-100 img-fluid mt-2" style="object-fit: cover;"
    data-doc-id="{{ i.doc_id }}"
    muted loop playsinline preload="auto">
    <source src="{{ i.media }}" type="video/mp4">
</video>
{{ else }}
<img ...>
{{ endif }}
```

### Why it failed

Google Drive's `uc?id=FILE_ID` endpoint does not serve files with the HTTP response headers
that the browser's native video engine requires:

| Requirement | Drive `uc?id=` behaviour |
|---|---|
| `Content-Range` (byte-range requests for seeking/streaming) | Not supported → browser cannot seek or buffer ahead |
| `Content-Type: video/mp4` | Sometimes served as `application/octet-stream` |
| Inline playback (`Content-Disposition: inline`) | Served as `attachment` → browser tries to download, not play |
| Cross-origin media (`CORS`) | No `Access-Control-Allow-Origin` header on some redirects |
| Files > ~25 MB | Returns an HTML virus-scan confirmation page instead of video bytes |

**Observed result:** `<video>` element displayed a black rectangle with native controls.
Controls appeared but were unresponsive. `IntersectionObserver` called `.play()` correctly,
but the Promise rejected silently (`.catch(function(){})`) because no valid media stream
was available. The video never played and no error was shown to the user.

The `uc?id=` tricks and `confirm=t` bypass parameters that occasionally appear in forum posts
are undocumented, unstable across Google updates, and still fail for large files.

### Current state after revert

Both files were reverted to the working UPDATE B state:
- `drive_preview()` in `__init__.py` builds `/preview` embed URLs → stored in `drive_embed` column
- `T_Item_Insta.html` has the `{{if i.is_drive}}` iframe sub-branch in both sponsored and organic blocks
- Drive videos display via Drive's own iframe player (manual play, no autoplay, Drive controls)
- GitHub raw `.mp4` videos continue to use the `<video>` tag with full autoplay and mute control

### Paths forward (if uniform autoplay for Drive is needed in the future)

**Option 1 — Move Drive videos to GitHub raw (recommended)**
Simply upload the `.mp4` files to the GitHub repo and use
`https://raw.githubusercontent.com/<user>/<repo>/main/<path>.mp4` in the CSV.
Already works perfectly. No code change needed. GitHub has a soft 100 MB per-file
limit; use GitHub Releases (`/releases/download/`) for larger files.

**Option 2 — Use a real CDN or object storage**
Services that serve files with proper `Content-Range`, CORS, and `Content-Type` headers:
- **AWS S3** (public bucket) or **Cloudflare R2** — direct `https://<bucket>.s3.amazonaws.com/<key>.mp4`
- **Google Cloud Storage** (public bucket) — `https://storage.googleapis.com/<bucket>/<key>.mp4`
- **Bunny CDN**, **Backblaze B2** — similar direct URLs

All of these work directly in a `<video>` tag without any code change — just put the URL
in the CSV `media` column. The extension detection (`video_ext` regex) already handles them.

**Option 3 — Server-side proxy in oTree**
Add a page/endpoint in oTree that fetches the Drive file server-side and streams it to
the client. The browser then sees a same-origin response with correct headers.
Significant complexity: needs an extra oTree `Page` or Django view, service account
credentials (Google Drive API), and streaming logic. Not practical for a typical
experiment deployment.

**Option 4 — Accept Drive as iframe, add a CSS workaround for autoplay appearance**
Keep the current iframe approach but set `autoplay=1` as a URL parameter on the
`/preview` embed URL: `https://drive.google.com/file/d/{file_id}/preview?autoplay=1`.
Drive's embedded player does honour `autoplay=1` in some browsers/contexts — it starts
playback when the iframe loads, which gives a rough approximation of autoplay even though
the `IntersectionObserver` cannot control it. The video will play immediately when the
page loads (not scroll-triggered). To combine this with scroll-triggered behaviour,
swap the iframe `src` on intersection using JS (add/remove `?autoplay=1` param):
```javascript
// Approximate scroll-autoplay for Drive iframes (no pause on scroll-out)
var iframeObserver = new IntersectionObserver(function(entries) {
    entries.forEach(function(entry) {
        var iframe = entry.target;
        var base = iframe.dataset.src; // store original src in data-src
        if (entry.isIntersecting) {
            iframe.src = base + '?autoplay=1';
        } else {
            iframe.src = base; // reload without autoplay → effectively pauses
        }
    });
}, { threshold: 0.5 });
document.querySelectorAll('iframe[data-src]').forEach(function(f) {
    iframeObserver.observe(f);
});
```
Caveats: reloading the iframe `src` causes a full re-fetch of the Drive page on each
scroll event (flash/flicker), no mute control, and behaviour varies by browser. Acceptable
only for rough demos, not for a clean research instrument.

### Recommendation

For a behavioral experiment where consistent UX matters, **Option 1 or 2** is the only
reliable path. Drive was not designed as a video CDN. Use it for CSV/data file hosting
(which `read_feed` handles well) but host video files on GitHub raw or a proper CDN.
