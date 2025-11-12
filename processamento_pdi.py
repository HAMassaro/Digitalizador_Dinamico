import cv2  
import numpy as np  
import pytesseract  
import json  
import re  
from collections import OrderedDict  

#define caminho do tesseract(windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

#função principal que usa um mapa de rótulos dinâmico vindo do usuário
def digitalizar_formulario_dinamico(caminho_imagem, rotulos_map_usuario):

    #carrega a imagem e converte para escala de cinza
    imagem = cv2.imread(caminho_imagem)
    if imagem is None: 
        return {"erro": f"Não foi possível carregar a imagem: {caminho_imagem}"}
        
    cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY) 
    
    #redimensionamento, melhora a precisão do OCR
    fator_escala = 2 
    largura = int(cinza.shape[1] * fator_escala)
    altura = int(cinza.shape[0] * fator_escala)
    dimensoes = (largura, altura)
    imagem_ampliada = cv2.resize(cinza, dimensoes, interpolation=cv2.INTER_CUBIC)

    #binarizaçaõ com metodo de Otsu
    #converte para preto e branco buscando o limiar ideal automaticamente
    _, imagem_final_pdi = cv2.threshold(imagem_ampliada, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    #arquivo de debug para ver o que o tesseract ta recebendo
    cv2.imwrite("debug_para_tesseract.png", imagem_final_pdi)

    #prepara dados do ocr
    config_ocr = r'--oem 3 --psm 4' 

    #logica de texto a direita
    print("Executando OCR (Texto Completo)...")
    texto_completo = pytesseract.image_to_string(imagem_final_pdi, lang='por', config=config_ocr)
    
    #logica de texto abaixo
    print("Executando OCR (Dados Espaciais)...")
    dados_ocr = pytesseract.image_to_data(imagem_final_pdi, lang='por', config=config_ocr, output_type=pytesseract.Output.DICT)

    #pre processamento das alavras p /lógica abaixo
    palavras = []
    n_palavras = len(dados_ocr['text'])
    for i in range(n_palavras):
        #filtra palavras de baixa confiança ou vazias
        if int(dados_ocr['conf'][i]) > 40 and dados_ocr['text'][i].strip(): 
            texto = dados_ocr['text'][i]
            texto_limpo = re.sub(r'[^\w]', '', texto).upper()
            if texto_limpo:
                palavras.append({
                    "texto_limpo": texto_limpo, 
                    "texto_original": texto,
                    "x": dados_ocr['left'][i], "y": dados_ocr['top'][i],
                    "w": dados_ocr['width'][i], "h": dados_ocr['height'][i]
                })

    #iterar pelo mapa do usuario
    dados_finais = OrderedDict()
    

    #conjunto com todas as palavras que compoem os rotulos definidos pelo usuário
    all_label_keys = set()
    for campo in rotulos_map_usuario:
        #limpa o rotulo, ex: nome da empresa -> NOMEDAEMPRESA
        label_limpo = re.sub(r'[^\w]', '', campo['label']).upper()
        #encontra as palavras individuais ex: "NOME", "DA", "EMPRESA"
        palavras_do_label = re.findall(r'\w+', label_limpo)
        #adiciona essas palavras ao conjunto
        all_label_keys.update(palavras_do_label)
   

    
    #processa cada campo
    for campo in rotulos_map_usuario:
        label_usuario = campo['label']
        layout = campo['layout']
        
        label_limpo_busca = re.sub(r'[^\w]', '', label_usuario).upper()
        
        valor_encontrado = None

        if layout == 'inline':
            #logica do regex
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
            #lógica espacial (abaixo)
            anchor_word = None
            
            #encontrar a ancora
            for p in palavras:
                #a palavra lida ('NOME') está contida na minha busca 'NOMEDAEMPRESA' ?
                if p['texto_limpo'] in label_limpo_busca:
                    if len(p['texto_limpo']) < 2: continue
                    #pega a palavra âncora mais embaixo e à direita
                    if anchor_word is None:
                        anchor_word = p
                    elif p['y'] > anchor_word['y']:
                         anchor_word = p
                    elif p['y'] == anchor_word['y'] and p['x'] > anchor_word['x']:
                         anchor_word = p
            
            #se a ancora foi encontrada procurar abaixo dela
            if anchor_word:
                valores_encontrados_lista = []
                
                #ROI (região de interesse)
                roi_below = {
                    "y_inicio": anchor_word['y'] + anchor_word['h'],
                    "y_fim": anchor_word['y'] + anchor_word['h'] + 75,
                    "x_centro": anchor_word['x'] + (anchor_word['w'] / 2),
                    "x_tolerancia": anchor_word['w'] * 1.5
                }
                
                for p_valor in palavras: 
                    if p_valor == anchor_word: continue #ignora a própria ancora
                    
                    # --- APLICAÇÃO DO FILTRO INTELIGENTE ---
                    #antes de capturar um valor, verfica: a palavra 'SEXO' está no meu conjunto de rótulos?
                    #se sim ela é um rotulo, não um valor, pula
                    if p_valor['texto_limpo'] in all_label_keys:
                        continue

                    #verifica se a palavra está dentro da ROI
                    valor_x_centro = p_valor['x'] + (p_valor['w'] / 2)
                    esta_abaixo = p_valor['y'] >= roi_below['y_inicio'] and p_valor['y'] < roi_below['y_fim']
                    esta_alinhado = abs(valor_x_centro - roi_below['x_centro']) < roi_below['x_tolerancia']
                    
                    if esta_abaixo and esta_alinhado:
                        valores_encontrados_lista.append({ "texto": p_valor['texto_original'], "x": p_valor['x'] })

                #monta os resultados finais
                if valores_encontrados_lista:
                    valores_ordenados = sorted(valores_encontrados_lista, key=lambda v: v['x'])
                    valor_final = " ".join([v['texto'] for v in valores_ordenados]).strip()
                    valor_encontrado = re.sub(r'^[O\s]+', '', valor_final, flags=re.IGNORECASE)

        #adiciona o valor encontrado ou "N/A" ao resultado
        dados_finais[label_usuario] = valor_encontrado if valor_encontrado else "N/A"

    return dados_finais