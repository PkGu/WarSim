# server.py
import socket
import threading
import time
import json
import random
import pygame
from game_core import *

# === Pygame 초기화 ===
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("국가전쟁 게임 - 국가1 (서버)")
font = pygame.font.Font("NotoSansKR-Regular.ttf", 30)
clock = pygame.time.Clock()

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# === 국가 생성 ===
nation1 = Nation("국가1")
nation2 = Nation("국가2")

# === 버튼 클래스 ===
class Button:
    def __init__(self, x, y, w, h, text, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.action = action

    def draw(self):
        pygame.draw.rect(screen, GREEN, self.rect)
        text_surf = font.render(self.text, True, BLACK)
        screen.blit(text_surf, (self.rect.x + 10, self.rect.y + 10))

    def click(self):
        self.action()

# === 버튼 목록 ===
buttons = [
    Button(50, 400, 150, 50, "유닛 생성", lambda: print("생성 성공" if nation1.create_unit(4) else "훈련장 필요")),
    Button(220, 400, 150, 50, "훈련장 건설", lambda: print("건설 성공" if nation1.build_facility(FacilityType.TRAINING) else "자원 부족")),
    Button(390, 400, 150, 50, "정비소 건설", lambda: print("건설 성공" if nation1.build_facility(FacilityType.REPAIR) else "자원 부족")),
    Button(560, 400, 150, 50, "종료", lambda: pygame.quit() or exit())
]

# === 화면 그리기 ===
def draw_game_state():
    screen.fill(WHITE)
    text = font.render(f"{nation1.name} | 자원: {nation1.resources} | 유닛: {len(nation1.units)}", True, BLACK)
    screen.blit(text, (50, 50))
    text = font.render(f"분야: {nation1.field or '미정'} | 종교: {nation1.religion or '미정'} | 위인: {nation1.hero or '미정'}", True, BLACK)
    screen.blit(text, (50, 100))
    text = font.render(f"적군 유닛: {len(nation2.units)}", True, RED)
    screen.blit(text, (50, 150))
    for btn in buttons:
        btn.draw()
    pygame.display.flip()

# === 클라이언트 처리 ===
def handle_client(conn):
    global nation2
    try:
        data = json.loads(conn.recv(2048).decode())
        nation2.choose_field(data['field'])
        nation2.choose_religion(data['religion'])
        nation2.choose_hero(data['hero'])
    except:
        return

    try:
        conn.sendall(json.dumps({
            'field': FIELDS.index(nation1.field),
            'religion': RELIGIONS.index(nation1.religion),
            'hero': HEROES.index(nation1.hero)
        }).encode())
    except:
        return

    # 준비 시간
    start = time.time()
    while time.time() - start < PREP_TIME:
        if random.random() < 0.05:
            nation1.debuffs['corruption'] = True
        time.sleep(1)

    # 전투 루프
    while nation1.facilities[FacilityType.PINPOINT] and nation2.facilities[FacilityType.PINPOINT]:
        atk1 = sum(u['atk'] for u in nation1.units) * nation1.apply_buffs()
        atk2 = sum(u['atk'] for u in nation2.units) * nation2.apply_buffs()

        for u in nation2.units:
            u['hp'] -= atk1 / max(1, len(nation2.units))
        for u in nation1.units:
            u['hp'] -= atk2 / max(1, len(nation1.units))

        nation2.units = [u for u in nation2.units if u['hp'] > 0]
        nation1.units = [u for u in nation1.units if u['hp'] > 0]

        try:
            conn.sendall(json.dumps({
                'units1': len(nation1.units),
                'units2': len(nation2.units),
                'winner': None
            }).encode())
        except:
            break
        time.sleep(2)

    winner = nation1.name if not nation2.facilities[FacilityType.PINPOINT] else nation2.name
    try:
        conn.sendall(json.dumps({'winner': winner}).encode())
    except:
        pass
    conn.close()

# === 메인 함수 ===
def main():
    running = True
    input_field = 0
    inputs = ["", "", ""]

    # 초기 설정 입력
    while running and input_field < 3:
        screen.fill(WHITE)
        text = font.render("초기 설정 (숫자 입력 후 엔터):", True, BLACK)
        screen.blit(text, (50, 50))
        prompts = ["분야 (0~3): ", "종교 (0~2): ", "위인 (0~3): "]
        for i, p in enumerate(prompts):
            color = RED if i == input_field else BLACK
            text = font.render(p + inputs[i], True, color)
            screen.blit(text, (50, 100 + i*50))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and inputs[input_field]:
                    val = int(inputs[input_field])
                    if input_field == 0: field = val
                    elif input_field == 1: religion = val
                    elif input_field == 2: hero = val
                    input_field += 1
                    if input_field < 3:
                        inputs[input_field] = ""
                elif event.key == pygame.K_BACKSPACE:
                    inputs[input_field] = inputs[input_field][:-1]
                elif event.unicode.isdigit():
                    inputs[input_field] += event.unicode

    if not running: return

    nation1.choose_field(field)
    nation1.choose_religion(religion)
    nation1.choose_hero(hero)

    # 서버 시작
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('0.0.0.0', 5555))
    server.listen(1)
    print("서버 대기 중... (클라이언트 연결 대기)")

    conn, addr = server.accept()
    print(f"연결됨: {addr}")
    threading.Thread(target=handle_client, args=(conn,), daemon=True).start()

    # GUI 루프
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(event.pos):
                        btn.click()
        draw_game_state()
        clock.tick(30)

    pygame.quit()
    server.close()

if __name__ == "__main__":
    main()