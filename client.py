import socket
import threading
import time
import random  # 추가됨
import json

# 상수 및 Nation 클래스 (server.py와 동일)
PREP_TIME = 60
RESOURCE_START = 1000
UNIT_COST = 100
LEVEL_UP_COST = 50
MAX_LEVEL = 10

FIELDS = ["마법", "검술", "무술", "과학기술"]
RELIGIONS = ["신앙A", "신앙B"]
HEROES = ["대마법사", "소드마스터", "무신", "매드 사이언티스트"]

class Nation:
    def __init__(self, name):
        self.name = name
        self.field = None
        self.religion = None
        self.hero = None
        self.resources = RESOURCE_START
        self.units = []
        self.pinpoint_hp = 1000
        self.buffs = {}

    def choose_field(self, choice):
        self.field = FIELDS[choice - 1]
        print(f"{self.name} 분야 선택: {self.field}")

    def choose_religion(self, choice):
        self.religion = RELIGIONS[choice - 1]
        if self.field == "마법" and self.religion == "신앙A":
            self.buffs['atk'] = 1.1
        else:
            self.buffs['atk'] = 0.9
        print(f"{self.name} 종교 선택: {self.religion}")

    def choose_hero(self, choice):
        self.hero = HEROES[choice - 1]
        print(f"{self.name} 위인 선택: {self.hero}")

    def create_unit(self):
        if self.resources >= UNIT_COST:
            self.resources -= UNIT_COST
            unit = {'level': 1, 'hp': 100, 'atk': 10}
            if self.hero == "대마법사" and self.field == "마법":
                unit['atk'] += 5
            self.units.append(unit)
            print(f"{self.name} 유닛 생성 → 총 {len(self.units)}기")
        else:
            print("자원 부족!")

    def level_up_unit(self, index):
        if 0 <= index < len(self.units) and self.resources >= LEVEL_UP_COST:
            unit = self.units[index]
            if unit['level'] < MAX_LEVEL:
                self.resources -= LEVEL_UP_COST
                unit['level'] += 1
                unit['hp'] += 50
                unit['atk'] += 5
                print(f"{self.name} 유닛 {index} 레벨업 → 레벨 {unit['level']}")
            else:
                print("최대 레벨입니다.")
        else:
            print("자원 부족 또는 잘못된 인덱스")

def handle_server(conn, nation2):
    print("준비 시간 시작...")
    start = time.time()
    while time.time() - start < PREP_TIME:
        if random.random() < 0.1:
            nation2.buffs['atk'] = 0.8
            print(f"{nation2.name} 디버프 발생! (공격력 0.8배)")
        time.sleep(1)

    print("전쟁 시작! HP 업데이트 수신 중...")
    while True:
        try:
            data = conn.recv(1024).decode()
            if not data:
                break
            hps = json.loads(data)
            print(f"국가1 HP: {hps['hp1']:<6} | {nation2.name} HP: {hps['hp2']:<6}")
            if hps['hp1'] <= 0 or hps['hp2'] <= 0:
                winner = "국가1" if hps['hp2'] <= 0 else nation2.name
                print(f"\n=== {winner} 승리! ===")
                break
        except:
            break

def main():
    nation2 = Nation("국가2")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect(('localhost', 5555))
    except:
        print("서버에 연결할 수 없습니다. server.py를 먼저 실행하세요.")
        return

    # 상대 정보 수신
    try:
        opp_data = client.recv(1024).decode()
        opponent = json.loads(opp_data)
        print(f"\n상대 → 분야:{opponent['field']} | 종교:{opponent['religion']} | 위인:{opponent['hero']}\n")
    except:
        print("상대 정보 수신 실패")
        return

    # 본인 설정 입력
    print("=== 국가2 설정 ===")
    field = int(input("분야 선택 (1~4): "))
    nation2.choose_field(field)
    religion = int(input("종교 선택 (1~2): "))
    nation2.choose_religion(religion)
    hero = int(input("위인 선택 (1~4): "))
    nation2.choose_hero(hero)

    client.sendall(json.dumps({'field': field, 'religion': religion, 'hero': hero}).encode())

    # 통신 스레드 시작
    threading.Thread(target=handle_server, args=(client, nation2), daemon=True).start()

    # 입력 루프
    print("\n명령어: create, level <번호>, quit")
    while True:
        try:
            cmd = input().strip()
            if cmd == "create":
                nation2.create_unit()
            elif cmd.startswith("level"):
                parts = cmd.split()
                if len(parts) == 2:
                    idx = int(parts[1])
                    nation2.level_up_unit(idx)
            elif cmd == "quit":
                break
        except:
            pass

    client.close()

if __name__ == "__main__":
    main()
