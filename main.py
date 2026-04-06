import pygame
import sys
import json
import random

pygame.init()

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


# 🔥 carregar imagem do fogo
fire_img = pygame.image.load("fogo-aviso.png")
fire_img = pygame.transform.scale(fire_img, (CELL_SIZE, CELL_SIZE))

# ⚠️ carregar imagem dos feridos
ferido_img = pygame.image.load("icon-ferido.png")
ferido_img = pygame.transform.scale(ferido_img, (CELL_SIZE, CELL_SIZE))

#  carregar imagem dos feridos drones //
drone_img = pygame.image.load("drone-icon-png.png")
drone_img = pygame.transform.scale(drone_img, (CELL_SIZE, CELL_SIZE))

font = pygame.font.SysFont("Arial", 20)


#Leitura dos Jsons com as coordenadas (x,y) para realizações dos eventos
# ================= JSON =================

def load_points(filename, key):
    with open(filename, "r") as f:
        data = json.load(f)
    return [tuple(p) for p in data[key]]

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




# Função de percepção para usar no agente - vai ser chamada pelo sensor
def perceber(self, fires, feridos):
    eventos = []

    for dx in range(-2, 3):  # raio = 2
        for dy in range(-2, 3):
            nx = self.x + dx
            ny = self.y + dy

            if (nx, ny) in fires:
                eventos.append(("fogo", (nx, ny)))

            if (nx, ny) in feridos:
                eventos.append(("ferido", (nx, ny)))

    return eventos


# criação dos agentes -

class AgenteSimples:
    def __init__(self, x, y, quadrante, nome="Drone"):
        self.x = x
        self.y = y
        self.quadrante = quadrante
        self.nome = nome
        self.move_delay = 70  # quanto maior, mais lento
        self.move_counter = 0

    # 🚶 Movimento aleatório limitado ao quadrante
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

    # 👁️ PERCEPÇÃO LOCAL (MESMA CÉLULA)
    def perceber(self, fires, feridos):
        eventos = []

        if (self.x, self.y) in fires:
            eventos.append(("fogo", (self.x, self.y)))

        if (self.x, self.y) in feridos:
            eventos.append(("ferido", (self.x, self.y)))

        return eventos

    # 📡 SENSOR (usa perceber + comunica)
    def sensor(self, fires, feridos, agenteBDI):
        eventos = self.perceber(fires, feridos)

        if eventos:
            for tipo, pos in eventos:
                msg = {
                    "de": self.nome,
                    "tipo": tipo,
                    "pos": pos
                }

                print(f"📡 {self.nome} detectou {tipo} em {pos}")
                agenteBDI.receber_mensagem(msg)

    def atualizar(self, fires, feridos, agenteBDI):
        self.sensor(fires, feridos, agenteBDI)

        self.move_counter += 1

        if self.move_counter >= self.move_delay:
            self.mover()
            self.move_counter = 0


class AgenteBDI:  #ilustração por enquanto
    def __init__(self):
        self.mensagens = []
        self.relatorio_incendios = []
        self.lista_feridos = []

    def receber_mensagem(self, msg):
        print(f"📥 agenteBDI recebeu: {msg}")
        self.mensagens.append(msg)

        if msg["tipo"] == "fogo":
            if msg["pos"] not in self.relatorio_incendios:
                self.relatorio_incendios.append(msg["pos"])

        elif msg["tipo"] == "ferido":
            if msg["pos"] not in self.lista_feridos:
                self.lista_feridos.append(msg["pos"])


agenteBDI = AgenteBDI()

agentes = [
    AgenteSimples(5, 5, "Q1", "Drone1"),
    AgenteSimples(20, 5, "Q2", "Drone2"),
    AgenteSimples(5, 20, "Q3", "Drone3"),
    AgenteSimples(20, 20, "Q4", "Drone4"),
]






# ================= INCÊNDIOS =================
fires = []

