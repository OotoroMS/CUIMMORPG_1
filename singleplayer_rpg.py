#!/usr/bin/env python3
import json
import random
import os

# Base stats for each job
BASE_STATS = {
    '戦士':    {'HP': 30, 'MP': 5,  'ATK': 8, 'DEF': 8, 'MAT': 2, 'MDE': 3, 'AGI': 5, 'LUK': 5},
    '神官':    {'HP': 20, 'MP': 15, 'ATK': 4, 'DEF': 4, 'MAT': 6, 'MDE': 6, 'AGI': 4, 'LUK': 5},
    '魔法使い': {'HP': 18, 'MP': 20, 'ATK': 3, 'DEF': 3, 'MAT': 8, 'MDE': 5, 'AGI': 5, 'LUK': 5},
    '盗賊':    {'HP': 22, 'MP': 8,  'ATK': 5, 'DEF': 4, 'MAT': 3, 'MDE': 3, 'AGI': 8, 'LUK': 7},
    '魔法戦士': {'HP': 25, 'MP': 10, 'ATK': 6, 'DEF': 6, 'MAT': 4, 'MDE': 4, 'AGI': 6, 'LUK': 5},
    'どうぐ使い': {'HP': 20, 'MP': 10, 'ATK': 4, 'DEF': 4, 'MAT': 2, 'MDE': 4, 'AGI': 6, 'LUK': 8},
}

MAX_LEVEL = 20
SAVE_FILE = 'savegame.json'

# Experience needed for each level
LEVEL_EXP = [0]
for lv in range(1, MAX_LEVEL + 1):
    LEVEL_EXP.append(LEVEL_EXP[-1] + lv * 10)

# Item definitions
ITEMS = {
    '回復薬-1': {'type': 'heal', 'power': 20, 'target': 'ally'},
    '回復薬-2': {'type': 'heal', 'power': 40, 'target': 'ally'},
    '火炎草':   {'type': 'attack', 'power': 20, 'target': 'enemy'},
    'ばくだん石': {'type': 'attack', 'power': 20, 'target': 'all_enemies'},
}

class Character:
    def __init__(self, name, job):
        self.name = name
        self.job = job
        self.level = 1
        self.exp = 0
        self.stats = BASE_STATS[job].copy()
        self.hp = self.stats['HP']
        self.mp = self.stats['MP']
        self.defending = False

    def is_alive(self):
        return self.hp > 0

    def gain_exp(self, amount):
        self.exp += amount
        while self.level < MAX_LEVEL and self.exp >= LEVEL_EXP[self.level]:
            self.level += 1
            self.level_up()
            print(f"{self.name}はレベル{self.level}に上がった！")

    def level_up(self):
        # Simple stat growth
        for key in ['HP', 'MP', 'ATK', 'DEF', 'MAT', 'MDE', 'AGI', 'LUK']:
            self.stats[key] += 2
        self.hp = self.stats['HP']
        self.mp = self.stats['MP']

    def attack(self, target):
        base = self.stats['ATK'] / 2 - target.stats['DEF'] / 4
        base = max(1, base)
        variation = random.uniform(0.92, 1.08)
        dmg = int(base * variation)
        if target.defending:
            dmg //= 2
        target.hp = max(0, target.hp - dmg)
        return dmg

class Enemy:
    def __init__(self, name, hp, atk, defense, agi, exp):
        self.name = name
        self.stats = {'HP': hp, 'ATK': atk, 'DEF': defense, 'AGI': agi}
        self.hp = hp
        self.exp = exp
        self.defending = False

    def is_alive(self):
        return self.hp > 0

    def attack(self, target):
        base = self.stats['ATK'] / 2 - target.stats['DEF'] / 4
        base = max(1, base)
        variation = random.uniform(0.92, 1.08)
        dmg = int(base * variation)
        if target.defending:
            dmg //= 2
        target.hp = max(0, target.hp - dmg)
        return dmg

