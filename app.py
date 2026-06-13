import os
import requests
import urllib.parse
import re
from bs4 import BeautifulSoup
from flask import Flask, render_template_string, request, jsonify

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pinkle Library</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f0f2f5; margin: 0; padding: 20px; }
        .container { max-width: 100%; margin: auto; background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
        h2 { text-align: center; color: #1a1a1a; margin-top: 0; }
        input[type="text"] { width: 100%; padding: 14px; margin-bottom: 12px; border: 1px solid #ccc; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
        button { width: 100%; padding: 14px; background: #6200ea; color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:active { background: #3700b3; }
        ul { list-style-type: none; padding: 0; margin-top: 20px; }
        li { padding: 16px; border-bottom: 1px solid #eee; display: flex; flex-direction: column; background: #fafafa; margin-bottom: 8px; border-radius: 8px; }
        .title { font-weight: 600; color: #333; font-size: 15px; }
        a { text-decoration: none; color: white; background: #03dac6; text-align: center; font-weight: bold; margin-top: 10px; padding: 10px; border-radius: 6px; }
        .loading { text-align: center; color: #666; font-style: italic; display: none; margin-top: 15px; font-weight: bold; }
        .error { color: #b00020; font-weight: bold; text-align: center; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2>📚 Pinkle Library (Render Cloud)</h2>
        <input type="text" id="query" placeholder="🔎 Nome do livro ou autor...">
        <button onclick="buscar()">Buscar no Acervo</button>
        <div id="loading" class="loading">⏳ Consultando servidores...</div>
        <ul id="results"></ul>
    </div>

    <script>
        function buscar() {
            const query = document.getElementById('query').value;
            if(!query) return;
            
            document.getElementById('loading').style.display = 'block';
            document.getElementById('results').innerHTML = '';
            
            fetch('/search?q=' + encodeURIComponent(query))
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    const ul = document.getElementById('results');
                    if(data.error) {
                        ul.innerHTML = `<li class="error">❌ ${data.error}</li>`;
                    } else {
                        data.forEach(item => {
                            const li = document.createElement('li');
                            li.innerHTML = `<span class="title">${item.title}</span> 
                                            <a href="${item.link}" target="_blank">📥 Abrir Download</a>`;
                            ul.appendChild(li);
                        });
                    }
                })
                .catch(() => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('results').innerHTML = '<li class="error">❌ Erro de conexão com o motor.</li>';
                });
        }
    </script>
</body>
</html>
"""

MIRRORS = ["https://annas-archive.li", "https://annas-archive.vg", "https://annas-archive.gl"]
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

@app.route('/')
def index():
    return render_template_string(HTML_PAGE)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query: return jsonify([])

    q = urllib.parse.quote(query)
    for mirror in MIRRORS:
        try:
            url = f"{mirror}/search?q={q}&lang=pt"
            res = requests.get(url, headers=HEADERS, timeout=15)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                items = soup.find_all('a', href=re.compile(r'^/md5/'))
                if not items: continue
                
                results = []
                for item in items[:20]:
                    title = item.get_text().strip()
                    title = re.sub(r'\s+', ' ', title)[:80]
                    link = mirror + item['href']
                    results.append({'title': title, 'link': link})
                return jsonify(results)
        except:
            continue
            
    return jsonify({'error': 'Servidores indisponíveis ou tráfego bloqueado.'})

# O Render.com gerencia a inicialização usando Gunicorn, não precisamos do app.run()
