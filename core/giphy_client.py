import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json

def get_giphy_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('GIPHY_API_KEY='):
                    return line.strip().split('=', 1)[1]
    return os.environ.get('GIPHY_API_KEY', '')

def _sanitize_url(url: str) -> str:
    return re.sub(r'([?&](?:key|api_key)=)[^&]+', r'\1***', url)

def _make_request(url, headers, timeout=15, max_retries=3):
    """Executes HTTP request with timeout and exponential backoff retry."""
    delay = 1.0
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            safe_url = _sanitize_url(url)
            if attempt == max_retries:
                print(f"[GIPHY API Error] Failed after {max_retries} attempts: {e} | URL: {safe_url[:80]}...")
                raise
            print(f"[GIPHY Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2

def search_gifs(query, limit=5, rating='g', lang='en', timeout=15):
    """
    Search GIPHY for animated GIFs.
    Returns list of dicts with id, title, width, height, mp4_url, and gif_url.
    """
    api_key = get_giphy_api_key()
    if not api_key:
        raise ValueError("GIPHY_API_KEY not found in .env!")

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={encoded_query}&limit={limit}&rating={rating}&lang={lang}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    data = _make_request(url, headers, timeout=timeout)

    results = []
    for item in data.get('data', []):
        g_id = item.get('id')
        title = item.get('title')
        images = item.get('images', {})
        
        orig = images.get('original', {})
        mp4_url = orig.get('mp4') or images.get('looping', {}).get('mp4') or images.get('hd', {}).get('mp4')
        gif_url = orig.get('url') or images.get('downsized', {}).get('url')
        
        width = int(orig.get('width', 0) or 0)
        height = int(orig.get('height', 0) or 0)

        results.append({
            'id': g_id,
            'provider': 'giphy',
            'title': title,
            'width': width,
            'height': height,
            'mp4_url': mp4_url,
            'gif_url': gif_url
        })
    return results

def search_stickers(query, limit=5, rating='g', lang='en', timeout=15):
    """
    Search GIPHY for transparent animated stickers.
    """
    api_key = get_giphy_api_key()
    if not api_key:
        raise ValueError("GIPHY_API_KEY not found in .env!")

    encoded_query = urllib.parse.quote(query)
    url = f"https://api.giphy.com/v1/stickers/search?api_key={api_key}&q={encoded_query}&limit={limit}&rating={rating}&lang={lang}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    data = _make_request(url, headers, timeout=timeout)

    results = []
    for item in data.get('data', []):
        g_id = item.get('id')
        title = item.get('title')
        images = item.get('images', {})
        
        orig = images.get('original', {})
        mp4_url = orig.get('mp4')
        gif_url = orig.get('url')
        
        width = int(orig.get('width', 0) or 0)
        height = int(orig.get('height', 0) or 0)

        results.append({
            'id': g_id,
            'provider': 'giphy',
            'title': title,
            'width': width,
            'height': height,
            'mp4_url': mp4_url,
            'gif_url': gif_url
        })
    return results

def download_file(url, output_path, timeout=25, max_retries=3, min_bytes=3000):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                safe_url = _sanitize_url(url)
                print(f"[GIPHY Download Error] Failed after {max_retries} attempts: {e} | URL: {safe_url[:80]}")
                raise
            print(f"[GIPHY Download Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
