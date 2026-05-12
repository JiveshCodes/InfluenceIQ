"""
InfluenceIQ v2 — ML Engine (Production)
Pipeline: Text Embedding → Cosine Similarity → Weighted Scoring → XAI Explanations
Handles both sentence-transformers (primary) and TF-IDF fallback gracefully.
"""

import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import os, warnings
import ml_models

warnings.filterwarnings('ignore')

# ── Global state ──────────────────────────────────────────────
_df         = None
_embeddings = None          # (N, D) matrix — pre-computed at startup
_tfidf_vec  = None          # fallback vectoriser (shared dim)
_emb_dim    = None          # actual embedding dimension
_use_st     = False         # whether sentence-transformers loaded OK
_st_model   = None
_ml_engine_models = None    # Scikit-learn models manager

# ── Config ────────────────────────────────────────────────────
CURRENCY_RATES   = {'USD':1.0,'INR':83.5,'EUR':0.92,'GBP':0.79,'CAD':1.36,'AED':3.67}
CURRENCY_SYMBOLS = {'USD':'$','INR':'₹','EUR':'€','GBP':'£','CAD':'C$','AED':'AED '}

PLATFORM_META = {
    'Instagram':{'color':'#E1306C','icon':'📸'},
    'YouTube':  {'color':'#FF0000','icon':'▶️'},
    'Twitter':  {'color':'#1DA1F2','icon':'🐦'},
    'LinkedIn': {'color':'#0A66C2','icon':'💼'},
}

CONTRACT_MULTIPLIERS = {
    '1_post':       1.0,
    '2_posts':      1.8, # 10% bulk discount
    'ambassador':   5.0, # 5x for long-term partnership
    'product_ad':   2.5, # includes usage rights
    'shoutout':     0.4, # quick mention
}

CATEGORY_KW = {
    ('Fashion','Streetwear'):         'streetwear urban ootd style fashion casual hype sneakers trending outfit',
    ('Fashion','Luxury fashion'):     'luxury designer highend premium fashion elite couture brand exclusive',
    ('Fashion','Ethnic wear'):        'ethnic traditional saree Indian cultural heritage kurti lehenga festive',
    ('Fashion','Sustainable fashion'):'sustainable eco environment conscious green organic thrift slow fashion',
    ('Sports','Cricket'):             'cricket IPL BCCI batting bowling sports wicket match test T20 ODI',
    ('Sports','Football'):            'football soccer skills match ISL FIFA sport striker goal pitch',
    ('Sports','Fitness training'):    'fitness training gym workout health sports cardio strength endurance',
    ('Sports','Outdoor adventure'):   'outdoor adventure nature extreme sports exploration trekking hiking',
    ('Tech','Smartphones'):           'smartphones mobile gadgets review unboxing tech comparison specs camera',
    ('Tech','AI/ML'):                 'AI ML machine learning artificial intelligence tech future deep learning NLP',
    ('Tech','Gaming'):                'gaming esports streaming game play gamer fps mobile battlegrounds BGMI',
    ('Tech','Software development'):  'programming coding software developer tech tutorial webdev javascript python',
    ('Lifestyle','Travel'):           'travel explore destination adventure tourism wanderlust trip vacation',
    ('Lifestyle','Food'):             'food recipe restaurant cuisine cooking eat chef gourmet street food',
    ('Lifestyle','Daily vlogging'):   'vlog daily lifestyle content life routine diary personal day',
    ('Lifestyle','Minimalism'):       'minimalism simple clean mindful intentional wellness zen declutter calm',
    ('Fitness','Bodybuilding'):       'bodybuilding muscle gym strength workout physique aesthetics bulk shred',
    ('Fitness','Yoga'):               'yoga flexibility mindfulness wellness asana peace meditation breathwork',
    ('Fitness','Home workouts'):      'home workout fitness exercise noequipment indoor calisthenics HIIT',
    ('Fitness','Nutrition'):          'nutrition diet health food supplement wellness macros protein vitamins',
}


# ── Text builder ──────────────────────────────────────────────
def _profile_text(row):
    kw = str(row.get('keywords','')).replace(',',' ')
    return ' '.join(filter(None,[
        row.get('name',''), row.get('category',''), row.get('subcategory',''),
        row.get('platform',''), row.get('location',''), row.get('content_type',''), kw
    ]))


# ── Embedding layer ───────────────────────────────────────────
def _try_load_st():
    """Try to load sentence-transformers; return model or None."""
    try:
        from sentence_transformers import SentenceTransformer
        m = SentenceTransformer('all-MiniLM-L6-v2')
        return m
    except Exception:
        return None


