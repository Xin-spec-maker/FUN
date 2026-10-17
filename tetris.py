#!/usr/bin/env python3
"""
经典终端版俄罗斯方块 (Terminal Tetris)
适用于 macOS / VS Code 内置终端，基于 Python 标准库 curses，零第三方依赖。
"""

import curses
import random
import time

# 游戏区域尺寸（标准 10 列 x 20 行）
BOARD_WIDTH = 10
BOARD_HEIGHT = 20

# 七种经典方块形状定义 (I, O, T, S, Z, J, L) 及对应颜色编号
SHAPES = {
    "I": {
        "blocks": [[1, 1, 1, 1]],
        "color": 1,  # 青色 Cyan
    },
    "O": {
        "blocks": [
            [1, 1],
            [1, 1],
        ],
        "color": 2,  # 黄色 Yellow
    },
    "T": {
        "blocks": [
            [0, 1, 0],
            [1, 1, 1],
        ],
        "color": 3,  # 紫色 Magenta
    },
    "S": {
        "blocks": [
            [0, 1, 1],
            [1, 1, 0],
        ],
        "color": 4,  # 绿色 Green
    },
    "Z": {
        "blocks": [
            [1, 1, 0],
            [0, 1, 1],
        ],
        "color": 5,  # 红色 Red
    },
    "J": {
        "blocks": [
            [1, 0, 0],
            [1, 1, 1],
        ],
        "color": 6,  # 蓝色 Blue
    },
    "L": {
        "blocks": [
            [0, 0, 1],
            [1, 1, 1],
        ],
        "color": 7,  # 白色/橙色替用 White
    },
}

# 消除行数对应基础加分
LINE_SCORES = {1: 100, 2: 300, 3: 500, 4: 800}


def rotate_clockwise(matrix):
    """顺时针旋转方块矩阵 90 度"""
    return [list(row) for row in zip(*matrix[::-1])]


class TetrisGame:
    def __init__(self):
        self.reset()

    def reset(self):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.score = 0
        self.lines = 0
        self.level = 1
        self.game_over = False
        self.paused = False
        self.bag = []
        self.next_type = self._draw_from_bag()
        self.spawn_piece()

    def _draw_from_bag(self):
        """使用 7-Bag 随机算法，保证方块分布均匀，体验更解压"""
        if not self.bag:
            self.bag = list(SHAPES.keys())
            random.shuffle(self.bag)
        return self.bag.pop()

    def spawn_piece(self):
        self.current_type = self.next_type
        self.next_type = self._draw_from_bag()
        shape_info = SHAPES[self.current_type]
        self.current_matrix = [row[:] for row in shape_info["blocks"]]
        self.current_color = shape_info["color"]
        self.current_x = BOARD_WIDTH // 2 - len(self.current_matrix[0]) // 2
        self.current_y = 0

        if self.check_collision(self.current_matrix, self.current_x, self.current_y):
            self.game_over = True

    def check_collision(self, matrix, offset_x, offset_y):
        for r, row in enumerate(matrix):
            for c, val in enumerate(row):
                if not val:
                    continue
                nx = offset_x + c
                ny = offset_y + r
                if nx < 0 or nx >= BOARD_WIDTH or ny >= BOARD_HEIGHT:
                    return True
                if ny >= 0 and self.board[ny][nx] != 0:
                    return True
        return False

    def move(self, dx, dy):
        if self.game_over or self.paused:
            return False
        if not self.check_collision(self.current_matrix, self.current_x + dx, self.current_y + dy):
            self.current_x += dx
            self.current_y += dy
            return True
        return False

    def rotate(self):
        if self.game_over or self.paused:
            return
        rotated = rotate_clockwise(self.current_matrix)
        # 简易踢墙（Wall Kick）：如果靠边旋转碰撞，尝试左右微调 1~2 格
        for kick_x in (0, -1, 1, -2, 2):
            if not self.check_collision(rotated, self.current_x + kick_x, self.current_y):
                self.current_matrix = rotated
                self.current_x += kick_x
                return

    def hard_drop(self):
        if self.game_over or self.paused:
            return
        drop_distance = 0
        while self.move(0, 1):
            drop_distance += 1
        self.score += drop_distance * 2
        self.lock_piece()

    def step(self):
        """定时器触发下落一步"""
        if self.game_over or self.paused:
            return
        if not self.move(0, 1):
            self.lock_piece()

    def lock_piece(self):
        for r, row in enumerate(self.current_matrix):
            for c, val in enumerate(row):
                if val:
                    by = self.current_y + r
                    bx = self.current_x + c
                    if 0 <= by < BOARD_HEIGHT and 0 <= bx < BOARD_WIDTH:
                        self.board[by][bx] = self.current_color

        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        new_board = [row for row in self.board if any(cell == 0 for cell in row)]
        cleared = BOARD_HEIGHT - len(new_board)
        if cleared > 0:
            for _ in range(cleared):
                new_board.insert(0, [0 for _ in range(BOARD_WIDTH)])
            self.board = new_board
            self.lines += cleared
            self.score += LINE_SCORES.get(cleared, cleared * 200) * self.level
            self.level = self.lines // 10 + 1

    @property
    def drop_interval(self):
        """随等级提升加快下落速度（最快 0.10 秒/格）"""
        return max(0.10, 0.65 - (self.level - 1) * 0.05)


