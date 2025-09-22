from flask import Flask, request, jsonify, render_template_string, Response
import yt_dlp
import requests
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# ----------------- HTML Frontend -----------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TikTok Downloader</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Poppins', sans-serif;
      background: linear-gradient(135deg, #22c1c3, #fdbb2d);
      display: flex;
      justify-content: center;
      align-items: center;
      height: 100vh;
      margin: 0;
    }
    .card {
      backdrop-filter: blur(12px) saturate(180%);
      -webkit-backdrop-filter: blur(12px) saturate(180%);
      background: rgba(255, 255, 255, 0.2);
      border-radius: 16px;
      padding: 30px;
      width: 90%;
      max-width: 420px;
      text-align: center;
      color: #fff;
      box-shadow: 0 8px 32px rgba(0,0,0,0.25);
    }
    h1 {
      margin-bottom: 10px;
      font-size: 24px;
      font-weight: 600;
    }
    input, select {
      width: 100%;
      padding: 12px;
      margin: 12px 0;
      border: none;
      border-radius: 8px;
      outline: none;
      font-size: 14px;
    }
    button {
      background: #22c55e;
      color: #fff;
      padding: 12px;
      width: 100%;
      border: none;
      border-radius: 8px;
      cursor: pointer;
      font-size: 16px;
      margin-top: 8px;
      transition: background 0.3s ease, transform 0.2s;
    }
    button:hover:enabled {
      background: #16a34a;
      transform: translateY(-2px);
    }
    button:disabled {
      background: #9ca3af;
      cursor: not-allowed;
    }
    .preview {
      margin-top: 20px;
      display: none;
    }
    .preview img {
      width: 100%;
      border-radius: 12px;
      margin-bottom: 12px;
      box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    .spinner {
      border: 4px solid rgba(255,255,255,0.3);
      border-top: 4px solid #22c55e;
      border-radius: 50%;
      width: 32px;
      height: 32px;
      animation: spin 1s linear infinite;
      margin: 20px auto 0;
      display: none;
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>🎵 TikTok Downloader</h1>
    <p style="font-size:14px; margin-bottom:15px;">Download videos without watermark • Free • Fast</p>
    <input type="text" id="url" placeholder="Paste TikTok link here" required>
    <button onclick="fetchInfo()">🔍 Preview</button>

    <div class="preview" id="preview">
      <img id="thumbnail" src="">
      <h3 id="title"></h3>
      <p id="duration"></p>
      <select id="quality">
        <option value="best">Best Quality</option>
        <option value="720">720p</option>
        <option value="480">480p</option>
        <option value="360">360p</option>
      </select>
      <button onclick="startDownload('video')">⬇ Download Video</button>
      <button onclick="startDownload('audio')">🎵 Download MP3</button>
    </div>

    <div class="spinner" id="spinner"></div>
  </div>
</body>
</html>
"""

# ----------------- Backend -----------------
@app.route("/")
def home():
    return render_template_string(HTML_PAGE)

# Get video info
@app.route("/info")
def info():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)
            return jsonify({
                "title": info.get("title"),
                "thumbnail": info.get("thumbnail"),
                "duration": info.get("duration"),
            })
    except Exception:
        # fallback to TikWM API
        try:
            r = requests.post("https://www.tikwm.com/api/", data={"url": url})
            data = r.json()
            if data.get("data"):
                return jsonify({
                    "title": data["data"].get("title", "Unknown"),
                    "thumbnail": data["data"].get("cover", ""),
                    "duration": data["data"].get("duration", 0),
                })
        except Exception as e2:
            return jsonify({"error": f"All methods failed: {e2}"}), 500

# Download route
@app.route("/download")
def download():
    url = request.args.get("url")
    d_type = request.args.get("type", "video")
    quality = request.args.get("quality", "best")

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    # --- yt-dlp first ---
    try:
        if d_type == "audio":
            ydl_opts = {
                "quiet": True,
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            }
            filename = "audio.mp3"
            content_type = "audio/mpeg"
        else:
            if quality == "720":
                fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
            elif quality == "480":
                fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
            elif quality == "360":
                fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]"
            else:
                fmt = "best"

            ydl_opts = {"quiet": True, "format": fmt}
            filename = "video.mp4"
            content_type = "video/mp4"

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get("url")

            r = requests.get(download_url, stream=True)
            return Response(
                r.iter_content(chunk_size=1024),
                headers={
                    "Content-Disposition": f"attachment; filename={filename}",
                    "Content-Type": content_type
                }
            )
    except Exception as e:
        print("yt-dlp failed:", str(e))

    # --- TikWM fallback ---
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url})
        data = r.json()
        if data.get("data") and data["data"].get("play"):
            video_url = data["data"]["play"]
            r2 = requests.get(video_url, stream=True)
            return Response(
                r2.iter_content(chunk_size=1024),
                headers={
                    "Content-Disposition": "attachment; filename=video.mp4",
                    "Content-Type": "video/mp4"
                }
            )
        else:
            return jsonify({"error": "TikWM API failed"}), 500
    except Exception as e2:
        return jsonify({"error": f"All methods failed: {e2}"}), 500


# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)                    return mp4, r.text
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