def _embed_corpus(texts):
    """Embed a list of texts. Uses ST if available, else TF-IDF (shared vectoriser)."""
    global _st_model, _use_st, _tfidf_vec, _emb_dim

    if _use_st and _st_model:
        vecs = _st_model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        _emb_dim = vecs.shape[1]
        return vecs.astype(np.float32)

    # TF-IDF path — fit vectoriser on corpus once
    if _tfidf_vec is None:
        _tfidf_vec = TfidfVectorizer(max_features=256, ngram_range=(1,2), sublinear_tf=True)
        mat = _tfidf_vec.fit_transform(texts).toarray().astype(np.float32)
    else:
        mat = _tfidf_vec.transform(texts).toarray().astype(np.float32)

    # L2-normalise
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    _emb_dim = mat.shape[1]
    return mat / norms


def _embed_query(text):
    """Embed a single query string — MUST use same vectoriser as corpus."""
    global _st_model, _use_st, _tfidf_vec, _emb_dim

    if _use_st and _st_model:
        vec = _st_model.encode([text], show_progress_bar=False, normalize_embeddings=True)
        return vec.astype(np.float32)   # (1, D)

    if _tfidf_vec is None:
        raise RuntimeError('TF-IDF vectoriser not fitted yet — call load_data() first')
    mat = _tfidf_vec.transform([text]).toarray().astype(np.float32)
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1
    return mat / norms   # (1, D)


# ── Scoring helpers ───────────────────────────────────────────
def get_quality_score(row):
    s  = min(float(row.get('engagement_rate',0)) / 10.0, 1.0) * 35
    s += min(np.log10(max(float(row.get('followers',1)), 1)) / 8.0, 1.0) * 20
    s += (1.0 - float(row.get('fraud_risk',0.1))) * 25
    s += (1 if row.get('keywords','') else 0) * 5
    s += (1 if row.get('content_type','') else 0) * 5
    s += 10 if str(row.get('verified','false')).lower() == 'true' else 0
    return round(min(s, 100.0), 1)


def get_fraud_info(risk):
    r = float(risk)
    if r <= 0.07: return {'label':'Low',    'class':'low',    'color':'#22c55e','icon':'✓'}
    if r <= 0.12: return {'label':'Medium', 'class':'medium', 'color':'#f59e0b','icon':'△'}
    return               {'label':'High',   'class':'high',   'color':'#ef4444','icon':'⚠'}


def get_pop_tag(followers):
    f = float(followers)
    if f >= 50_000_000: return 'Mega Celebrity'
    if f >= 10_000_000: return 'Mega Influencer'
    if f >= 1_000_000:  return 'Macro Influencer'
    if f >= 100_000:    return 'Mid-tier Creator'
    return 'Micro Creator'


def get_reasons(row, category, subcategory):
    out = []
    eng    = float(row['engagement_rate'])
    fraud  = float(row['fraud_risk'])
    followers = float(row['followers'])

    if row['subcategory'].lower() == subcategory.lower():
        out.append(f"Exact niche match — {subcategory}")
    elif row['category'].lower() == category.lower():
        out.append(f"Category alignment with {category}")

    if eng >= 7:   out.append(f"Exceptional {eng:.1f}% engagement rate")
    elif eng >= 5: out.append(f"Above-average {eng:.1f}% engagement")
    elif eng >= 3: out.append(f"Solid {eng:.1f}% engagement rate")

    if fraud <= 0.05:   out.append("Excellent audience authenticity score")
    elif fraud <= 0.07: out.append("Verified authentic audience")

    if followers >= 10_000_000:  out.append("Massive reach — 10M+ followers")
    elif followers >= 1_000_000: out.append(f"Strong reach — {followers/1e6:.1f}M followers")

    if str(row.get('verified','false')).lower() == 'true':
        out.append("Platform-verified creator profile")

    if not out:
        out.append("Strong keyword and content alignment")
    return out[:4]


def get_vibe(score):
    s = float(score)
    if s >= 0.75: return {'label':'Exceptional Positivity', 'class':'vibe-pos', 'color':'#22c55e', 'icon':'✨'}
    if s >= 0.55: return {'label':'Strongly Positive',    'class':'vibe-pos', 'color':'#4ade80', 'icon':'😊'}
    if s >= 0.45: return {'label':'Mixed / Neutral',       'class':'vibe-neu', 'color':'#f59e0b', 'icon':'😐'}
    return               {'label':'Negative Vibe',        'class':'vibe-neg', 'color':'#ef4444', 'icon':'⚠️'}


