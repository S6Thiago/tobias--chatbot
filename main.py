from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return '''<!DOCTYPE html>
<html lang="pt-br">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Chatbot de Profissionais</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: Arial, sans-serif; background: #f0f2f5; display: flex; justify-content: center; align-items: center; height: 100vh; }
    .chat-container { background: white; width: 400px; max-width: 95vw; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.15); display: flex; flex-direction: column; height: 580px; }
    .chat-header { background: #075e54; color: white; padding: 16px 20px; border-radius: 16px 16px 0 0; font-size: 18px; font-weight: bold; }
    .chat-header span { font-size: 13px; font-weight: normal; opacity: 0.8; display: block; }
    .chat-messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
    .msg { max-width: 80%; padding: 10px 14px; border-radius: 12px; font-size: 14px; line-height: 1.4; white-space: pre-wrap; }
    .msg.bot { background: #e9ecef; align-self: flex-start; border-bottom-left-radius: 4px; }
    .msg.user { background: #dcf8c6; align-self: flex-end; border-bottom-right-radius: 4px; }
    .chat-input { display: flex; padding: 12px; border-top: 1px solid #eee; gap: 8px; }
    .chat-input input { flex: 1; padding: 10px 14px; border: 1px solid #ddd; border-radius: 24px; outline: none; font-size: 14px; }
    .chat-input input:focus { border-color: #075e54; }
    .chat-input button { background: #075e54; color: white; border: none; border-radius: 50%; width: 42px; height: 42px; cursor: pointer; font-size: 18px; display: flex; align-items: center; justify-content: center; }
    .chat-input button:hover { background: #128c7e; }
  </style>
</head>
<body>
  <div class="chat-container">
    <div class="chat-header">
      🤖 Chatbot de Profissionais
      <span>Encontre eletricistas, diaristas e muito mais!</span>
    </div>
    <div class="chat-messages" id="messages">
      <div class="msg bot">Olá! Eu sou seu assistente de profissionais. 👋\nDigite o serviço que você precisa, como <b>eletricista</b> ou <b>diarista</b>.</div>
    </div>
    <div class="chat-input">
      <input type="text" id="msgInput" placeholder="Digite sua mensagem..." onkeydown="if(event.key==='Enter') enviar()">
      <button onclick="enviar()">➤</button>
    </div>
  </div>
  <script>
    async function enviar() {
      const input = document.getElementById("msgInput");
      const msg = input.value.trim();
      if (!msg) return;
      adicionarMsg(msg, "user");
      input.value = "";
      try {
        const res = await fetch("/chat", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ msg }) });
        const data = await res.json();
        adicionarMsg(data.resposta, "bot");
      } catch(e) {
        adicionarMsg("Erro ao conectar com o servidor.", "bot");
      }
    }
    function adicionarMsg(texto, tipo) {
      const messages = document.getElementById("messages");
      const div = document.createElement("div");
      div.className = "msg " + tipo;
      div.innerHTML = texto;
      messages.appendChild(div);
      messages.scrollTop = messages.scrollHeight;
    }
  </script>
</body>
</html>'''

# ===== DADOS =====
profissionais = [
    {"nome": "João", "servico": "eletricista", "bairro": "centro", "avaliacao": 4.8},
    {"nome": "Maria", "servico": "diarista", "bairro": "zona sul", "avaliacao": 4.5},
    {"nome": "Carlos", "servico": "pedreiro", "bairro": "centro", "avaliacao": 4.7},
    {"nome": "Ana", "servico": "manicure", "bairro": "jardim sao luis", "avaliacao": 4.9},
]

servicos_validos = list(set(p["servico"] for p in profissionais))

# ===== ESTADO (simples - 1 usuário) =====
estado = "esperando_pesquisa"
ultimos_resultados = []
profissional_top = None

# ===== ROTA DO CHAT =====
@app.route("/chat", methods=["POST"])
def chat():
    global estado, ultimos_resultados, profissional_top

    msg = request.json.get("msg", "").lower().strip()

    # SAIR
    if msg in ["sair", "fim"]:
        return jsonify({"resposta": "Foi um prazer ajudar você!"})

    # =========================
    # FLUXO
    # =========================

    if estado == "esperando_pesquisa":
        servico_encontrado = None

        for s in servicos_validos:
            if s in msg:
                servico_encontrado = s
                break

        if not servico_encontrado:
            return jsonify({"resposta": "Não entendi. Tente algo como 'eletricista' ou 'diarista'."})

        resultados = [p for p in profissionais if p["servico"] == servico_encontrado]

        if resultados:
            ultimos_resultados = resultados
            estado = "esperando_confirmacao"

            nomes = ", ".join([f'{p["nome"]} ({p["avaliacao"]}⭐)' for p in resultados])

            return jsonify({
                "resposta": f"Encontrei: {nomes}. Deseja ver o mais bem avaliado?"
            })

        else:
            return jsonify({"resposta": "Nenhum profissional encontrado."})

    elif estado == "esperando_confirmacao":

        if msg == "sim":
            ultimos_resultados.sort(key=lambda x: x["avaliacao"], reverse=True)
            profissional_top = ultimos_resultados[0]

            estado = "menu_contratacao"

            return jsonify({
                "resposta": f"O melhor é {profissional_top['nome']} ({profissional_top['avaliacao']}⭐).\n1 - Contratar\n2 - Buscar outro"
            })

        elif msg in ["nao", "não"]:
            estado = "esperando_pesquisa"
            return jsonify({"resposta": "Ok! Pode buscar outro serviço."})

        else:
            return jsonify({"resposta": "Responda com 'sim' ou 'não'."})

    elif estado == "menu_contratacao":

        if msg == "1":
            nome = profissional_top["nome"]
            estado = "esperando_pesquisa"

            return jsonify({
                "resposta": f"Solicitação enviada para {nome}!"
            })

        elif msg == "2":
            estado = "esperando_pesquisa"
            return jsonify({"resposta": "Busque outro serviço."})

        else:
            return jsonify({"resposta": "Digite 1 ou 2."})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)