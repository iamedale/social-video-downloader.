from flask import Flask, request, jsonify, redirect, render_template_string
import requests

app = Flask(__name__)

HTML_FORM = """
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Video Downloader</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        input { width: 80%; padding: 10px; margin: 10px 0; border-radius: 8px; border: 1px solid #ccc; }
        button { padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 8px; cursor: pointer; }
        button:hover { background: #45a049; }
    </style>
</head>
<body>
    <h1>Download TikTok Videos</h1>
    <form action="/download" method="get">
        <input type="text" name="url" placeholder="Paste TikTok link here" required>
        <br>
        <button type="submit">Download</button>
    </form>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML_FORM)

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Please provide a TikTok video URL"}), 400

    try:
        # SSSTik backend API endpoint
        api_url = "https://ssstik.io/abc"  # SSSTik uses POST requests
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0"
        }
        payload = {"id": url, "locale": "en", "tt": "MzdfRFJk"}
        response = requests.post(api_url, headers=headers, data=payload)

        if response.status_code == 200 and "url" in response.text:
            # Find direct download link in response text
            # We just look for the first href ending with .mp4
            import re
            match = re.search(r'href="([^"]+\.mp4)"', response.text)
            if match:
                return redirect(match.group(1), code=302)

        return jsonify({"error": "Could not find a downloadable link."}), 500

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
