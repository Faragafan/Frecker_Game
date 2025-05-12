# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from __future__ import annotations
from typing import List
from referee.game import PlayerColor, Coord, Direction, Action, MoveAction, GrowAction
import time

class Agent:
    """
    Freckers agent using alpha-beta pruning over GameState.
    """
    def __init__(self, color: PlayerColor, **referee):
        self.color = color
        self.enemy = PlayerColor.RED if color == PlayerColor.BLUE else PlayerColor.BLUE
        self.state = GameState()
        self.time_limit = 1.0  # seconds per move

    def action(self, **referee) -> Action:
        start_time = time.time()
        self.state.current_player = self.color

        # Apply alpha-beta pruning
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

        return best_action

    def update(self, color_of_player_who_acted: PlayerColor, action_performed: Action, **referee):
        self.state.current_player = color_of_player_who_acted
        self.state.apply_action(action_performed)

    def _max_value(self, state: GameState, depth: int, alpha: float, beta: float, start_time: float) -> float:
        # Function to calculate the maximum value of a state
        if depth == 0 or state.is_terminal():
            return self._evaluate(state)
        value = float('-inf')
        for act in state.get_legal_actions():
            nxt = state.clone()
            nxt.apply_action(act)
            value = max(value, self._min_value(nxt, depth - 1, alpha, beta, start_time))
            if value >= beta or time.time() - start_time > self.time_limit:
                return value
            alpha = max(alpha, value)
        return value

    def _min_value(self, state: GameState, depth: int, alpha: float, beta: float, start_time: float) -> float:
        # Function to calculate the minimum value of a state
        if depth == 0 or state.is_terminal():
            return self._evaluate(state)
        value = float('inf')
        for act in state.get_legal_actions():
            nxt = state.clone()
            nxt.apply_action(act)
            value = min(value, self._max_value(nxt, depth - 1, alpha, beta, start_time))
            if value <= alpha or time.time() - start_time > self.time_limit:
                return value
            beta = min(beta, value)
        return value

    def _evaluate(self, state: GameState) -> float:
        # Heuristic evaluation function for alpha-beta pruning, involving multiple factors:
        
        # Distance to goal rows
        red_dist = sum((7 - pos.r) for pos, owner in state.frogs.items() if owner == PlayerColor.RED)
        blue_dist = sum(pos.r for pos, owner in state.frogs.items() if owner == PlayerColor.BLUE)
        dist_score = (blue_dist - red_dist) if self.color == PlayerColor.RED else (red_dist - blue_dist)

        # Number of legal moves
        my_moves = len(state.get_legal_actions())
        state.current_player = self.enemy
        opp_moves = len(state.get_legal_actions())
        state.current_player = self.color
        mobility_score = my_moves - opp_moves

        # Number of adjacent lily pads
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

        if state.is_terminal():
            winner = state.get_winner()
            if winner == self.color:
                return float('inf')
            if winner == self.enemy:
                return float('-inf')

        return 40 * dist_score + 5 * mobility_score + pad_bonus

