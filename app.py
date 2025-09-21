from flask import Flask, request, send_file, jsonify
from TikTokApi import TikTokApi
import io

app = Flask(__name__)

# ✅ Correct way to initialize TikTokApi (no context manager)
api = TikTokApi()

@app.route("/")
def home():
    return "TikTok Downloader is ready! Use /download?url=<video-link>"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "Please provide a TikTok video URL using ?url="}), 400

    try:
        # ✅ Fetch the video data directly
        video = api.video(url=url)
        video_bytes = video.bytes()

        # Put video bytes into a memory buffer
        buffer = io.BytesIO(video_bytes)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="tiktok_video.mp4"
        )

    except Exception as e:
        return jsonify({"error": f"Download failed: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
