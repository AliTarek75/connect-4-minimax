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
RED = "#e53935"
YELLOW = "#fdd835"
HOVER = "#2b3a85"

MAX_COLOR = "#38e1c6"
MIN_COLOR = "#ff5d8f"
LEAF_COLOR = "#ffc857"
PRUNED_COLOR = "#59628a"
LINE = "#2c3868"
CHOSEN_COLOR = "#ffe600"

FONT = ("Segoe UI", 10)
FONT_B = ("Segoe UI", 10, "bold")
FONT_BIG = ("Segoe UI", 18, "bold")
FONT_XL = ("Segoe UI", 26, "bold")

CELL = 72
R = 28
NODE_R = 18
COL_GAP = 110   # horizontal distance between depth levels
ROW_GAP = 56    # vertical distance between leaves
V_COL_GAP = 80  # top-down mode: distance between depth levels
V_ROW_GAP = 54  # top-down mode: distance between leaves
PAD = 44
MIN_ZOOM = 0.002   # how far you can zoom out

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
        self.color_choice = "red"
        self.human_id = 0
        self.ai_id = 1
        self.human_color = RED
        self.ai_color = YELLOW
        self.tree = None
        self.max_depth = 1
        self.drawn = []
        self.busy = False
        self.total_pruned = 0
        self.total_nodes = 0
        self.hover_col = None
        self.last_move = None
        self.root_evals = {}
        self.best_col = None
        self.zoom = 1.0
        self.view = (0, 0, 0, 0)
        self._draw_job = None
        self._press = None
        self._dragged = False
        self.path = []
        self.path_idx = 0
        self.top_down = False   # False: root left, depth -> right. True: root top, depth -> down

        self.setup = tk.Frame(root, bg=BG)
        self.main = tk.Frame(root, bg=BG)
        self.build_setup()
        self.build_main()
        self.show_setup()

    def build_setup(self):
        box = tk.Frame(self.setup, bg=CARD, padx=50, pady=36)
        box.pack(padx=120, pady=100)

        tk.Label(box, text="Connect 4", bg=CARD, fg=TEXT, font=FONT_XL).pack()
        tk.Label(box, text="Minimax with alpha-beta pruning", bg=CARD, fg=MUTED,
                 font=FONT).pack(pady=(2, 22))

        tk.Label(box, text="Search depth (K)", bg=CARD, fg=MUTED, font=FONT).pack()
        self.k_var = tk.StringVar(value="3")
        self.k_entry = tk.Spinbox(box, from_=1, to=1000000, width=6, textvariable=self.k_var,
                                  bg=CARD_2, fg=TEXT, buttonbackground=CARD_2, relief="flat",
                                  insertbackground=TEXT, font=FONT_BIG, justify="center")
        self.k_entry.pack(pady=(6, 4))
        self.k_entry.bind("<Return>", lambda e: self.start_game())

        self.k_error = tk.Label(box, text="", bg=CARD, fg=ERROR, font=FONT)
        self.k_error.pack(pady=(0, 10))

        tk.Label(box, text="Your color", bg=CARD, fg=MUTED, font=FONT).pack()
        row = tk.Frame(box, bg=CARD)
        row.pack(pady=(6, 18))
        self.color_cv = {}
        for name, hexcol, sub in (("red", RED, "You move first"),
                                  ("yellow", YELLOW, "AI moves first")):
            f = tk.Frame(row, bg=CARD, padx=12)
            f.pack(side="left")
            cv = tk.Canvas(f, width=84, height=84, bg=CARD, highlightthickness=0,
                           cursor="hand2")
            cv.pack()
            cv.bind("<Button-1>", lambda e, n=name: self.pick_color(n))
            tk.Label(f, text=sub, bg=CARD, fg=MUTED, font=("Segoe UI", 9)).pack()
            self.color_cv[name] = (cv, hexcol)
        self.pick_color("red")

        self.button(box, "Start Game", self.start_game).pack()

    def pick_color(self, name):
        self.color_choice = name
        for n, (cv, hexcol) in self.color_cv.items():
            cv.delete("all")
            if n == name:
                cv.create_oval(4, 4, 80, 80, outline="white", width=3)
            cv.create_oval(14, 14, 70, 70, fill=hexcol, outline="")

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

        if self.color_choice == "red":
            self.human_id, self.ai_id = 0, 1
            self.human_color, self.ai_color = RED, YELLOW
        else:
            self.human_id, self.ai_id = 1, 0
            self.human_color, self.ai_color = YELLOW, RED
        self.you_title.config(fg=self.human_color)
        self.ai_title.config(fg=self.ai_color)

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

        self.button(ctrl, "New Game", self.show_setup).pack(side="right")

        score = tk.Frame(left, bg=BG)
        score.pack(fill="x", pady=(10, 0))
        self.you_var = tk.StringVar(value="0")
        self.ai_var = tk.StringVar(value="0")
        titles = {}
        for key, title, var, side in (("you", "YOU", self.you_var, "left"),
                                      ("ai", "AI", self.ai_var, "right")):
            c = tk.Frame(score, bg=CARD, padx=16, pady=8)
            c.pack(side=side, expand=True, fill="x",
                   padx=(0, 5) if side == "left" else (5, 0))
            titles[key] = tk.Label(c, text=title, bg=CARD, fg=TEXT, font=FONT_B)
            titles[key].pack()
            tk.Label(c, textvariable=var, bg=CARD, fg=TEXT, font=FONT_XL).pack()
            tk.Label(c, text="connected fours", bg=CARD, fg=MUTED,
                     font=("Segoe UI", 8)).pack()
        self.you_title = titles["you"]
        self.ai_title = titles["ai"]

        self.status = tk.Label(left, text="", bg=BG, fg=TEXT, font=("Segoe UI", 12, "bold"))
        self.status.pack(pady=(10, 6))

        self.board = tk.Canvas(left, width=WIDTH * CELL + 24, height=HEIGHT * CELL + 24,
                               bg=BG, highlightthickness=0)
        self.board.pack()
        self.board.bind("<Button-1>", self.on_board_click)
        self.board.bind("<Motion>", self.on_board_motion)
        self.board.bind("<Leave>", self.on_board_leave)

        self.eval_canvas = tk.Canvas(left, width=WIDTH * CELL + 24, height=40,
                                     bg=BG, highlightthickness=0)
        self.eval_canvas.pack(pady=(6, 0))

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

        depth_card = tk.Frame(right, bg=CARD, padx=12, pady=8)
        depth_card.pack(fill="x", pady=(0, 6))
        top = tk.Frame(depth_card, bg=CARD)
        top.pack(fill="x")
        self.show_var = tk.IntVar(value=1)
        self.depth_label = tk.Label(top, text="Levels shown: -", bg=CARD, fg=TEXT, font=FONT_B)
        self.depth_label.pack(side="left")
        self.button(top, "Show more", lambda: self.change_depth(1)).pack(side="right")
        self.button(top, "Show less", lambda: self.change_depth(-1)).pack(side="right", padx=(0, 8))
        self.button(top, "100%", self.fit_view).pack(side="right", padx=(0, 8))
        self.orient_btn = self.button(top, "Top-down ↓", self.toggle_orientation)
        self.orient_btn.pack(side="right", padx=(0, 8))
        self.button(top, "−", lambda: self.zoom_by(0.8)).pack(side="right", padx=(0, 8))
        self.button(top, "+", lambda: self.zoom_by(1.25)).pack(side="right", padx=(0, 8))
        nav = tk.Frame(depth_card, bg=CARD)
        nav.pack(fill="x", pady=(8, 0))
        self.button(nav, "Root", self.go_root).pack(side="left")
        self.button(nav, "Next on path ▶", self.next_on_path).pack(side="left", padx=(8, 0))
        self.path_label = tk.Label(nav, text="", bg=CARD, fg=MUTED, font=FONT)
        self.path_label.pack(side="left", padx=10)
        tk.Label(depth_card, bg=CARD, fg=MUTED, font=("Segoe UI", 9), justify="left",
                 anchor="w", wraplength=620,
                 text="Only the first level is shown. Press \"Show more\" to open deeper levels "
                      "of the search tree, or click any circle to open / fold it.").pack(fill="x", pady=(6, 0))

        box = tk.Frame(right, bg=BG)
        box.pack(fill="both", expand=True)
        hbar = tk.Scrollbar(box, orient="horizontal")
        vbar = tk.Scrollbar(box, orient="vertical")
        hbar.pack(side="bottom", fill="x")
        vbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(box, bg=CARD, width=640, height=480, highlightthickness=0,
                                xscrollcommand=hbar.set, yscrollcommand=vbar.set)
        self.canvas.pack(fill="both", expand=True)
        hbar.config(command=self.xscroll)
        vbar.config(command=self.yscroll)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Motion>", self.on_hover)
        self.canvas.bind("<Leave>", lambda e: self.tip.place_forget())
        self.canvas.bind("<MouseWheel>", self.on_wheel)
        self.canvas.bind("<Shift-MouseWheel>", self.on_hwheel)
        self.canvas.bind("<Control-MouseWheel>", self.on_zoom_wheel)
        self.canvas.bind("<Configure>", lambda e: self.schedule_draw())

        self.tip = tk.Label(self.canvas, bg="#000000", fg=TEXT, font=("Consolas", 9),
                            justify="left", padx=8, pady=6)

    def reset_game(self):
        self.game = Game()
        self.game.ai = self.ai_id
        self.tree = None
        self.tree = None
        self.drawn = []
        self.busy = False
        self.total_pruned = 0
        self.total_nodes = 0
        self.last_move = None
        self.hover_col = None
        self.root_evals = {}
        self.best_col = None
        for var in self.stat_vars.values():
            var.set("-")
        self.canvas.delete("all")
        self.path = []
        self.path_idx = 0
        self.path_label.config(text="")
        self.depth_label.config(text="Levels shown: -")
        self.tip.place_forget()
        self.update_scores()
        self.draw_board()
        self.draw_eval_strip()
        self.update_moves_played()

        if self.game.turn != self.human_id:
            self.busy = True
            self.set_status("AI thinking...", self.ai_color)
            self.root.after(60, self.ai_turn)
        else:
            self.set_status("Your turn", self.human_color)

    def set_status(self, text, color=TEXT):
        self.status.config(text=text, fg=color)

    def piece_color(self, player):
        return RED if player == 0 else YELLOW

    def update_scores(self):
        self.you_var.set(str(self.game.connected_four[self.human_id]))
        self.ai_var.set(str(self.game.connected_four[self.ai_id]))

    def update_moves_played(self):
        self.stat_vars["Moves played"].set(str(self.game.moves_played))

    def on_board_click(self, event):
        if self.busy or self.game.check_finished() or self.game.turn != self.human_id:
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
        self.set_status("AI thinking...", self.ai_color)
        self.root.after(60, self.ai_turn)

    def ai_turn(self):
        if self.game.check_finished():
            self.busy = False
            self.show_result()
            return

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
        self.total_nodes += len(records)
        self.stat_vars["Search time"].set(f"{search_time:.3f} s")
        self.stat_vars["Nodes"].set(str(len(records)))
        self.stat_vars["Pruned (move)"].set(str(pruned_now))
        self.stat_vars["Pruned (total)"].set(str(self.total_pruned))
        self.stat_vars["Nodes (total)"].set(str(self.total_nodes))

        self.root_evals = {r['move']: r['value'] for r in records if r['depth'] == 1}
        self.best_col = col
        self.draw_eval_strip()

        self.update_scores()
        self.draw_board()
        self.update_moves_played()
        self.build_tree(records, val)

        if self.game.check_finished():
            self.show_result()
        else:
            self.set_status("Your turn", self.human_color)

        self.root.after(250, self.unlock)

    def unlock(self):
        self.busy = False

    def show_result(self):
        mine = self.game.connected_four[self.human_id]
        theirs = self.game.connected_four[self.ai_id]
        if theirs > mine:
            self.set_status(f"AI wins  {theirs} - {mine}", self.ai_color)
        elif mine > theirs:
            self.set_status(f"You win  {mine} - {theirs}", self.human_color)
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

        can_play = (not self.busy and not self.game.check_finished()
                    and self.game.turn == self.human_id)
        if self.hover_col is not None and can_play:
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

    def draw_eval_strip(self):
        c = self.eval_canvas
        c.delete("all")
        for col in range(WIDTH):
            x0 = 12 + col * CELL
            chosen = (col == self.best_col)
            self.round_rect(c, x0 + 3, 2, x0 + CELL - 3, 36, 10,
                            ACCENT if chosen else CARD_2)
            if col in self.root_evals:
                text = fmt(self.root_evals[col])
                color = "white" if chosen else TEXT
            else:
                text, color = "-", MUTED
            c.create_text(x0 + CELL // 2, 19, text=text, fill=color, font=FONT_B)

    def round_rect(self, canvas, x1, y1, x2, y2, r, fill):
        pts = [x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r, x2, y2 - r, x2, y2,
               x2 - r, y2, x1 + r, y2, x1, y2, x1, y2 - r, x1, y1 + r, x1, y1]
        canvas.create_polygon(pts, smooth=True, fill=fill, outline="")

    def build_tree(self, flat, root_value):
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
        self.mark_chosen(self.tree)
        self.path = [self.tree]
        while True:
            nxt = next((c for c in self.path[-1]['children'] if c.get('chosen')), None)
            if nxt is None:
                break
            self.path.append(nxt)
        self.path_idx = 0
        self.path_label.config(text=f"Path: 1 / {len(self.path)}")
        self.apply_depth()

    def change_depth(self, delta):
        try:
            cur = int(self.show_var.get())
        except (tk.TclError, ValueError):
            cur = 1
        self.show_var.set(max(0, min(self.max_depth, cur + delta)))
        self.apply_depth()

    def set_open(self, node, depth_limit):
        node['open'] = node['depth'] < depth_limit
        for child in node['children']:
            self.set_open(child, depth_limit)

    def mark_chosen(self, node):
        # follow ONLY the principal path: root -> chosen child -> its chosen child -> ...
        # chosen child = first child whose value equals the parent's value
        while node['children']:
            best = None
            for child in node['children']:
                child['chosen'] = False
                if best is None and child['value'] == node['value']:
                    best = child
            if best is None:
                break
            best['chosen'] = True
            node = best

    def apply_depth(self):
        if self.tree is None:
            return
        try:
            limit = int(self.show_var.get())
        except (tk.TclError, ValueError):
            limit = 1
        limit = max(0, min(self.max_depth, limit))
        self.show_var.set(limit)
        self.depth_label.config(text=f"Levels shown: {limit} / {self.max_depth}")
        self.set_open(self.tree, limit)
        self.relayout()
        self.draw_tree()

    def layout(self, node, counter):
        # horizontal tree: depth goes left->right, leaves are stacked top->bottom
        node['col'] = node['depth']
        if node['open'] and node['children']:
            for child in node['children']:
                self.layout(child, counter)
            node['row'] = (node['children'][0]['row'] + node['children'][-1]['row']) / 2
            node['r0'] = node['children'][0]['r0']      # subtree vertical extent (for culling)
            node['r1'] = node['children'][-1]['r1']
        else:
            node['row'] = node['r0'] = node['r1'] = counter[0]
            counter[0] += 1

    def relayout(self):
        if self.tree is None:
            return
        counter = [0]
        self.layout(self.tree, counter)
        depth_n, leaf_n = self.max_depth + 1, max(counter[0], 1)
        if self.top_down:
            self.units_w, self.units_h = leaf_n * V_ROW_GAP, depth_n * V_COL_GAP
        else:
            self.units_w, self.units_h = depth_n * COL_GAP, leaf_n * ROW_GAP
        self.world_w = max(self.units_w * self.zoom + 2 * PAD, 640)
        self.world_h = max(self.units_h * self.zoom + 2 * PAD, 480)
        self.canvas.config(scrollregion=(0, 0, self.world_w, self.world_h))

    def schedule_draw(self):
        if self._draw_job is None:
            self._draw_job = self.root.after(16, self._do_draw)

    def _do_draw(self):
        self._draw_job = None
        self.draw_tree()

    def draw_tree(self):
        self.canvas.delete("all")
        self.drawn = []
        if self.tree is None:
            return
        m = NODE_R * self.zoom + 20
        c = self.canvas
        self.view = (c.canvasx(0) - m, c.canvasy(0) - m,
                     c.canvasx(c.winfo_width()) + m, c.canvasy(c.winfo_height()) + m)
        self.draw_node(self.tree)

    def node_xy(self, node):
        z = self.zoom
        if self.top_down:
            return node['row'] * V_ROW_GAP * z + PAD, node['col'] * V_COL_GAP * z + PAD
        return node['col'] * COL_GAP * z + PAD, node['row'] * ROW_GAP * z + PAD

    def draw_node(self, node):
        z = self.zoom
        vx0, vy0, vx1, vy1 = self.view
        cx, cy = self.node_xy(node)

        # cull the whole subtree if it is past the view in depth direction
        # or outside the view along the leaf axis
        g = (V_ROW_GAP if self.top_down else ROW_GAP) * z
        lo, hi = node['r0'] * g + PAD, node['r1'] * g + PAD
        if self.top_down:
            if cy > vy1 or lo > vx1 or hi < vx0:
                return
        else:
            if cx > vx1 or lo > vy1 or hi < vy0:
                return

        if node['open']:
            for child in node['children']:
                ccx, ccy = self.node_xy(child)
                if (max(cx, ccx) >= vx0 and min(cx, ccx) <= vx1
                        and max(cy, ccy) >= vy0 and min(cy, ccy) <= vy1):
                    ch = child.get('chosen')
                    self.canvas.create_line(cx, cy, ccx, ccy,
                                            fill=CHOSEN_COLOR if ch else LINE,
                                            width=max(1, round((3 if ch else 2) * z)))
                self.draw_node(child)

        if not (vx0 <= cx <= vx1 and vy0 <= cy <= vy1):
            return

        if node['pruned']:
            color = PRUNED_COLOR
        elif node['is_leaf']:
            color = LEAF_COLOR
        elif node['is_max']:
            color = MAX_COLOR
        else:
            color = MIN_COLOR

        important = bool(node.get('chosen')) or node is self.tree
        r = max(NODE_R * z, 6 if important else 3)
        folded = len(node['children']) > 0 and not node['open']
        if node.get('chosen'):
            outline, width = CHOSEN_COLOR, max(2, round(4 * z))
        elif folded:
            outline, width = "white", max(1, round(3 * z))
        else:
            outline, width = CARD, max(1, round(2 * z))
        self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                fill=color, outline=outline, width=width)

        # level of detail: no text when zoomed far out (except the chosen path)
        if z >= 0.45:
            label = "R" if node['move'] is None else str(node['move'])
            self.canvas.create_text(cx, cy, text=label, fill="#0b1020",
                                    font=("Segoe UI", max(6, int(10 * z)), "bold"))
            if z >= 0.6:
                self.canvas.create_text(cx, cy + r + 10 * z, text=fmt(node['value']),
                                        fill=MUTED, font=("Segoe UI", max(6, int(8 * z))))
        elif important:
            label = "R" if node['move'] is None else str(node['move'])
            self.canvas.create_text(cx + r + 4, cy, anchor="w",
                                    text=f"{label}: {fmt(node['value'])}",
                                    fill=CHOSEN_COLOR, font=("Segoe UI", 9, "bold"))
        self.drawn.append((cx, cy, r, node))

    def node_at(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        for cx, cy, r, node in self.drawn:
            if (x - cx) ** 2 + (y - cy) ** 2 <= r ** 2:
                return node
        return None

    # ---------- navigation ----------
    def center_at(self, px, py):
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        self.canvas.xview_moveto(max(0, (px - cw / 2) / self.world_w))
        self.canvas.yview_moveto(max(0, (py - ch / 2) / self.world_h))
        self.draw_tree()

    def go_to(self, node):
        px, py = self.node_xy(node)
        self.center_at(px, py)

    def toggle_orientation(self):
        self.top_down = not self.top_down
        self.orient_btn.config(text="Left-right →" if self.top_down else "Top-down ↓")
        if self.tree is None:
            return
        self.relayout()
        self.go_to(self.tree)

    def go_root(self):
        if self.tree is None:
            return
        self.path_idx = 0
        self.path_label.config(text=f"Path: 1 / {len(self.path)}")
        self.go_to(self.tree)

    def next_on_path(self):
        # step along the chosen path: root -> chosen child -> ... -> leaf -> back to root
        if self.tree is None or len(self.path) < 2:
            return
        self.path_idx = self.path_idx + 1 if self.path_idx + 1 < len(self.path) else 0
        for n in self.path[:self.path_idx]:
            n['open'] = True
        self.relayout()
        self.path_label.config(text=f"Path: {self.path_idx + 1} / {len(self.path)}")
        self.go_to(self.path[self.path_idx])

    # ---------- zoom / pan / scroll ----------
    def zoom_by(self, factor, ex=None, ey=None):
        if self.tree is None:
            return
        old = self.zoom
        new = max(MIN_ZOOM, min(3.0, old * factor))
        if new == old:
            return
        if ex is None:
            ex, ey = self.canvas.winfo_width() / 2, self.canvas.winfo_height() / 2
        wx = (self.canvas.canvasx(ex) - PAD) / old     # world point under the cursor
        wy = (self.canvas.canvasy(ey) - PAD) / old
        self.zoom = new
        self.relayout()
        self.canvas.xview_moveto(max(0, wx * new + PAD - ex) / self.world_w)
        self.canvas.yview_moveto(max(0, wy * new + PAD - ey) / self.world_h)
        self.draw_tree()

    def fit_view(self):
        # back to the readable 100% size, from the top of the tree
        if self.tree is None:
            return
        self.zoom = 1.0
        self.relayout()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)
        self.draw_tree()

    def on_zoom_wheel(self, e):
        self.zoom_by(1.15 if e.delta > 0 else 1 / 1.15, e.x, e.y)

    def on_wheel(self, e):
        self.canvas.yview_scroll(-(e.delta // 120), "units")
        self.schedule_draw()

    def on_hwheel(self, e):
        self.canvas.xview_scroll(-(e.delta // 120), "units")
        self.schedule_draw()

    def xscroll(self, *args):
        self.canvas.xview(*args)
        self.schedule_draw()

    def yscroll(self, *args):
        self.canvas.yview(*args)
        self.schedule_draw()

    def on_press(self, e):
        self._press = (e.x, e.y)
        self._dragged = False
        self.canvas.scan_mark(e.x, e.y)

    def on_drag(self, e):
        if self._press is None:
            return
        if not self._dragged and abs(e.x - self._press[0]) + abs(e.y - self._press[1]) < 4:
            return
        self._dragged = True
        self.canvas.scan_dragto(e.x, e.y, gain=1)
        self.schedule_draw()

    def on_release(self, e):
        if not self._dragged:                      # plain click = open/fold
            node = self.node_at(e)
            if node is not None and node['children']:
                node['open'] = not node['open']
                self.relayout()
                self.draw_tree()
        self._press = None

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