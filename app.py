import os
from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json() or {}
    url = data.get('url')
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'error': 'Por favor introduce una URL válida.'}), 400

    # Configuración de extracción según la opción seleccionada
    if quality == 'audio':
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
        }
    elif quality == '720':
        ydl_opts = {
            'format': 'best[height<=720]/best',
            'quiet': True,
            'no_warnings': True,
        }
    elif quality == '1080':
        ydl_opts = {
            'format': 'best[height<=1080]/best',
            'quiet': True,
            'no_warnings': True,
        }
    else:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            download_url = info.get('url')

            if not download_url:
                # Si es un formato de múltiples flujos, obtenemos el directo
                formats = info.get('formats', [])
                if formats:
                    download_url = formats[-1].get('url')

            if download_url:
                return jsonify({'download_url': download_url})
            else:
                return jsonify({'error': 'No se pudo generar el enlace de descarga.'}), 400

    except Exception as e:
        return jsonify({'error': f'Error al procesar el video: {str(e)}'}), 500

@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)