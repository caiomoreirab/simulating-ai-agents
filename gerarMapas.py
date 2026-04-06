import json
import re

raw_data = """
Você clicou em: (4, 13)
Você clicou em: (5, 13)
Você clicou em: (4, 23)
Você clicou em: (5, 23)
Você clicou em: (5, 24)
Você clicou em: (4, 24)
Você clicou em: (4, 25)
Você clicou em: (5, 25)
Você clicou em: (5, 26)
Você clicou em: (4, 26)
Você clicou em: (4, 27)
Você clicou em: (5, 27)
Você clicou em: (5, 28)
Você clicou em: (4, 28)
Você clicou em: (4, 29)
Você clicou em: (5, 29)
Você clicou em: (4, 22)
Você clicou em: (5, 22)
Você clicou em: (4, 21)
Você clicou em: (4, 20)
Você clicou em: (5, 20)
Você clicou em: (5, 21)
Você clicou em: (5, 19)
Você clicou em: (4, 19)
Você clicou em: (4, 18)
Você clicou em: (5, 18)
Você clicou em: (5, 17)
Você clicou em: (4, 17)
Você clicou em: (4, 16)
Você clicou em: (5, 15)
Você clicou em: (5, 16)
Você clicou em: (4, 15)
Você clicou em: (4, 14)
Você clicou em: (5, 14)
"""

# Extrair coordenadas com regex
coords = re.findall(r"\((\d+), (\d+)\)", raw_data)

# Converter para lista de listas e remover duplicados
trem= list(set([ (int(x), int(y)) for x, y in coords ]))

# Converter tupla → lista (pra JSON)
trem= [list(r) for r in trem]

# Criar JSON
data = {
    "trem": trem
}

# Salvar arquivo
with open("trem.json", "w") as f:
    json.dump(data, f, indent=4)

print("JSON criado com sucesso!")