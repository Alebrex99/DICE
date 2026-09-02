from otree.api import *
import pandas as pd
import numpy as np
import re
import os
import random
import httplib2
import itertools



doc = """
Mimic social media feeds with DICE.
"""


class C(BaseConstants):
    NAME_IN_URL = 'DICE'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1

    RULES_TEMPLATE = "DICE/T_Rules.html"
    CONSENT_TEMPLATE = "DICE/T_Consent.html"
    TOPICS_TEMPLATE = "DICE/T_Trending_Topics.html"
    BANNER_TEMPLATE = "DICE/T_Banner_Ads.html"

    ITEM_TWITTER = "DICE/T_Item_Twitter.html"
    ITEM_LINKEDIN = "DICE/T_Item_Linkedin.html"
    ITEM_MASS_MEDIA = "DICE/T_Item_Mass_Media.html"
    ITEM_GENERIC = "DICE/T_Item_Generic.html"
    ITEM_INSTA = "DICE/T_Item_Insta.html"
    ITEM_STORIES = "DICE/T_Item_Stories.html"

class Subsession(BaseSubsession):
    feed_conditions = models.StringField(doc='indicates the feed condition a player is randomly assigned to')
    FEED = models.StringField(doc='')

class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # ad_condition = models.StringField(doc='indicates the ad condition a player is randomly assigned to')
    feed_condition = models.StringField(doc='indicates the feed condition a player is randomly assigned to')
    sequence = models.StringField(doc='prints the sequence of tweets based on doc_id')

    # cta = models.BooleanField(doc='indicates whether CTA was clicked or not')
    scroll_sequence = models.LongStringField(doc='tracks the sequence of feed items a participant scrolled through.')
    viewport_data = models.LongStringField(doc='tracks the time feed items were visible in a participants viewport.')
    rowheight_data = models.LongStringField(doc='tracks the time feed items were visible in a participants viewport.')
    likes_data = models.LongStringField(doc='tracks likes.', blank=True)
    replies_data = models.LongStringField(doc='tracks replies.', blank=True)
    promoted_post_clicks = models.LongStringField(doc='tracks the clicks on sponsored posts.', blank=True)


    touch_capability = models.BooleanField(doc="indicates whether a participant uses a touch device to access survey.",
                                           blank=True)
    device_type = models.StringField(doc="indicates the participant's device type based on screen width.",
                                           blank=True)
    screen_resolution = models.StringField(doc="indicates the participant's screen resolution, i.e., width x height.",
                                           blank=True)



