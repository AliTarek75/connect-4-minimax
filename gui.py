import tkinter as tk

import algorithm
from algorithm import get_best_move
from game import Game, WIDTH, HEIGHT

BG = "#0b1020"
CARD = "#151c33"
CARD_2 = "#1d2645"
TEXT = "#e8ecff"
MUTED = "#8b95b8"
ACCENT = "#7c5cff"
ACCENT_2 = "#5b3fe0"
ERROR = "#ff5d8f"

BOARD_BG = "#1b2a6b"
HOLE = "#0b1020"
HUMAN = "#e53935"
AI = "#fdd835"
HOVER = "#2b3a85"

MAX_COLOR = "#38e1c6"
MIN_COLOR = "#ff5d8f"
LEAF_COLOR = "#ffc857"
PRUNED_COLOR = "#59628a"
LINE = "#2c3868"

FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_BIG = ("Segoe UI", 18, "bold")
FONT_XL = ("Segoe UI", 26, "bold")

CELL = 72
R = 28
NODE_R = 18
X_GAP = 54
Y_GAP = 80
PAD = 44

HUMAN_ID = 0


def fmt(v):
    if v is None:
        return "?"
    if v == float('inf'):
        return "+inf"
    if v == -float('inf'):
        return "-inf"
    return f"{v:.2f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


