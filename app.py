# app.py
from flask import Flask, request, redirect, render_template_string, jsonify, Response
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus
import traceback

app = Flask(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36"
)

HTML_FORM = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Social Video Downloader</title>
  <style>
    body{font-family: Arial, sans-serif; max-width:720px;margin:40px auto;padding:0 16px;}
    input[type=text]{width:100%;padding:12px;border-radius:8px;border:1px solid #ccc;margin:8px 0;}
    button{padding:10px 18px;border-radius:8px;background:#1f8ef1;color:#fff;border:none;cursor:pointer;}
    .note{color:#666;font-size:0.9rem;margin-top:8px;}
    .result{margin-top:18px;padding:12px;border-radius:8px;background:#f6f9ff;}
    a.link{display:inline-block;margin:8px 0;padding:8px 12px;background:#2ecc71;color:white;border-radius:6px;text-decoration:none;}
    .error{color:#b00020}
  </style>
</head>
<body>
  <h1>Social Video Downloader</h1>
  <p class="note">Paste a TikTok video link below and click Download. This app will try several methods to get a no-watermark MP4 (redirect recommended).</p>

  <form action="/download" method="get">
    <input name="url" type="text" placeholder="Paste TikTok link (https://www.tiktok.com/…)" required>
    <label style="display:block;margin:8px 0;">
      <input type="checkbox" name="proxy"> Also offer server-proxied download (may be slower)
    </label>
    <button type="submit">Download</button>
  </form>

  {% if status %}
    <div class="result">
      {% if status.success %}
        <p><strong>Found:</strong> {{ status.method }}</p>
        <p><a class="link" href="{{ status.mp4_url }}" target="_blank" rel="noopener">Direct download / open in new tab</a></p>
        {% if status.proxy_url %}
          <p><a class="link" href="{{ status.proxy_url }}" target="_blank" rel="noopener">Server-proxied download (stream through this app)</a></p>
        {% endif %}
      {% else %}
        <p class="error"><strong>Error:</strong> {{ status.error }}</p>
        {% if status.details %}
          <pre style="white-space:pre-wrap;font-size:0.9rem;color:#333">{{ status.details }}</pre>
        {% endif %}
      {% endif %}
    </div>
  {% endif %}

  <p class="note">Respect creators' rights and platform terms — use downloads for personal/educational reasons only.</p>
</body>
</html>
"""

# ------------------------
# helper functions
# ------------------------
def extract_mp4_from_html(html):
    """Try a few HTML parsing strategies (meta tags, regex) to find a direct .mp4 URL."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # 1) Common meta properties
        for prop in ("og:video:secure_url", "og:video", "og:video:url", "og:image"):
            tag = soup.find("meta", {"property": prop})
            if tag and tag.get("content"):
                content = tag["content"]
                if ".mp4" in content:
                    return content

        # 2) Look for plain links that end with .mp4
        m = re.search(r"https?://[^\s\"'>]+\.mp4[^\s\"'>]*", html)
        if m:
            return m.group(0)

        # 3) Try to find playAddr in JS-like content (escaped)
        m2 = re.search(r'playAddr":"([^"]+)"', html)
        if m2:
            link = m2.group(1).replace("\\u0026", "&").replace("\\/", "/")
            if ".mp4" in link:
                return link

    except Exception:
        pass
    return None

def try_ssstik(url):
    """Use ssstik.io endpoint and parse the returned HTML for an mp4 link."""
    try:
        api_url = "https://ssstik.io/abc"
        headers = {"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"}
        payload = {"id": url, "locale": "en", "tt": "MzdfRFJk"}
        r = requests.post(api_url, headers=headers, data=payload, timeout=20)
        if r.status_code == 200:
            mp4 = extract_mp4_from_html(r.text)
            if mp4:
                return mp4, r.text
    except Exception:
        pass
    return None, None

def try_tikcdn(url):
    """Call tikcdn endpoint and try to parse JSON, else HTML."""
    try:
        api_url = f"https://www.tikcdn.io/ssstik/?url={quote_plus(url)}"
        headers = {"User-Agent": USER_AGENT}
        r = requests.get(api_url, headers=headers, timeout=15)
        if r.status_code == 200:
            # maybe JSON
            try:
                data = r.json()
                if isinstance(data, dict) and "video" in data and isinstance(data["video"], dict) and "url" in data["video"]:
                    return data["video"]["url"], data
            except ValueError:
                # not JSON, try HTML extraction
                mp4 = extract_mp4_from_html(r.text)
                if mp4:
                    return mp4, r.text
    except Exception:
        pass
    return None, None

def try_fetch_tiktok_page(url):
    """Request the TikTok page and try to extract mp4 from meta tags or JS."""
    try:
        headers = {"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
        r = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        if r.status_code == 200:
            mp4 = extract_mp4_from_html(r.text)
            if mp4:
                return mp4, r.text
    except Exception:
        pass
    return None, None

# Stream the remote file through this server (proxy) — use only if requested by user.
def stream_remote_file(remote_url):
    try:
        headers = {"User-Agent": USER_AGENT}
        r = requests.get(remote_url, headers=headers, stream=True, timeout=30)
        if r.status_code != 200:
            return None
        def generate():
            try:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        yield chunk
            finally:
                r.close()
        content_type = r.headers.get("Content-Type", "application/octet-stream")
        disposition = r.headers.get("Content-Disposition")
        headers_out = {"Content-Type": content_type}
        if disposition:
            headers_out["Content-Disposition"] = disposition
        else:
            headers_out["Content-Disposition"] = 'attachment; filename="video.mp4"'
        return Response(generate(), headers=headers_out)
    except Exception:
        return None

# ------------------------
# Flask routes
# ------------------------
@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_FORM)

@app.route("/download", methods=["GET"])
def download():
    url = request.args.get("url", "").strip()
    proxy = request.args.get("proxy") is not None or request.args.get("proxy") == "on"

    status = {"success": False, "method": None, "mp4_url": None, "error": None, "details": None, "proxy_url": None}

    if not url:
        status["error"] = "No URL provided. Paste a TikTok video link and try again."
        return render_template_string(HTML_FORM, status=status), 400

    try:
        # Attempt 1: ssstik.io
        mp4, details = try_ssstik(url)
        if mp4:
            status.update(success=True, method="ssstik.io", mp4_url=mp4, details=None)
            if proxy:
                status["proxy_url"] = f"/proxy?url={quote_plus(mp4)}"
            return render_template_string(HTML_FORM, status=status)

        # Attempt 2: tikcdn
        mp4, details = try_tikcdn(url)
        if mp4:
            status.update(success=True, method="tikcdn.io", mp4_url=mp4, details=None)
            if proxy:
                status["proxy_url"] = f"/proxy?url={quote_plus(mp4)}"
            return render_template_string(HTML_FORM, status=status)

        # Attempt 3: direct TikTok page scrape
        mp4, details = try_fetch_tiktok_page(url)
        if mp4:
            status.update(success=True, method="tiktok-page-scrape", mp4_url=mp4, details=None)
            if proxy:
                status["proxy_url"] = f"/proxy?url={quote_plus(mp4)}"
            return render_template_string(HTML_FORM, status=status)

        # nothing worked
        status["error"] = "Could not find a downloadable MP4 link using available methods."
        # include some debug info (truncated) if available
        status["details"] = "Tried ssstik.io, tikcdn.io, and direct page scraping. If this keeps failing, the target site may block automated requests."
        return render_template_string(HTML_FORM, status=status), 502

    except Exception as e:
        status["error"] = "Unexpected server error."
        status["details"] = traceback.format_exc()
        return render_template_string(HTML_FORM, status=status), 500

@app.route("/proxy")
def proxy_download():
    """Stream-through proxy of a remote mp4 URL. Use with caution (bandwidth)."""
    remote = request.args.get("url", "")
    if not remote:
        return "Missing url param", 400
    # basic safety: only allow obvious http(s)
    if not remote.lower().startswith(("http://", "https://")):
        return "Invalid url", 400
    streaming_resp = stream_remote_file(remote)
    if streaming_resp:
        return streaming_resp
    else:
        return "Failed to stream remote file.", 502

@app.route("/api/download")
def api_download():
    """API-style JSON endpoint that returns the first-found mp4 link (no redirects)."""
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # try the same sequence quickly and return JSON result
    try:
        mp4, _ = try_ssstik(url)
        if mp4:
            return jsonify({"method": "ssstik.io", "mp4_url": mp4})
        mp4, _ = try_tikcdn(url)
        if mp4:
            return jsonify({"method": "tikcdn.io", "mp4_url": mp4})
        mp4, _ = try_fetch_tiktok_page(url)
        if mp4:
            return jsonify({"method": "tiktok-page-scrape", "mp4_url": mp4})
        return jsonify({"error": "No mp4 found"}), 404
    except Exception as e:
        return jsonify({"error": "Server error", "details": str(e)}), 500

if __name__ == "__main__":
    # Use port 10000 for Render compatibility
    app.run(host="0.0.0.0", port=10000)
