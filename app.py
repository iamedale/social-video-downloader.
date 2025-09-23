from flask import Flask, request, jsonify, render_template_string, Response, send_file
import yt_dlp
import requests
import os
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
    background: #f9fafb;
    margin: 0;
    padding: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }
  /* Navbar */
  .navbar {
    width: 100%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: white;
    border-bottom: 1px solid #e5e7eb;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  .logo {
    font-size: 22px;
    font-weight: 700;
  }
  .logo span:first-child {
    color: #111;
  }
  .logo span:last-child {
    color: #2563eb;
  }
  .menu {
    font-size: 22px;
    cursor: pointer;
    user-select: none;
  }

  /* Dropdown */
  .dropdown {
    display: none;
    position: absolute;
    top: 55px;
    right: 20px;
    background: white;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    border-radius: 8px;
    overflow: hidden;
    opacity: 0;
    transform: translateY(-10px);
    transition: all 0.25s ease;
  }
  .dropdown.show {
    display: block;
    opacity: 1;
    transform: translateY(0);
  }
  .dropdown a {
    display: block;
    padding: 12px 16px;
    text-decoration: none;
    color: #333;
    font-size: 14px;
  }
  .dropdown a:hover {
    background: #f3f4f6;
  }

  .header {
    width: 100%;
    background: #2563eb;
    color: white;
    text-align: center;
    padding: 40px 20px;
    border-bottom-left-radius: 30px;
    border-bottom-right-radius: 30px;
  }
  .header h1 {
    font-size: 22px;
    margin-bottom: 8px;
  }
  .header p {
    font-size: 14px;
    opacity: 0.9;
    margin: 0;
  }

  /* Full-width Card */
  .card {
    background: white;
    border-radius: 0; /* remove own corners */
    box-shadow: 0 8px 32px rgba(0,0,0,0.05);
    padding: 20px;
    width: 100%;
    max-width: 100%; /* match header width */
    margin-top: -20px;
    border-top-left-radius: 30px;
    border-top-right-radius: 30px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  .input-group {
    display: flex;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    overflow: hidden;
    margin-bottom: 12px;
  }
  .input-group input {
    flex: 1;
    border: none;
    padding: 12px;
    font-size: 14px;
    outline: none;
  }
  .input-group button {
    background: #e5e7eb;
    border: none;
    padding: 0 16px;
    cursor: pointer;
    font-weight: 600;
  }
  .download-btn {
    background: #22c55e;
    color: white;
    padding: 14px;
    width: 100%;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    margin-bottom: 10px;
    transition: background 0.3s;
  }
  .download-btn:hover {
    background: #16a34a;
  }
  .preview {
    margin-top: 20px;
    display: none;
    text-align: left;
  }
  .preview img {
    width: 100%;
    border-radius: 12px;
    margin-bottom: 12px;
  }
  .preview h3 {
    margin: 0 0 5px 0;
    font-size: 16px;
  }
  .preview p {
    margin: 0 0 10px 0;
    font-size: 14px;
    color: gray;
  }
  select {
    width: 100%;
    padding: 10px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
    margin-bottom: 12px;
    font-size: 14px;
  }
  .secondary-btn {
    background: #3b82f6;
    color: white;
    padding: 12px;
    width: 100%;
    border: none;
    border-radius: 8px;
    font-size: 16px;
    cursor: pointer;
    margin-top: 6px;
    transition: background 0.3s;
  }
  .secondary-btn:hover {
    background: #2563eb;
  }
  .spinner {
    border: 4px solid #f3f3f3;
    border-top: 4px solid #2563eb;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    animation: spin 1s linear infinite;
    margin: 20px auto 0;
    display: none;
  }
  #spinner-text {
    text-align: center;
    margin-top: 8px;
    font-size: 14px;
    color: #555;
    display: none;
  }
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }

  /* Responsive */
  @media (max-width: 480px) {
    .input-group {
      flex-direction: column;
    }
    .input-group button {
      width: 100%;
      padding: 12px;
    }
  }
  @media (min-width: 768px) {
    .menu {
      display: none;
    }
    .dropdown {
      position: static;
      display: flex !important;
      opacity: 1 !important;
      transform: none !important;
      box-shadow: none;
      background: transparent;
    }
    .dropdown a {
      padding: 0 12px;
      color: #2563eb;
      font-weight: 500;
    }
    .dropdown a:hover {
      background: none;
      text-decoration: underline;
    }
  }
  </style>
