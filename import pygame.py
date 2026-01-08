import pygame
import copy
import sys
import os

pygame.init()

# Konstanta Ukuran
WIDTH, HEIGHT = 900, 650
BOARD_SIZE = 400
SQUARE_SIZE = BOARD_SIZE // 8
BOARD_OFFSET = (50, 120)
SIDEBAR_X = 500
SIDEBAR_WIDTH = 300

# Warna
BG_GRADIENT_DARK = (44, 62, 80)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (255, 255, 0, 120)
CAPTURE = (255, 0, 0, 120)
SIDEBAR_BG = (0, 0, 0, 180)
BUTTON_BG = (255, 255, 255, 40)
BUTTON_HOVER = (255, 255, 255, 100)
TEXT_COLOR = (236, 240, 241)
TURN_WHITE_BG = (255, 255, 255, 50)
TURN_BLACK_BG = (0, 0, 0, 150)
CHECK_BG = (255, 165, 0, 50)
CHECKMATE_BG = (255, 0, 0, 50)
STALEMATE_BG = (128, 128, 128, 50)

# Font
FONT_TITLE = pygame.font.Font(None, 56)
FONT_MED = pygame.font.Font(None, 36)
FONT_SMALL = pygame.font.Font(None, 28)
FONT_TINY = pygame.font.Font(None, 24)

class ChessGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("♔ Chess - Dengan Gambar PNG")
        self.clock = pygame.time.Clock()

        # Load gambar bidak
        self.pieces_images = self.load_piece_images()

        self.board = self.init_board()
        self.turn = 'white'
        self.selected = None
        self.possible_moves = []
        self.history = []
        self.states = []  # Untuk undo
        self.game_state = 'playing'

        self.button_new = pygame.Rect(SIDEBAR_X + 50, HEIGHT - 150, 200, 50)
        self.button_undo = pygame.Rect(SIDEBAR_X + 50, HEIGHT - 90, 200, 50)

    def load_piece_images(self):
        pieces = {}
        names = {
            'pawn': 'p', 'rook': 'r', 'knight': 'n',
            'bishop': 'b', 'queen': 'q', 'king': 'k'
        }
        colors = {'white': 'w', 'black': 'b'}

        base_path = os.path.dirname(__file__)  # Folder script

        for color_name, color_code in colors.items():
            for piece_name, code in names.items():
                filename = f"{color_code}_{piece_name}.png"
                filepath = os.path.join(base_path, filename)
                if os.path.exists(filepath):
                    img = pygame.image.load(filepath).convert_alpha()
                    # Scale ke ukuran kotak
                    img = pygame.transform.smoothscale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                    pieces[f"{color_name}_{piece_name}"] = img
                else:
                    print(f"Warning: Gambar tidak ditemukan: {filename}")
                    # Fallback ke kotak warna jika gambar hilang
                    fallback = pygame.Surface((SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                    fallback.fill((255, 0, 0) if color_name == 'black' else (255, 255, 255))
                    pieces[f"{color_name}_{piece_name}"] = fallback

        return pieces

    def init_board(self):
        board = [[None] * 8 for _ in range(8)]
        for c in range(8):
            board[1][c] = {'type': 'pawn', 'color': 'black'}
            board[6][c] = {'type': 'pawn', 'color': 'white'}
        order = ['rook', 'knight', 'bishop', 'queen', 'king', 'bishop', 'knight', 'rook']
        for c in range(8):
            board[0][c] = {'type': order[c], 'color': 'black'}
            board[7][c] = {'type': order[c], 'color': 'white'}
        return board

    def get_piece_image(self, piece):
        if not piece: return None
        key = f"{piece['color']}_{piece['type']}"
        return self.pieces_images.get(key)

    def save_state(self):
        self.states.append({
            'board': copy.deepcopy(self.board),
            'turn': self.turn,
            'history': self.history[:],
            'game_state': self.game_state
        })

    def get_moves(self, r, c):
        piece = self.board[r][c]
        if not piece or piece['color'] != self.turn: return []

        def pawn():
            moves = []
            dir = -1 if piece['color'] == 'white' else 1
            start = 6 if piece['color'] == 'white' else 1
            if 0 <= r + dir < 8 and not self.board[r + dir][c]:
                moves.append((r + dir, c))
                if r == start and not self.board[r + 2 * dir][c]:
                    moves.append((r + 2 * dir, c))
            for dc in [-1, 1]:
                nc = c + dc
                nr = r + dir
                if 0 <= nc < 8 and 0 <= nr < 8:
                    target = self.board[nr][nc]
                    if target and target['color'] != piece['color']:
                        moves.append((nr, nc))
            return moves

        def rook():
            moves = []
            for dr, dc in [(0,1),(0,-1),(1,0),(-1,0)]:
                for i in range(1,8):
                    nr, nc = r + dr*i, c + dc*i
                    if not (0 <= nr < 8 and 0 <= nc < 8): break
                    target = self.board[nr][nc]
                    if target:
                        if target['color'] != piece['color']:
                            moves.append((nr, nc))
                        break
                    moves.append((nr, nc))
            return moves

        def knight():
            deltas = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
            return [(r+dr, c+dc) for dr, dc in deltas
                    if 0 <= r+dr < 8 and 0 <= c+dc < 8
                    and (not self.board[r+dr][c+dc] or self.board[r+dr][c+dc]['color'] != piece['color'])]

        def bishop():
            moves = []
            for dr, dc in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                for i in range(1,8):
                    nr, nc = r + dr*i, c + dc*i
                    if not (0 <= nr < 8 and 0 <= nc < 8): break
                    target = self.board[nr][nc]
                    if target:
                        if target['color'] != piece['color']:
                            moves.append((nr, nc))
                        break
                    moves.append((nr, nc))
            return moves

        def queen(): return rook() + bishop()
        def king():
            deltas = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            return [(r+dr, c+dc) for dr, dc in deltas
                    if 0 <= r+dr < 8 and 0 <= c+dc < 8
                    and (not self.board[r+dr][c+dc] or self.board[r+dr][c+dc]['color'] != piece['color'])]

        funcs = {'pawn': pawn, 'rook': rook, 'knight': knight, 'bishop': bishop, 'queen': queen, 'king': king}
        raw_moves = funcs[piece['type']]()
        return [m for m in raw_moves if self.is_legal(r, c, m[0], m[1])]

    def is_legal(self, fr, fc, tr, tc):
        piece = self.board[fr][fc]
        target = self.board[tr][tc]
        if target and target['color'] == piece['color']: return False

        backup = self.board[tr][tc]
        self.board[tr][tc] = piece
        self.board[fr][fc] = None
        king_pos = (tr, tc) if piece['type'] == 'king' else self.find_king(piece['color'])
        safe = not self.in_check(piece['color'], king_pos[0], king_pos[1])
        self.board[fr][fc] = piece
        self.board[tr][tc] = backup
        return safe

    def find_king(self, color):
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p['type'] == 'king' and p['color'] == color:
                    return (r, c)

    def in_check(self, color, kr, kc):
        opp = 'black' if color == 'white' else 'white'
        for r in range(8):
            for c in range(8):
                p = self.board[r][c]
                if p and p['color'] == opp:
                    if (kr, kc) in self.get_moves(r, c):
                        return True
        return False

    def check_state(self):
        king_pos = self.find_king(self.turn)
        in_check = self.in_check(self.turn, king_pos[0], king_pos[1])
        has_move = any(self.get_moves(r, c) for r in range(8) for c in range(8)
                       if self.board[r][c] and self.board[r][c]['color'] == self.turn)

        if in_check and not has_move:
            self.game_state = 'checkmate'
        elif not has_move:
            self.game_state = 'stalemate'
        elif in_check:
            self.game_state = 'check'
        else:
            self.game_state = 'playing'

    def make_move(self, fr, fc, tr, tc):
        self.save_state()
        piece = self.board[fr][fc]
        captured = self.board[tr][tc]

        notation = self.notation(piece, fr, fc, tr, tc, captured)
        self.history.append(notation)

        self.board[tr][tc] = piece
        self.board[fr][fc] = None

        if piece['type'] == 'pawn' and tr in (0, 7):
            self.board[tr][tc] = {'type': 'queen', 'color': piece['color']}

        self.turn = 'black' if self.turn == 'white' else 'white'
        self.check_state()

    def notation(self, piece, fr, fc, tr, tc, captured):
        sym = {'king': 'K', 'queen': 'Q', 'rook': 'R', 'bishop': 'B', 'knight': 'N', 'pawn': ''}
        cols = 'abcdefgh'
        n = sym[piece['type']]
        if captured:
            if piece['type'] == 'pawn':
                n = cols[fc] + 'x'
            else:
                n += 'x'
        n += cols[tc] + str(8 - tr)
        return n

    def undo(self):
        if not self.states: return
        state = self.states.pop()
        self.board = state['board']
        self.turn = state['turn']
        self.history = state['history']
        self.game_state = state['game_state']
        self.selected = None
        self.possible_moves = []

    def reset(self):
        self.__init__()

    def handle_click(self, pos):
        x, y = pos
        if self.button_new.collidepoint(pos):
            self.reset()
        elif self.button_undo.collidepoint(pos):
            self.undo()
        elif BOARD_OFFSET[0] <= x < BOARD_OFFSET[0] + BOARD_SIZE and BOARD_OFFSET[1] <= y < BOARD_OFFSET[1] + BOARD_SIZE:
            col = (x - BOARD_OFFSET[0]) // SQUARE_SIZE
            row = (y - BOARD_OFFSET[1]) // SQUARE_SIZE
            if self.selected == (row, col):
                self.selected = None
                self.possible_moves = []
            elif self.selected:
                if (row, col) in self.possible_moves:
                    self.make_move(self.selected[0], self.selected[1], row, col)
                self.selected = None
                self.possible_moves = []
            else:
                if self.board[row][col] and self.board[row][col]['color'] == self.turn and self.game_state == 'playing':
                    self.selected = (row, col)
                    self.possible_moves = self.get_moves(row, col)

    def draw(self):
        self.screen.fill(BG_GRADIENT_DARK)

        title = FONT_TITLE.render("♔ Chess", True, TEXT_COLOR)
        self.screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 30))

        # Turn indicator
        turn_text = FONT_MED.render(f"Giliran: {'Putih' if self.turn == 'white' else 'Hitam'}", True, TEXT_COLOR)
        turn_rect = pygame.Rect(70, 70, 250, 50)
        pygame.draw.rect(self.screen, TURN_WHITE_BG if self.turn == 'white' else TURN_BLACK_BG, turn_rect, border_radius=20)
        self.screen.blit(turn_text, (90, 80))

        # Status
        status_text = ""
        status_color = TEXT_COLOR
        status_rect = pygame.Rect(340, 70, 220, 50)
        if self.game_state == 'check':
            status_text = "Check!"
            status_color = (255, 170, 0)
            pygame.draw.rect(self.screen, CHECK_BG, status_rect, border_radius=15)
        elif self.game_state == 'checkmate':
            winner = 'Hitam' if self.turn == 'white' else 'Putih'
            status_text = f"{winner} Menang!"
            status_color = (255, 107, 107)
            pygame.draw.rect(self.screen, CHECKMATE_BG, status_rect, border_radius=15)
        elif self.game_state == 'stalemate':
            status_text = "Stalemate!"
            status_color = (200, 200, 200)
            pygame.draw.rect(self.screen, STALEMATE_BG, status_rect, border_radius=15)

        if status_text:
            status_surf = FONT_MED.render(status_text, True, status_color)
            self.screen.blit(status_surf, (360, 80))

        # Board
        for r in range(8):
            for c in range(8):
                x = BOARD_OFFSET[0] + c * SQUARE_SIZE
                y = BOARD_OFFSET[1] + r * SQUARE_SIZE
                color = LIGHT_SQUARE if (r + c) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Highlight
                if self.selected == (r, c):
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(HIGHLIGHT)
                    self.screen.blit(s, (x, y))
                if (r, c) in self.possible_moves:
                    s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), pygame.SRCALPHA)
                    s.fill(CAPTURE if self.board[r][c] else HIGHLIGHT)
                    self.screen.blit(s, (x, y))

                # Gambar bidak PNG
                img = self.get_piece_image(self.board[r][c])
                if img:
                    img_rect = img.get_rect(center=(x + SQUARE_SIZE//2, y + SQUARE_SIZE//2))
                    self.screen.blit(img, img_rect)

        # Board border
        pygame.draw.rect(self.screen, TEXT_COLOR, (BOARD_OFFSET[0]-3, BOARD_OFFSET[1]-3, BOARD_SIZE+6, BOARD_SIZE+6), 3, border_radius=10)

        # Sidebar
        sidebar = pygame.Rect(SIDEBAR_X - 20, 100, SIDEBAR_WIDTH, HEIGHT - 200)
        pygame.draw.rect(self.screen, SIDEBAR_BG, sidebar, border_radius=15)

        hist_title = FONT_MED.render("Riwayat Gerakan", True, TEXT_COLOR)
        self.screen.blit(hist_title, (SIDEBAR_X, 120))

        for i, move in enumerate(self.history[-12:]):
            num = len(self.history) - len(self.history[-12:]) + i + 1
            text = FONT_TINY.render(f"{num}. {move}", True, (189, 195, 199))
            self.screen.blit(text, (SIDEBAR_X, 160 + i * 30))

        # Buttons
        mouse = pygame.mouse.get_pos()
        for btn, text_str in [(self.button_new, "Game Baru"), (self.button_undo, "Undo")]:
            hover = btn.collidepoint(mouse)
            pygame.draw.rect(self.screen, BUTTON_HOVER if hover else BUTTON_BG, btn, border_radius=25)
            pygame.draw.rect(self.screen, TEXT_COLOR, btn, 2, border_radius=25)
            btn_text = FONT_SMALL.render(text_str, True, TEXT_COLOR)
            self.screen.blit(btn_text, (btn.centerx - btn_text.get_width()//2, btn.centery - btn_text.get_height()//2))

        pygame.display.flip()

    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    self.handle_click(event.pos)

            self.draw()
            self.clock.tick(60)

if __name__ == "__main__":
    ChessGame().run()