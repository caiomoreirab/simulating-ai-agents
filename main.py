import pygame
import sys
import json
import random

pygame.init()
#---------------------------------------------------------------------------------------------
#TELA ----------------------------------------------------------------------------------------
# Tamanhos
MAP_SIZE = 600
PANEL_WIDTH = 250
MID = 30 // 2

WIDTH = MAP_SIZE + PANEL_WIDTH
HEIGHT = MAP_SIZE

# Grid
GRID_SIZE = 30
CELL_SIZE = MAP_SIZE // GRID_SIZE

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulação de Cidade")

# Carregar imagem da cidade
background = pygame.image.load("cidade.png").convert_alpha()
background = pygame.transform.smoothscale(background, (MAP_SIZE, MAP_SIZE))
background.set_alpha(1000)

#  carregar imagem do fogo
fire_img = pygame.image.load("fogo-aviso.png")
fire_img = pygame.transform.scale(fire_img, (CELL_SIZE, CELL_SIZE))

# carregar imagem dos feridos
ferido_img = pygame.image.load("icon-ferido.png")
ferido_img = pygame.transform.scale(ferido_img, (CELL_SIZE, CELL_SIZE))

# carregar imagem dos feridos drones //
drone_img = pygame.image.load("drone-icon-png.png")
drone_img = pygame.transform.scale(drone_img, (CELL_SIZE, CELL_SIZE))

# carregar imagem do bombeiro
bombeiro_img = pygame.image.load("caminhao-de-bombeiros.png")
bombeiro_img = pygame.transform.scale(bombeiro_img, (CELL_SIZE, CELL_SIZE))

#  carregar imagem do socorrista sequencial
try:
    socorrista_img = pygame.image.load("socorista.png")
    socorrista_img = pygame.transform.scale(socorrista_img, (CELL_SIZE, CELL_SIZE))
except:
    socorrista_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
    socorrista_img.fill((0, 255, 0))

#  carregar imagem do socorrista otimizado
try:
    socorrista_otimo_img = pygame.image.load("socorista-otimizado.png")
    socorrista_otimo_img = pygame.transform.scale(socorrista_otimo_img, (CELL_SIZE, CELL_SIZE))
except:
    socorrista_otimo_img = pygame.Surface((CELL_SIZE, CELL_SIZE))
    socorrista_otimo_img.fill((0, 200, 255))