# ── Public API ────────────────────────────────────────────────
def load_data():
    global _df, _embeddings, _st_model, _use_st, _tfidf_vec, _ml_engine_models

    base = os.path.dirname(os.path.abspath(__file__))
    _df  = pd.read_csv(os.path.join(base, 'dataset.csv'))

    for col in ['price_usd','fraud_risk','followers','engagement_rate','avg_likes','avg_comments']:
        _df[col] = pd.to_numeric(_df[col], errors='coerce').fillna(0)

    # Initialize Scikit-Learn Models
    _ml_engine_models = ml_models.MLEngineModels()
    _ml_engine_models.load_or_train(_df)

    # Try sentence-transformers
    _st_model = _try_load_st()
    _use_st   = _st_model is not None

    # Build corpus texts and embed ALL influencer profiles
    texts = [_profile_text(row) for _, row in _df.iterrows()]
    _embeddings = _embed_corpus(texts)   # (N, D)

    print(f"[ML] Loaded {len(_df)} influencers | "
          f"Embeddings: {_embeddings.shape} | "
          f"Model: {'Sentence-BERT' if _use_st else 'TF-IDF (fallback)'}")
    return _df


def predict(category, subcategory, platforms=None, gender=None, budget=None, country=None, state=None, contract_type='1_post', limit=12, page=1):
    if _df is None or _embeddings is None:
        load_data()

    # Build rich query text
    extra_kw  = CATEGORY_KW.get((category, subcategory), f'{category} {subcategory}')
    query_txt = f"{category} {subcategory} {extra_kw}"

    # Embed query with SAME model/vectoriser used for corpus
    q_vec = _embed_query(query_txt)           # (1, D)
    sims  = cosine_similarity(q_vec, _embeddings)[0]   # (N,)

    data = _df.copy()
    data['_sim'] = sims

    # ── Weighted composite score ──────────────────────────────
    scores = []
    for i, (_, row) in enumerate(data.iterrows()):
        sim      = float(sims[i])
        eng      = min(float(row['engagement_rate']) / 12.0, 1.0)
        fraud    = float(row['fraud_risk'])
        # Keyword Jaccard
        a = set(str(row['keywords']).lower().replace(',',' ').split())
        b = set(extra_kw.lower().split())
        kw_s = len(a & b) / len(a | b) if (a and b) else 0.0

        final = (sim * 0.35 + eng * 0.30 + kw_s * 0.15 + (1 - fraud) * 0.10 + float(row.get('sentiment_score', 0.5)) * 0.10)
        scores.append(round(final * 100, 2))

    data['suitability_score'] = scores

    # ── Strict Filtering ────────────────────────────────────────────────
    # Enforce Category & Subcategory match
    data = data[data['category'].str.lower() == category.lower()]
    data = data[data['subcategory'].str.lower() == subcategory.lower()]

    # Enforce Platform match if selected
    if platforms and len(platforms) > 0:
        data = data[data['platform'].isin(platforms)]

    if country:
        if country.lower() == 'global':
            c_filter = ~data['location'].str.contains('India', case=False, na=False)
        else:
            c_filter = data['location'].str.contains(country, case=False, na=False)
            
        if c_filter.sum() >= 1:
            data = data[c_filter]
            
    if state:
        s_filter = data['location'].str.contains(state, case=False, na=False)
        if s_filter.sum() >= 3:
            data = data[s_filter]
            
    if gender:
        # Check if 'gender' column exists (to prevent errors if dataset is not yet updated)
        if 'gender' in data.columns:
            g_filter = data['gender'].str.lower() == gender.lower()
            if g_filter.sum() >= 1:
                data = data[g_filter]

    relevant = data[data['subcategory'].str.lower() == subcategory.lower()].copy()
    if len(relevant) < 5:
        relevant = data[data['category'].str.lower() == category.lower()].copy()
    if len(relevant) < 5:
        relevant = data.copy()

    if budget:
        b = float(budget)
        relevant = relevant[(relevant['price_usd'] <= b) | (relevant['price_usd'] == 0)]

    relevant = relevant.sort_values('suitability_score', ascending=False)
    
    total_available = len(relevant)
    
    # Apply limit/page
    limit = min(int(limit), 50)
    page = max(int(page), 1)
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    
    paginated = relevant.iloc[start_idx:end_idx]
    has_more = end_idx < total_available

    # ── Build response ────────────────────────────────────────
    mult = CONTRACT_MULTIPLIERS.get(contract_type, 1.0)
    
    results = []
    for idx, (_, row) in enumerate(paginated.iterrows()):
        raw_price = float(row['price_usd'])
        price   = (raw_price * mult) if raw_price > 0 else None
        fi      = get_fraud_info(row['fraud_risk'])
        pm      = PLATFORM_META.get(row['platform'], {'color':'#666','icon':'📱'})
        reach   = min(float(row['followers']) / 15_000_000 * 100, 100)

        # Scikit-Learn predictions
        pred_cat, cat_conf = _ml_engine_models.predict_classification(
            row['followers'], row['engagement_rate'], row['category'], row['subcategory'], row['avg_likes'], row['avg_comments'], row.get('gender', 'Unknown')
        )
        pred_eng = _ml_engine_models.predict_engagement(
            row['followers'], row['category'], row['subcategory'], row['avg_likes'], row['avg_comments'], row.get('gender', 'Unknown')
        )
        similar_infs = _ml_engine_models.recommend_similar(_df, row['name'], top_n=2)

        results.append({
            'rank':             start_idx + idx + 1,
            'name':             row['name'],
            'category':         row['category'],
            'subcategory':      row['subcategory'],
            'platform':         row['platform'],
            'platform_color':   pm['color'],
            'platform_icon':    pm['icon'],
            'followers':        int(row['followers']),
            'engagement_rate':  round(float(row['engagement_rate']), 2),
            'avg_likes':        int(row['avg_likes']),
            'avg_comments':     int(row['avg_comments']),
            'keywords':         str(row['keywords']),
            'fraud_risk':       round(float(row['fraud_risk']), 3),
            'fraud_label':      fi['label'],
            'fraud_class':      fi['class'],
            'fraud_color':      fi['color'],
            'fraud_icon':       fi['icon'],
            'location':         row['location'],
            'gender':           row.get('gender', 'Unknown'),
            'content_type':     row['content_type'],
            'price_usd':        price,
            'suitability_score':float(row['suitability_score']),
            'sentiment_score':  float(row.get('sentiment_score', 0.5)),
            'vibe':             get_vibe(row.get('sentiment_score', 0.5)),
            'cosine_sim':       round(float(row['_sim']) * 100, 1),
            'profile_quality':  get_quality_score(row),
            'reasons':          get_reasons(row, category, subcategory),
            'popularity_tag':   get_pop_tag(row['followers']),
            'reach_pct':        round(reach, 1),
            'verified':         str(row.get('verified','false')).lower() == 'true',
            # ML Enhancements
            'predicted_category': pred_cat,
            'category_confidence': round(cat_conf, 1),
            'predicted_engagement': pred_eng,
            'similar_influencers': similar_infs
        })
        
    return {
        'results': results,
        'total_available': total_available,
        'page': page,
        'limit': limit,
        'has_more': has_more,
        'algorithm': 'BERT' if _use_st else 'TF-IDF'
    }


