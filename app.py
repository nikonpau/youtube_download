import os
import requests
from flask import Flask, render_template, request, send_file, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/progress/<download_id>')
def get_progress(download_id):
    # Con la API externa no hay barra de progreso por bloques, 
    # simulamos un 100% inmediato al responder
    return jsonify({'progress': 100})

@app.route('/download', methods=['POST'])
def download_video():
    data = request.get_json()
    url = data.get('url')
    quality = data.get('quality', 'best')

    if not url:
        return jsonify({'error': 'Por favor introduce una URL válida.'}), 400

    # Mapeo de calidad para la API
    v_quality = '1080'
    if quality == '720':
        v_quality = '720'
    elif quality == 'audio':
        v_quality = 'audio'

    try:
        # Petición a la API externa para esquivar el bloqueo de IP
        response = requests.post(
            'https://api.cobalt.tools/api/json',
            headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={
                'url': url,
                'vQuality': v_quality,
                'isAudioOnly': True if quality == 'audio' else False
            }
        )
        
        result = response.json()

        # Si nos devuelve una URL directa para descargar
        if result.get('status') in ['stream', 'redirect', 'tunnel']:
            return jsonify({'download_url': result.get('url')})
        elif result.get('status') == 'picker':
            # Si hay múltiples archivos (ej. lista/playlist), cogemos el primero
            picker_items = result.get('picker', [])
            if picker_items:
                return jsonify({'download_url': picker_items[0].get('url')})
            return jsonify({'error': 'No se encontró un enlace válido.'}), 400
        else:
            return jsonify({'error': 'No se pudo procesar el video. Inténtalo de nuevo.'}), 400

    except Exception as e:
        return jsonify({'error': f'Error en el servidor: {str(e)}'}), 500

# --- RUTA PARA EL SERVICE WORKER DE OUTPUSH ---
@app.route('/sw.js')
def service_worker():
    return send_file('sw.js', mimetype='application/javascript')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)