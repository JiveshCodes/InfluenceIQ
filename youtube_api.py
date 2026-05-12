import os
import json
import urllib.request
from urllib.parse import quote
import pandas as pd
import threading
from concurrent.futures import ThreadPoolExecutor

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
        # Add 10 second timeout to prevent server hanging
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        err_msg = str(e)
        print(f"[YouTube API] Request failed: {err_msg}")
        # Detect quota error
        if '403' in err_msg:
             print("[YouTube API] QUOTA EXCEEDED! Please wait 24 hours or use a new API key.")
             return {"error": "quota_exceeded", "message": "YouTube API quota exceeded."}
        return None

def get_channel_id(channel_name):
    """Search for a channel by name to get its exact YouTube Channel ID."""
    if not API_KEY:
        print("[YouTube API] No API Key found.")
        return None
        
    url = f"{BASE_URL}/search?part=snippet&q={quote(channel_name)}&type=channel&maxResults=1&key={API_KEY}"
    data = fetch_json(url)
    if isinstance(data, dict) and data.get('error') == 'quota_exceeded':
        return data
    if data and 'items' in data and len(data['items']) > 0:
        return data['items'][0]['snippet']['channelId']
    return None

def get_channel_stats(channel_id):
    """Fetch subscriber count, views, and description for a given channel ID."""
    url = f"{BASE_URL}/channels?part=statistics,snippet,contentDetails&id={channel_id}&key={API_KEY}"
    data = fetch_json(url)
    if isinstance(data, dict) and data.get('error') == 'quota_exceeded':
        return data
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
        
    return round(eng_rate, 2), avg_likes, avg_comments, video_ids[0] if video_ids else None

def get_video_sentiment(video_id):
    """Fetch recent comments and calculate a basic sentiment score."""
    if not API_KEY or not video_id:
        return 0.5 # Neutral fallback
        
    url = f"{BASE_URL}/commentThreads?part=snippet&videoId={video_id}&maxResults=20&key={API_KEY}"
    data = fetch_json(url)
    
    if not data or 'items' not in data:
        return 0.5
        
    positive_words = {'great', 'love', 'amazing', 'best', 'good', 'awesome', 'helpful', 'wow', 'nice', 'informative'}
    negative_words = {'bad', 'hate', 'boring', 'wrong', 'fake', 'worst', 'poor', 'disappointed', 'stop', 'scam'}
    
    total_score = 0
    count = 0
    
    for item in data['items']:
        text = item['snippet']['topLevelComment']['snippet']['textDisplay'].lower()
        words = text.split()
        score = 0.5 # start neutral
        for w in words:
            if w in positive_words: score += 0.1
            if w in negative_words: score -= 0.1
        total_score += max(0, min(1, score))
        count += 1
        
    return round(total_score / count, 2) if count > 0 else 0.5

def sync_influencer(name):
    """Master function: Takes a name, finds the channel, and returns fresh stats."""
    if not API_KEY or API_KEY == 'paste_your_api_key_here':
        return {"error": "Invalid or missing API Key."}
        
    print(f"[YouTube API] Syncing data for: {name}...")
    cid = get_channel_id(name)
    if isinstance(cid, dict) and cid.get('error') == 'quota_exceeded':
        return cid
    if not cid:
        return {"error": "Channel not found."}
        
    stats = get_channel_stats(cid)
    if isinstance(stats, dict) and stats.get('error') == 'quota_exceeded':
        return stats
    if not stats:
        return {"error": "Could not fetch channel statistics."}
        
    eng_rate, avg_likes, avg_comments = 0.0, 0, 0
    sentiment = 0.5
    
    try:
        if stats.get('uploads_id'):
            res_eng = get_recent_videos_engagement(stats['uploads_id'])
            if res_eng:
                eng_rate, avg_likes, avg_comments, latest_vid = res_eng
                # Attempt sentiment, but don't fail if it crashes
                try:
                    sentiment = get_video_sentiment(latest_vid)
                except:
                    sentiment = 0.5
    except Exception as e:
        print(f"[YouTube API] Error during stats extraction: {e}")

    return {
        "success": True,
        "followers": stats.get('followers', 0),
        "engagement_rate": eng_rate,
        "avg_likes": avg_likes,
        "avg_comments": avg_comments,
        "sentiment_score": sentiment,
        "keywords": stats.get('description', '')[:200]
    }

def search_influencers(category, subcategory, max_results=8):
    """Discover NEW influencers directly from YouTube based on category/niche."""
    if not API_KEY:
        return []
        
    query = f"{category} {subcategory} review"
    url = f"{BASE_URL}/search?part=snippet&q={quote(query)}&type=channel&maxResults={max_results}&key={API_KEY}"
    data = fetch_json(url)
    
    if isinstance(data, dict) and data.get('error') == 'quota_exceeded':
        return data

    discovered = []
    if data and 'items' in data:
        channel_names = [item['snippet']['channelTitle'] for item in data['items']]
        
        # Use ThreadPoolExecutor to fetch stats in parallel (FASTER)
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(sync_influencer, channel_names))
            
            for i, stats in enumerate(results):
                if stats.get('success'):
                    discovered.append({
                        'name': channel_names[i],
                        'followers': stats['followers'],
                        'engagement_rate': stats['engagement_rate'],
                        'avg_likes': stats['avg_likes'],
                        'avg_comments': stats['avg_comments'],
                        'keywords': stats['keywords']
                    })
    return discovered

if __name__ == "__main__":
    # Test block
    res = sync_influencer("MKBHD")
    print(json.dumps(res, indent=2))
