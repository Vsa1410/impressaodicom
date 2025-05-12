from flask import Flask, render_template, request, send_file
from gerar_pdf import gerar_relatorio_em_pdf  # sua função com todos os argumentos
import io

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/gerar-pdf', methods=['POST'])
def gerar_pdf():
    pasta_dicom = request.form.get('pasta_dicom')
    logo_path = request.form.get('logo_path')
    colunas = int(request.form.get('colunas', 4))
    linhas = int(request.form.get('linhas', 6))
    brilho = float(request.form.get('brilho', 1.2))
    contraste = float(request.form.get('contraste', 1.0))
    espacamento = float(request.form.get('espacamento', 0))
    largura_pagina_mm = float(request.form.get('largura_pagina_mm', 297))
    altura_pagina_mm = float(request.form.get('altura_pagina_mm', 400))
    
    # Gerar o PDF em memória (em vez de salvar no disco)
    output = io.BytesIO()
    pdf_buffer = gerar_relatorio_em_pdf(
    pasta_dicom,
    logo_path,
    colunas,
    linhas,
    brilho,
    None,  # output_path agora não é necessário
    contraste
)

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        download_name='relatorio.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)
