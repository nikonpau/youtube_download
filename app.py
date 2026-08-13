import os
import time
import threading
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
import yt_dlp

app = Flask(__name__)
DOWNLOAD_FOLDER = 'downloads'

if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Diccionario global para guardar el progreso de cada descarga
PROGRESS = {}

def progress_hook(d, download_id):
    if d['status'] == 'downloading':
        total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        downloaded = d.get('downloaded_bytes', 0)
        if total > 0:
            percentage = int((downloaded / total) * 100)
            PROGRESS[download_id] = percentage
    elif d['status'] == 'finished':
        PROGRESS[download_id] = 100

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress/<download_id>')
def get_progress(download_id):
    percent = PROGRESS.get(download_id, 0)
    return jsonify({'progress': percent})

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'best')
    download_id = data.get('download_id')

    if not url:
        return {'error': 'Por favor introduce una URL válida.'}, 400

    out_template = os.path.join(DOWNLOAD_FOLDER, f'%(id)s_{download_id}.%(ext)s')

    if quality == '1080':
        fmt = 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif quality == '720':
        fmt = 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    elif quality == 'audio':
        fmt = 'bestaudio/best'
    else:
        fmt = 'bestvideo+bestaudio/best'

    ydl_opts = {
        'format': fmt,
        'outtmpl': out_template,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: progress_hook(d, download_id)],
        'extractor_args': {
            'youtube': {
                'player_client': ['web_creator', 'android', 'ios'],
                'player_skip': ['configs', 'webpage']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        @after_this_request
        def remove_file(response):
            try:
                if os.path.exists(filename):
                    os.remove(filename)
                PROGRESS.pop(download_id, None)
            except Exception as e:
                app.logger.error(f"Error limpiando archivo: {e}")
            return response

        title = info.get('title', 'video')
        ext = info.get('ext', 'mp4')
        return send_file(filename, as_attachment=True, download_name=f"{title}.{ext}")
    except Exception as e:
        PROGRESS.pop(download_id, None)
        return {'error': f'Error al procesar el video: {str(e)}'}, 500

# --- RUTA PARA EL SERVICE WORKER DE OUTPUSH ---
@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)