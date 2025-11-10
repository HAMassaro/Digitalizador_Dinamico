# PFinal_Pdi

## 1. Pré Requisitos
### Windows

Baixe o instalador neste link: [UB-Mannheim Tesseract Installer](https://github.com/tesseract-ocr/tesseract/wiki)

Durante a instalação, na tela "Select Additional Language data...", marque a opção "Portuguese" para instalar o pacote de idioma português.

Na última etapa, anote o local onde o Tesseract foi instalado. O padrão é C:\Program Files\Tesseract-OCR.

Após instalar, você precisa informar ao código Python onde encontrar o Tesseract.

Verifique se o caminho no topo do arquivo processamento_pdi.py está correto: `pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'`