def update_influencer_stats(name, stats):
    """Dynamically update the in-memory dataset with live YouTube stats."""
    global _df
    if _df is None:
        return
        
    matches = _df[_df['name'].str.lower() == name.lower()]
    if not matches.empty:
        idx = matches.index[0]
        if 'followers' in stats:
            _df.at[idx, 'followers'] = float(stats['followers'])
        if 'engagement_rate' in stats:
            _df.at[idx, 'engagement_rate'] = float(stats['engagement_rate'])
        if 'avg_likes' in stats:
            _df.at[idx, 'avg_likes'] = float(stats['avg_likes'])
        if 'avg_comments' in stats:
            _df.at[idx, 'avg_comments'] = float(stats['avg_comments'])
            
        # Persist the live data back to the CSV so it survives server restarts
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            csv_path = os.path.join(base, 'dataset.csv')
            _df.to_csv(csv_path, index=False)
            print(f"[ML] Successfully saved synced live data for {name} to dataset.csv")
        except Exception as e:
            print(f"[ML] Error saving live data for {name} to dataset.csv: {e}")

def add_influencer(influencer_data):
    """Add a newly discovered influencer to the dataset permanently."""
    global _df, _embeddings
    if _df is None:
        load_data()
        
    name = influencer_data.get('name')
    if name and not _df[_df['name'].str.lower() == name.lower()].empty:
        return # Already exists
        
    # Build new row
    new_id = int(_df['id'].max()) + 1 if not _df.empty else 1
    # Smart Price Estimation for discovered influencers
    # Formula: $15 base per 1k followers + Engagement Bonus
    f_count = float(influencer_data.get('followers', 0))
    eng     = float(influencer_data.get('engagement_rate', 0.0))
    
    # CPM-based pricing ($15 per 1k subs)
    base_price = (f_count / 1000) * 15
    
    # Engagement Multiplier (e.g. 5% engagement gives a 1.2x boost)
    eng_mult = 1.0 + (eng / 10.0) 
    
    # Floor price of $50, cap at $50,000 for safety
    estimated_price = max(50, min(base_price * eng_mult, 50000))

    new_row = {
        'id': new_id,
        'name': name,
        'category': influencer_data.get('category', 'Tech'),
        'subcategory': influencer_data.get('subcategory', 'General'),
        'platform': influencer_data.get('platform', 'YouTube'),
        'followers': f_count,
        'engagement_rate': eng,
        'avg_likes': influencer_data.get('avg_likes', 0),
        'avg_comments': influencer_data.get('avg_comments', 0),
        'keywords': influencer_data.get('keywords', ''),
        'fraud_risk': 0.05, # Default for new
        'fraud_label': 'Low',
        'location': influencer_data.get('location', 'India'),
        'content_type': 'Videos',
        'price_usd': round(estimated_price, 2),
        'verified': True,
        'gender': influencer_data.get('gender', 'Female')
    }
    
    _df = pd.concat([_df, pd.DataFrame([new_row])], ignore_index=True)
    
    # Save to CSV
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        _df.to_csv(os.path.join(base, 'dataset.csv'), index=False)
        # Reload embeddings to include the new person
        texts = [_profile_text(row) for _, row in _df.iterrows()]
        _embeddings = _embed_corpus(texts)
        print(f"[ML] Discovery! Added {name} to dataset.csv and reloaded embeddings.")
    except Exception as e:
        print(f"[ML] Error adding new influencer: {e}")