class GUI:
    def __init__(self, root):
        self.root = root
        root.title("Connect 4 AI")
        root.configure(bg=BG)

        self.game = Game()
        self.k = 3
        self.tree = None
        self.max_depth = 1
        self.drawn = []
        self.busy = False
        self.total_pruned = 0
        self.hover_col = None
        self.last_move = None

        self.setup = tk.Frame(root, bg=BG)
        self.main = tk.Frame(root, bg=BG)
        self.build_setup()
        self.build_main()
        self.show_setup()

    def build_setup(self):
        box = tk.Frame(self.setup, bg=CARD, padx=50, pady=40)
        box.pack(padx=120, pady=120)

        tk.Label(box, text="Connect 4", bg=CARD, fg=TEXT, font=FONT_XL).pack()
        tk.Label(box, text="Minimax with alpha-beta pruning", bg=CARD, fg=MUTED,
                 font=FONT).pack(pady=(2, 24))

        tk.Label(box, text="Search depth (K)", bg=CARD, fg=MUTED, font=FONT).pack()
        self.k_var = tk.StringVar(value="3")
        self.k_entry = tk.Spinbox(box, from_=1, to=1000000, width=6, textvariable=self.k_var,
                                  bg=CARD_2, fg=TEXT, buttonbackground=CARD_2, relief="flat",
                                  insertbackground=TEXT, font=FONT_BIG, justify="center")
        self.k_entry.pack(pady=(6, 4))
        self.k_entry.bind("<Return>", lambda e: self.start_game())

        self.k_error = tk.Label(box, text="", bg=CARD, fg=ERROR, font=FONT)
        self.k_error.pack(pady=(0, 14))

        self.button(box, "Start Game", self.start_game).pack()

    def show_setup(self):
        self.main.pack_forget()
        self.k_error.config(text="")
        self.setup.pack(expand=True)
        self.k_entry.focus_set()

    def start_game(self):
        try:
            k = int(self.k_var.get())
            if k < 1:
                raise ValueError
        except ValueError:
            self.k_error.config(text="Enter a whole number, 1 or more")
            return
        self.k = k
        self.setup.pack_forget()
        self.main.pack(fill="both", expand=True)
        self.k_label.config(text=f"K = {k}")
        self.reset_game()

    def button(self, parent, text, cmd):
        return tk.Button(parent, text=text, command=cmd, bg=ACCENT, fg="white",
                         activebackground=ACCENT_2, activeforeground="white",
                         relief="flat", bd=0, padx=14, pady=6, font=FONT_B, cursor="hand2")

    def build_main(self):
        left = tk.Frame(self.main, bg=BG)
        left.pack(side="left", padx=16, pady=16, anchor="n")
        right = tk.Frame(self.main, bg=BG)
        right.pack(side="left", fill="both", expand=True, padx=(0, 16), pady=16)

        ctrl = tk.Frame(left, bg=CARD, padx=12, pady=10)
        ctrl.pack(fill="x")
        self.k_label = tk.Label(ctrl, text="K = 3", bg=CARD, fg=TEXT, font=FONT_B)
        self.k_label.pack(side="left", padx=(0, 16))

        tk.Label(ctrl, text="Show depth", bg=CARD, fg=MUTED, font=FONT).pack(side="left")
        self.show_var = tk.IntVar(value=1)
        sp = tk.Spinbox(ctrl, from_=0, to=99, width=3, textvariable=self.show_var,
                        command=self.apply_depth, bg=CARD_2, fg=TEXT, buttonbackground=CARD_2,
                        relief="flat", insertbackground=TEXT, font=FONT_B, justify="center")
        sp.pack(side="left", padx=(6, 0))
        sp.bind("<Return>", lambda e: self.apply_depth())

        self.button(ctrl, "New Game", self.show_setup).pack(side="right")

        score = tk.Frame(left, bg=BG)
        score.pack(fill="x", pady=(10, 0))
        self.you_var = tk.StringVar(value="0")
        self.ai_var = tk.StringVar(value="0")
        for title, var, color, side in (("YOU", self.you_var, HUMAN, "left"),
                                         ("AI", self.ai_var, AI, "right")):
            c = tk.Frame(score, bg=CARD, padx=16, pady=8)
            c.pack(side=side, expand=True, fill="x",
                   padx=(0, 5) if side == "left" else (5, 0))
            tk.Label(c, text=title, bg=CARD, fg=color, font=FONT_B).pack()
            tk.Label(c, textvariable=var, bg=CARD, fg=TEXT, font=FONT_XL).pack()
            tk.Label(c, text="connected fours", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8)).pack()

        self.status = tk.Label(left, text="", bg=BG, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.status.pack(pady=(10, 6))

        self.board = tk.Canvas(left, width=WIDTH * CELL + 24, height=HEIGHT * CELL + 24,
                               bg=BG, highlightthickness=0)
        self.board.pack()
        self.board.bind("<Button-1>", self.on_board_click)
        self.board.bind("<Motion>", self.on_board_motion)
        self.board.bind("<Leave>", self.on_board_leave)

        grid = tk.Frame(right, bg=BG)
        grid.pack(fill="x")
        self.stat_vars = {}
        names = ["Search time", "Nodes", "Pruned (move)",
                 "Pruned (total)", "Nodes (total)", "Moves played"]
        for i, name in enumerate(names):
            t = tk.Frame(grid, bg=CARD, padx=12, pady=8)
            t.grid(row=i // 3, column=i % 3, sticky="nsew", padx=4, pady=4)
            grid.columnconfigure(i % 3, weight=1)
            tk.Label(t, text=name, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack(anchor="w")
            var = tk.StringVar(value="-")
            tk.Label(t, textvariable=var, bg=CARD, fg=TEXT, font=FONT_BIG).pack(anchor="w")
            self.stat_vars[name] = var

        legend = tk.Frame(right, bg=BG)
        legend.pack(fill="x", pady=(10, 6))
        for text, color in (("MAX", MAX_COLOR), ("MIN", MIN_COLOR),
                            ("Leaf", LEAF_COLOR), ("Cutoff", PRUNED_COLOR)):
            dot = tk.Canvas(legend, width=14, height=14, bg=BG, highlightthickness=0)
            dot.create_oval(1, 1, 13, 13, fill=color, outline="")
            dot.pack(side="left")
            tk.Label(legend, text=text, bg=BG, fg=MUTED, font=FONT).pack(side="left",
                                                                         padx=(4, 14))

        box = tk.Frame(right, bg=BG)
        box.pack(fill="both", expand=True)
        hbar = tk.Scrollbar(box, orient="horizontal")
        vbar = tk.Scrollbar(box, orient="vertical")
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(box, bg=CARD, width=640, height=480, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(fill="both", expand=True)
        hbar.config(command=self.canvas.xview)
        vbar.config(command=self.canvas.yview)

        self.canvas.bind("<Button-1>", self.on_tree_click)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda e: self.tip.place_forget())
        self.canvas.bind("<MouseWheel>",
                         lambda e: self.canvas.yview_scroll(-(e.delta // 120), "units"))

        self.tip = tk.Label(self.canvas, bg="#000000", fg=TEXT, font=("Consolas", 9),
                            justify="left", padx=8, pady=6)

    def reset_game(self):
        self.game = Game()
        self.tree = None
        self.drawn = []
        self.busy = False
        self.total_pruned = 0
        self.total_nodes = 0
        self.last_move = None
        self.hover_col = None
        for var in self.stat_vars.values():
            var.set("-")
        self.canvas.delete("all")
        self.tip.place_forget()
        self.update_scores()
        self.draw_board()
        self.update_moves_played()
        self.set_status("Your turn", HUMAN)

    def set_status(self, text, color=TEXT):
        self.status.config(text=text, fg=color)

    def piece_color(self, player):
        return HUMAN if player == HUMAN_ID else AI

    def update_scores(self):
        self.you_var.set(str(self.game.connected_four[0]))
        self.ai_var.set(str(self.game.connected_four[1]))

    def update_moves_played(self):
        self.stat_vars["Moves played"].set(str(self.game.moves_played))

    def on_board_click(self, event):
        if self.busy or self.game.check_finished() or self.game.turn != HUMAN_ID:
            return
        col = (event.x - 12) // CELL
        if col < 0 or col >= WIDTH:
            return
        try:
            self.game.play_move(col)
        except ValueError:
            return

        self.last_move = (col, len(self.game.game[col]) - 1)
        self.update_scores()
        self.draw_board()
        self.update_moves_played()

        if self.game.check_finished():
            self.show_result()
            return

        self.busy = True
        self.set_status("AI thinking...", AI)
        self.root.after(60, self.ai_turn)

    def ai_turn(self):
        val, col, search_time = get_best_move(self.game, self.k)
        print(f"[AI] k={self.k} -> col={col} value={val} ({search_time:.3f}s)")

        if col is None or col < 0:
            legal = self.game.get_legal_moves()
            col = legal[0] if legal else None
        if col is not None:
            self.game.play_move(col)
            self.last_move = (col, len(self.game.game[col]) - 1)

        records = [dict(n) for n in algorithm.nodes]
        pruned_now = sum(1 for n in records if n['pruned'])
        self.total_pruned += pruned_now
        self.stat_vars["Search time"].set(f"{search_time:.3f} s")
        self.stat_vars["Nodes"].set(str(len(records)))
        self.stat_vars["Pruned (move)"].set(str(pruned_now))
        self.stat_vars["Pruned (total)"].set(str(self.total_pruned))
        self.total_nodes += len(records)
        self.stat_vars["Nodes (total)"].set(str(self.total_nodes))

        self.update_scores()
        self.draw_board()
        self.update_moves_played()
        self.build_tree(records, val)

        if self.game.check_finished():
            self.show_result()
        else:
            self.set_status("Your turn", HUMAN)

        self.root.after(250, self.unlock)

    def unlock(self):
        self.busy = False

    def show_result(self):
        mine = self.game.connected_four[0]
        theirs = self.game.connected_four[1]
        if theirs > mine:
            self.set_status(f"AI wins  {theirs} - {mine}", AI)
        elif mine > theirs:
            self.set_status(f"You win  {mine} - {theirs}", HUMAN)
        else:
            self.set_status(f"Draw  {mine} - {theirs}", TEXT)

    def on_board_motion(self, event):
        col = (event.x - 12) // CELL
        col = col if 0 <= col < WIDTH else None
        if col != self.hover_col:
            self.hover_col = col
            self.draw_board()

    def on_board_leave(self, event):
        self.hover_col = None
        self.draw_board()

    def draw_board(self):
        b = self.board
        b.delete("all")
        w = WIDTH * CELL + 24
        h = HEIGHT * CELL + 24
        self.round_rect(b, 2, 2, w - 2, h - 2, 22, BOARD_BG)

        if self.hover_col is not None and not self.busy and not self.game.check_finished():
            x0 = 12 + self.hover_col * CELL
            self.round_rect(b, x0 + 3, 8, x0 + CELL - 3, h - 8, 18, HOVER)

        for col in range(WIDTH):
            for row in range(HEIGHT):
                x = 12 + col * CELL + CELL // 2
                y = 12 + (HEIGHT - 1 - row) * CELL + CELL // 2
                if row < len(self.game.game[col]):
                    color = self.piece_color(self.game.game[col][row])
                else:
                    color = HOLE
                b.create_oval(x - R, y - R, x + R, y + R, fill=color, outline="")
                if self.last_move == (col, row):
                    b.create_oval(x - R - 3, y - R - 3, x + R + 3, y + R + 3,
                                  outline="white", width=3)

    def round_rect(self, canvas, x1, y1, x2, y2, r, fill):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        canvas.create_polygon(pts, smooth=True, fill=fill, outline="")

    def build_tree(self, flat, root_value):
        """Records arrive children-first. pending[d] = nodes of depth d waiting for
        a parent; when a node of depth d arrives, pending[d+1] are its children."""
        pending = {}
        deepest = 1
        for rec in flat:
            node = dict(rec)
            node['open'] = False
            node['children'] = pending.pop(rec['depth'] + 1, [])
            pending.setdefault(rec['depth'], []).append(node)
            deepest = max(deepest, rec['depth'])

        self.tree = {'depth': 0, 'move': None, 'value': root_value,
                     'alpha': -float('inf'), 'beta': float('inf'),
                     'is_max': True, 'is_leaf': False, 'pruned': False,
                     'open': False, 'children': pending.get(1, [])}
        self.max_depth = deepest
        self.apply_depth()

    def apply_depth(self):
        if self.tree is None:
            return
        try:
            limit = int(self.show_var.get())
        except (tk.TclError, ValueError):
            limit = 1
        self.set_open(self.tree, limit)
        self.draw_tree()

    def set_open(self, node, depth_limit):
        node['open'] = node['depth'] < depth_limit
        for child in node['children']:
            self.set_open(child, depth_limit)

    def layout(self, node, counter):
        node['y'] = node['depth']
        if node['open'] and node['children']:
            for child in node['children']:
                self.layout(child, counter)
            node['x'] = (node['children'][0]['x'] + node['children'][-1]['x']) / 2
        else:
            node['x'] = counter[0]
            counter[0] += 1

    def draw_tree(self):
        self.canvas.delete("all")
        self.drawn = []
        if self.tree is None:
            return
        counter = [0]
        self.layout(self.tree, counter)
        width = max(counter[0] * X_GAP + 2 * PAD, 640)
        height = max((self.max_depth + 1) * Y_GAP + 2 * PAD, 480)
        self.canvas.config(scrollregion=(0, 0, width, height))
        self.draw_node(self.tree)

    def draw_node(self, node):
        cx = node['x'] * X_GAP + PAD
        cy = node['y'] * Y_GAP + PAD

        if node['open']:
            for child in node['children']:
                ccx = child['x'] * X_GAP + PAD
                ccy = child['y'] * Y_GAP + PAD
                self.canvas.create_line(cx, cy, ccx, ccy, fill=LINE, width=2)
                self.draw_node(child)

        if node['pruned']:
            color = PRUNED_COLOR
        elif node['is_leaf']:
            color = LEAF_COLOR
        elif node['is_max']:
            color = MAX_COLOR
        else:
            color = MIN_COLOR

        folded = len(node['children']) > 0 and not node['open']
        self.canvas.create_oval(cx - NODE_R, cy - NODE_R, cx + NODE_R, cy + NODE_R,
                                fill=color, outline="white" if folded else CARD,
                                width=3 if folded else 2)
        label = "R" if node['move'] is None else str(node['move'])
        self.canvas.create_text(cx, cy, text=label, fill="#0b1020",
                                font=("Segoe UI", 10, "bold"))
        self.canvas.create_text(cx, cy + NODE_R + 10, text=fmt(node['value']),
                                fill=MUTED, font=("Segoe UI", 8))
        self.drawn.append((cx, cy, node))

    def node_at(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for cx, cy, node in self.drawn:
            if (x - cx) ** 2 + (y - cy) ** 2 <= NODE_R ** 2:
                return node
        return None

    def on_tree_click(self, event):
        node = self.node_at(event)
        if node is not None and node['children']:
            node['open'] = not node['open']
            self.draw_tree()

    def on_hover(self, event):
        node = self.node_at(event)
        if node is None:
            self.tip.place_forget()
            return
        text = (f"type     {'MAX' if node['is_max'] else 'MIN'}\n"
                f"depth    {node['depth']}\n"
                f"move     {node['move']}\n"
                f"value    {fmt(node['value'])}\n"
                f"alpha    {fmt(node['alpha'])}\n"
                f"beta     {fmt(node['beta'])}\n"
                f"children {len(node['children'])}\n"
                f"leaf     {node['is_leaf']}\n"
                f"pruned   {node['pruned']}")
        self.tip.config(text=text)
        self.tip.place(x=event.x + 16, y=event.y + 16)


if __name__ == "__main__":
    root = tk.Tk()
    GUI(root)
    root.mainloop()