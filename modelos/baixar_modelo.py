import requests
from tqdm import tqdm
import os


url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"


os.makedirs("modelos", exist_ok=True)
destino = os.path.join("modelos", "mistral-7b-instruct-v0.1.Q4_K_M.gguf")


resposta = requests.get(url, stream=True)
tamanho_total = int(resposta.headers.get('content-length', 0))
progresso = tqdm(total=tamanho_total, unit='B', unit_scale=True, desc="Baixando modelo")

with open(destino, 'wb') as f:
    for dados in resposta.iter_content(1024):
        f.write(dados)
        progresso.update(len(dados))

print(f"\n✅ Download concluído! Modelo salvo em: {destino}")