</head>
<body>
  <!-- Top Navbar -->
  <div class="navbar">
    <div class="logo"><span>Your</span><span>Name</span></div>
    <div class="menu" onclick="toggleDropdown()">☰</div>
    <div class="dropdown" id="dropdown">
      <a href="#">🏠 Home</a>
      <a href="#">ℹ️ About</a>
      <a href="#">📂 GitHub</a>
      <a href="#">✉️ Contact</a>
    </div>
  </div>

  <div class="header">
    <h1>TikTok Video Download</h1>
    <p>Without Watermark. Fast. Works on all devices.</p>
  </div>

  <div class="card">
    <div class="input-group">
      <input type="text" id="url" placeholder="Paste TikTok link here" required>
      <button onclick="pasteLink()">📋 Paste</button>
    </div>
    <button class="download-btn" onclick="fetchInfo()">🔍 Preview</button>

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
      <button class="download-btn" onclick="startDownload('video')">⬇ Download Video</button>
      <button class="secondary-btn" onclick="startDownload('audio')">🎵 Download MP3</button>
    </div>

    <div class="spinner" id="spinner"></div>
    <div id="spinner-text">Loading...</div>
  </div>
  
<!-- Footer -->
<footer class="footer">
  <div class="footer-content">
    <div class="footer-links">
      <a href="#">Home</a> | 
      <a href="#">About</a> | 
      <a href="#">GitHub</a> | 
      <a href="#">Contact</a>
    </div>
    <div class="footer-copy">
      © 2025 <span class="brand"><span class="brand-dark">Your</span><span class="brand-blue">Name</span></span>. All rights reserved.
    </div>
  </div>
</footer>

