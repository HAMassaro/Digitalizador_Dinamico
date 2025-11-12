import os
from flask import Flask, request, render_template, jsonify, Response
import processamento_pdi
import json 

#pasta para salvar temporariamente as imagens que o usuário envia
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True) #cria a pasta se não existir

app = Flask(__name__) #incia a aplicação Flask

#por padrão o flask reordena chaves de JSON alfabeticamente
app.config['JSON_SORT_KEYS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

#rota principal pra exibir a pag
@app.route('/')
def index():
    
    return render_template('index.html')

#rota da api
@app.route('/upload', methods=['POST'])#recebe os dados
def upload_file():
    
    #vefificaçaõ de segurança
    if 'file' not in request.files:
        return jsonify({"erro": "Nenhum arquivo enviado"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"erro": "Nenhum arquivo selecionado"}), 400
    
    #pega o 'rotulos_map' que o js enviou, vem como uma string de JSON
    rotulos_json = request.form.get('rotulos_map')
    if not rotulos_json:
        return jsonify({"erro": "Nenhum mapa de rótulos foi enviado"}), 400
        
    try:
        # Converte a string do JSON em uma lista
        rotulos_map_usuario = json.loads(rotulos_json)
    except Exception as e:
        return jsonify({"erro": f"JSON de rótulos inválido: {str(e)}"}), 400

    if not rotulos_map_usuario:
        return jsonify({"erro": "A lista de rótulos está vazia."}), 400

    if file:
        try:
            #salva o arquivo temporariamente
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            
            #passa o caminho do arquivo e a extração
            dados_extraidos = processamento_pdi.digitalizar_formulario_dinamico(filepath, rotulos_map_usuario)
            
            #resposta
            json_string = json.dumps(dados_extraidos, indent=4, ensure_ascii=False)
            
            #retorna uma resposta do flask, definindo o tipo de conteúdo como application/json para o navegador entender
            return Response(json_string, mimetype='application/json')
            
        except Exception as e:
            #captura qualquer erro que acontecer no pdi
            print(f"Erro no processamento: {e}")
            return jsonify({"erro": f"Falha no processamento: {str(e)}"}), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)