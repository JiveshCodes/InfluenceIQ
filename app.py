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
    platform    = data.get('platform') or None
    budget      = data.get('budget') or None
    country     = data.get('country') or None
    state       = data.get('state') or None
    limit       = data.get('limit', 12)
    page        = data.get('page', 1)

    if not category or not subcategory:
        return jsonify({'error':'category and subcategory required'}), 400

    res_data = ml.predict(category, subcategory, platform, budget, country, state, limit, page)

    return jsonify({
        'results':         res_data['results'],
        'total_available': res_data['total_available'],
        'page':            res_data['page'],
        'limit':           res_data['limit'],
        'has_more':        res_data['has_more'],
        'total':           len(res_data['results']), # Backward compatibility
        'meta': {
            'category':    category,
            'subcategory': subcategory,
            'platform':    platform,
            'country':     country,
            'state':       state,
            'algorithm':   res_data.get('algorithm', 'Transformer Cosine Similarity + Weighted ML Scoring'),
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
    data = request.json or {}
    name = data.get('name')
    
    if not name:
        return jsonify({'error': 'Name is required'}), 400
        
    res = youtube_api.sync_influencer(name)
    if res.get('error'):
        return jsonify(res), 500
        
    # Dynamically update the ml_engine dataframe so the ML accuracy uses real live data!
    ml.update_influencer_stats(name, res)
    return jsonify(res)

if __name__ == '__main__':
    app.run(debug=True, port=5000, host='0.0.0.0')
