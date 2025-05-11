# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent
from __future__ import annotations
from typing import List, Set
from referee.game import PlayerColor, Coord, Direction, Action, MoveAction, GrowAction
import random
import math
import time

class Agent:
    """
    Freckers agent using alpha-beta search over GameState.
    """
    def __init__(self, color: PlayerColor, **referee):
        self.color = color
        self.enemy = PlayerColor.RED if color == PlayerColor.BLUE else PlayerColor.BLUE
        self.state = GameState()
        self.time_limit = 1.0  # seconds per move

    def action(self, **referee) -> Action:
        start_time = time.time()
        # set turn
        self.state.current_player = self.color

        best_action = GrowAction()
        best_value = float('-inf')
        alpha, beta = float('-inf'), float('inf')
        depth = 3

        for act in self.state.get_legal_actions():
            next_state = self.state.clone()
            next_state.apply_action(act)
            value = self._min_value(next_state, depth - 1, alpha, beta, start_time)
            if value > best_value:
                best_value, best_action = value, act
                alpha = max(alpha, value)
            if alpha >= beta or time.time() - start_time > self.time_limit:
                break

        # **DO NOT** mutate self.state here; referee will call update()
        return best_action

    def update(self, color_of_player_who_acted: PlayerColor, action_performed: Action, **referee):
        self.state.current_player = color_of_player_who_acted
        self.state.apply_action(action_performed)

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, start_time: float) -> float:
        if depth == 0 or state.is_terminal():
            return self._evaluate(state)
        v = float('-inf')
        for act in state.get_legal_actions():
            nxt = state.clone()
            nxt.apply_action(act)
            v = max(v, self._min_value(nxt, depth - 1, alpha, beta, start_time))
            if v >= beta or time.time() - start_time > self.time_limit:
                return v
            alpha = max(alpha, v)
        return v

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, start_time: float) -> float:
        if depth == 0 or state.is_terminal():
            return self._evaluate(state)
        v = float('inf')
        for act in state.get_legal_actions():
            nxt = state.clone()
            nxt.apply_action(act)
            v = min(v, self._max_value(nxt, depth - 1, alpha, beta, start_time))
            if v <= alpha or time.time() - start_time > self.time_limit:
                return v
            beta = min(beta, v)
        return v

    def _evaluate(self, state: GameState) -> float:
        # Distance to goal
        red_dist = sum((7 - pos.r) for pos, owner in state.frogs.items() if owner == PlayerColor.RED)
        blue_dist = sum(pos.r for pos, owner in state.frogs.items() if owner == PlayerColor.BLUE)
        dist_score = (blue_dist - red_dist) if self.color == PlayerColor.RED else (red_dist - blue_dist)
        # Mobility
        my_moves = len(state.get_legal_actions())
        # temporarily flip to get opponent moves
        state.current_player = self.enemy
        opp_moves = len(state.get_legal_actions())
        state.current_player = self.color
        mobility_score = my_moves - opp_moves
        # Pad adjacency
        pad_bonus = 0
        for pos, owner in state.frogs.items():
            cnt = 0
            for d in Direction:
                try:
                    nbr = pos + d
                    if 0 <= nbr.r < 8 and 0 <= nbr.c < 8 and nbr in state.lily_pads:
                        cnt += 1
                except ValueError:
                    continue
            pad_bonus += cnt if owner == self.color else -cnt
        # Terminal
        if state.is_terminal():
            winner = state.get_winner()
            if winner == self.color: return float('inf')
            if winner == self.enemy: return float('-inf')
        return 40 * dist_score + 5 * mobility_score + pad_bonus
    