def init_colors():
    if not curses.has_colors():
        return
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_CYAN, -1)
    curses.init_pair(2, curses.COLOR_YELLOW, -1)
    curses.init_pair(3, curses.COLOR_MAGENTA, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_RED, -1)
    curses.init_pair(6, curses.COLOR_BLUE, -1)
    curses.init_pair(7, curses.COLOR_WHITE, -1)


def safe_addstr(stdscr, y, x, text, attr=0):
    """安全绘制文本，避免终端边缘报错"""
    max_y, max_x = stdscr.getmaxyx()
    if 0 <= y < max_y and 0 <= x < max_x:
        available = max_x - x - 1
        if available > 0:
            try:
                stdscr.addstr(y, x, text[:available], attr)
            except curses.error:
                pass


def draw_game(stdscr, game):
    stdscr.erase()
    max_y, max_x = stdscr.getmaxyx()

    min_height = BOARD_HEIGHT + 4
    min_width = BOARD_WIDTH * 2 + 28
    if max_y < min_height or max_x < min_width:
        safe_addstr(stdscr, 1, 2, "终端窗口太小，请拉高或拉宽 VS Code 终端面板后继续!", curses.A_BOLD)
        safe_addstr(stdscr, 3, 2, f"当前尺寸: {max_x}x{max_y}，需要至少: {min_width}x{min_height}")
        stdscr.refresh()
        return

    top_y = 1
    left_x = 2
    board_pixel_w = BOARD_WIDTH * 2

    # 顶部标题与外框
    safe_addstr(stdscr, top_y, left_x, "=== 经典俄罗斯方块 TETRIS ===", curses.A_BOLD)
    box_top = top_y + 1
    safe_addstr(stdscr, box_top, left_x, "┌" + "──" * BOARD_WIDTH + "┐")
    for r in range(BOARD_HEIGHT):
        safe_addstr(stdscr, box_top + 1 + r, left_x, "│")
        for c in range(BOARD_WIDTH):
            cell_color = game.board[r][c]
            px = left_x + 1 + c * 2
            py = box_top + 1 + r
            if cell_color:
                safe_addstr(
                    stdscr,
                    py,
                    px,
                    "[]",
                    curses.color_pair(cell_color) | curses.A_BOLD,
                )
            else:
                safe_addstr(stdscr, py, px, " .", curses.A_DIM)
        safe_addstr(stdscr, box_top + 1 + r, left_x + 1 + board_pixel_w, "│")
    safe_addstr(stdscr, box_top + 1 + BOARD_HEIGHT, left_x, "└" + "──" * BOARD_WIDTH + "┘")

    # 绘制当前下落中的方块
    if not game.game_over:
        for r, row in enumerate(game.current_matrix):
            for c, val in enumerate(row):
                if val:
                    by = game.current_y + r
                    bx = game.current_x + c
                    if 0 <= by < BOARD_HEIGHT and 0 <= bx < BOARD_WIDTH:
                        safe_addstr(
                            stdscr,
                            box_top + 1 + by,
                            left_x + 1 + bx * 2,
                            "[]",
                            curses.color_pair(game.current_color) | curses.A_BOLD,
                        )

    # 右侧信息面板
    panel_x = left_x + board_pixel_w + 5
    safe_addstr(stdscr, box_top + 1, panel_x, f"得分 (Score): {game.score}", curses.A_BOLD)
    safe_addstr(stdscr, box_top + 3, panel_x, f"消行 (Lines): {game.lines}")
    safe_addstr(stdscr, box_top + 5, panel_x, f"等级 (Level): {game.level}")

    # 下一个方块预览
    safe_addstr(stdscr, box_top + 8, panel_x, "下一个 (Next):", curses.A_BOLD)
    next_info = SHAPES[game.next_type]
    next_matrix = next_info["blocks"]
    next_color = next_info["color"]
    for r, row in enumerate(next_matrix):
        for c, val in enumerate(row):
            if val:
                safe_addstr(
                    stdscr,
                    box_top + 10 + r,
                    panel_x + c * 2,
                    "[]",
                    curses.color_pair(next_color) | curses.A_BOLD,
                )

    # 操作说明
    help_y = box_top + 14
    safe_addstr(stdscr, help_y, panel_x, "操作按键:", curses.A_BOLD)
    safe_addstr(stdscr, help_y + 1, panel_x, "← / → 或 A / D : 左右移动")
    safe_addstr(stdscr, help_y + 2, panel_x, "↑ 或 W         : 旋转方块")
    safe_addstr(stdscr, help_y + 3, panel_x, "↓ 或 S         : 加速下落")
    safe_addstr(stdscr, help_y + 4, panel_x, "空格 (Space)   : 直接落底")
    safe_addstr(stdscr, help_y + 5, panel_x, "P : 暂停/继续  R : 重开")
    safe_addstr(stdscr, help_y + 6, panel_x, "Q : 退出游戏")

    # 暂停或游戏结束浮层提示
    center_y = box_top + BOARD_HEIGHT // 2
    if game.paused and not game.game_over:
        safe_addstr(stdscr, center_y, left_x + 5, "=== 已暂停 (PAUSED) ===", curses.A_REVERSE | curses.A_BOLD)
    elif game.game_over:
        safe_addstr(stdscr, center_y - 1, left_x + 3, "=== 游戏结束 GAME OVER ===", curses.A_REVERSE | curses.A_BOLD)
        safe_addstr(stdscr, center_y + 1, left_x + 3, "按 R 重新开始 / 按 Q 退出", curses.A_BOLD)

    stdscr.refresh()


