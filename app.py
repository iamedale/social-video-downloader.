from flask import Flask, request, jsonify
from TikTokApi import TikTokApi

app = Flask(__name__)

@app.route("/")
def home():
    return "TikTok Downloader is ready! Use /download?url=<video-link>"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Please provide a TikTok video URL using ?url="}), 400

    try:
        with TikTokApi() as api:
            video = api.video(url=url)
            video_data = video.bytes()
            # Instead of sending bytes directly, return a download link
            return jsonify({"success": True, "message": "Video fetched!", "size": len(video_data)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
