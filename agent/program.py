from referee.game import MoveAction, GrowAction, Direction, Coord, PlayerColor, Action
import math

class Agent:
    """
    Game-playing agent for Freckers using Alpha-Beta search for MOVE and GROW actions.
    """
    def __init__(self, color: PlayerColor, **referee):
        self._color = color
        self.enemy_color = PlayerColor.RED if color == PlayerColor.BLUE else PlayerColor.BLUE
        # Initial board and frog lists
        self.board = self._init_board()
        self.my_frogs = self._init_frogs(self._color)
        self.opp_frogs = self._init_frogs(self.enemy_color)

    def _init_board(self) -> list[list[str | None]]:
        board = [[None for _ in range(8)] for _ in range(8)]
        # Place frogs
        for r, c, color_str in [
            (0,1,'red'),(0,2,'red'),(0,3,'red'),(0,4,'red'),(0,5,'red'),(0,6,'red'),
            (7,1,'blue'),(7,2,'blue'),(7,3,'blue'),(7,4,'blue'),(7,5,'blue'),(7,6,'blue')]:
            board[r][c] = color_str
        # Place lilypads
        for r, c in [
            (0,0),(0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
            (1,1),(1,2),(1,3),(1,4),(1,5),(1,6),
            (6,1),(6,2),(6,3),(6,4),(6,5),(6,6),
            (7,0),(7,1),(7,2),(7,3),(7,4),(7,5),(7,6),(7,7)
        ]:
            if board[r][c] is None:
                board[r][c] = 'lilypad'
        return board

    def _init_frogs(self, color: PlayerColor) -> list[Coord]:
        if color == PlayerColor.RED:
            return [Coord(0,1), Coord(0,2), Coord(0,3), Coord(0,4), Coord(0,5), Coord(0,6)]
        else:
            return [Coord(7,1), Coord(7,2), Coord(7,3), Coord(7,4), Coord(7,5), Coord(7,6)]

    def action(self, **referee) -> Action:
        # Choose best action via alpha-beta search
        choice = self._alpha_beta_search(depth=3)
        return choice if choice is not None else GrowAction()

    def update(self, color: PlayerColor, action: Action, **referee):
        # Apply the executed action to real game state
        if isinstance(action, MoveAction):
            self._apply_move(color, action.coord, action.dirs, self.board,
                              self.my_frogs if color==self._color else self.opp_frogs)
        else:
            self._apply_grow(color, self.board)

    def _apply_move(self, color: PlayerColor, start: Coord, dirs: list[Direction],
                    board: list[list[str|None]], frogs: list[Coord]):
        cur = start
        for d in dirs:
            cur = cur + d
        dest = cur
        cstr = 'red' if color==PlayerColor.RED else 'blue'
        board[start.r][start.c] = None
        board[dest.r][dest.c] = cstr
        frogs.remove(start)
        frogs.append(dest)

    def _apply_grow(self, color: PlayerColor, board: list[list[str|None]]):
        cstr = 'red' if color==PlayerColor.RED else 'blue'
        for r in range(8):
            for c in range(8):
                if board[r][c] == cstr:
                    origin = Coord(r,c)
                    for d in Direction:
                        try:
                            adj = origin + d
                            if 0 <= adj.r < 8 and 0 <= adj.c < 8 and board[adj.r][adj.c] is None:
                                board[adj.r][adj.c] = 'lilypad'
                        except ValueError:
                            continue

    def _clone_state(self):
        return [row.copy() for row in self.board], self.my_frogs.copy(), self.opp_frogs.copy()

    def _clone_inner(self, board: list[list[str|None]], frogs: list[Coord]):
        return [row.copy() for row in board], frogs.copy()

    def _alpha_beta_search(self, depth: int) -> Action | None:
        board0, my0, op0 = self._clone_state()
        actions = self._generate_moves_from(board0, my0, op0, self._color) + [GrowAction()]
        alpha, beta = -math.inf, math.inf
        best_val, best_act = -math.inf, None
        for act in actions:
            b1, m1, o1 = self._clone_state()
            if isinstance(act, MoveAction):
                self._apply_move(self._color, act.coord, act.dirs, b1, m1)
            else:
                self._apply_grow(self._color, b1)
            val = self._min_value(b1, m1, o1, depth-1, alpha, beta)
            if val > best_val:
                best_val, best_act = val, act
                alpha = max(alpha, val)
        return best_act

    def _max_value(self, board, my_frogs, opp_frogs, depth, alpha, beta):
        if depth == 0:
            return self._evaluate(board, my_frogs)
        value = -math.inf
        for mv in self._generate_moves_from(board, my_frogs, opp_frogs, self._color):
            b2, m2 = self._clone_inner(board, my_frogs)
            o2 = opp_frogs.copy()
            self._apply_move(self._color, mv.coord, mv.dirs, b2, m2)
            res = self._min_value(b2, m2, o2, depth-1, alpha, beta)
            value = max(value, res)
            if value >= beta:
                return value
            alpha = max(alpha, value)
        return value

    def _min_value(self, board, my_frogs, opp_frogs, depth, alpha, beta):
        if depth == 0:
            return self._evaluate(board, opp_frogs)
        value = math.inf
        for mv in self._generate_moves_from(board, opp_frogs, my_frogs, self.enemy_color):
            b2, o2 = self._clone_inner(board, opp_frogs)
            m2 = my_frogs.copy()
            if isinstance(mv, MoveAction):
                self._apply_move(self.enemy_color, mv.coord, mv.dirs, b2, o2)
            else:
                self._apply_grow(self.enemy_color, b2)
            res = self._max_value(b2, m2, o2, depth-1, alpha, beta)
            value = min(value, res)
            if value <= alpha:
                return value
            beta = min(beta, value)
        return value

    def _generate_moves_from(self,
                             board: list[list[str|None]],
                             my_frogs: list[Coord],
                             opp_frogs: list[Coord],
                             color: PlayerColor
                            ) -> list[MoveAction]:
        def in_bounds(co: Coord) -> bool:
            return 0 <= co.r < 8 and 0 <= co.c < 8
        def neighbor(co: Coord, d: Direction, steps: int=1) -> Coord | None:
            try:
                nx = co + (d.value * steps)
                return nx if in_bounds(nx) else None
            except ValueError:
                return None
        frogs = my_frogs if color == self._color else opp_frogs
        moves: list[MoveAction] = []
        for f in frogs:
            # single-hop
            for d in Direction:
                n = neighbor(f, d, 1)
                if n and board[n.r][n.c] == 'lilypad':
                    moves.append(MoveAction(f, [d]))
            # single-jump
            for d in Direction:
                mid = neighbor(f, d, 1)
                dst = neighbor(f, d, 2)
                if mid and dst and board[mid.r][mid.c] in ('red','blue') and board[dst.r][dst.c] == 'lilypad':
                    moves.append(MoveAction(f, [d]))
        return moves

    def _evaluate(self, board: list[list[str|None]], frogs: list[Coord]) -> float:
        my_dist = sum(f.r for f in frogs)
        opp_list = [Coord(r,c) for r in range(8) for c in range(8)
                    if board[r][c] == ('blue' if self._color==PlayerColor.RED else 'red')]
        opp_dist = sum(f.r for f in opp_list)
        score = my_dist - opp_dist
        goal = 7 if self._color==PlayerColor.RED else 0
        score += 50 * sum(1 for f in frogs if f.r == goal)
        og = 7 if self.enemy_color==PlayerColor.RED else 0
        score -= 50 * sum(1 for f in opp_list if f.r == og)
        # trapped/mobility
        for f in frogs:
            cnt = sum(1 for d in Direction if (n:=f+d) and 0<=n.r<8 and 0<=n.c<8 and board[n.r][n.c]=='lilypad')
            if cnt == 0: score -= 20
        for f in opp_list:
            cnt = sum(1 for d in Direction if (n:=f+d) and 0<=n.r<8 and 0<=n.c<8 and board[n.r][n.c]=='lilypad')
            if cnt == 0: score += 20
        # adjacency reward
        for f in frogs:
            for d in Direction:
                try:
                    n = f + d
                    if 0<=n.r<8 and 0<=n.c<8 and board[n.r][n.c]=='lilypad': score += 1
                except ValueError: pass
        return score
