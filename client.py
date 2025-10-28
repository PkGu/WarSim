import socket
import threading
import json
import pygame
from game_core import *

# Pygame 초기화
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("국가전쟁 게임 - 국가2 (클라이언트)")
font = pygame.font.SysFont(None, 30)
clock = pygame.time.Clock()

# 색상 (server.py와 동일)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

nation2 = Nation("국가2")

# 버튼 (server.py와 유사)
buttons = [
    Button(50, 400, 150, 50, "유닛 생성", lambda: nation2.create_unit(4) if nation2.create_unit(4) else print("실패")),
    Button(220, 400, 150, 50, "훈련장 건설", lambda: nation2.build_facility(FacilityType.TRAINING)),
    Button(390, 400, 150, 50, "정비소 건설", lambda: nation2.build_facility(FacilityType.REPAIR)),
    Button(560, 400, 150, 50, "종료", lambda: pygame.quit())
]

# Button 클래스 (server.py와 동일 복사)
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

def draw_game_state(nation, opponent_units):
    screen.fill(WHITE)
    
    text = font.render(f"{nation.name} | 자원: {nation.resources} | 땅: {nation.land} | 유닛 수: {len(nation.units)}", True, BLACK)
    screen.blit(text, (50, 50))
    
    text = font.render(f"분야: {nation.field} | 종교: {nation.religion} | 위인: {nation.hero}", True, BLACK)
    screen.blit(text, (50, 100))
    
    text = font.render(f"상대 유닛 수: {opponent_units}", True, BLACK)
    screen.blit(text, (50, 150))
    
    for btn in buttons:
        btn.draw()

    pygame.display.flip()

def receive_thread(conn):
    while True:
        try:
            data = json.loads(conn.recv(2048).decode())
            if 'winner' in data:
                print(f"\n=== {data['winner']} 승리! ===")
                break
            else:
                global opponent_units
                opponent_units = data['units1']  # 서버의 유닛 수
        except:
            break

def main():
    global opponent_units
    opponent_units = 0

    client = socket.socket()
    client.connect(('192.168.1.100', 5555))  # 서버 IP 변경

    # 초기 설정 (Pygame 입력)
    running = True
    input_field = 0
    inputs = ["", "", ""]

    while running and input_field < 3:
        screen.fill(WHITE)
        text = font.render("초기 설정 입력 (숫자 키):", True, BLACK)
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
                if event.key == pygame.K_RETURN:
                    try:
                        val = int(inputs[input_field])
                        if input_field == 0: field = val
                        elif input_field == 1: religion = val
                        elif input_field == 2: hero = val
                        input_field += 1
                    except:
                        pass
                elif event.key == pygame.K_BACKSPACE:
                    inputs[input_field] = inputs[input_field][:-1]
                else:
                    inputs[input_field] += event.unicode

    if not running: return

    # 설정 전송 & 상대 수신
    client.sendall(json.dumps({'field': field, 'religion': religion, 'hero': hero}).encode())
    opp = json.loads(client.recv(2048).decode())
    print(f"상대: 분야{FIELDS[opp['field']]}, 종교{RELIGIONS[opp['religion']]}, 위인{HEROES[opp['hero']]}")

    nation2.choose_field(field)
    nation2.choose_religion(religion)
    nation2.choose_hero(hero)

    threading.Thread(target=receive_thread, args=(client,)).start()

    # GUI 루프
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for btn in buttons:
                    if btn.rect.collidepoint(event.pos):
                        btn.click()

        draw_game_state(nation2, opponent_units)
        clock.tick(30)

    pygame.quit()
    client.close()

if __name__ == "__main__":
    main()
