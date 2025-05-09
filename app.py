import datetime
import os
import pydicom
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from fpdf import FPDF

# === CONFIGURAÇÃO DO LAYOUT ===
layout_colunas = 4
layout_linhas = 3
espacamento = 0

largura_pagina_mm = 297
altura_pagina_mm = 400  # A3 em orientação vertical

# === CALCULAR TAMANHO DAS IMAGENS ===
largura_img_mm = (largura_pagina_mm - (layout_colunas + 1) * espacamento) / layout_colunas
altura_img_mm = (altura_pagina_mm - (layout_linhas + 1) * espacamento) / layout_linhas

# === Fonte para cabeçalho ===
try:
    fonte = ImageFont.truetype("arial.ttf", 18)
except:
    fonte = ImageFont.load_default()

# === Preparar DICOMs ===
pasta_dicom = "dicoms/"
arquivos_dcm = [f for f in os.listdir(pasta_dicom) if f.endswith(".dcm")]
arquivos_dcm.sort(key=lambda f: pydicom.dcmread(os.path.join(pasta_dicom, f)).InstanceNumber)

metadados_paciente = ""
imagens_convertidas = []

for arquivo in arquivos_dcm:
    caminho = os.path.join(pasta_dicom, arquivo)
    ds = pydicom.dcmread(caminho)

    if not metadados_paciente:
        nome = str(ds.get("PatientName", "Desconhecido"))
        id_paciente = str(ds.get("PatientID", "N/A"))
        nascimento = str(ds.get("PatientBirthDate", "N/A"))
        sexo = str(ds.get("PatientSex", "N/A"))
        metadados_paciente = f"Paciente: {nome} | Protocolo: {id_paciente} | Nascimento: {nascimento} | Sexo: {sexo}"

    imagem = ds.pixel_array
    fator_brilho = 1.2  # Aumente (>1.0) para mais brilho, diminua (<1.0) para menos
    imagem_normalizada = np.clip((imagem / imagem.max()) * 255 * fator_brilho, 0, 255) 
    imagem_uint8 = imagem_normalizada.astype(np.uint8)
    imagem_pil = Image.fromarray(imagem_uint8).convert("L")
    imagens_convertidas.append(imagem_pil)

# === Criar PDF ===
pdf = FPDF(orientation='P', unit='mm', format='A3')

logo_path = "logo.jpg"
logo_largura_mm = 40
logo_altura_mm = 15
margem_topo = 5
margem_esquerda = 5

def adicionar_cabecalho():
    pdf.add_page()
    pdf.image(logo_path, x=margem_esquerda, y=margem_topo, w=logo_largura_mm, h=logo_altura_mm)
    pdf.set_xy(margem_esquerda + logo_largura_mm + 5, margem_topo)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 6, metadados_paciente)
    return margem_topo + logo_altura_mm + 5  # y inicial após o cabeçalho

y0 = adicionar_cabecalho()
contador = 0
total_imagens_por_pagina = layout_colunas * layout_linhas

for i, img in enumerate(imagens_convertidas):
    linha = (i % total_imagens_por_pagina) // layout_colunas
    coluna = (i % total_imagens_por_pagina) % layout_colunas

    if i != 0 and i % total_imagens_por_pagina == 0:
        y0 = adicionar_cabecalho()  # Nova página com cabeçalho

    max_w_px = int(largura_img_mm * 11.81)
    max_h_px = int(altura_img_mm * 11.81)

    img_w, img_h = img.size
    proporcao = max(max_w_px / img_w, max_h_px / img_h)
    novo_w = int(img_w * proporcao)
    novo_h = int(img_h * proporcao)
    img_resized = img.resize((novo_w, novo_h))

    # Criar uma imagem de fundo branca no tamanho ideal e colar a imagem centralizada
    fundo = Image.new("L", (max_w_px, max_h_px), color=255)
    offset_x = (max_w_px - novo_w)  
    offset_y = (max_h_px - novo_h) // 2
    fundo.paste(img_resized, (offset_x, offset_y))

    # Inserir dados do exame na primeira imagem (linha 0, coluna 0)
    if linha == 0 and coluna == 0:
        exame = ds.get("StudyDescription", "Exame não especificado")
        data_exame = ds.get("StudyDate", "00000000")
        try:
            data_exame_formatada = datetime.strptime(data_exame, "%Y%m%d").strftime("%d/%m/%Y")
        except:
            data_exame_formatada = data_exame

        draw = ImageDraw.Draw(fundo)
        texto = f"{exame} - {data_exame_formatada}"
        try:
            fonte_texto = ImageFont.truetype("arial.ttf", 22)
        except:
            fonte_texto = ImageFont.load_default()
        draw.text((10, 10), texto, fill=255, font=fonte_texto)


    img_path = f"temp_{i}.jpg"
    fundo.save(img_path)

    x = espacamento + coluna * (largura_img_mm + espacamento)
    y = y0 + linha * (altura_img_mm + espacamento)
    pdf.image(img_path, x=x, y=y, w=largura_img_mm, h=altura_img_mm)
    os.remove(img_path)

# === Salvar PDF ===
pdf.output("laudo_A3.pdf")
print("PDF gerado com cabeçalho em todas as páginas.")