# Hospital no mapa (centralizado)
HOSPITAL_POS = (GRID_SIZE // 2, GRID_SIZE // 2)
font = pygame.font.SysFont("Arial", 20)

#==================================================================================================
#Leitura dos Jsons com as coordenadas (x,y) para realizações dos eventos
# ================= JSON ==========================================================================
def load_points(filename, key):
    try:
        with open(filename, "r") as f:
            data = json.load(f)
        return [tuple(p) for p in data[key]]
    except FileNotFoundError:
        return []

# carregar tudo
casas = load_points("casas.json", "casas")
estacionamentos = load_points("estacionamentos.json", "estacionamentos")
trem = load_points("trem.json", "trem")
carros = load_points("carros.json", "carros")
mapa = load_points("mapas.json", "mapas")
trilhos = load_points("trilhos.json", "trilhos")

# juntar todos os locais possíveis de incêndio
locais_incendio = casas + estacionamentos + trem
# juntar todos os locais possíveis de feridos
locais_feridos = casas + estacionamentos + trem + carros + mapa + trilhos



#===================================================================================================
# criação dos agentes -
#===================================================================================================

class AgenteSimples:
    def __init__(self, x, y, quadrante, nome="Drone"):
        self.x = x
        self.y = y
        self.quadrante = quadrante
        self.nome = nome
        self.move_delay = 25  # quanto maior, mais lento
        self.move_counter = 0

    #  Movimento aleatório limitado ao quadrante
    def mover(self):
        for _ in range(10):
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            nx = self.x + dx
            ny = self.y + dy

            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                if get_quadrant(nx, ny) == self.quadrante:
                    self.x = nx
                    self.y = ny
                    return

    #  PERCEPÇÃO LOCAL (MESMA CÉLULA)
    def perceber(self, focos, feridos):
        eventos = []
        if (self.x, self.y) in focos:
            eventos.append(("fogo", (self.x, self.y)))  #verifica a posição em que o drono esta e ve se tem algum foco ou ferido ali e adiciona em evento 
        if (self.x, self.y) in feridos:
            eventos.append(("ferido", (self.x, self.y)))
        return eventos

    #  SENSOR (usa perceber + comunica)
    def sensor(self, focos, feridos, agenteBDI):
        eventos = self.perceber(focos, feridos)  # verifica se tem um evento usando a função perceber() e se tiver, envia uma mensagem ao BDI com as informações
        if eventos:
            for tipo, pos in eventos:
                msg = {"de": self.nome, "tipo": tipo, "pos": pos}
                agenteBDI.receber_mensagem(msg) #manda mensagem ao BDI

    def atualizar(self, focos, feridos, agenteBDI):
        self.sensor(focos, feridos, agenteBDI)
        self.move_counter += 1
        if self.move_counter >= self.move_delay:
            self.mover()
            self.move_counter = 0

class AgenteBDI:
    def __init__(self):
        self.mensagens = []
        self.relatorio_incendios = []
        self.lista_feridos = []

    def receber_mensagem(self, msg):
        print(f" agenteBDI recebeu: {msg}")
        self.mensagens.append(msg)
        if msg["tipo"] == "fogo":
            if msg["pos"] not in self.relatorio_incendios:  #se o evento for fogo, guarda na lista de incendios
                self.relatorio_incendios.append(msg["pos"])
        elif msg["tipo"] == "ferido":  #se o evento for ferido ele guarda na lista de feridos
            if msg["pos"] not in self.lista_feridos:
                self.lista_feridos.append(msg["pos"])

    #  Comandante BDI despacha todas as intenções
    def despachar(self, bombeiros, socorristas, focos, feridos):
        # BELIEFS: Limpar listas com base no que os drones param de ver
        self.relatorio_incendios = [pos for pos in self.relatorio_incendios if pos in focos]
        self.lista_feridos = [pos for pos in self.lista_feridos if pos in feridos]

        # DESIRE: Apagar todos os incêndios (Intenção de Fogo)
        for pos in self.relatorio_incendios:
            # Verifica se já existe um bombeiro indo para este foco
            if any(b.alvo == pos for b in bombeiros): continue
            
            alocado = False
            quadrante_alvo = get_quadrant(pos[0], pos[1])
            
            # 1. Tentar alocar o bombeiro do mesmo quadrante (Prioridade)
            for b in bombeiros:
                if b.alvo is None and b.quadrante == quadrante_alvo:
                    b.receber_ocorrencia(pos)
                    alocado = True
                    break
            
            # 2. REGRA DE EXCEÇÃO: Alocar qualquer bombeiro vago mais próximo (Ajuda externa)
            if not alocado:
                b_livres = [b for b in bombeiros if b.alvo is None]
                if b_livres:
                    # Cálculo de Utilidade: menor distância de Manhattan
                    b_aux = min(b_livres, key=lambda b: abs(b.x - pos[0]) + abs(b.y - pos[1]))
                    b_aux.receber_ocorrencia(pos)

        # DESIRE: Salvar todos os feridos (Intenção de Resgate)
        for pos in self.lista_feridos:
            # Não duplicar se já estiver em alguma fila ou sendo buscado
            ja_atendido = any(pos in s.lista_resgates for s in socorristas) or \
                          any(s.vítima_atual == pos for s in socorristas)
            
            if not ja_atendido:
                # Cálculo de Utilidade para decidir qual Socorrista despachar
                # Quem estiver mais perto no momento ganha o chamado
                s_escolhido = min(socorristas, key=lambda s: abs(s.x - pos[0]) + abs(s.y - pos[1]))
                s_escolhido.receber_lista_resgate(pos)

class AgenteSocorrista: # Agente Baseado em Objetivos
    def __init__(self, x, y, nome="Socorrista"):
        self.x = x
        self.y = y
        self.nome = nome
        self.lista_resgates = [] # Fila FIFO
        self.vítima_atual = None
        self.tem_passageiro = False
        
        self.move_delay = 60
        self.move_counter = 0
        self.vítimas_salvas = 0 # Contar apenas na entrega real
        self.distancia_total = 0 # Hodômetro

    def receber_lista_resgate(self, pos):
        if pos not in self.lista_resgates:
            self.lista_resgates.append(pos)
            print(f" {self.nome} adicionou {pos} à sua lista de resgates")

    def mover(self, feridos):
        # Se não tem passageiro e tem gente na lista, define a PRIMEIRA (FIFO)
        if not self.tem_passageiro and len(self.lista_resgates) > 0:
            self.vítima_atual = self.lista_resgates[0]
            alvo = self.vítima_atual
        elif self.tem_passageiro:
            alvo = HOSPITAL_POS
        else:
            return

        # Planejamento de caminho simples
        tx, ty = alvo
        dx = 1 if tx > self.x else -1 if tx < self.x else 0
        dy = 1 if ty > self.y else -1 if ty < self.y else 0

        self.x += dx
        self.y += dy

        # se chegar ao destino
        if (self.x, self.y) == alvo:
            if self.tem_passageiro:
                print(f"🏥 {self.nome} entregou vítima no hospital")
                self.tem_passageiro = False
                self.vítimas_salvas += 1 # Contar apenas na entrega real
                # Remove da lista de resgates APÓS entrega
                if len(self.lista_resgates) > 0:
                    self.lista_resgates.pop(0)
            else:
                print(f"🚑 {self.nome} resgatou vítima em {alvo}")
                if alvo in feridos:
                    feridos.remove(alvo)
                self.tem_passageiro = True

    def atualizar(self, feridos):
        # Filtra a lista para remover quem já foi salvo por outro agente
        self.lista_resgates = [p for p in self.lista_resgates if p in feridos or (self.tem_passageiro and p == self.vítima_atual)]
        
        self.move_counter += 1
        if self.move_counter >= self.move_delay:
            self.mover(feridos)
            self.move_counter = 0

class AgenteSocorristaOtimizador(AgenteSocorrista): #  SEQUENCIAL vs OTIMIZADOR (Diferença entre Objetivos e Utilidade).
    def __init__(self, x, y, nome="Socorrista Otimizado"):
        super().__init__(x, y, nome)
        self.move_delay = 50 

    def escolher_melhor_vitima(self, feridos):
        if not self.lista_resgates:
            return None
        
        # Função de Utilidade: Menor distância de Manhattan
        melhor_pos = min(self.lista_resgates, 
                         key=lambda p: abs(p[0] - self.x) + abs(p[1] - self.y))
        return melhor_pos

    def mover(self, feridos):
        if not self.tem_passageiro and len(self.lista_resgates) > 0:
            # Reavalia a melhor vítima a cada passo (Otimização dinâmica)
            self.vítima_atual = self.escolher_melhor_vitima(feridos)
            alvo = self.vítima_atual
        elif self.tem_passageiro:
            alvo = HOSPITAL_POS
        else:
            return

        tx, ty = alvo
        dx = 1 if tx > self.x else -1 if tx < self.x else 0
        dy = 1 if ty > self.y else -1 if ty < self.y else 0
        self.x += dx
        self.y += dy

        if (self.x, self.y) == alvo:
            if self.tem_passageiro:
                print(f" {self.nome} entregou vítima no hospital")
                self.tem_passageiro = False
                self.vítimas_salvas += 1 # BETA agora também ganha pontos!
                if self.vítima_atual in self.lista_resgates:
                    self.lista_resgates.remove(self.vítima_atual)
            else:
                if alvo in feridos:
                    print(f" {self.nome} otimizou e resgatou vítima em {alvo}")
                    feridos.remove(alvo)
                    self.tem_passageiro = True
                else:
                    # Se alguém chegou antes, remove da lista e tenta de novo
                    if alvo in self.lista_resgates:
                        self.lista_resgates.remove(alvo)

class AgenteReativo:
    def __init__(self, x, y, quadrante, nome="Bombeiro"):
        self.x = x
        self.y = y
        self.quadrante = quadrante
        self.nome = nome
        self.move_delay = 80
        self.move_counter = 0
        self.alvo = None
        self.base_pos = (x, y) # Posição inicial para retorno
        self.fogo_vitorias = 0
        self.vítimas_salvas = 0 # Inicializado para evitar erro de atributo
        self.distancia_total = 0 # Hodômetro

    def receber_ocorrencia(self, pos):
        # Agora o BDI decide quem vai, então o bombeiro apenas aceita se estiver livre
        if self.alvo is None:
            self.alvo = pos
            print(f"{self.nome} recebeu missão em {pos}")

    def mover(self, focos, feridos):
        # Se não tem alvo, o objetivo é a base. Se tem, é a ocorrência.
        alvo_atual = self.alvo if self.alvo else self.base_pos
        
        if (self.x, self.y) == alvo_atual:
            if self.alvo is None: return # Já está na base e livre
            
            # Chegou na ocorrência (Lógica original de sucesso)
            print(f" {self.nome} chegou em {self.alvo}")
            if self.alvo in focos:
                focos.remove(self.alvo)
                self.fogo_vitorias += 1
                print(f" {self.nome} apagou fogo em {self.alvo}")
            elif self.alvo in feridos:
                feridos.remove(self.alvo)
                self.vítimas_salvas += 1
                print(f" {self.nome} socorreu ferido em {self.alvo}")
            
            self.alvo = None
            return

        # Movimentação calculada (suporta diagonal)
        tx, ty = alvo_atual
        dx = 1 if tx > self.x else -1 if tx < self.x else 0
        dy = 1 if ty > self.y else -1 if ty < self.y else 0
        
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
             self.x, self.y = nx, ny
             self.distancia_total += 1 # Conta passo do bombeiro

    def atualizar(self, focos, feridos):
        self.move_counter += 1
        if self.move_counter >= self.move_delay:
            self.mover(focos, feridos)
            self.move_counter = 0

agenteBDI = AgenteBDI()

#=================================================================================================
#criando os drones
agentesSimples = [
    AgenteSimples(5, 5, "Q1", "Drone1"),
    AgenteSimples(20, 5, "Q2", "Drone2"),
    AgenteSimples(5, 20, "Q3", "Drone3"),
    AgenteSimples(20, 20, "Q4", "Drone4"),
]

#criando os bombeiros
bombeiros = [
    AgenteReativo(5, 5, "Q1", "Bombeiro Q1"),
    AgenteReativo(20, 5, "Q2", "Bombeiro Q2"),
    AgenteReativo(5, 20, "Q3", "Bombeiro Q3"),
    AgenteReativo(20, 20, "Q4", "Bombeiro Q4"),
]

# criando os socorristas
socorrista_sequencial = AgenteSocorrista(5, 15, "SEQUENCIAL")
socorrista_otimizador = AgenteSocorristaOtimizador(25, 15, "OTIMIZADOR")
socorristas = [socorrista_sequencial, socorrista_otimizador]

# ================= INCÊNDIOS =================
focos = []
def spawn_fire():
    for _ in range(10):
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        pos = (x, y)
        if pos not in focos:
            focos.append(pos)
            print(f"🔥 Incêndio criado em {pos}")
            return

# ================= feridos =================
feridos = []
def feridos2():
    for _ in range(10):
        x = random.randint(0, GRID_SIZE - 1)
        y = random.randint(0, GRID_SIZE - 1)
        pos = (x, y)
        if pos not in focos and pos not in feridos: # correção: não criar ferido sobre incêndio ou outro ferido
            feridos.append(pos)
            print(f" Ferido criado em {pos}")
            return

# Função: pixel → grid
def pixel_to_grid(px, py):
    x = px // CELL_SIZE
    y = py // CELL_SIZE
    return x, y

# (opcional) guardar cliques
clicked_cells = []

def get_quadrant(x, y):
    MID_GRID = GRID_SIZE // 2
    if x < MID_GRID and y < MID_GRID:
        return "Q1"
    elif x >= MID_GRID and y < MID_GRID:
        return "Q2"
    elif x < MID_GRID and y >= MID_GRID:
        return "Q3"
    else:
        return "Q4"

# timers para a geração de incendios e feridos (Acelerado para testar inteligência)
fire_timer = 0
fire_delay = 600 
ferido_timer = 0
ferido_delay = 600

overlay = pygame.Surface((MAP_SIZE, MAP_SIZE))
overlay.fill((0, 0, 0))
overlay.set_alpha(150) 

# --- LOOP PRINCIPAL ---
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            if mx < MAP_SIZE:
                gx, gy = pixel_to_grid(mx, my)
                print(f"Você clicou em: ({gx}, {gy})")
                clicked_cells.append((gx, gy))

    # ================= ATUALIZAÇÃO =================
    for agente in agentesSimples:
        agente.atualizar(focos, feridos, agenteBDI)

    for b in bombeiros:
        b.move_delay = 80 
        b.atualizar(focos, feridos)

    for s in socorristas:
        s.atualizar(feridos)

    # 🔥 incêndios
    fire_timer += 1
    if fire_timer >= fire_delay:
        spawn_fire()
        fire_timer = 0

    # 🚑 feridos
    ferido_timer += 1
    if ferido_timer >= ferido_delay:
        feridos2()
        ferido_timer = 0

    # 🧠 BDI decide e envia tarefas
    agenteBDI.despachar(bombeiros, socorristas, focos, feridos)

    # ================= RENDER =================
    screen.blit(background, (0, 0))
    screen.blit(overlay, (0, 0))

    # GRID
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            pygame.draw.rect(screen, (255, 255, 255),
                             (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

    # 4. EVENTOS (🔥 incêndios)
    for (x, y) in focos:
        px = x * CELL_SIZE
        py = y * CELL_SIZE
        screen.blit(fire_img, (px, py))

    # 5. EVENTOS (🚑 feridos)
    for (x, y) in feridos:
        px = x * CELL_SIZE
        py = y * CELL_SIZE
        screen.blit(ferido_img, (px, py))

    # 6. AGENTES (🚁 drones)
    for agente in agentesSimples:
        px = agente.x * CELL_SIZE
        py = agente.y * CELL_SIZE
        screen.blit(drone_img, (px, py))
     
    # 🚒 BOMBEIROS
    for b in bombeiros:
        px = b.x * CELL_SIZE
        py = b.y * CELL_SIZE
        screen.blit(bombeiro_img, (px, py))

    # 🏥 HOSPITAL (visualização)
    hx, hy = HOSPITAL_POS
    pygame.draw.rect(screen, (255, 255, 255), (hx * CELL_SIZE, hy * CELL_SIZE, CELL_SIZE, CELL_SIZE))
    h_text = font.render("H", True, (0, 0, 0))
    screen.blit(h_text, (hx * CELL_SIZE + 5, hy * CELL_SIZE + 2))

    # 🚑 SOCORRISTAS
    for s in socorristas:
        px = s.x * CELL_SIZE
        py = s.y * CELL_SIZE
        # Escolhe a imagem com base no tipo
        img = socorrista_otimo_img if isinstance(s, AgenteSocorristaOtimizador) else socorrista_img
        screen.blit(img, (px, py))
        
        # Mostrar o nome sobre o agente para debug
        name_tag = font.render(s.nome, True, (255, 255, 255))
        screen.blit(name_tag, (px, py - 15))
        
        if s.tem_passageiro:
            screen.blit(ferido_img, (px+10, py-5))

    # 7. CLIQUES (debug)
    for (gx, gy) in clicked_cells:
        px = gx * CELL_SIZE
        py = gy * CELL_SIZE
        pygame.draw.rect(screen, (255, 0, 0),
                         (px, py, CELL_SIZE, CELL_SIZE), 3)

    # 8. PAINEL
    pygame.draw.rect(screen, (40, 40, 40), (MAP_SIZE, 0, PANEL_WIDTH, HEIGHT))
    title = font.render("Simulação", True, (255, 255, 255))
    focos_text = font.render(f"Incêndios: {len(focos)}", True, (255, 100, 100))
    feridos_text = font.render(f"Feridos: {len(feridos)}", True, (100, 200, 255))
    info_text = font.render("Clique no mapa", True, (200, 200, 200))

    screen.blit(title, (MAP_SIZE + 20, 20))
    screen.blit(focos_text, (MAP_SIZE + 20, 60))
    screen.blit(feridos_text, (MAP_SIZE + 20, 100))
    
    # --- PLACAR DE DESEMPENHO ---
    score_title = font.render("DESEMPENHO", True, (255, 255, 0))
    screen.blit(score_title, (MAP_SIZE + 20, 160))
    
    y_offset = 200
    for b in bombeiros:
        b_score = font.render(f"{b.nome}: {b.fogo_vitorias} | {b.distancia_total}m", True, (255, 150, 150))
        screen.blit(b_score, (MAP_SIZE + 20, y_offset))
        y_offset += 30
        
    for s in socorristas:
        # Cálculo de eficiência: Vítimas por 100 passos (evita divisão por zero)
        eficiencia = (s.vítimas_salvas / s.distancia_total * 100) if s.distancia_total > 0 else 0
        
        s_score = font.render(f"{s.nome}: {s.vítimas_salvas} | {s.distancia_total}m", True, (150, 255, 150))
        screen.blit(s_score, (MAP_SIZE + 20, y_offset))
        y_offset += 25
        eff_text = font.render(f"   Eficiência: {eficiencia:.1f}%", True, (200, 255, 200))
        screen.blit(eff_text, (MAP_SIZE + 20, y_offset))
        y_offset += 35

    screen.blit(info_text, (MAP_SIZE + 20, HEIGHT - 40))

    # 9. LINHAS DOS QUADRANTES
    pygame.draw.line(screen, (255, 0, 0),
                     (MID * CELL_SIZE, 0),
                     (MID * CELL_SIZE, MAP_SIZE), 2)
    pygame.draw.line(screen, (255, 0, 0),
                     (0, MID * CELL_SIZE),
                     (MAP_SIZE, MID * CELL_SIZE), 2)

    pygame.display.update()
