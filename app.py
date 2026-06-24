import os
import uuid
import glob
import json
import subprocess
import threading
import time
from flask import Flask, request, jsonify, send_file, render_template

app = Flask(__name__)
DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

jobs = {}
jobs_lock = threading.Lock()


def get_ytdlp_path():
    """Tự động tìm kiếm đường dẫn yt-dlp trong môi trường ảo venv của dự án"""
    venv_dir = os.path.join(os.path.dirname(__file__), "venv")
    if os.path.exists(venv_dir):
        # Windows
        win_path = os.path.join(venv_dir, "Scripts", "yt-dlp.exe")
        if os.path.exists(win_path):
            return win_path
        # Unix/Linux/macOS
        unix_path = os.path.join(venv_dir, "bin", "yt-dlp")
        if os.path.exists(unix_path):
            return unix_path
    return "yt-dlp"


def run_download(job_id, url, format_choice, format_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return
    out_template = os.path.join(DOWNLOAD_DIR, f"{job_id}.%(ext)s")

    ytdlp_bin = get_ytdlp_path()
    cmd = [ytdlp_bin, "--no-playlist", "-o", out_template]

    if format_choice == "audio":
        cmd += ["-x", "--audio-format", "mp3"]
    elif format_id:
        cmd += ["-f", f"{format_id}+bestaudio/best", "--merge-output-format", "mp4"]
    else:
        cmd += ["-f", "bestvideo+bestaudio/best", "--merge-output-format", "mp4"]

    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            job["status"] = "error"
            job["error"] = result.stderr.strip().split("\n")[-1]
            return

        files = glob.glob(os.path.join(DOWNLOAD_DIR, f"{job_id}.*"))
        if not files:
            job["status"] = "error"
            job["error"] = "Tải xong nhưng không tìm thấy file"
            return

        if format_choice == "audio":
            target = [f for f in files if f.endswith(".mp3")]
            chosen = target[0] if target else files[0]
        else:
            target = [f for f in files if f.endswith(".mp4")]
            chosen = target[0] if target else files[0]

        for f in files:
            if f != chosen:
                try:
                    os.remove(f)
                except OSError:
                    pass

        job["status"] = "done"
        job["file"] = chosen
        ext = os.path.splitext(chosen)[1]
        title = job.get("title", "").strip()
        # Sanitize title for filename
        if title:
            safe_title = "".join(c for c in title if c not in r'\/:*?"<>|').strip()[:20].strip()
            job["filename"] = f"{safe_title}{ext}" if safe_title else os.path.basename(chosen)
        else:
            job["filename"] = os.path.basename(chosen)
    except subprocess.TimeoutExpired:
        job["status"] = "error"
        job["error"] = "Hết thời gian tải (giới hạn 5 phút)"
    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def get_info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "Chưa nhập đường dẫn"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "Đường dẫn không hợp lệ. Phải bắt đầu bằng http:// hoặc https://"}), 400

    ytdlp_bin = get_ytdlp_path()
    cmd = [ytdlp_bin, "--no-playlist", "-j", url]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            return jsonify({"error": result.stderr.strip().split("\n")[-1]}), 400

        info = json.loads(result.stdout)

        # Build quality options — keep best format per resolution
        best_by_height = {}
        for f in info.get("formats", []):
            height = f.get("height")
            if height and f.get("vcodec", "none") != "none":
                tbr = f.get("tbr") or 0
                if height not in best_by_height or tbr > (best_by_height[height].get("tbr") or 0):
                    best_by_height[height] = f

        formats = []
        for height, f in best_by_height.items():
            formats.append({
                "id": f["format_id"],
                "label": f"{height}p",
                "height": height,
            })
        formats.sort(key=lambda x: x["height"], reverse=True)

        return jsonify({
            "title": info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration"),
            "uploader": info.get("uploader", ""),
            "formats": formats,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Hết thời gian lấy thông tin video"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.json
    url = data.get("url", "").strip()
    format_choice = data.get("format", "video")
    format_id = data.get("format_id")
    title = data.get("title", "")

    if not url:
        return jsonify({"error": "Chưa nhập đường dẫn"}), 400
    if not (url.startswith("http://") or url.startswith("https://")):
        return jsonify({"error": "Đường dẫn không hợp lệ. Phải bắt đầu bằng http:// hoặc https://"}), 400

    job_id = uuid.uuid4().hex[:10]
    with jobs_lock:
        jobs[job_id] = {
            "status": "downloading",
            "url": url,
            "title": title,
            "created_at": time.time()
        }

    thread = threading.Thread(target=run_download, args=(job_id, url, format_choice, format_id))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def check_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Không tìm thấy tác vụ"}), 404
    return jsonify({
        "status": job["status"],
        "error": job.get("error"),
        "filename": job.get("filename"),
    })


@app.route("/api/file/<job_id>")
def download_file(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job or job["status"] != "done":
        return jsonify({"error": "File chưa sẵn sàng"}), 404
    return send_file(job["file"], as_attachment=True, download_name=job["filename"])


def cleanup_old_jobs():
    """Tiến trình chạy ngầm để dọn dẹp các tệp tải về và dữ liệu task cũ sau 1 giờ"""
    while True:
        time.sleep(600)  # Chạy mỗi 10 phút
        try:
            now = time.time()
            cutoff = now - 3600  # 1 giờ trước
            
            # Xóa các file cũ trong downloads
            for filepath in glob.glob(os.path.join(DOWNLOAD_DIR, "*")):
                try:
                    if os.path.getmtime(filepath) < cutoff:
                        os.remove(filepath)
                except OSError:
                    pass
            
            # Xóa các job cũ khỏi jobs dict để tránh memory leak
            with jobs_lock:
                for j_id in list(jobs.keys()):
                    j_data = jobs[j_id]
                    if j_data.get("created_at", 0) < cutoff:
                        jobs.pop(j_id, None)
        except Exception:
            pass


# Khởi động thread dọn dẹp
cleanup_thread = threading.Thread(target=cleanup_old_jobs, daemon=True)
cleanup_thread.start()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8899))
    host = os.environ.get("HOST", "127.0.0.1")
    app.run(host=host, port=port)