# FUNCTIONS -----
def creating_session(subsession):
    subsession.FEED = "DICE/T_Feed_" + subsession.session.config['channel_type'] + ".html"

    # Load and preprocess data once but shuffle and assign for each player
    df = read_feed(path=subsession.session.config['data_path'], delim=subsession.session.config['delimiter'])
    processed_tweets = preprocessing(df, subsession.session.config)

    # Check if the file contains any conditions and assign groups to it
    condition = subsession.session.config['condition_col']
    if condition in processed_tweets.columns:
        feed_conditions = itertools.cycle(processed_tweets[condition].unique())
        subsession.feed_conditions = str(feed_conditions)

    for player in subsession.get_players():
        # Deep copy the DataFrame to ensure each player gets a unique shuffled version
        tweets = processed_tweets.copy()

        # Assign a condition to the player if conditions are present
        if condition in tweets.columns:
            player.feed_condition = next(feed_conditions)
            tweets = tweets[tweets[condition] == player.feed_condition]

        # Ensure the random number generator's seed is different for each player if needed
        # np.random.seed()  # Optionally reset the seed for true randomness

        # Initialize 'commented_post_exists' as False in case the column doesn't exist
        commented_post_exists = False

        # Only perform operations involving 'commented_post' if it exists in the DataFrame
        if 'commented_post' in tweets.columns:
            # Check for unique commented post
            commented_post_exists = ((tweets['commented_post'] == 1) & (tweets["condition"] == player.feed_condition)).sum() == 1
            if commented_post_exists == 1:
                player.subsession.FEED = "DICE/T_Feed_" + subsession.session.config['channel_type'] + "_Replies.html"

            # Set sequence to 1 for the row where commented_post is 1
            tweets.loc[tweets['commented_post'] == 1, 'sequence'] = 1
        else:
            tweets['commented_post'] = 0

        # Conditional update of sequence if there is a unique commented post and sequence is 1
        tweets.loc[(tweets['sequence'] == 1) & (tweets['commented_post'] == 0), 'sequence'] = \
            np.where(commented_post_exists, np.nan, 1)

        # Generate ranks and exclude used ranks
        ranks = np.arange(1, len(tweets) + 1)
        available_ranks = ranks[~np.isin(ranks, tweets['sequence'].dropna())]

        # Randomly sample available ranks to fill missing sequence values
        np.random.shuffle(available_ranks)
        missing_indices = tweets['sequence'].isnull()
        tweets.loc[missing_indices, 'sequence'] = available_ranks[:sum(missing_indices)]

        # Sort DataFrame by sequence
        tweets.sort_values(by='sequence', inplace=True)
        # Reset index after sorting to ensure clean sequential indices
        tweets.reset_index(drop=True, inplace=True)

        # Assign processed tweets to player-specific variable
        player.participant.tweets = tweets

        # Record the sequence for each player
        player.sequence = ', '.join(map(str, tweets['doc_id'].tolist()))
        # print(player.sequence)




# make pictures (if any) visible
def extract_first_url(text):
    urls = re.findall(r"(?P<url>https?://[\S]+)", str(text))
    if urls:
        return urls[0]
    return None

# check urls
# h = httplib2.Http()

# function that reads data
def read_feed(path, delim):
    if re.match(r'^https?://\S+', path):
        if 'github' in path:
            tweets = pd.read_csv(path, sep = delim)
        elif 'docs.google.com/spreadsheets' in path:
            sheet_id = path.split('/d/')[1].split('/')[0]
            gid = '0'
            if 'gid=' in path:
                gid = path.split('gid=')[1].split('&')[0].split('#')[0]
            export_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}'
            tweets = pd.read_csv(export_url, sep=delim)
        elif 'drive.google.com' in path:
            if '/uc?' in path:
                # Already in the correct format
                tweets = pd.read_csv(path, sep = delim)
            else:
                # Convert from /file/d/ format
                file_id = path.split('/')[-2]
                download_url = f'https://drive.google.com/uc?id={file_id}'
                tweets = pd.read_csv(download_url, sep = delim)
        else:
            raise ValueError("Unrecognized URL format")
    else:
        tweets = pd.read_csv(path, sep = delim)
    return tweets

# Function to check if a URL exists in the text
def is_url(s):
    return bool(re.match(r'^https?:\/\/', str(s)))

def to_bool(v):
    """CSV truthiness: 1 / true / vero / yes / x -> True, anything else (incl. empty/false/falso) -> False."""
    return str(v).strip().lower() in ('1', 'true', 'vero', 'yes', 'x')

def to_int(v, default=0):
    """CSV integer: '12' / '12.0' -> 12; empty/invalid -> default."""
    try:
        return int(float(str(v).strip()))
    except (ValueError, TypeError):
        return default


# COMMENTS
def highlight_entities(text):
    """Wrap #hashtags, $cashtags, @mentions and links in the same styling used for captions."""
    text = str(text)
    text = re.sub(r'\B(#[a-zA-Z0-9_]+\b)', r'<span class="text-primary">\g<0></span>', text)
    text = re.sub(r'\B(\$[a-zA-Z0-9_\.]+\b)', r'<span class="text-primary">\g<0></span>', text)
    text = re.sub(r'\B(@[a-zA-Z0-9_]+\b)', r'<span class="text-primary">\g<0></span>', text)
    text = re.sub(
        r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])',
        r'<a class="text-primary">\g<0></a>', text)
    return text



