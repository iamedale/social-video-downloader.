from flask import Flask, request, send_file, Response
from TikTokApi import TikTokApi
import io

app = Flask(__name__)

@app.route("/")
def home():
    return "TikTok Downloader is ready! Use /download?url=<video-link>"

@app.route("/download")
def download():
    url = request.args.get("url")
    if not url:
        return {"error": "Please provide a TikTok video URL using ?url="}, 400

    try:
        with TikTokApi() as api:
            video = api.video(url=url)
            video_bytes = video.bytes()

            # Use an in-memory bytes buffer
            buffer = io.BytesIO(video_bytes)
            buffer.seek(0)

            # send_file or send from memory
            return send_file(
                buffer,
                mimetype="video/mp4",
                as_attachment=True,
                download_name="video.mp4"
            )

    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
