import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json

def get_pixabay_api_key():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('PIXABAY_API_KEY='):
                    return line.strip().split('=', 1)[1]
    return os.environ.get('PIXABAY_API_KEY', '')

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
                print(f"[Pixabay API Error] Failed after {max_retries} attempts: {e} | URL: {safe_url[:80]}...")
                raise
            print(f"[Pixabay Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2

def search_pixabay_videos(query, per_page=5, timeout=15):
    """
    Search Pixabay for stock videos.
    """
    api_key = get_pixabay_api_key()
    if not api_key:
        raise ValueError("PIXABAY_API_KEY not found in .env!")

    per_page = max(3, min(200, per_page))
    encoded_query = urllib.parse.quote(query)
    url = f"https://pixabay.com/api/videos/?key={api_key}&q={encoded_query}&per_page={per_page}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    data = _make_request(url, headers, timeout=timeout)

    results = []
    for hit in data.get('hits', []):
        v_id = hit.get('id')
        duration = hit.get('duration', 0)
        videos = hit.get('videos', {})
        best = videos.get('large') or videos.get('medium') or videos.get('small')
        if best and best.get('url'):
            results.append({
                'id': v_id,
                'provider': 'pixabay',
                'duration': duration,
                'width': best.get('width'),
                'height': best.get('height'),
                'download_url': best.get('url'),
                'tags': hit.get('tags', '')
            })
    return results

def search_pixabay_images(query, orientation='vertical', per_page=5, timeout=15):
    """
    Search Pixabay for stock images (vertical or any).
    """
    api_key = get_pixabay_api_key()
    if not api_key:
        raise ValueError("PIXABAY_API_KEY not found in .env!")

    per_page = max(3, min(200, per_page))
    encoded_query = urllib.parse.quote(query)
    url = f"https://pixabay.com/api/?key={api_key}&q={encoded_query}&per_page={per_page}"
    if orientation and orientation != 'all':
        url += f"&orientation={orientation}"
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    data = _make_request(url, headers, timeout=timeout)

    results = []
    for hit in data.get('hits', []):
        results.append({
            'id': hit.get('id'),
            'provider': 'pixabay',
            'width': hit.get('imageWidth'),
            'height': hit.get('imageHeight'),
            'download_url': hit.get('largeImageURL') or hit.get('webformatURL'),
            'tags': hit.get('tags', '')
        })
    return results

def download_file(url, output_path, timeout=25, max_retries=3, min_bytes=5000):
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
                print(f"[Pixabay Download Error] Failed after {max_retries} attempts: {e} | URL: {safe_url[:80]}")
                raise
            print(f"[Pixabay Download Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
            delay *= 2
