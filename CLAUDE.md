# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DICE (Digital Interface for Controlled Experiments) is an **oTree 5.x** app that simulates social media feeds (Twitter/X, Instagram, LinkedIn, Stories, Generic) for academic behavioral research. Participants scroll through a realistic-looking feed, and the app records their behavioral data (dwell time, scroll sequence, likes, replies) before redirecting them to an external survey.

## Running the App

The `.venv` is at the repo root. All `otree` commands must be run from the **`DICE/`** subdirectory (the oTree project root, which contains `settings.py`):

```bash
# Activate the venv first (Windows)
.venv\Scripts\activate

cd DICE
otree devserver          # local development server (default: http://localhost:8000)
otree devserver 8001     # on a specific port
```

For production (matches the Procfile):
```bash
otree prodserver1of2     # web process
otree prodserver2of2     # worker process
```

Reset the database (wipes all session data):
```bash
otree resetdb
```

Package the app for deployment to oTree Hub:
```bash
otree zip                # produces DICE.otreezip in the project root
```

oTree has no separate build or lint step. There is no test suite in this repo.

> **Note:** `.python-version` (used by pyenv) specifies `3.12`, while `runtime.txt` (used by Heroku-style deploys) specifies `3.11.9`. The local venv was created with 3.12; production targets 3.11.9.

## Architecture

### Directory Layout

```
DICE/               ← oTree project root (settings.py, requirements.txt)
  DICE/             ← oTree app
    __init__.py     ← ALL Python logic: models, session creation, page classes, data export
    A_Intro.html    ← Welcome/consent page
    B_Briefing.html ← Optional briefing (skipped if briefing='' or skip_briefing=True)
    C_Feed.html     ← Main feed page (scripts/styles; includes subsession.FEED at runtime)
    D_Redirect.html ← Post-feed redirect to external survey
    D_Debrief.html  ← Alternative ending when no survey_link is set
    T_Feed_*.html   ← Feed layout templates (one per channel type)
    T_Item_*.html   ← Individual post/item templates (one per channel type)
    T_*.html        ← Other reusable template fragments (consent, trending topics, banner ads)
    static/
      js/           ← All behavioral tracking scripts
      css/          ← Channel-specific styles and preloader animations
      data/         ← Sample CSV feed files
  _static/global/   ← Project-level static files (overrides app-level if same name)
  _templates/global/Page.html  ← Base page template (extends otree's Page.html)
  settings.py       ← SESSION_CONFIGS, SESSION_CONFIG_DEFAULTS
```

### Data Flow

1. **Session creation** (`creating_session` in `__init__.py`):
   - Reads a CSV from `data_path` (supports local paths, GitHub raw URLs, Google Sheets URLs, Google Drive URLs)
   - Preprocesses: parses dates, highlights hashtags/mentions with `<span>` tags, fills in fallback profile icons
   - Assigns each player a shuffled, condition-filtered copy of the feed in `participant.tweets` (a pandas DataFrame)
   - Sets `subsession.FEED` to `"DICE/T_Feed_{channel_type}.html"`

2. **C_Feed page** (`C_Feed` class + `C_Feed.html`):
   - `vars_for_template` passes `tweets` as `dict` (index→row) to the template
   - `C_Feed.html` includes `{{ subsession.FEED }}` at runtime, which renders the appropriate `T_Feed_*.html`
   - `T_Feed_*.html` loops over `tweets.values()` and includes the corresponding `T_Item_*.html` for each post
   - Hidden `<input>` fields collect behavioral data from JS

3. **JavaScript tracking** (loaded conditionally in `C_Feed.html`):
   - `dwell.js` — IntersectionObserver that measures how long each feed item is visible (writes to `#viewport_data`)
   - `rowheights.js` — records rendered height of each row (writes to `#rowheight_data`)
   - `scrolling.js` — tracks scroll order (writes to `#scroll_sequence`)
   - `like_button.js` — records like interactions (writes to `#likes_data`)
   - `stories.js` / `insta_feed.js` / `swipes.js` — channel-specific navigation behaviors
   - `interactions.js` — frontend-only repost/share toggles (not recorded server-side)

### Channel Types and Templates

| `channel_type` in config | Feed template | Item template |
|---|---|---|
| `Twitter` | `T_Feed_Twitter.html` | `T_Item_Twitter.html` |
| `Twitter_Replies` | `T_Feed_Twitter_Replies.html` | `T_Item_Twitter.html` |
| `Insta` | `T_Feed_Insta.html` | `T_Item_Insta.html` |
| `Stories` | `T_Feed_Stories.html` | `T_Item_Stories.html` |
| `Linkedin` | `T_Feed_Linkedin.html` | `T_Item_Linkedin.html` |
| `Generic` | `T_Feed_Generic.html` | `T_Item_Generic.html` |

The `T_Feed_Twitter_Replies.html` layout is automatically selected (overrides Twitter) when the CSV contains a column `commented_post` with exactly one row set to `1` for the player's condition.

### CSV Feed Data Format

Required columns: `doc_id`, `datetime`, `text`, `username`, `handle`, `user_image`, `user_description`, `user_followers`, `replies`, `reposts`, `likes`, `media`

Optional columns: `condition` (for A/B splits, named by `condition_col` config), `sponsored` (renders as promoted post), `commented_post` (marks the post being replied to in Replies layout), `sequence` (pin a post to a specific position; others are shuffled around it), `alt_text` (image accessibility)

### Key Session Config Parameters

Defined in `settings.py` under `SESSION_CONFIG_DEFAULTS` and overridable per session in `SESSION_CONFIGS`:

- `channel_type` — which platform UI to render
- `data_path` — CSV URL or path (supports GitHub raw, Google Sheets export URL, Google Drive)
- `delimiter` — CSV field separator (default `;`)
- `condition_col` — column name holding A/B condition labels
- `dwell_threshold` — integer 0–100; percentage of an item that must be visible to count as "viewed" (passed to `IntersectionObserver` as a 0–1 ratio)
- `sort_by` — column name used to sort the feed before per-player randomization (default `'datetime'`)
- `story_duration` — seconds each story displays before auto-advancing
- `survey_link` — external Qualtrics/Prolific URL; empty string shows D_Debrief instead
- `url_param` — query param name appended to `survey_link` for participant ID (default `PROLIFIC_PID`)
- `skip_intro` / `skip_briefing` — booleans to bypass those pages
- `briefing` — raw HTML shown on B_Briefing; if empty, B_Briefing is skipped

### Data Export

`custom_export(players)` in `__init__.py` defines the custom oTree data export. Access via the oTree admin panel → Data → Custom export. Exports: session code, participant code/label, condition, item sequence, scroll sequence, dwell times, likes, and replies.

## oTree Template Syntax

oTree uses its own template engine (not Django's default). Key differences:
- Variables: `{{ variable }}` (double curly braces, no spaces required)
- Tags: `{{ if ... }} ... {{ elif ... }} ... {{ else }} ... {{ endif }}`
- Loops: `{{ for x in iterable }} ... {{ endfor }}`
- Include: `{{ include "app/template.html" }}`
- Static files: `{{ static 'path/to/file' }}` or Django-style `{% static '...' %}` (both work in oTree 5)
- JS variables from server: accessed via `js_vars` object in JS (populated by `js_vars()` method on the Page class)
