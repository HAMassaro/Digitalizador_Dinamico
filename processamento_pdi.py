import cv2
import numpy as np
import pytesseract
import json
import re
from collections import OrderedDict

#define o caminho do Tesseract p windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def digitalizar_formulario_dinamico(caminho_imagem, rotulos_map_usuario):

    #carrega a imagem e converte para escala de cinza
    imagem = cv2.imread(caminho_imagem)
    if imagem is None:
        return {"erro": f"Não foi possível carregar a imagem: {caminho_imagem}"}
        
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
    
    #redimensionamento p/ melhorar a precisão do OCR
    fator_escala = 2
    largura = int(cinza.shape[1] * fator_escala)
    altura = int(cinza.shape[0] * fator_escala)
    dimensoes = (largura, altura)
    imagem_ampliada = cv2.resize(cinza, dimensoes, interpolation=cv2.INTER_CUBIC)

    #binarização com metodo de Otsu, converte para P&B buscando o limiar ideal automaticamente
    _, imagem_final_pdi = cv2.threshold(imagem_ampliada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    #arquivo de debug para ver o que o Tesseract ta recebendo
    cv2.imwrite("debug_para_tesseract.png", imagem_final_pdi)

    #config do OCR
    config_ocr = r'--oem 3 --psm 4' 

    #logica para texto ao lado
    print("Executando OCR (Texto Completo)...")
    texto_completo = pytesseract.image_to_string(imagem_final_pdi, lang='por', config=config_ocr)
    
    #logica para texto abaixo
    print("Executando OCR (Dados Espaciais)...")
    dados_ocr = pytesseract.image_to_data(imagem_final_pdi, lang='por', config=config_ocr, output_type=pytesseract.Output.DICT)

    #pré processamento das palavras para a lógica abaixo
    palavras = []
    n_palavras = len(dados_ocr['text'])
    for i in range(n_palavras):
        #filtra palavras de baixa confiança ou vazias
        if int(dados_ocr['conf'][i]) > 40 and dados_ocr['text'][i].strip():
            texto = dados_ocr['text'][i]
            #limpa o texto para uma correspondência simples
            texto_limpo = re.sub(r'[^\w]', '', texto).upper()
            if texto_limpo:
                palavras.append({
                    "texto_limpo": texto_limpo,
                    "texto_original": texto,
                    "x": dados_ocr['left'][i], "y": dados_ocr['top'][i],
                    "w": dados_ocr['width'][i], "h": dados_ocr['height'][i]
                })


    #conjunto com todas as palavraschave individuais dos rótulos do usuário
    all_label_keys = set()
    for campo in rotulos_map_usuario:
        #encontra palavras individuais (ex: "Nome", "de", "Usuário")
        palavras_do_label = re.findall(r'\w+', campo['label'].upper())
        #adiciona ao conjunto (ex: {"NOME", "DE", "USUÁRIO", "SOBRENOME"})
        all_label_keys.update(palavras_do_label)
   
    #processa cada campo
    dados_finais = OrderedDict()
    for campo in rotulos_map_usuario:
        label_usuario = campo['label']
        layout = campo['layout']
        
        valor_encontrado = None

        if layout == 'inline':
            #logica do Regex
            padrao_regex = re.escape(label_usuario) + r"\.*:?\s*(.*)"
            for linha in texto_completo.split('\n'):
                match = re.search(padrao_regex, linha, re.IGNORECASE)
                if match:
                    valor = match.group(1).strip()
                    if valor:
                        #limpa lixo do início do valor
                        valor_limpo = re.sub(r'^[.,:=>\s]+', '', valor)
                        valor_encontrado = valor_limpo
                        break 

        elif layout == 'below':
            #logica espacial, abaixo
            anchor_word = None
            
            #cria um conjunto de palavras para o rotulo atual (ex: {"SOBRENOME"} ou {"NOME", "DE", "USUÁRIO"})
            palavras_do_label_atual = set(re.findall(r'\w+', label_usuario.upper()))

            #tenta encontrar a ancora
            for p in palavras:
                #a palavra da imagem é uma correspondência exata a uma das palavraschave deste rótulo?
                if p['texto_limpo'] in palavras_do_label_atual:
                    if len(p['texto_limpo']) < 2: continue #ignora palavras muito pequenas
                    
                    #pega a palavra ancora mais embaixo e à direita
                    if anchor_word is None:
                        anchor_word = p
                    elif p['y'] > anchor_word['y']:
                         anchor_word = p
                    elif p['y'] == anchor_word['y'] and p['x'] > anchor_word['x']:
                         anchor_word = p
            
            #se a ancora for encontrada, procurar abaixo dela
            if anchor_word:
                valores_encontrados_lista = []
                
                #ROI (região de interesse)
                roi_below = {
                    "y_inicio": anchor_word['y'] + anchor_word['h'],
                    "y_fim": anchor_word['y'] + anchor_word['h'] + 75, #janela de 75px
                    "x_centro": anchor_word['x'] + (anchor_word['w'] / 2),
                    "x_tolerancia": anchor_word['w'] * 1.5 #alinhamento vertical
                }
                
                for p_valor in palavras: 
                    if p_valor == anchor_word: continue #ignora a própria ancora
                    
                    #a palavra valor está no conjunto de rótulos?
                    #se sim, ela é um rótulo, não um valor. Pula.
                    if p_valor['texto_limpo'] in all_label_keys:
                        continue

                    #verifica se a palavra está dentro da ROI
                    valor_x_centro = p_valor['x'] + (p_valor['w'] / 2)
                    esta_abaixo = p_valor['y'] >= roi_below['y_inicio'] and p_valor['y'] < roi_below['y_fim']
                    esta_alinhado = abs(valor_x_centro - roi_below['x_centro']) < roi_below['x_tolerancia']
                    
                    if esta_abaixo and esta_alinhado:
                        valores_encontrados_lista.append({ "texto": p_valor['texto_original'], "x": p_valor['x'] })

                #resultados finais
                if valores_encontrados_lista:
                    valores_ordenados = sorted(valores_encontrados_lista, key=lambda v: v['x'])
                    valor_final = " ".join([v['texto'] for v in valores_ordenados]).strip()
                    valor_encontrado = re.sub(r'^[O\s]+', '', valor_final, flags=re.IGNORECASE)

        #adiciona o valor encontrado ou N/A ao resultado
        dados_finais[label_usuario] = valor_encontrado if valor_encontrado else "N/A"

    return dados_finais