def recompute_analysis(row, category, subcategory):
    """Re-run the ML analysis for a specific influencer after a live sync."""
    # 1. Recalculate basic metrics
    fi = get_fraud_info(row['fraud_risk'])
    
    # 2. Recalculate suitability score
    eng = min(float(row['engagement_rate']) / 12.0, 1.0)
    fraud = float(row['fraud_risk'])
    sent = float(row.get('sentiment_score', 0.5))
    
    # Updated weighted logic with sentiment
    final = (0.8 * 0.35 + eng * 0.30 + 0.15 * 0.15 + (1 - fraud) * 0.10 + sent * 0.10)
    
    return {
        'followers':        int(row['followers']),
        'engagement_rate':  round(float(row['engagement_rate']), 2),
        'avg_likes':        int(row['avg_likes']),
        'avg_comments':     int(row['avg_comments']),
        'sentiment_score':  sent,
        'vibe':             get_vibe(sent),
        'suitability_score':round(final * 100, 2),
        'profile_quality':  get_quality_score(row),
        'reasons':          get_reasons(row, category, subcategory),
        'popularity_tag':   get_pop_tag(row['followers']),
        'fraud_label':      fi['label'],
        'fraud_class':      fi['class']
    }

def get_trending(limit=9):
    if _df is None:
        load_data()
    d = _df.copy()
    d['trend_score'] = d['engagement_rate'] * np.log10(d['followers'].clip(lower=1))
    d = d.sort_values('trend_score', ascending=False).head(limit)
    return [{
        'name':           row['name'],
        'category':       row['category'],
        'subcategory':    row['subcategory'],
        'platform':       row['platform'],
        'followers':      int(row['followers']),
        'engagement_rate':round(float(row['engagement_rate']), 2),
        'location':       row['location'],
        'trend_score':    round(float(row['trend_score']), 2),
        'verified':       str(row.get('verified','false')).lower() == 'true',
    } for _, row in d.iterrows()]


def get_stats():
    if _df is None:
        load_data()
    return {
        'total_influencers': len(_df),
        'categories':        int(_df['category'].nunique()),
        'platforms':         int(_df['platform'].nunique()),
        'avg_engagement':    round(float(_df['engagement_rate'].mean()), 2),
        'avg_fraud_risk':    round(float(_df['fraud_risk'].mean()), 3),
        'verified_count':    int((_df['verified'].astype(str).str.lower() == 'true').sum()),
    }
