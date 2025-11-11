# PFinal_Pdi

## 1. Pré Requisitos (instalação do tesseract)
### Windows

Baixe o instalador neste link: [UB-Mannheim Tesseract Installer](https://github.com/tesseract-ocr/tesseract/wiki)

Durante a instalação, na tela "Select Additional Language data...", marque a opção "Portuguese" para instalar o pacote de idioma português.

Na última etapa, anote o local onde o Tesseract foi instalado. O padrão é `C:\Program Files\Tesseract-OCR`.

Após instalar, você precisa informar ao código Python onde encontrar o Tesseract.

Verifique se o caminho no topo do arquivo processamento_pdi.py está correto: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`

### MacOS

`brew install tesseract tesseract-lang`

### Linux

`sudo apt-get install tesseract-ocr tesseract-ocr-por`

## 2. Configurações do projeto

No terminal:

1. Clone o repositório: `git clone https:\\...`.

2. Abra dentro da pasta que você baixou e digite: `cd {CAMINHO DA PASTA}`.

3. Crie um ambiente virtual: `python -m venv venv`.
  
4. Ative ele(windows): `.\venv\Scripts\activate`.
5. Ative ele(linux/mac): `source venv/bin/activate`.

6. Instale as dependências: `pip install -r requirements.txt`.

## 3. Como executar

Digite no terminal : `python app.py`

Acesse: http://127.0.0.1:5000

## 4. Como usar

1. Clique em `+ Adicionar campo` para cada dado que deseja extrair.

2. No campo de texto, digite o rótulo exatamente como ele aparece na imagem.

3. `Layout ao lado`: para recibos e documentos onde o valor está à direita do rótulo.

4. `Layout abaixo`: para formulários onde o valor está abaixo do rótulo.

5. Selecione o arquivo de imagem que você deseja processar.

6. Clique no botão `Digitalizar`.

7. O JSON com os dados extraídos aparecerá na caixa `Resultados da extração`.

