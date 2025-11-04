# client/client_main.py
import pygame
import socket
import threading
import json

HOST = "127.0.0.1"
PORT = 5000

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
state = {"gold": 0, "units": [], "has_parliament": False}

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))

def listen_server():
    global state
    while True:
        try:
            data = client.recv(4096)
            if not data:
                break
            msg = json.loads(data.decode())
            if msg.get("type") == "update":
                state = msg["state"]
        except:
            break

threading.Thread(target=listen_server, daemon=True).start()

def draw():
    screen.fill((40, 40, 60))
    # 맵 영역 (2D)
    pygame.draw.rect(screen, (70, 100, 70), (50, 50, 600, 400))
    # UI 아래쪽
    ui_y = 480
    pygame.draw.rect(screen, (30, 30, 30), (0, ui_y, 800, 120))
    screen.blit(font.render(f"Gold: {state['gold']}", True, (255,255,0)), (50, ui_y + 20))
    screen.blit(font.render(f"Units: {len(state['units'])}", True, (255,255,255)), (50, ui_y + 50))
    if state['has_parliament']:
        screen.blit(font.render("Parliament built ✅", True, (100,255,100)), (250, ui_y + 20))
    else:
        screen.blit(font.render("No parliament yet", True, (255,100,100)), (250, ui_y + 20))
    pygame.display.flip()

def send_command(cmd):
    client.sendall(json.dumps({"command": cmd}).encode())

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                send_command("build_parliament")
            elif event.key == pygame.K_2:
                send_command("create_unit")

    draw()
    clock.tick(30)

pygame.quit()
