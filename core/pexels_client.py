import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json

def get_pexels_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('PEXELS_API_KEY='):
                    return line.strip().split('=', 1)[1]
    return os.environ.get('PEXELS_API_KEY', '')

def _make_request(url, headers, timeout=15, max_retries=3):
    """Executes HTTP request with timeout and exponential backoff retry."""
    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if attempt == max_retries:
                print(f"[Pexels API Error] Failed after {max_retries} attempts: {e} | URL: {url[:80]}...")
                raise
            print(f"[Pexels Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2

def search_broll_video(query, orientation='portrait', per_page=5, timeout=15):
    """
    Search Pexels for stock videos matching query.
    If orientation is None or 'all', searches without orientation constraint.
    Returns list of dicts with id, duration, width, height, download_url, author.
    """
    api_key = get_pexels_api_key()
    if not api_key:
        raise ValueError("Pexels API key not found in .env!")

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.pexels.com/videos/search?query={encoded_query}&per_page={per_page}"
    if orientation and orientation != 'all':
        url += f"&orientation={orientation}"
    
    headers = {
        'Authorization': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    data = _make_request(url, headers, timeout=timeout)

    results = []
    for v in data.get('videos', []):
        v_id = v.get('id')
        duration = v.get('duration', 0)
        user = v.get('user', {}).get('name', '')
        v_url = v.get('url', '')
        
        mp4_files = [f for f in v.get('video_files', []) if f.get('file_type') == 'video/mp4']
        mp4_files.sort(key=lambda x: (x.get('height', 0) * x.get('width', 0)), reverse=True)
        best_file = mp4_files[0] if mp4_files else None

        if best_file:
            results.append({
                'id': v_id,
                'provider': 'pexels',
                'duration': duration,
                'width': best_file.get('width'),
                'height': best_file.get('height'),
                'download_url': best_file.get('link'),
                'author': user,
                'url': v_url
            })

    return results

def search_broll_photo(query, orientation='portrait', per_page=5, timeout=15):
    """
    Search Pexels for stock photos matching query.
    Returns list of dicts with id, width, height, download_url, alt.
    """
    api_key = get_pexels_api_key()
    if not api_key:
        raise ValueError("Pexels API key not found in .env!")

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page={per_page}"
    if orientation and orientation != 'all':
        url += f"&orientation={orientation}"
    
    headers = {
        'Authorization': api_key,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    data = _make_request(url, headers, timeout=timeout)

    results = []
    for p in data.get('photos', []):
        results.append({
            'id': p.get('id'),
            'provider': 'pexels',
            'width': p.get('width'),
            'height': p.get('height'),
            'download_url': p.get('src', {}).get('large2x') or p.get('src', {}).get('original'),
            'alt': p.get('alt', '')
        })
    return results

def download_file(url, output_path, timeout=25, max_retries=3, min_bytes=5000):
    """
    Downloads file atomically via a temporary file with chunked streaming.
    Verifies that the file size is >= min_bytes before renaming.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    tmp_path = output_path + ".tmp"
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp, open(tmp_path, 'wb') as out_f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    out_f.write(chunk)
            
            file_size = os.path.getsize(tmp_path)
            if file_size < min_bytes:
                raise ValueError(f"Downloaded file too small: {file_size} bytes (minimum {min_bytes} expected)")
            
            os.replace(tmp_path, output_path)
            return output_path
        except Exception as e:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass
            if attempt == max_retries:
                print(f"[Download Error] Failed after {max_retries} attempts: {e}")
                raise
            print(f"[Download Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2

def download_video(url, output_path, timeout=30):
    return download_file(url, output_path, timeout=timeout, min_bytes=20000)