class Game:
    def __init__(self):
        self.party = []
        self.floor = 1
        self.inventory = {name: 2 for name in ITEMS}  # start with some items

    def save(self):
        data = {
            'floor': self.floor,
            'party': [self.char_to_dict(c) for c in self.party],
            'inventory': self.inventory,
        }
        with open(SAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print('ゲームを保存しました。')

    @staticmethod
    def char_to_dict(c):
        return {
            'name': c.name,
            'job': c.job,
            'level': c.level,
            'exp': c.exp,
            'stats': c.stats,
            'hp': c.hp,
            'mp': c.mp,
        }

    @staticmethod
    def dict_to_char(d):
        c = Character(d['name'], d['job'])
        c.level = d['level']
        c.exp = d['exp']
        c.stats = d['stats']
        c.hp = d['hp']
        c.mp = d['mp']
        return c

    def load(self):
        if not os.path.exists(SAVE_FILE):
            print('セーブデータがありません。')
            return False
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.floor = data.get('floor', 1)
        self.party = [self.dict_to_char(d) for d in data.get('party', [])]
        self.inventory = data.get('inventory', {})
        print('ゲームをロードしました。')
        return True

    def create_party(self):
        print('--- キャラ作成 ---')
        jobs = list(BASE_STATS.keys())
        for i in range(4):
            name = input(f'キャラ{i+1}の名前: ')
            while True:
                for j, job in enumerate(jobs, 1):
                    print(f'{j}. {job}')
                try:
                    choice = int(input('職業を選択: ')) - 1
                    job = jobs[choice]
                except (ValueError, IndexError):
                    print('もう一度入力してください')
                    continue
                break
            self.party.append(Character(name, job))
        print('パーティを作成しました。')

    def run(self):
        print('ゲーム開始！')
        while self.floor <= 5:
            print(f'\n-- {self.floor}階 --')
            if self.floor == 5:
                self.boss_battle()
                if not any(c.is_alive() for c in self.party):
                    print('全滅しました...ゲームオーバー')
                    return
                print('ボスを倒した！ ゲームクリア！')
                self.save()
                return
            self.floor_event()
            if not any(c.is_alive() for c in self.party):
                print('全滅しました...ゲームオーバー')
                return
            self.floor += 1
        self.save()

    def floor_event(self):
        r = random.random()
        if r < 0.8:
            enemy = self.random_enemy()
            self.battle(enemy)
        elif r < 0.9:
            item = '回復薬-1'
            self.inventory[item] = self.inventory.get(item, 0) + 1
            print('宝箱を見つけた！ 回復薬-1を手に入れた。')
        else:
            for c in self.party:
                c.hp = c.stats['HP']
            print('回復ポイントだ！ HPが全回復した。')

    def random_enemy(self):
        enemies = [
            Enemy('スライム', 15, 5, 2, 3, 5),
            Enemy('ゴブリン', 20, 6, 3, 4, 8),
            Enemy('オオカミ', 25, 7, 4, 6, 10),
        ]
        return random.choice(enemies)

    def boss_battle(self):
        boss = Enemy('ダンジョンボス', 50, 10, 6, 5, 50)
        print(f'{boss.name}が現れた！')
        self.battle(boss)

    def battle(self, enemy):
        print(f'{enemy.name}との戦闘！')
        escape_chance = 0.25
        while enemy.is_alive() and any(c.is_alive() for c in self.party):
            order = sorted([c for c in self.party if c.is_alive()], key=lambda x: x.stats['AGI'], reverse=True)
            enemy_turn = enemy.stats['AGI'] >= max(c.stats['AGI'] for c in order)
            if enemy_turn:
                self.enemy_action(enemy, random.choice(order))
            for char in order:
                if not enemy.is_alive():
                    break
                if char.is_alive():
                    self.player_action(char, enemy, escape_chance)
                    if escape_chance < 1:
                        escape_chance += 0.25
            if enemy.is_alive() and any(c.is_alive() for c in self.party):
                self.enemy_action(enemy, random.choice(order))
        if enemy.hp <= 0:
            print(f'{enemy.name}を倒した！')
            for c in self.party:
                if c.is_alive():
                    c.gain_exp(enemy.exp)
        else:
            print('戦闘から離脱した。')

    def player_action(self, char, enemy, escape_chance):
        char.defending = False
        while True:
            print(f'\n{char.name}のターン HP:{char.hp}/{char.stats["HP"]} MP:{char.mp}/{char.stats["MP"]}')
            print('1. 攻撃 2. 防御 3. アイテム 4. 逃げる')
            cmd = input('> ')
            if cmd == '1':
                dmg = char.attack(enemy)
                print(f'{char.name}の攻撃！ {enemy.name}に{dmg}のダメージ')
                break
            elif cmd == '2':
                char.defending = True
                print(f'{char.name}は身を守っている')
                break
            elif cmd == '3':
                if not self.inventory:
                    print('アイテムがない')
                    continue
                self.use_item(char, enemy)
                break
            elif cmd == '4':
                if random.random() < escape_chance:
                    enemy.hp = 0
                    print('逃げ出した！')
                else:
                    print('逃げられなかった')
                break
            else:
                print('もう一度入力してください')

    def use_item(self, char, enemy):
        items = [name for name, cnt in self.inventory.items() if cnt > 0]
        for i, name in enumerate(items, 1):
            print(f'{i}. {name} x{self.inventory[name]}')
        try:
            choice = int(input('使うアイテムを選択: ')) - 1
            item_name = items[choice]
        except (ValueError, IndexError):
            print('キャンセル')
            return
        item = ITEMS[item_name]
        self.inventory[item_name] -= 1
        if item['type'] == 'heal':
            char.hp = min(char.stats['HP'], char.hp + item['power'])
            print(f'{char.name}のHPが{item["power"]}回復した')
        elif item['type'] == 'attack':
            if item['target'] == 'enemy':
                enemy.hp = max(0, enemy.hp - item['power'])
                print(f'{enemy.name}に{item["power"]}のダメージを与えた')
            else:
                enemy.hp = max(0, enemy.hp - item['power'])
                print(f'{enemy.name}に{item["power"]}のダメージを与えた')

    def enemy_action(self, enemy, target):
        if not target.is_alive():
            return
        dmg = enemy.attack(target)
        print(f'{enemy.name}の攻撃！ {target.name}に{dmg}のダメージ')


def main():
    game = Game()
    print('1) 最初から\n2) ロード')
    choice = input('> ')
    if choice == '2' and game.load():
        pass
    else:
        game.create_party()
    game.run()

if __name__ == '__main__':
    main()