def spawn_fire():
    if not locais_incendio:
        return

    for _ in range(10):
        pos = random.choice(locais_incendio)

        if pos not in fires:
            fires.append(pos)
            print(f"🔥 Incêndio criado em {pos}")
            return
        


        # ================= feridos =================
feridos = []

def feridos2():
    if not locais_feridos:
        return

    for _ in range(10):
        pos = random.choice(locais_feridos)

        if pos not in feridos:
            feridos.append(pos)
            print(f"|Ferido criada em {pos}")
            return

# Função: pixel → grid
def pixel_to_grid(px, py):
    x = px // CELL_SIZE
    y = py // CELL_SIZE
    return x, y

# (opcional) guardar cliques
clicked_cells = []

def get_quadrant(x, y):
    MID = GRID_SIZE // 2

    if x < MID and y < MID:
        return "Q1"
    elif x >= MID and y < MID:
        return "Q2"
    elif x < MID and y >= MID:
        return "Q3"
    else:
        return "Q4"

# timers para a gera ção de incendios e feridos 
fire_timer = 0
fire_delay = 600  # quanto maior, mais lento
ferido_timer = 0
ferido_delay = 700

overlay = pygame.Surface((MAP_SIZE, MAP_SIZE))
overlay.fill((0, 0, 0))
overlay.set_alpha(150)  # ajusta aqui a opacidade para melhorar a visualização

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

    for agente in agentes:
        agente.atualizar(fires, feridos, agenteBDI)

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

    # ================= RENDER =================

    # 1. FUNDO
    screen.blit(background, (0, 0))

    # 2. OVERLAY (escurece a cidade)
    screen.blit(overlay, (0, 0))

    # 3. GRID (opcional)
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            pygame.draw.rect(
                screen,
                (255, 255, 255),
                (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE),
                1
            )

    # 4. EVENTOS (🔥 incêndios)
    for (x, y) in fires:
        px = x * CELL_SIZE
        py = y * CELL_SIZE
        screen.blit(fire_img, (px, py))

    # 5. EVENTOS (🚑 feridos)
    for (x, y) in feridos:
        px = x * CELL_SIZE
        py = y * CELL_SIZE
        screen.blit(ferido_img, (px, py))

    # 6. AGENTES (🚁 drones)
    for agente in agentes:
        px = agente.x * CELL_SIZE
        py = agente.y * CELL_SIZE
        screen.blit(drone_img, (px, py))

    # 7. CLIQUES (debug)
    for (gx, gy) in clicked_cells:
        px = gx * CELL_SIZE
        py = gy * CELL_SIZE
        pygame.draw.rect(screen, (255, 0, 0),
                         (px, py, CELL_SIZE, CELL_SIZE), 3)

    # 8. PAINEL
    pygame.draw.rect(screen, (40, 40, 40), (MAP_SIZE, 0, PANEL_WIDTH, HEIGHT))

    title = font.render("Simulação", True, (255, 255, 255))
    fires_text = font.render(f"Incêndios: {len(fires)}", True, (255, 100, 100))
    feridos_text = font.render(f"Feridos: {len(feridos)}", True, (100, 200, 255))
    info_text = font.render("Clique no mapa", True, (200, 200, 200))

    screen.blit(title, (MAP_SIZE + 20, 20))
    screen.blit(fires_text, (MAP_SIZE + 20, 60))
    screen.blit(feridos_text, (MAP_SIZE + 20, 100))
    screen.blit(info_text, (MAP_SIZE + 20, 140))

    # 9. LINHAS DOS QUADRANTES
    pygame.draw.line(screen, (255, 0, 0),
                     (MID * CELL_SIZE, 0),
                     (MID * CELL_SIZE, MAP_SIZE), 2)

    pygame.draw.line(screen, (255, 0, 0),
                     (0, MID * CELL_SIZE),
                     (MAP_SIZE, MID * CELL_SIZE), 2)

    pygame.display.update()