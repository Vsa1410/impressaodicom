import datetime
import os
import pydicom
from PIL import Image, ImageFont, ImageDraw
import numpy as np
from fpdf import FPDF
from io import BytesIO
from datetime import datetime
import zipfile
import tempfile
from PIL import Image
import base64
from io import BytesIO






# === CONFIGURAÇÃO DO LAYOUT ===
def gerar_relatorio_em_pdf(pasta_dicom, logo_path,
                            layout_colunas, layout_linhas,
                            fator_brilho, output_path, fator_contraste):

    # A3 em orientação vertical
    largura_pagina_mm = 297
    altura_pagina_mm = 400
    espacamento = 0
    # === CALCULAR TAMANHO DAS IMAGENS ===
    largura_img_mm = (largura_pagina_mm - (layout_colunas + 1) * espacamento) / layout_colunas
    altura_img_mm = (altura_pagina_mm - (layout_linhas + 1) * espacamento) / layout_linhas
    if largura_img_mm <= 0 or altura_img_mm <= 0:
        raise ValueError(f"Tamanho da imagem em mm inválido: largura={largura_img_mm}, altura={altura_img_mm}")
    
    # === Preparar DICOMs ===
    pasta_dicom
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
            data_paciente_formatada = datetime.strptime(nascimento, "%Y%m%d").strftime("%d/%m/%Y")
            sexo = str(ds.get("PatientSex", "N/A"))
            if sexo == "M":
                sexo = "Masculino"
            elif sexo == "F":
                sexo = "Feminino"
            metadados_paciente = f"""Paciente: {nome} | Protocolo: {id_paciente} | 
                    Data de Nascimento: {data_paciente_formatada} | Sexo: {sexo}"""

        imagem = ds.pixel_array

        # Normalização de brilho
        imagem_normalizada = np.clip((imagem / imagem.max()) * 255 * fator_brilho, 0, 255)

        # Aplicando brilho (já calculado) e depois o contraste
        imagem_float = imagem_normalizada.astype(np.float32)
        media = np.mean(imagem_float)
        imagem_contraste = np.clip((imagem_float - media) * fator_contraste + media, 0, 255)

        imagem_uint8 = imagem_contraste.astype(np.uint8)  # Resultado final após brilho e contraste
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
        
        offset_x = (max_w_px - novo_w) // 2
        offset_y = (max_h_px - novo_h) // 2
        
        
        fundo.paste(img_resized, (offset_x, offset_y))

        # Inserir dados do exame na primeira imagem (linha 0, coluna 0)
        if linha == 0 and coluna == 0:
            exame = ds.get("StudyDescription", "Exame não especificado")
            data_exame = ds.get("StudyDate", "00000000")
            corte = ds.get("SeriesDescription", "Serie não especificada")
            data_exame = ds.get("StudyDate", "")
            data_exame = str(ds.get("StudyDate", "")).strip()
            data_exame_raw = str(ds.get("StudyDate", "")).strip()
            if len(data_exame_raw) == 8:
                data_exame_raw = data_exame_raw[:4] + data_exame_raw[4:6] + data_exame_raw[6:]

            data_exame_formatada = datetime.strptime(data_exame_raw, "%Y%m%d").strftime("%d/%m/%Y")



            draw = ImageDraw.Draw(fundo)
            texto = f"""Exame: {exame} - 
                        Data: {data_exame_formatada}
                        Sequencia: {corte}"""
            try:
                fonte_texto = ImageFont.truetype("arial.ttf", 40)
            except:
                fonte_texto = ImageFont.load_default()
            draw.text((10, 10), texto, fill=255, font=fonte_texto)

        img_path = f"temp_{i}.jpg"
        fundo.save(img_path)

        x = espacamento + coluna * (largura_img_mm + espacamento)
        y = y0 + linha * (altura_img_mm + espacamento)
        pdf.image(img_path, x=x, y=y, w=largura_img_mm, h=altura_img_mm)
        os.remove(img_path)

    pdf_bytes = pdf.output(dest='S').encode('latin1')  # conteúdo em bytes
    buffer = BytesIO(pdf_bytes)
    buffer.seek(0)
    return buffer

    
