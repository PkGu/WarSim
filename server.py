# server.py
import socket, threading, time, json, random, pygame
from game_core import *

pygame.init()
W, H = 800, 600
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("국가1 - 서버")
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
BROWN = (139, 69, 19)

nation1 = Nation("국가1")
nation2 = Nation("국가2")
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
    Button(50, 500, 140, 50, "유닛 생성", lambda: nation1.create_unit(nation1.border_line-1) or print("유닛 생성")),
    Button(200, 500, 140, 50, "훈련장 건설", lambda: nation1.build_facility(FacilityType.TRAINING) or print("훈련장 건설")),
    Button(350, 500, 140, 50, "의회 건설", lambda: nation1.build_facility(FacilityType.PARLIAMENT) or print("의회 건설")),
    Button(600, 500, 140, 50, "종료", lambda: pygame.quit() or exit())
]

def draw_map():
    map_y = 180
    cell_w = 65
    for i in range(MAP_SIZE):
        x = 60 + i * cell_w
        # 배경
        color = BLUE if i < nation1.border_line else RED
        pygame.draw.rect(screen, color, (x, map_y, cell_w-5, 140), border_radius=5)
        # 분계선
        if i == nation1.border_line:
            pygame.draw.line(screen, (200,0,0), (x, map_y), (x, map_y+140), 6)
        # 의회 (자원 수급처)
        if nation1.facilities[FacilityType.PARLIAMENT] and i == 0:
            pygame.draw.rect(screen, BROWN, (x+10, map_y+80, 40, 50))
            pygame.draw.polygon(screen, (200,200,200), [(x+30, map_y+80), (x+15, map_y+60), (x+45, map_y+60)])
        # 유닛
        for u in nation1.units:
            if u['pos'] == i:
                size = 12 + u['level']*2
                pygame.draw.circle(screen, GREEN, (x+20, map_y+70), size)
                if u == selected_unit:
                    pygame.draw.circle(screen, YELLOW, (x+20, map_y+70), size+5, 3)
        for u in nation2.units:
            if u['pos'] == i:
                pygame.draw.circle(screen, (200,0,0), (x+40, map_y+70), 12 + u['level']*2)

def draw():
    screen.fill(WHITE)
    nation1.collect_tax()
    tax = TAX_RATE if nation1.facilities[FacilityType.PARLIAMENT] else 0
    screen.blit(font.render(f"{nation1.name} | 자원: {nation1.resources} (+{tax}/s)", True, BLACK), (50, 50))
    screen.blit(font.render(f"유닛: {len(nation1.units)} | 적: {len(nation2.units)}", True, BLACK), (50, 90))
    draw_map()
    for b in buttons: b.draw()
    pygame.display.flip()

def handle_client(conn):
    global nation2
    try:
        data = json.loads(conn.recv(1024).decode())
        nation2.choose_field(data["field"])
        nation2.choose_religion(data["religion"])
        nation2.choose_hero(data["hero"])
    except: return
    conn.sendall(json.dumps({
        "field": FIELDS.index(nation1.field),
        "religion": RELIGIONS.index(nation1.religion),
        "hero": HEROES.index(nation1.hero)
    }).encode())

    start = time.time()
    while time.time() - start < PREP_TIME:
        time.sleep(1)

    while nation1.facilities[FacilityType.PINPOINT] and nation2.facilities[FacilityType.PINPOINT]:
        atk1 = sum(u["atk"] for u in nation1.units) * nation1.apply_buffs()
        atk2 = sum(u["atk"] for u in nation2.units) * nation2.apply_buffs()
        for u in nation2.units: u["hp"] -= atk1 / max(1, len(nation2.units))
        for u in nation1.units: u["hp"] -= atk2 / max(1, len(nation1.units))
        nation2.units = [u for u in nation2.units if u["hp"] > 0]
        nation1.units = [u for u in nation1.units if u["hp"] > 0]
        try: conn.sendall(json.dumps({"units1": len(nation1.units), "units2": len(nation2.units)}).encode())
        except: break
        time.sleep(1.5)

    winner = "국가1" if not nation2.facilities[FacilityType.PINPOINT] else "국가2"
    conn.sendall(json.dumps({"winner": winner}).encode())
    conn.close()

# === 입력 안전 처리 ===
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
        if e.type == pygame.QUIT: exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_RETURN and inputs[idx].strip():
                try:
                    val = int(inputs[idx])
                    if idx == 0 and 0 <= val < 4: field = val
                    elif idx == 1 and 0 <= val < 3: religion = val
                    elif idx == 2 and 0 <= val < 4: hero = val
                    else: continue
                    idx += 1
                    if idx < 3: inputs[idx] = ""
                    else: break
                except: pass
            elif e.key == pygame.K_BACKSPACE: inputs[idx] = inputs[idx][:-1]
            elif e.unicode.isdigit(): inputs[idx] += e.unicode
    else: continue
    break

nation1.choose_field(field); nation1.choose_religion(religion); nation1.choose_hero(hero)

s = socket.socket(); s.bind(('0.0.0.0', 5555)); s.listen(1)
print("서버 대기 중...")
conn, _ = s.accept()
threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT: exit()
        if e.type == pygame.MOUSEBUTTONDOWN:
            pos = e.pos
            for b in buttons:
                if b.rect.collidepoint(pos): b.click()
            cell = (pos[0] - 60) // 65
            if 0 <= cell < MAP_SIZE:
                for u in nation1.units:
                    if u['pos'] == cell:
                        selected_unit = u; break
        if e.type == pygame.MOUSEBUTTONUP and selected_unit:
            cell = (e.pos[0] - 60) // 65
            if 0 <= cell < nation1.border_line and cell != selected_unit['pos']:
                selected_unit['pos'] = cell
            selected_unit = None
    draw(); clock.tick(30)