<style>
  body { padding-bottom: 60px; }
  .footer {
    width: 100%;
    background: rgba(17, 24, 39, 0.6);
    backdrop-filter: blur(8px);
    color: #f9fafb;
    padding: 12px 20px;
    position: fixed;
    bottom: 0;
    left: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }
  .footer-content { text-align: center; font-size: 14px; }
  .footer-links { margin-bottom: 6px; }
  .footer-links a { color: #d1d5db; text-decoration: none; margin: 0 6px; transition: color 0.3s; }
  .footer-links a:hover { color: white; }
  .footer-copy { font-size: 12px; color: #e5e7eb; }
  .brand-dark { color: #111; }
  .brand-blue { color: #2563eb; }
</style>

  <script>
    const spinner = document.getElementById("spinner");
    const spinnerText = document.getElementById("spinner-text");
    const preview = document.getElementById("preview");
    const dropdown = document.getElementById("dropdown");

    function toggleDropdown() {
      dropdown.classList.toggle("show");
    }

    function pasteLink() {
      const input = document.getElementById("url");
      if (navigator.clipboard && navigator.clipboard.readText) {
        navigator.clipboard.readText()
          .then(text => { if (text) input.value = text; })
          .catch(() => alert("Clipboard access blocked. Please paste manually."));
      } else {
        alert("Your browser does not support auto-paste.");
      }
    }

    function showSpinner(message) {
      spinner.style.display = "block";
      spinnerText.style.display = "block";
      spinnerText.innerText = message;
    }

    function hideSpinner() {
      spinner.style.display = "none";
      spinnerText.style.display = "none";
    }

    async function fetchInfo() {
      const url = document.getElementById("url").value;
      if (!url) return alert("Please paste a TikTok link");

      showSpinner("Fetching video info...");
      try {
        const res = await fetch("/info?url=" + encodeURIComponent(url));
        const data = await res.json();
        if (data.error) {
          alert(data.error);
        } else {
          document.getElementById("thumbnail").src = data.thumbnail;
          document.getElementById("title").innerText = data.title;
          document.getElementById("duration").innerText = "Duration: " + data.duration + "s";
          preview.style.display = "block";
        }
      } catch (err) {
        alert("Failed to fetch video info");
      }
      hideSpinner();
    }

    function startDownload(type) {
      const url = document.getElementById("url").value;
      const quality = document.getElementById("quality").value;

      if (type === "video") {
        showSpinner("Downloading video...");
      } else {
        showSpinner("Downloading audio...");
      }

      window.location.href = "/download?url=" + encodeURIComponent(url) + "&type=" + type + "&quality=" + quality;
      setTimeout(() => { hideSpinner(); }, 5000);
    }
  </script>
</body>
</html>
<!-- paste your HTML here -->
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
                "outtmpl": "downloads/%(title)s.%(ext)s"
            }
            os.makedirs("downloads", exist_ok=True)
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    file_path = ydl.prepare_filename(info).rsplit(".", 1)[0] + ".mp3"
                return send_file(file_path, as_attachment=True)
            except Exception as e_ffmpeg:
                print("⚠️ FFmpeg not available, falling back to raw audio:", str(e_ffmpeg))
                fallback_opts = {
                    "quiet": True,
                    "format": "bestaudio/best",
                    "outtmpl": "downloads/%(title)s.%(ext)s"
                }
                with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    raw_path = ydl.prepare_filename(info)
                mp3_path = raw_path.rsplit(".", 1)[0] + ".mp3"
                os.rename(raw_path, mp3_path)
                return send_file(mp3_path, as_attachment=True)
        else:
            if quality == "720":
                fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
            elif quality == "480":
                fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
            elif quality == "360":
                fmt = "bestvideo[height<=360]+bestaudio/best[height<=360]"
            else:
                fmt = "best"
            ydl_opts = {
                "quiet": True,
                "format": fmt,
                "outtmpl": "downloads/%(title)s.%(ext)s"
            }
            os.makedirs("downloads", exist_ok=True)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                file_path = ydl.prepare_filename(info)
            return send_file(file_path, as_attachment=True)
    except Exception as e:
        print("yt-dlp failed:", str(e))

    # --- TikWM fallback with proper filename ---
    try:
        r = requests.post("https://www.tikwm.com/api/", data={"url": url})
        data = r.json()
        if data.get("data") and data["data"].get("play"):
            video_url = data["data"]["play"]
            title = data["data"].get("title", "tiktok_video").replace(" ", "_")
            ext = "mp3" if d_type == "audio" else "mp4"

            r2 = requests.get(video_url, stream=True)
            return Response(
                r2.iter_content(chunk_size=1024),
                headers={
                    "Content-Disposition": f"attachment; filename={title}.{ext}",
                    "Content-Type": "video/mp4" if d_type == "video" else "audio/mpeg"
                }
            )
        else:
            return jsonify({"error": "TikWM API failed"}), 500
    except Exception as e2:
        return jsonify({"error": f"All methods failed: {e2}"}), 500

# ----------------- Run -----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
    @keyframes fadeIn {
      from { opacity: 0; transform: scale(0.95); }
      to { opacity: 1; transform: scale(1); }
    }
    @media (max-width: 480px) {
      h1 { font-size: 22px; }
      .card { padding: 20px; }
    }
  </style>
</head>
<body>
  <div class="card">
    <h1>🎵 TikTok Downloader</h1>
    <p>Download videos without watermark • Free • Fast</p>
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
    <footer>⚡ Built with Flask + yt-dlp</footer>
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