def main(stdscr):
    try:
        curses.curs_set(0)
    except curses.error:
        pass
    stdscr.nodelay(True)
    stdscr.keypad(True)
    init_colors()

    game = TetrisGame()
    last_drop_time = time.monotonic()

    while True:
        key = stdscr.getch()
        if key != -1:
            if key in (ord("q"), ord("Q")):
                break
            elif key in (ord("r"), ord("R")):
                game.reset()
                last_drop_time = time.monotonic()
            elif key in (ord("p"), ord("P")):
                if not game.game_over:
                    game.paused = not game.paused
                    last_drop_time = time.monotonic()
            elif not game.paused and not game.game_over:
                if key in (curses.KEY_LEFT, ord("a"), ord("A")):
                    game.move(-1, 0)
                elif key in (curses.KEY_RIGHT, ord("d"), ord("D")):
                    game.move(1, 0)
                elif key in (curses.KEY_DOWN, ord("s"), ord("S")):
                    if game.move(0, 1):
                        game.score += 1
                        last_drop_time = time.monotonic()
                elif key in (curses.KEY_UP, ord("w"), ord("W")):
                    game.rotate()
                elif key == ord(" "):
                    game.hard_drop()
                    last_drop_time = time.monotonic()

        now = time.monotonic()
        if not game.paused and not game.game_over:
            if now - last_drop_time >= game.drop_interval:
                game.step()
                last_drop_time = now

        draw_game(stdscr, game)
        time.sleep(0.016)  # ~60 FPS 刷新率，低 CPU 占用


if __name__ == "__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
