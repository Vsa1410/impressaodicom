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

import os
import zipfile
import tempfile

def extrair_zip_para_temp(zip_path):
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    imagens_path = os.path.join(temp_dir, "Imagenes")
    if not os.path.exists(imagens_path):
        raise FileNotFoundError("Pasta 'Imagenes' não encontrada dentro do ZIP.")

    # Listar os diretórios dentro de Imagenes (ex: serie_0, serie_1)
    series = [
        os.path.join(imagens_path, d)
        for d in os.listdir(imagens_path)
        if os.path.isdir(os.path.join(imagens_path, d))
    ]
    
    return series  # retorna lista dos caminhos das sequências



def obter_descricoes_series(pasta_dicom):
    descricoes = []
    for raiz, dirs, _ in os.walk(pasta_dicom):
        for pasta in dirs:
            caminho_serie = os.path.join(raiz, pasta)
            arquivos = [f for f in os.listdir(caminho_serie) if f.lower().endswith('.dcm')]
            if arquivos:
                dicom_path = os.path.join(caminho_serie, arquivos[0])
                ds = pydicom.dcmread(dicom_path, stop_before_pixels=True)
                descricao = ds.SeriesDescription if 'SeriesDescription' in ds else pasta
                descricoes.append({'pasta': caminho_serie, 'descricao': descricao})
    return descricoes

def dicom_para_base64(path_dcm):
    ds = pydicom.dcmread(path_dcm)
    img = Image.fromarray(ds.pixel_array)
    img.thumbnail((256, 256))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")