class GameState:
    """
    Freckers game state: tracks lily pads, frog positions,
    current player, and turn counter.
    """
    RED_DIRS = [Direction.Right, Direction.Left, Direction.Down, Direction.DownRight, Direction.DownLeft]
    BLUE_DIRS = [Direction.Right, Direction.Left, Direction.Up, Direction.UpRight, Direction.UpLeft]
    ALL_DIRS = list(Direction)
    MAX_TURNS = 150

    def __init__(self, lily_pads=None, frogs=None, current_player=PlayerColor.RED, turn=0):
        # Initialize the game state
        if lily_pads is None or frogs is None:
            self.lily_pads, self.frogs = self._init_board()
        else:
            self.lily_pads = set(lily_pads)
            self.frogs = dict(frogs)
        self.current_player = current_player
        self.turn = turn

    def _init_board(self):
        # Initial lily pad and frog placement based on the rules
        initial_lily = set([
            Coord(0,0),Coord(0,1),Coord(0,2),Coord(0,3),Coord(0,4),Coord(0,5),Coord(0,6),Coord(0,7),
            Coord(1,1),Coord(1,2),Coord(1,3),Coord(1,4),Coord(1,5),Coord(1,6),
            Coord(6,1),Coord(6,2),Coord(6,3),Coord(6,4),Coord(6,5),Coord(6,6),
            Coord(7,0),Coord(7,1),Coord(7,2),Coord(7,3),Coord(7,4),Coord(7,5),Coord(7,6),Coord(7,7)
        ])
        initial_frogs = {
            Coord(0, 1): PlayerColor.RED, Coord(0, 2): PlayerColor.RED,
            Coord(0, 3): PlayerColor.RED, Coord(0, 4): PlayerColor.RED,
            Coord(0, 5): PlayerColor.RED, Coord(0, 6): PlayerColor.RED,
            Coord(7, 1): PlayerColor.BLUE, Coord(7, 2): PlayerColor.BLUE,
            Coord(7, 3): PlayerColor.BLUE, Coord(7, 4): PlayerColor.BLUE,
            Coord(7, 5): PlayerColor.BLUE, Coord(7, 6): PlayerColor.BLUE
        }
        return initial_lily, initial_frogs

    def clone(self):
        # Create a deep copy of the game state for simulation in alpha-beta pruning search
        return GameState(self.lily_pads, self.frogs, self.current_player, self.turn)

    def get_legal_actions(self) -> List[Action]:
        # Generate all legal actions for the current player
        player = self.current_player
        actions: List[Action] = []
        dirs = self.RED_DIRS if player == PlayerColor.RED else self.BLUE_DIRS

        for start_pos, frog_owner in self.frogs.items():
            if frog_owner != player:
                continue

            # Single-step hops
            for d in dirs:
                try:
                    dst = start_pos + d
                    if dst in self.lily_pads and dst not in self.frogs:
                        actions.append(MoveAction(start_pos, (d,)))
                except ValueError:
                    pass

            # Multi-step jumps
            self._get_all_jump_sequences(player, start_pos, start_pos, [], actions, set())

        # Grow is always allowed
        actions.append(GrowAction())

        def action_priority(act: Action):
            # Prioritise jumps and vertical moves over left and right moves
            if isinstance(act, MoveAction):
                is_jump = len(act.directions) > 1
                start_pos = act.coord
                dst = start_pos
                for step in act.directions:
                    dst = dst + step
                forward_delta = (dst.r - start_pos.r) if player == PlayerColor.RED else (start_pos.r - dst.r)
                lateral_delta = abs(dst.c - start_pos.c)
                return (0 if is_jump else 1, -forward_delta, lateral_delta)
            return (2, 0, 0)

        actions.sort(key=action_priority)
        return actions

    def _get_all_jump_sequences(self, player, original_start, current_pos, current_path_dirs, legal_actions_list, visited_landings):
        jump_dirs = self.RED_DIRS if player == PlayerColor.RED else self.BLUE_DIRS
        # Get all possible jump sequences from the current position
        for d in jump_dirs:
            try:
                mid = current_pos + d
                landing = mid + d
                if (mid in self.frogs and landing in self.lily_pads
                    and landing not in self.frogs and landing not in visited_landings):

                    new_path = current_path_dirs + [d]
                    legal_actions_list.append(MoveAction(original_start, tuple(new_path)))
                    visited_landings.add(landing)
                    self._get_all_jump_sequences(player, original_start, landing, new_path, legal_actions_list, visited_landings)
                    visited_landings.remove(landing)
            except ValueError:
                continue

    def apply_action(self, action):
        # Apply the action to the game state
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
            start_pos = action.coord
            if start_pos in self.lily_pads:
                self.lily_pads.remove(start_pos)
            pos = start_pos
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
            self.frogs.pop(start_pos)
            self.frogs[pos] = self.current_player

        self.current_player = PlayerColor.BLUE if self.current_player == PlayerColor.RED else PlayerColor.RED
        self.turn += 1

    def is_terminal(self):
        # Check if the game is over
        red_goal = [f.r == 7 for f, p in self.frogs.items() if p == PlayerColor.RED]
        blue_goal = [f.r == 0 for f, p in self.frogs.items() if p == PlayerColor.BLUE]
        if len(red_goal) == 6 and all(red_goal):
            return True
        if len(blue_goal) == 6 and all(blue_goal):
            return True
        return self.turn >= self.MAX_TURNS

    def get_winner(self):
        # Determine the winner of the game
        if all(f.r == 7 for f, p in self.frogs.items() if p == PlayerColor.RED):
            return PlayerColor.RED
        if all(f.r == 0 for f, p in self.frogs.items() if p == PlayerColor.BLUE):
            return PlayerColor.BLUE
        red_count = sum(1 for f, p in self.frogs.items() if p == PlayerColor.RED and f.r == 7)
        blue_count = sum(1 for f, p in self.frogs.items() if p == PlayerColor.BLUE and f.r == 0)
        if red_count > blue_count:
            return PlayerColor.RED
        if blue_count > red_count:
            return PlayerColor.BLUE
        return None