class GameState:
    """
    Freckers 游戏状态：跟踪莲叶和青蛙位置，维护当前玩家和回合计数。
    """
    # 两种玩家的前进方向（红方：向下及横向；蓝方：向上及横向） 
    RED_DIRS = [Direction.Right, Direction.Left, Direction.Down, Direction.DownRight, Direction.DownLeft]
    BLUE_DIRS = [Direction.Right, Direction.Left, Direction.Up, Direction.UpRight, Direction.UpLeft]
    ALL_DIRS = list(Direction)
    MAX_TURNS = 150  # 上限动作数 

    def __init__(self, lily_pads=None, frogs=None, current_player=PlayerColor.RED, turn=0):
        if lily_pads is None or frogs is None:
            self.lily_pads, self.frogs = self._init_board()
        else:
            self.lily_pads = set(lily_pads)
            self.frogs = dict(frogs)
        self.current_player = current_player
        self.turn = turn

    def _init_board(self):
        # 根据规则文档 Fig3 初始化28个莲叶和12个青蛙位置。
        # 这里需填入实际坐标列表，示例中留作占位。
        initial_lily = set([Coord(0,0),Coord(0,1),Coord(0,2),Coord(0,3),Coord(0,4),Coord(0,5),Coord(0,6),Coord(0,7),
            Coord(1,1),Coord(1,2),Coord(1,3),Coord(1,4),Coord(1,5),Coord(1,6),
            Coord(6,1),Coord(6,2),Coord(6,3),Coord(6,4),Coord(6,5),Coord(6,6),
            Coord(7,0),Coord(7,1),Coord(7,2),Coord(7,3),Coord(7,4),Coord(7,5),Coord(7,6),Coord(7,7)
            
        ])
        initial_frogs = {
            # TODO: 填入红方6只青蛙和蓝方6只青蛙初始位置
            # 例如 Coord(0,3): PlayerColor.RED, Coord(7,4): PlayerColor.BLUE, ...
            Coord(0, 1): PlayerColor.RED, Coord(0, 2): PlayerColor.RED,
            Coord(0, 3): PlayerColor.RED, Coord(0, 4): PlayerColor.RED,
            Coord(0, 5): PlayerColor.RED, Coord(0, 6): PlayerColor.RED,
            Coord(7, 1): PlayerColor.BLUE, Coord(7, 2): PlayerColor.BLUE,
            Coord(7, 3): PlayerColor.BLUE, Coord(7, 4): PlayerColor.BLUE,
            Coord(7, 5): PlayerColor.BLUE, Coord(7, 6): PlayerColor.BLUE
        }
        return initial_lily, initial_frogs

    def clone(self):
        return GameState(self.lily_pads, self.frogs, self.current_player, self.turn)

    def get_legal_actions(self) -> List[Action]:
        """
        Return only the moves and grow for `player`.  
        Single‐step moves are one‐cell hops; multi‐jumps are built
        by _get_all_jump_sequences. No mixing.
        """
        player = self.current_player
        actions: List[Action] = []
        dirs = self.RED_DIRS if player == PlayerColor.RED else self.BLUE_DIRS

        for src, frog_owner in self.frogs.items():
            if frog_owner != player:
                continue

            # 1) Single‐step moves (exactly one cell)
            for d in dirs:
                try:
                    dst = src + d
                    if dst in self.lily_pads and dst not in self.frogs:
                        actions.append(MoveAction(src, (d,)))
                except ValueError:
                    pass

            # 2) Jump sequences (2+ cells per segment), only over occupied mids
            self._get_all_jump_sequences(
                player=player,
                original_src=src,
                current_pos=src,
                current_path_dirs=[],
                legal_actions_list=actions,
                visited_landings=set()
            )

        # 3) Growing is always legal
        actions.append(GrowAction())
        def action_priority(act: Action):
            # multi-jump has highest priority
            if isinstance(act, MoveAction):
                is_jump = len(act.directions) > 1
                # compute net row change for forward move
                src = act.coord
                dst = src
                for step in act.directions:
                    dst = dst + step
                # for RED, forward is increasing r; for BLUE, decreasing r
                forward_delta = (dst.r - src.r) if player == PlayerColor.RED else (src.r - dst.r)
                lateral_delta = abs(dst.c - src.c)
                # priority tuple: jump first, then larger forward_delta, then smaller lateral
                return (0 if is_jump else 1, -forward_delta, lateral_delta)
            # grow last
            return (2, 0, 0)
        actions.sort(key=action_priority)
        return actions



    def _get_all_jump_sequences(self,
                                player: PlayerColor,
                                original_src: Coord,
                                current_pos: Coord,
                                current_path_dirs: List[Direction],
                                legal_actions_list: List[Action],
                                visited_landings: Set[Coord]):
        """
        Build ALL valid jump MoveActions for a frog of `player` starting
        at original_src.  Each direction d here represents a *jump* of 2 cells:
        mid = current_pos + d  (must have a frog)
        landing = mid + d      (must be an empty lily pad)
        """
        jump_dirs = self.RED_DIRS if player == PlayerColor.RED else self.BLUE_DIRS

        for d in jump_dirs:
            try:
                mid     = current_pos + d
                landing = mid + d

                # check the four jump conditions
                if (mid in self.frogs
                    and landing in self.lily_pads
                    and landing not in self.frogs
                    and landing not in visited_landings):

                    new_path = current_path_dirs + [d]
                    legal_actions_list.append(MoveAction(original_src, tuple(new_path)))

                    visited_landings.add(landing)
                    # recurse to chain further jumps
                    self._get_all_jump_sequences(
                        player=player,
                        original_src=original_src,
                        current_pos=landing,
                        current_path_dirs=new_path,
                        legal_actions_list=legal_actions_list,
                        visited_landings=visited_landings
                    )
                    visited_landings.remove(landing)

            except ValueError:
                # move off‐board
                continue


    def apply_action(self, action):
        if isinstance(action, GrowAction):
            new_pads = set()
            for pos, owner in self.frogs.items():
                if owner != self.current_player: continue
                for d in self.ALL_DIRS:
                    try:
                        pad = pos + d
                        if 0 <= pad.r < 8 and 0 <= pad.c < 8 and pad not in self.lily_pads and pad not in self.frogs:
                            new_pads.add(pad)
                    except ValueError:
                        pass
            self.lily_pads |= new_pads
        else:
            # MOVEAction
            assert action.coord in self.frogs, f"No frog at {action.coord!r}"
            src = action.coord
            if src in self.lily_pads:
                self.lily_pads.remove(src)
            pos = src
            for d in action.directions:
                try:
                    mid = pos + d
                    land = mid + d
                    if mid in self.frogs and land in self.lily_pads and land not in self.frogs:
                        pos = land
                    else:
                        pos = pos + d
                except ValueError:
                    pos = pos + d
            self.frogs.pop(src)
            self.frogs[pos] = self.current_player
        # flip turn
        self.current_player = PlayerColor.BLUE if self.current_player == PlayerColor.RED else PlayerColor.RED
        self.turn += 1


    def is_terminal(self):
        # 检查任一玩家是否所有青蛙抵达对岸，或达到最大回合数
        red_goal = [f.r == 7 for f, p in self.frogs.items() if p == PlayerColor.RED]
        blue_goal = [f.r == 0 for f, p in self.frogs.items() if p == PlayerColor.BLUE]
        if len(red_goal) == 6 and all(red_goal):
            return True
        if len(blue_goal) == 6 and all(blue_goal):
            return True
        return self.turn >= self.MAX_TURNS

    def get_winner(self):
        # 根据胜利条件返回胜者或 None 表示平局
        if all(f.r == 7 for f, p in self.frogs.items() if p == PlayerColor.RED):
            return PlayerColor.RED
        if all(f.r == 0 for f, p in self.frogs.items() if p == PlayerColor.BLUE):
            return PlayerColor.BLUE
        # 回合耗尽，比较抵达对岸数量
        red_count = sum(1 for f, p in self.frogs.items() if p == PlayerColor.RED and f.r == 7)
        blue_count = sum(1 for f, p in self.frogs.items() if p == PlayerColor.BLUE and f.r == 0)
        if red_count > blue_count:
            return PlayerColor.RED
        if blue_count > red_count:
            return PlayerColor.BLUE
        return None
