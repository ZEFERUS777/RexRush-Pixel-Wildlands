import json
import os
import random
import sys
from datetime import datetime

import pygame

# Инициализация Pygame
pygame.init()

# Константы
WIDTH = 800
HEIGHT = 600
GRID_SIZE = 20
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
BLACK = (0, 0, 0)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

# Пути
FONT_PATH = os.path.join('fonts', 'TeletactileRus.ttf')
SAVE_FILE = 'save.json'

# Проверка и загрузка шрифта
if not os.path.exists(FONT_PATH):
    print(f"Ошибка: Файл шрифта {FONT_PATH} не найден!")
    sys.exit()

try:
    CUSTOM_FONT = pygame.font.Font(FONT_PATH, 24)
except pygame.error:
    print("Ошибка загрузки шрифта, используется стандартный шрифт")
    CUSTOM_FONT = pygame.font.Font(None, 24)


class Snake:
    def __init__(self):
        self.reset()

    def reset(self):
        self.body = [(WIDTH // 2, HEIGHT // 2)]
        self.direction = (1, 0)
        self.new_direction = (1, 0)
        self.speed_multiplier = 1.0
        self.growing = False
        self.rainbow_mode = False
        self.rainbow_offset = 0  # Смещение для переливания радуги

    def move(self):
        self.direction = self.new_direction
        new_head = (
            self.body[0][0] + self.direction[0] * GRID_SIZE,
            self.body[0][1] + self.direction[1] * GRID_SIZE
        )

        # Проверка столкновения с самим собой
        if new_head in self.body:
            return False

        # Проверка границ экрана
        if (new_head[0] < 0 or new_head[0] >= WIDTH or
                new_head[1] < 0 or new_head[1] >= HEIGHT):
            return False

        self.body.insert(0, new_head)

        if not self.growing:
            self.body.pop()
        else:
            self.growing = False
        return True

    def grow(self):
        self.growing = True

    def shrink(self):
        if len(self.body) > 1:
            self.body.pop()


class Enemy:
    def __init__(self):
        self.position = (
            random.randrange(0, WIDTH, GRID_SIZE),
            random.randrange(0, HEIGHT, GRID_SIZE)
        )
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        self.color = CYAN

    def move(self):
        new_x = self.position[0] + self.direction[0] * GRID_SIZE
        new_y = self.position[1] + self.direction[1] * GRID_SIZE

        if new_x < 0 or new_x >= WIDTH or new_y < 0 or new_y >= HEIGHT:
            self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        else:
            self.position = (new_x, new_y)


SOUNDS_DIR = 'sounds'


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Продвинутая Змейка")
        self.clock = pygame.time.Clock()
        self.snake = Snake()
        self.enemies = []
        self.food = self.generate_food()
        self.special_food = None
        self.coin = None
        self.bomb = None
        self.score = 0
        self.coins = 0
        self.lives = 3
        self.level = 1
        self.difficulty = 10
        self.running = True
        self.game_over = False
        self.speed_timer = 0
        self.special_effects = {'speed_boost': False, 'shield': False}
        self.achievements = {
            'first_coin': False,
            'coin_collector': False,
            'snake_master': False,
            'immortal': False,
            'speed_master': False
        }
        self.high_score = 0
        self.load_data()

        self.sounds = {}
        try:
            self.sounds['buy'] = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'buy_item.flac'))
            self.sounds['collision'] = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'collision.wav'))
            self.sounds['food'] = pygame.mixer.Sound(os.path.join(SOUNDS_DIR, 'food_collect.wav'))
        except Exception as e:
            print(f"Ошибка загрузки звуков: {e}")
            self.sounds = {}

    def load_data(self):
        if os.path.exists(SAVE_FILE):
            with open(SAVE_FILE, 'r') as f:
                data = json.load(f)
                self.coins = data.get('coins', 0)
                self.high_score = data.get('high_score', 0)
                self.achievements = data.get('achievements', self.achievements)

    def save_data(self):
        data = {
            'coins': self.coins,
            'high_score': self.high_score,
            'achievements': self.achievements,
            'save_date': str(datetime.now())
        }
        with open(SAVE_FILE, 'w') as f:
            json.dump(data, f)

    def generate_food(self, color=RED):
        while True:
            pos = (
                random.randrange(0, WIDTH, GRID_SIZE),
                random.randrange(0, HEIGHT, GRID_SIZE)
            )
            if pos not in self.snake.body:
                return pos, color

    def generate_special_food(self):
        types = [
            (BLUE, 'speed_boost'),
            (PURPLE, 'shrink'),
            (ORANGE, 'coin_bonus')
        ]
        color, effect = random.choice(types)
        return self.generate_food(color)[0], effect

    def generate_bomb(self):
        return self.generate_food(PURPLE)[0]

    def handle_input(self):
        keys = pygame.key.get_pressed()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if self.game_over:
                    if event.key == pygame.K_r:
                        self.reset_game()
                else:
                    if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                        self.snake.new_direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                        self.snake.new_direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                        self.snake.new_direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                        self.snake.new_direction = (1, 0)
                    elif event.key == pygame.K_b and self.coins >= 15 and self.lives < 5:
                        self.coins -= 15
                        self.lives += 1
                        if 'buy' in self.sounds:
                            self.sounds['buy'].play()
                    elif event.key == pygame.K_s and self.coins >= 30:
                        self.coins -= 30
                        self.special_effects['shield'] = True
                        if 'buy' in self.sounds:
                            self.sounds['buy'].play()
                    elif event.key == pygame.K_f and self.coins >= 50:
                        self.coins -= 50
                        for enemy in self.enemies:
                            enemy.direction = (0, 0)
                        if 'buy' in self.sounds:
                            self.sounds['buy'].play()
                    elif event.key == pygame.K_h:
                        self.snake.rainbow_mode = not self.snake.rainbow_mode

        # Ускорение при нажатии Shift
        if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
            self.snake.speed_multiplier = 2.0
        else:
            self.snake.speed_multiplier = 1.0

    def reset_game(self):
        self.snake.reset()
        self.food = self.generate_food()
        self.coin = None
        self.special_food = None
        self.bomb = None
        self.enemies.clear()
        self.score = 0
        self.lives = 3
        self.level = 1
        self.difficulty = 10
        self.game_over = False
        self.special_effects = {'speed_boost': False, 'shield': False}

    def check_achievements(self):
        if not self.achievements['first_coin'] and self.coins >= 1:
            self.achievements['first_coin'] = True
        if not self.achievements['coin_collector'] and self.coins >= 50:
            self.achievements['coin_collector'] = True
        if not self.achievements['snake_master'] and self.level >= 5:
            self.achievements['snake_master'] = True
        if not self.achievements['immortal'] and self.lives >= 5:
            self.achievements['immortal'] = True

    def update_level(self):
        if self.score // 100 + 1 > self.level:
            self.level += 1
            self.difficulty += 2
            self.lives = min(self.lives + 1, 5)
            # Добавление врагов в зависимости от сложности
            max_enemies = 1 if self.difficulty == 8 else 2 if self.difficulty == 12 else 3
            while len(self.enemies) < max_enemies:
                self.enemies.append(Enemy())

    def show_start_screen(self):
        self.screen.fill(BLACK)
        texts = [
            "Выберите сложность:",
            "1 - Легкая",
            "2 - Средняя",
            "3 - Сложная"
        ]
        for i, text in enumerate(texts):
            rendered = CUSTOM_FONT.render(text, True, WHITE)
            self.screen.blit(rendered, (WIDTH // 2 - rendered.get_width() // 2, HEIGHT // 2 - 60 + i * 30))
        pygame.display.flip()

        selecting = True
        while selecting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_1:
                        self.difficulty = 8
                        selecting = False
                    elif event.key == pygame.K_2:
                        self.difficulty = 12
                        selecting = False
                    elif event.key == pygame.K_3:
                        self.difficulty = 18
                        selecting = False

    def run(self):
        self.show_start_screen()

        while self.running:
            self.handle_input()

            if not self.game_over:
                # Движение змейки и проверка границ
                if not self.snake.move():
                    self.lives -= 1
                    if 'collision' in self.sounds:
                        self.sounds['collision'].play()
                    if self.lives <= 0:
                        self.game_over = True
                    else:
                        self.snake.reset()

                # Обновление врагов
                for enemy in self.enemies:
                    if enemy.position == self.snake.body[0]:
                        if self.special_effects['shield']:
                            self.special_effects['shield'] = False
                        else:
                            self.lives -= 1
                            if 'collision' in self.sounds:
                                self.sounds['collision'].play()
                    enemy.move()

                # Проверка столкновений с врагами
                for enemy in self.enemies:
                    if enemy.position == self.snake.body[0]:
                        if self.special_effects['shield']:
                            self.special_effects['shield'] = False
                        else:
                            self.lives -= 1
                            if self.lives <= 0:
                                self.game_over = True
                            else:
                                self.snake.reset()

                # Обновление игровой логики
                self.update_level()
                self.check_achievements()

                if self.score > self.high_score:
                    self.high_score = self.score

                if self.special_effects['speed_boost']:
                    self.speed_timer -= 1
                    if self.speed_timer <= 0:
                        self.special_effects['speed_boost'] = False
                        self.snake.speed_multiplier = 1.0

                # Проверка сбора еды
                if self.snake.body[0] == self.food[0]:
                    self.score += 10
                    self.coins += 2
                    self.snake.grow()
                    self.food = self.generate_food()
                    if 'food' in self.sounds:
                        self.sounds['food'].play()

                    if random.random() < 0.4:
                        self.coin = self.generate_food(YELLOW)[0]
                    if random.random() < 0.2:
                        self.special_food = self.generate_special_food()
                    if random.random() < 0.1:
                        self.bomb = self.generate_bomb()

                # Специальная еда
                if self.special_food and self.snake.body[0] == self.special_food[0]:
                    effect = self.special_food[1]
                    if effect == 'speed_boost':
                        self.special_effects['speed_boost'] = True
                        self.snake.speed_multiplier = 1.5
                        self.speed_timer = 150
                    elif effect == 'shrink':
                        for _ in range(3):
                            self.snake.shrink()
                    elif effect == 'coin_bonus':
                        self.coins += 15
                    self.special_food = None

                # Сбор монет
                if self.coin and self.snake.body[0] == self.coin:
                    self.coins += 5
                    self.coin = None

                # Бомба
                if self.bomb and self.snake.body[0] == self.bomb:
                    self.snake.shrink()
                    self.bomb = None

                # Отрисовка
                self.screen.fill(BLACK)

                # Змейка
                rainbow_colors = [(255, 0, 0), (255, 165, 0), (255, 255, 0), (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211)]
                self.snake.rainbow_offset += 0.1  # Увеличиваем смещение для эффекта переливания
                for i, segment in enumerate(self.snake.body):
                    if self.snake.rainbow_mode:
                        offset_color_index = int((i + self.snake.rainbow_offset) % len(rainbow_colors))
                        color = rainbow_colors[offset_color_index]
                    else:
                        color = GREEN if i == 0 else (0, 200, 0)
                    pygame.draw.rect(self.screen, color, (segment[0], segment[1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Еда
                pygame.draw.rect(self.screen, self.food[1],
                                 (self.food[0][0], self.food[0][1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Специальная еда
                if self.special_food:
                    pygame.draw.rect(self.screen, self.special_food[0][1],
                                     (self.special_food[0][0], self.special_food[0][1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Монеты
                if self.coin:
                    pygame.draw.rect(self.screen, YELLOW, (self.coin[0], self.coin[1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Бомба
                if self.bomb:
                    pygame.draw.rect(self.screen, PURPLE, (self.bomb[0], self.bomb[1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Враги
                for enemy in self.enemies:
                    pygame.draw.rect(self.screen, enemy.color,
                                     (enemy.position[0], enemy.position[1], GRID_SIZE - 1, GRID_SIZE - 1))

                # Интерфейс
                info_texts = [
                    f"Очки: {self.score} Рекорд: {self.high_score}",
                    f"Монеты: {self.coins}",
                    f"Жизни: {self.lives} Уровень: {self.level}",
                    f"Щит: {'Активен' if self.special_effects['shield'] else 'Нет'}",
                    f"Скорость: {'↑' if self.special_effects['speed_boost'] else 'Норма'}"
                ]

                for i, text in enumerate(info_texts):
                    rendered = CUSTOM_FONT.render(text, True, WHITE)
                    self.screen.blit(rendered, (10, 10 + i * 25))

                # Достижения
                achievement_text = CUSTOM_FONT.render("Достижения:", True, ORANGE)
                self.screen.blit(achievement_text, (WIDTH - 200, HEIGHT - 150))
                for i, (name, achieved) in enumerate(self.achievements.items()):
                    status = "✓" if achieved else "✗"
                    text = CUSTOM_FONT.render(f"{name}: {status}", True, ORANGE)
                    self.screen.blit(text, (WIDTH - 200, HEIGHT - 120 + i * 20))

                if self.game_over:
                    game_over_text = CUSTOM_FONT.render("Игра окончена! Нажмите R для рестарта", True, RED)
                    self.screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2))

                pygame.display.flip()
                self.clock.tick(int(self.difficulty * self.snake.speed_multiplier))
            else:
                self.handle_input()

        self.save_data()
        pygame.quit()


if __name__ == "__main__":
    game = Game()
    game.run()

# ---------