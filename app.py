"""
InfluenceIQ v2 — Flask Application
Production-ready backend with ML integration
"""

from flask import Flask, render_template, request, jsonify, abort
import ml_engine as ml
import os
import youtube_api
from config import config_by_name

# Initialize Flask App
app = Flask(__name__)

# Load configuration based on environment
env_name = os.getenv('FLASK_ENV', 'default')
app.config.from_object(config_by_name[env_name])

# Pre-load ML model on startup
ml.load_data()

# ── Currency (client-side conversion, server provides rates) ──
CURRENCY_RATES   = {'USD':1.0,'INR':83.5,'EUR':0.92,'GBP':0.79,'CAD':1.36,'AED':3.67}
CURRENCY_SYMBOLS = {'USD':'$','INR':'₹','EUR':'€','GBP':'£','CAD':'C$','AED':'AED '}

# ── Page Routes ───────────────────────────────────────────────

@app.route('/')
def index():
    stats = ml.get_stats()
    return render_template('landing.html', stats=stats)

@app.route('/login')
def login():
    return render_template('auth.html', mode='login')

@app.route('/signup')
def signup():
    return render_template('auth.html', mode='signup')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/creator_dashboard')
def creator_dashboard():
    return render_template('creator_dashboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# ── API Routes ────────────────────────────────────────────────

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json(silent=True) or {}
    category    = data.get('category','')
    subcategory = data.get('subcategory','')
    platforms   = data.get('platforms') or []
    gender      = data.get('gender') or None
    budget      = data.get('budget') or None
    country     = data.get('country') or None
    state       = data.get('state') or None
    contract    = data.get('contract_type') or '1_post'
    limit       = data.get('limit', 12)
    page        = data.get('page', 1)

    if not category or not subcategory:
        return jsonify({'error':'category and subcategory required'}), 400

    # ── YOUTUBE DISCOVERY: Find new people if YouTube is selected ──
    youtube_error = None
    if platforms and 'youtube' in [p.lower() for p in platforms]:
        print(f"[Discovery] Searching YouTube for new {category} influencers...")
        discovery_res = youtube_api.search_influencers(category, subcategory, max_results=8)
        
        if isinstance(discovery_res, dict) and discovery_res.get('error') == 'quota_exceeded':
            youtube_error = "YouTube recommendations temporarily unavailable (Quota Exceeded)"
            print("[Discovery] YouTube Quota Exceeded. Skipping discovery.")
        elif isinstance(discovery_res, list):
            for person in discovery_res:
                # Enrich with search context so they pass strict filters
                person['category'] = category
                person['subcategory'] = subcategory
                person['location'] = country if country and country.lower() != 'any location' else 'India'
                person['gender'] = gender if gender and gender.lower() != 'any gender' else 'Female'
                ml.add_influencer(person)

    res_data = ml.predict(category, subcategory, platforms, gender, budget, country, state, contract, limit, page)

    # ── AUTO-SYNC LOGIC: If YouTube is selected, fetch live data for top results ──
    if 'YouTube' in platforms and res_data['results'] and not youtube_error:
        for influencer in res_data['results'][:8]:
            if influencer.get('platform') == 'YouTube':
                name = influencer['name']
                sync_res = youtube_api.sync_influencer(name)
                
                if isinstance(sync_res, dict) and sync_res.get('error') == 'quota_exceeded':
                    youtube_error = "YouTube live sync temporarily unavailable (Quota Exceeded)"
                    break # Stop syncing further to save time/requests
                
                if sync_res.get('success'):
                    influencer.update(sync_res)
                    # Re-analyze live
                    live_analysis = ml.recompute_analysis(influencer, category, subcategory)
                    influencer.update(live_analysis)
                    ml.update_influencer_stats(name, sync_res)

    return jsonify({
        'results':         res_data['results'],
        'total_available': res_data['total_available'],
        'page':            res_data['page'],
        'limit':           res_data['limit'],
        'has_more':        res_data['has_more'],
        'total':           len(res_data['results']), # Backward compatibility
        'youtube_error':   youtube_error,
        'meta': {
            'category':    category,
            'subcategory': subcategory,
            'platforms':   platforms,
            'gender':      gender,
            'country':     country,
            'state':       state,
            'contract':    contract,
            'algorithm':   res_data.get('algorithm', 'Transformer Cosine Similarity + Weighted ML Scoring'),
            'live_sync':   'YouTube' in platforms and not youtube_error
        }
    })

@app.route('/api/trending')
def trending():
    limit = min(int(request.args.get('limit', 6)), 12)
    return jsonify({'trending': ml.get_trending(limit)})

@app.route('/api/stats')
def stats():
    return jsonify(ml.get_stats())

@app.route('/api/currencies')
def currencies():
    return jsonify({'rates': CURRENCY_RATES, 'symbols': CURRENCY_SYMBOLS})

@app.route('/api/categories')
def categories():
    return jsonify({
        'Fashion':   ['Streetwear','Luxury fashion','Ethnic wear','Sustainable fashion'],
        'Sports':    ['Cricket','Football','Fitness training','Outdoor adventure'],
        'Tech':      ['Smartphones','AI/ML','Gaming','Software development'],
        'Lifestyle': ['Travel','Food','Daily vlogging','Minimalism'],
        'Fitness':   ['Bodybuilding','Yoga','Home workouts','Nutrition'],
    })

@app.route('/api/negotiate', methods=['POST'])
def negotiate():
    data = request.json or {}
    inf = data.get('influencer', {})
    budget = data.get('budget', 500)
    goal = data.get('goal', 'brand awareness')
    
    name = inf.get('name', 'Creator').split()[0]
    eng = float(inf.get('engagement_rate', 0))
    followers = int(inf.get('followers', 0))
    
    script = f"Hi {name},\n\n"
    script += f"We absolutely love your content on {inf.get('platform', 'your channel')}. "
    
    if eng >= 5.0:
        script += f"Your outstanding {eng}% engagement rate shows how deeply connected your audience is. "
    elif followers >= 1000000:
        script += f"Your massive reach of over {followers//1000000}M followers is incredibly impressive. "
        
    script += f"We are launching a new campaign focused on {goal} and believe your authentic voice would be a perfect fit.\n\n"
    script += f"We have a budget of roughly ${budget} allocated for this partnership, though we are flexible depending on the scope of deliverables.\n\n"
    script += "Would you be open to a quick chat to explore this further?\n\nBest regards,\n[Your Name/Brand]"
    
    return jsonify({"script": script})

@app.route('/api/sync_youtube', methods=['POST'])
def sync_youtube():
    try:
        data = request.json or {}
        name = data.get('name')
        
        if not name:
            return jsonify({'success': False, 'error': 'Name is required'})
            
        res = youtube_api.sync_influencer(name)
        
        if isinstance(res, dict) and res.get('error') == 'quota_exceeded':
            return jsonify({'success': False, 'error': 'YouTube API Quota Exceeded. Please try again later.'})

        if res.get('error'):
            # Return 200 but with success False so the UI can show the message
            return jsonify({'success': False, 'error': res['error']})
            
        # Dynamically update the ml_engine dataframe
        ml.update_influencer_stats(name, res)
        
        # Return recomputed analysis
        analysis = ml.recompute_analysis({**res, 'name': name, 'fraud_risk': 0.05, 'keywords': '', 'content_type': ''}, 'Fashion', 'General')
        return jsonify({'success': True, **res, **analysis})
        
    except Exception as e:
        print(f"[Server] Crash in sync_youtube: {e}")
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
