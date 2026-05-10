import os
import json
import urllib.request
from urllib.parse import quote
import pandas as pd

# Simple .env parser
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_env()

API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
BASE_URL = 'https://www.googleapis.com/youtube/v3'

def fetch_json(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"[YouTube API] Request failed: {e}")
        return None

def get_channel_id(channel_name):
    """Search for a channel by name to get its exact YouTube Channel ID."""
    if not API_KEY:
        print("[YouTube API] No API Key found.")
        return None
        
    url = f"{BASE_URL}/search?part=snippet&q={quote(channel_name)}&type=channel&maxResults=1&key={API_KEY}"
    data = fetch_json(url)
    if data and 'items' in data and len(data['items']) > 0:
        return data['items'][0]['snippet']['channelId']
    return None

def get_channel_stats(channel_id):
    """Fetch subscriber count, views, and description for a given channel ID."""
    url = f"{BASE_URL}/channels?part=statistics,snippet,contentDetails&id={channel_id}&key={API_KEY}"
    data = fetch_json(url)
    if data and 'items' in data and len(data['items']) > 0:
        item = data['items'][0]
        stats = item.get('statistics', {})
        snippet = item.get('snippet', {})
        content = item.get('contentDetails', {})
        
        return {
            'followers': int(stats.get('subscriberCount', 0)),
            'views': int(stats.get('viewCount', 0)),
            'description': snippet.get('description', ''),
            'uploads_id': content.get('relatedPlaylists', {}).get('uploads')
        }
    return None

def get_recent_videos_engagement(uploads_id, max_results=10):
    """Fetch the latest videos to calculate real-time engagement rate."""
    url = f"{BASE_URL}/playlistItems?part=contentDetails&playlistId={uploads_id}&maxResults={max_results}&key={API_KEY}"
    data = fetch_json(url)
    if not data or 'items' not in data:
        return 0.0, 0, 0
        
    video_ids = [item['contentDetails']['videoId'] for item in data['items']]
    if not video_ids:
        return 0.0, 0, 0
        
    vids_str = ','.join(video_ids)
    stats_url = f"{BASE_URL}/videos?part=statistics&id={vids_str}&key={API_KEY}"
    
    stats_data = fetch_json(stats_url)
    if not stats_data:
        return 0.0, 0, 0
    
    total_views = 0
    total_engagements = 0
    total_likes = 0
    total_comments = 0
    
    if 'items' in stats_data:
        for v in stats_data['items']:
            s = v.get('statistics', {})
            v_views = int(s.get('viewCount', 0))
            v_likes = int(s.get('likeCount', 0))
            v_comments = int(s.get('commentCount', 0))
            
            total_views += v_views
            total_likes += v_likes
            total_comments += v_comments
            total_engagements += (v_likes + v_comments)
            
    if total_views > 0:
        eng_rate = (total_engagements / total_views) * 100
    else:
        eng_rate = 0.0
        
    avg_likes = total_likes // len(video_ids) if video_ids else 0
    avg_comments = total_comments // len(video_ids) if video_ids else 0
        
    return round(eng_rate, 2), avg_likes, avg_comments

def sync_influencer(name):
    """Master function: Takes a name, finds the channel, and returns fresh stats."""
    if not API_KEY or API_KEY == 'paste_your_api_key_here':
        return {"error": "Invalid or missing API Key."}
        
    print(f"[YouTube API] Syncing data for: {name}...")
    cid = get_channel_id(name)
    if not cid:
        return {"error": "Channel not found."}
        
    stats = get_channel_stats(cid)
    if not stats:
        return {"error": "Could not fetch channel statistics."}
        
    eng_rate, avg_likes, avg_comments = 0.0, 0, 0
    if stats.get('uploads_id'):
        eng_rate, avg_likes, avg_comments = get_recent_videos_engagement(stats['uploads_id'])
        
    return {
        "success": True,
        "followers": stats['followers'],
        "engagement_rate": eng_rate,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "keywords": stats['description'][:200]  # Just use the first 200 chars for NLP
    }

if __name__ == "__main__":
    # Test block
    res = sync_influencer("MKBHD")
    print(json.dumps(res, indent=2))
