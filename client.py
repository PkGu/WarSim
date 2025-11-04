# client.py
import socket, threading, json, pygame, time
from game_core import *

pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("국가2 - 클라이언트")
clock = pygame.time.Clock()

try:
    font = pygame.font.Font("NotoSansKR-Regular.ttf", 28)
except:
    font = pygame.font.SysFont("Malgun Gothic", 28)

WHITE = (255,255,255)
BLUE = (100,150,255)
RED = (255,100,100)
GREEN = (0,200,0)
YELLOW = (255,255,0)
BLACK = (0,0,0)

nation2 = Nation("국가2")
opponent_units = 0
game_over = False
selected_unit = None

class Button:
    def __init__(self, x, y, w, h, txt, act):
        self.rect = pygame.Rect(x, y, w, h)
        self.txt, self.act = txt, act
    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect, border_radius=8)
        screen.blit(font.render(self.txt, True, BLACK), (self.rect.x+10, self.rect.y+8))
    def click(self): self.act()

buttons = [
    Button(50, 500, 140, 50, "유닛 생성", lambda: nation2.create_unit(nation2.border_line) or print("유닛 생성!")),
    Button(200, 500, 140, 50, "훈련장 건설", lambda: nation2.build_facility(FacilityType.TRAINING) or print("훈련장 건설!")),
    Button(350, 500, 140, 50, "의회 건설", lambda: nation2.build_facility(FacilityType.PARLIAMENT) or print("의회 건설!")),
    Button(600, 500, 140, 50, "종료", lambda: pygame.quit() or exit())
]

def draw_map():
    map_y = 180
    cell_w = 65
    for i in range(MAP_SIZE):
        x = 60 + i * cell_w
        color = RED if i > nation2.border_line else BLUE
        pygame.draw.rect(screen, color, (x, map_y, cell_w-5, 140), border_radius=5)
        if i == nation2.border_line:
            pygame.draw.line(screen, (200,0,0), (x, map_y), (x, map_y+140), 6)
        for u in nation2.units:
            if u['pos'] == i:
                size = 12 + u['level']*2
                pygame.draw.circle(screen, GREEN, (x+20, map_y+70), size)
                if u == selected_unit:
                    pygame.draw.circle(screen, YELLOW, (x+20, map_y+70), size+5, 3)

def draw():
    screen.fill(WHITE)
    nation2.collect_tax()
    tax_rate = TAX_RATE if nation2.facilities[FacilityType.PARLIAMENT] else 0
    screen.blit(font.render(f"{nation2.name} | 자원: {nation2.resources} (+{tax_rate}/s)", True, BLACK), (50, 50))
    screen.blit(font.render(f"유닛: {len(nation2.units)} | 적군: {opponent_units}", True, BLACK), (50, 90))
    if game_over:
        screen.blit(font.render("게임 종료!", True, RED), (300, 250))
    draw_map()
    for b in buttons: b.draw()
    pygame.display.flip()

def recv_thread(conn):
    global opponent_units, game_over
    while True:
        try:
            data = json.loads(conn.recv(1024).decode())
            if "winner" in data:
                print(data["winner"], "승리!")
                game_over = True
                break
            opponent_units = data.get("units1", 0)
        except: break

# === 입력 안전하게 처리 ===
idx = 0
inputs = ["", "", ""]
field = religion = hero = None

while idx < 3:
    screen.fill(WHITE)
    for i, p in enumerate(["분야 (0~3): ", "종교 (0~2): ", "위인 (0~3): "]):
        col = RED if i == idx else BLACK
        screen.blit(font.render(p + inputs[i], True, col), (50, 100 + i*50))
    pygame.display.flip()

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN and inputs[idx].strip():
                try:
                    val = int(inputs[idx])
                    if idx == 0 and 0 <= val < 4: field = val
                    elif idx == 1 and 0 <= val < 3: religion = val
                    elif idx == 2 and 0 <= val < 4: hero = val
                    else: continue
                    idx += 1
                    if idx < 3:
                        inputs[idx] = ""
                    else:
                        break
                except: pass
            elif e.key == pygame.K_BACKSPACE:
                inputs[idx] = inputs[idx][:-1]
            elif e.unicode.isdigit():
                inputs[idx] += e.unicode
    else:
        continue
    break

cli = socket.socket()
cli.connect(('172.16.200.209', 5555))  # ← 서버 IP로 변경!
cli.sendall(json.dumps({"field": field, "religion": religion, "hero": hero}).encode())
opp = json.loads(cli.recv(1024).decode())
print(f"상대: {FIELDS[opp['field']]}, {RELIGIONS[opp['religion']]}, {HEROES[opp['hero']]}")

nation2.choose_field(field)
nation2.choose_religion(religion)
nation2.choose_hero(hero)
threading.Thread(target=recv_thread, args=(cli,), daemon=True).start()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: exit()
        if e.type == pygame.MOUSEBUTTONDOWN and not game_over:
            pos = e.pos
            for b in buttons:
                if b.rect.collidepoint(pos): b.click()
            cell = (pos[0] - 60) // 65
            if 0 <= cell < MAP_SIZE:
                for u in nation2.units:
                    if u['pos'] == cell:
                        selected_unit = u; break
        if e.type == pygame.MOUSEBUTTONUP and selected_unit and not game_over:
            cell = (e.pos[0] - 60) // 65
            if nation2.border_line < cell < MAP_SIZE and cell != selected_unit['pos']:
                selected_unit['pos'] = cell
            selected_unit = None
    draw()
    clock.tick(30)