# some pre-processing
def preprocessing(df, config):
    # reformat date — try European dot-style first to avoid day/month ambiguity, then fall back to pandas' flexible parser
    df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce', format='%d.%m.%y %H:%M')
    mask = df['datetime'].isna()
    if mask.any():
        df.loc[mask, 'datetime'] = pd.to_datetime(
            df.loc[mask, 'datetime'],
            errors='coerce',
        )
    # fall back to current date for any remaining unparseable values
    df['datetime'] = df['datetime'].fillna(pd.Timestamp.now())
    df['date'] = df['datetime'].dt.strftime('%d %b').str.replace(' ', '. ')
    df['date'] = df['date'].str.lstrip('0')
    df['formatted_datetime'] = df['datetime'].dt.strftime('%I:%M %p · %b %d, %Y')

    # highlight hashtags, cashtags, mentions, etc.
    df['text'] = df['text'].str.replace(r'\B(\#[a-zA-Z0-9_]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    df['text'] = df['text'].str.replace(r'\B(\$[a-zA-Z0-9_\.]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    df['text'] = df['text'].str.replace(r'\B(\@[a-zA-Z0-9_]+\b)',
                                                  r'<span class="text-primary">\g<0></span>', regex=True)
    # remove the href below, if you don't want them to leave your page
    df['text'] = df['text'].str.replace(
        r'(http|ftp|https):\/\/([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])',
        r'<a class="text-primary">\g<0></a>', regex=True)

    # make numeric information integers and fill NAs with 0
    df['replies'] = df['replies'].fillna(0).astype(int)
    df['reposts'] = df['reposts'].fillna(0).astype(int)
    df['likes'] = df['likes'].fillna(0).astype(int)

    # VIDEO MODE--------------------------------------------------------------------------------
    # OLD
    ## df['media'] = df['media'].apply(extract_first_url)
    # df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
    # df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False)
    ## print(df[['pic_available', 'media']])
    
    # NEW
    df['media'] = df['media'].astype(str).str.replace("'|,", '', regex=True)
    df['pic_available'] = np.where(df['media'].str.contains('http', na=False), True, False) # Vero ogni volta che colonna media contiene URL
    # Classify each media URL as video vs image (by file extension).
    video_ext = r'\.(mp4|webm|ogg|ogv|mov|m4v)(\?.*)?$'
    df['is_video'] = df['media'].str.contains(video_ext, case=False, regex=True, na=False) # Vero quando URL finisce con estensione video (regex data come video_ext)
    df['video_available'] = df['pic_available'] & df['is_video'] # due nuovi flag per T_Feed_Insta mutuamente esclusivi
    df['image_available'] = df['pic_available'] & ~df['is_video'] # la sigma vuol dire: vero se media è img, falso se video
    # -----------------------------------------------------------------------------------------

    # --- GOOGLE DRIVE SUPPORT (uncomment to support Drive video links) --------------------
    # Replace the three lines above with this block. Also search "GOOGLE DRIVE SUPPORT"
    # in T_Item_Insta.html, T_Item_Stories.html, insta_video.js, stories.js and
    # uncomment the matching sections there.
    #
    # Requirement: the Drive file must be shared as "Anyone with the link → Viewer".
    # Drive iframes are cross-origin — JS cannot call play()/pause(); the only lever is
    # setting/clearing the src attribute. Autoplay is browser-gesture-gated (works in
    # Stories after a tap, not guaranteed in Instagram scroll).
    #
    # df['is_drive'] = df['media'].str.contains('drive.google.com', na=False)
    # def drive_preview(url):
    #     if 'drive.google.com' not in str(url):
    #         return ''
    #     file_id = ''
    #     if '/file/d/' in url:
    #         file_id = url.split('/file/d/')[1].split('/')[0]
    #     elif 'id=' in url:
    #         file_id = url.split('id=')[1].split('&')[0]
    #     return f'https://drive.google.com/file/d/{file_id}/preview' if file_id else ''
    # df['drive_embed'] = df['media'].apply(drive_preview)
    # df['video_available'] = df['pic_available'] & (df['is_video'] | df['is_drive'])
    # df['image_available'] = df['pic_available'] & ~df['is_video'] & ~df['is_drive']
    # --------------------------------------------------------------------------------------
    # VIDEO MODE END------------------------------------------------------------------------


    # create a name icon as a profile pic
    df['profile_pic_available'] = df['user_image'].apply(is_url)
    df['icon'] = df['username'].str[:2].str.title()

    # Assign a random color class from a predefined list
    color_classes = ['p1', 'p2', 'p3', 'p4', 'p5', 'p6', 'p7', 'p8']
    df['color_class'] = np.random.choice(color_classes, size=len(df))

    # make sure user descriptions do not entail any '' or "" as this complicates visualization
    # also replace nan with some whitespace
    df['user_description'] = df['user_description'].str.replace("'", '')
    df['user_description'] = df['user_description'].str.replace('"', '')
    df['user_description'] = df['user_description'].fillna(' ')

    # make number of followers a formatted string
    df['user_followers'] = df['user_followers'].map('{:,.0f}'.format).str.replace(',', '.')

    # Check if 'condition_col' is set and not empty, and if it's an existing column in df
    # looks like legacy code as I force people to have a condition col by now.
    if ('condition_col' in config and
            config['condition_col'] and
            config['condition_col'] in df.columns):
        # Rename the specified column to 'condition'
        df.rename(columns={config['condition_col']: 'condition'}, inplace=True)

    # COMMENTS ------------------------------------------------------------------
    # Auto-detect how many comment slots the CSV provides (columns comment_0, comment_1, ...).
    comment_slot_ids = sorted(
        int(re.fullmatch(r'comment_(\d+)', col).group(1)) #group(1) = (\d+) = il numero del commento
        for col in df.columns
        if re.fullmatch(r'comment_(\d+)', col)
    )

    def build_comments(row): # ROW = il post i-esimo con i suoi commenti
        post_owner = str(row.get('username', '')).strip().lower()

        def cell(col):
            v = row.get(col, '') # can return NaN if the column exists but the cell is empty. return '' if that col is missing entirely
            return '' if pd.isna(v) else str(v).strip()

        # 1) Build every non-empty comment slot, keyed by its slot index j
        all_comments = {} # es. {0: {'idx': 0, 'text': '...', 'user': '...', 'image': '...', 'like_count': 123, ...}, 1: {...}, ...}
        raw_subrefs = {} # es. {0: '1,2', 1: '', 2: '3', ...} = comment_0 has subcomments comment_1 and comment_2; comment_1 has no subcomments; comment_2 has subcomment comment_3
        for j in comment_slot_ids:
            text  = cell(f'comment_{j}')
            user  = cell(f'comment_user_{j}')
            image = cell(f'comment_image_{j}')

            # Skip a slot only if the 3 core fields are all empty (unused slot)
            if not text and not user and not image:
                continue

            all_comments[j] = {
                'idx': j,
                'text': highlight_entities(text) if text else '',     # empty -> ""
                'user': user if user else 'unknown',                  # empty -> "unknown"
                'image': image,                                       # empty -> template icon fallback
                'image_available': is_url(image),
                'like_count': to_int(cell(f'comment_likes_count_{j}')),         # empty -> manual count from CSV (empty -> 0)
                'verified': to_bool(cell(f'verified_user_comment_{j}')),
                'time': cell(f'comment_time_{j}'),                    # empty -> "" (no timestamp)
                'liked_by_author': to_bool(cell(f'comment_liked_author_{j}')),  # red heart + "· Liked by Author"
                'is_author': bool(user) and user.lower() == post_owner,           # "· Author"
                'member': to_bool(cell(f'member_comment_{j}')),
                'pinned': to_bool(cell(f'pinned_comment_{j}')),
                'subcomments': [],
                'sub_count': 0,
            }
            raw_subrefs[j] = cell(f'subcomments_comment_{j}')

        # 2) Parse a subcomments cell -> referenced slot indices (accepts , or & delimiter)
        def parse_refs(s):
            refs = []
            for token in re.split(r'[,&]', s):
                m = re.search(r'\d+', token)
                if m:
                    refs.append(int(m.group()))
            return refs

        # 3) One pass in slot order, driven by a single rule: a comment that has ALREADY been claimed
        #    as a reply has its OWN list ignored. That one rule gives both:
        #      * the 1-level cap  -> a reply's list is dead, so replies never nest;
        #      * cycle safety     -> with comment_0 -> comment_1 and comment_1 -> comment_0, comment_1 is
        #                            already a reply when we reach it, so its list cannot steal comment_0,
        #                            which stays the parent.
        #    A comment named only by an ignored list is never claimed, so it simply renders as a normal
        #    top-level comment (nothing is lost, it just loses the link to its would-be parent).
        replies = set()
        for j in comment_slot_ids:
            if j not in all_comments or j in replies: 
                # se un commento non esiste o è già stato reclamato come reply, non guardare proprio la sua lista di subcomments
                continue
            for ref in parse_refs(raw_subrefs.get(j, '')): #raw_subrefs = { 0: "1,2",  1: "",  2: "0" } -> parse_refs("1,2") = [1, 2] -> comment_0 ha come subcomments comment_1 e comment_2
                if ref in all_comments and ref != j:      # must exist; no self-reference, cioè se ho errore di mettere un subcomment uguale al suo padre
                    replies.add(ref)
                    all_comments[j]['subcomments'].append(all_comments[ref])

        # CYCLE: RESOLVED! comment_0 -> comment_1 / comment_1 -> comment_0
        # all_comments = {0: {..., 'subcomments': []}, 1: {..., 'subcomments': []}} 
        # raw_subrefs = {0: "1", 1: "0"}
        # ----------ciclo 1---------------
        # comment_0: ref = 1 -> comment_1 in all_comments and comment_1 != comment_0 -> ok
        # replies = {1} ; all_comments[0]['subcomments'] = [comment_1]
        # ----------ciclo 2---------------
        # comment_1: WARNING! comment_1 in replies -> skip -> comment_0 trattato come top-level, comment_1 come reply

        # BACKWARD REFERENCE: WARNING! comment_0 -> comment_1 / comment_2 -> comment_0
        # all_comments = {0: {..., 'subcomments': []}, 1: {..., 'subcomments': []}, 2: {..., 'subcomments': []}}
        # raw_subrefs = {0: "1", 1: "", 2: "0"}
        # ----------ciclo 1---------------
        # comment_0: ref = 1 -> comment_1 in all_comments and comment_1 != comment_0 -> ok
        # replies = {1} ; all_comments[0]['subcomments'] = [comment_1]
        # ----------ciclo 2---------------
        # comment_1: no subcomments -> skip -> only a subcomment of comment_0
        # ----------ciclo 3---------------
        # comment_2: ref = 0 -> comment_0 in all_comments and comment_0 != comment_2 -> ok
        # replies = {1, 0} ; all_comments[2]['subcomments'] = [comment_0]
        # WARNING! comment_0 is a top-level, comment_1 will not be shown at all, deleted from the comment_0 subcomments list

        # 4) SAFETY NET for a malformed CSV: a "backward" reference, i.e. a comment citing an EARLIER
        #    slot that was already processed as a parent. Example: comment_0 -> comment_1 AND
        #    comment_2 -> comment_0. At j=0 comment_0 had not been claimed yet (comment_2 is read later),
        #    so it was treated as a parent and took comment_1; at j=2 it becomes a reply while still
        #    holding comment_1 -> that would render replies INSIDE a reply = 2 levels.
        #    Emptying every reply's own list makes the 1-level cap a GUARANTEE instead of a hope.
        #
        #    HOW TO AVOID THE SITUATION ENTIRELY (CSV convention):
        #      put all subcomments at the END of the row, with the HIGHEST indices, so a parent always
        #      cites a HIGHER index than its own  ->  comment_0 -> comment_5,comment_6
        #    With that convention every reference points forward and this loop is a pure NO-OP (a claimed
        #    comment already skipped its list, so its 'subcomments' is empty already).
        #
        #    Known cost, ONLY in the malformed case: the reply the demoted parent had claimed
        #    (comment_1 above) is left orphaned and is not rendered anywhere.
        #    A stronger variant that restores it is documented in FUTURE_UPDATES.md -> UPDATE G.
        for j in replies:
            all_comments[j]['subcomments'] = []

        for c in all_comments.values():
            c['sub_count'] = len(c['subcomments'])

        # 5) Top-level list = comments never claimed as a reply, in slot order; pinned first (stable)
        comments = [all_comments[j] for j in comment_slot_ids
                    if j in all_comments and j not in replies]
        comments.sort(key=lambda c: not c['pinned'])
        return comments
    # tu hai ogni riga = N commenti del post i-esimo
    # ogni riga (il post) ha N commenti del post (una lista), ogni commento è un dizionario: LISTA di DIZIONAI: ogni commento è testo, user, image, like_count.
    # Quindi df['comments'] diventa una colonna nel DF, dove ogni riga è i commenti relativi ad un POST, ovvero una LIST di dizionari.
    # List-comprehension (NOT df.apply) avoids pandas expanding equal-length lists into columns
    df['comments'] = [build_comments(row) for _, row in df.iterrows()] 
    #shape column comments: se assegni una lista alla colonna pandas, in automatico, ogni elemento della lista si inserisce nella riga corrispondente.
    # riga 1 (post 1): [{'text': '50M Jobseekers. <br><br> 150+ Job Boards. <br><br> One Click.', 'user': '9GAG', 'image': '', 'image_available': False, 'like_count': 0}, { ... }, { ... }, ...]
    # riga 2 (post 2): [{'text': '50M Jobseekers. <br><br> 150+ Job Boards. <br><br> One Click.', 'user': '9GAG', 'image': '', 'image_available': False, 'like_count': 0}, { ... }, { ... }, ...]
    # ---------------------------------------------------------------------------

    # VIEW DIRECT COMMENTS
    # Flag per-post: mostra i commenti anche sotto il post (non solo nel modale).
    if 'view_direct_comments' in df.columns:
        df['view_direct_comments'] = df['view_direct_comments'].apply(to_bool)
    else:
        df['view_direct_comments'] = False

    # preview_comments: quanti commenti PADRE (top-level) mostrare nella preview (per post).
    #   n > 0                                      -> primi n (troncati al totale se n li supera)
    #   n == 0  (o vuoto/non valido -> default 0)  -> NESSUN commento in preview
    #   n < 0                                      -> TUTTI i commenti
    if 'preview_comments' in df.columns:
        df['preview_comments'] = df['preview_comments'].apply(lambda v: to_int(v, default=0))
    else:
        df['preview_comments'] = 0

    # Commenti top-level mostrati nella preview sotto al post
    # (list-comprehension come per 'comments', per evitare l'espansione in colonne di pandas)
    df['comments_preview'] = [
        ([] if not vdc else (cs if n < 0 else cs[:n]))
        for cs, vdc, n in zip(df['comments'], df['view_direct_comments'], df['preview_comments'])
    ]

    return df


def create_redirect(player):
    if player.participant.label:
        link = player.session.config['survey_link'] + '?' + player.session.config['url_param'] + '=' + player.participant.label
    else:
        link = player.session.config['survey_link'] + '?' + player.session.config['url_param'] + '=' + player.participant.code

    completion_code = None

    # if 'prolific_completion_url' in player.session.config and player.session.config['prolific_completion_url'] is not None:
        # completion_code = player.session.config['prolific_completion_url'][-8:]

    if 'completion_code' in player.session.vars:
        if player.session.vars['completion_code'] is not None:
            link = link + '&' + 'cc=' + player.session.vars['completion_code']

    if player.feed_condition is not None:
        link = link + '&' + 'condition=' + player.feed_condition

    return link


# PAGES
class A_Intro(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return not player.session.config['skip_intro']

    @staticmethod
    def vars_for_template(player: Player):
        print(len(player.session.config['briefing']) > 0)
        return dict(
            custom_consent_available=len(player.session.config['briefing']) > 0,
        )
class B_Briefing(Page):
    form_model = 'player'

    @staticmethod
    def is_displayed(player):
        return not player.session.config['skip_briefing'] and len(player.session.config['briefing']) > 0


class C_Feed(Page):
    form_model = 'player'

    @staticmethod
    def get_form_fields(player: Player):
        fields =  ['likes_data', 'replies_data', 'promoted_post_clicks', 'touch_capability', 'device_type', 'screen_resolution']

        if not player.session.config['topics'] & player.session.config['show_cta']:
            more_fields =  ['scroll_sequence', 'viewport_data', "rowheight_data"] # , 'cta']
        else:
            more_fields =  ['scroll_sequence', 'viewport_data', "rowheight_data"]

        return fields + more_fields

    @staticmethod
    def vars_for_template(player: Player):
        # ad = player.ad_condition
        label_available = False
        if player.participant.label is not None:
            label_available = True
        # Reset index to ensure consistent ordering (important for generic feed swiper)
        tweets_df = player.participant.tweets.reset_index(drop=True)
        return dict(
            tweets=tweets_df.to_dict('index'),
            topics=player.session.config['topics'],
            search_term=player.session.config['search_term'],
            label_available=label_available,
            # banner_img='img/{}_banner.png'.format(ad),
        )

    @staticmethod
    def js_vars(player: Player):
        return dict(
            dwell_threshold=player.session.config['dwell_threshold'],
            story_duration=player.session.config['story_duration'],
        )


    @staticmethod
    def before_next_page(player, timeout_happened):
        player.participant.finished = True
        if 'prolific_completion_url' in player.session.vars:
            if player.session.vars['prolific_completion_url'] is not None:
                if 'completion_code' in player.session.vars:
                    if player.session.vars['completion_code'] is not None:
                        player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete?cc=' + player.session.vars['completion_code']
                    else:
                        player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete'
                else: player.session.vars['prolific_completion_url'] = 'https://app.prolific.com/submissions/complete'
            else:
                player.session.vars['prolific_completion_url'] = 'NA'
        else:
            player.session.vars['prolific_completion_url'] = 'NA'

        if player.id_in_group != 1:
            player.participant.tweets = ""


class D_Redirect(Page):

    @staticmethod
    def is_displayed(player):
        return len(player.session.config['survey_link']) > 0

    @staticmethod
    def vars_for_template(player: Player):
        return dict(link=create_redirect(player))

    @staticmethod
    def js_vars(player):
        return dict(link=create_redirect(player))

class D_Debrief(Page):

    @staticmethod
    def is_displayed(player):
        return len(player.session.config['survey_link']) == 0

page_sequence = [A_Intro,
                 B_Briefing,
                 C_Feed,
                 D_Redirect,
                 D_Debrief]


def custom_export(players):
    # header row
    yield ['session', 'participant_code', 'participant_label', 'participant_in_session', 'condition', 'item_sequence',
           'scroll_sequence', 'item_dwell_time', 'likes', 'replies']
    for p in players:
        participant = p.participant
        session = p.session
        yield [session.code, participant.code, participant.label, p.id_in_group, p.feed_condition, p.sequence,
               p.scroll_sequence, p.viewport_data, p.likes_data, p.replies_data]
