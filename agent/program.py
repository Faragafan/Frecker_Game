# COMP30024 Artificial Intelligence, Semester 1 2025
# Project Part B: Game Playing Agent

from referee.game import PlayerColor, Coord, Direction, \
    Action, MoveAction, GrowAction
    


class Agent:
    """
    This class is the "entry point" for your agent, providing an interface to
    respond to various Freckers game events.
    """
    
    def __init__(self, color: PlayerColor, **referee: dict):
        """
        This constructor method runs when the referee instantiates the agent.
        Any setup and/or precomputation should be done here.
        """
        self._color = color
        self.enemy_color = PlayerColor.RED if color == PlayerColor.BLUE else PlayerColor.BLUE
        self.board = self.initialize_board()
        self.frogs = self.initialize_frogs()
    
    def initialize_board(self):

        # Initialize the board here
        board = [[None for _ in range(8)] for _ in range(8)]
        # Red frogs
        board[0][1] = "red"
        board[0][2] = "red"
        board[0][3] = "red"
        board[0][4] = "red"
        board[0][5] = "red"
        board[0][6] = "red"
        # Blue frogs
        board[7][1] = "blue"
        board[7][2] = "blue"
        board[7][3] = "blue"
        board[7][4] = "blue"
        board[7][5] = "blue"
        board[7][6] = "blue"
        
        # Lily pads
        lilypad_coords = [
        (0,0), (0,1), (0,2), (0,3),
        (0,4), (0,5), (0,6), (0,7),
        (1,1), (1,2), (1,3), (1,4),
        (1,5), (1,6), (7,0), (7,1),
        (7,2), (7,3), (7,4), (7,5),
        (7,6), (7,7), (6,1), (6,2),
        (6,3), (6,4), (6,5), (6,6)
        ]
            
        for r,c in lilypad_coords:
            if board[r][c] is None:
                board[r][c] = "lilypad"
            
        return board
    
    def initialize_frogs(self):
        frogs = []
        if self._color == PlayerColor.RED:
            frogs = [Coord(0,1), Coord(0,2), Coord(0,3), Coord(0,4), Coord(0,5), Coord(0,6)]
        else:
            frogs = [Coord(7,1), Coord(7,2), Coord(7,3), Coord(7,4), Coord(7,5), Coord(7,6)]
        return frogs
            


    def action(self, **referee: dict) -> Action:
        """
        This method is called by the referee each time it is the agent's turn
        to take an action. It must always return an action object. 
        """

        # Below we have hardcoded two actions to be played depending on whether
        # the agent is playing as BLUE or RED. Obviously this won't work beyond
        # the initial moves of the game, so you should use some game playing
        # technique(s) to determine the best action to take.
        match self._color:
            case PlayerColor.RED:
                print("Testing: RED is playing a MOVE action")
                return MoveAction(
                    Coord(0, 3),
                    [Direction.Down]
                )
            case PlayerColor.BLUE:
                print("Testing: BLUE is playing a GROW action")
                return GrowAction()

    def update(self, color: PlayerColor, action: Action, **referee: dict):
        """
        This method is called by the referee after a player has taken their
        turn. You should use it to update the agent's internal game state. 
        """

        # There are two possible action types: MOVE and GROW. Below we check
        # which type of action was played and print out the details of the
        # action for demonstration purposes. You should replace this with your
        # own logic to update your agent's internal game state representation.
        match action:
            case MoveAction(coord, dirs):
                self.apply_move(self, color, coord, dirs)
            case GrowAction():
                self.apply_grow(self, color)
            case _:
                raise ValueError(f"Unknown action type: {action}")
    
    def apply_move(self, color: PlayerColor, coord: Coord, dirs: list[Direction]):
        for d in dir: 
            new = coord + d
            if 0 <= new.r < 8 and 0 <= new.c < 8:
                if self.board[new.r][new.c] is None:
                    self.board[new.r][new.c] = "frog"
                    self.board[coord.r][coord.c] = None
                    break
                elif self.board[new.r][new.c] == "lilypad":
                    self.board[new.r][new.c] = "frog"
                    self.board[coord.r][coord.c] = None
                    break
        
        
        
    def apply_grow(self, color: PlayerColor):
        frog_color = "red" if color == PlayerColor.RED else "blue"

        # Find all frogs of this color
        for r in range(8):
            for c in range(8):
                if self.board[r][c] == frog_color:
                    frog = Coord(r, c)
                    for dir in Direction:
                        new = frog + dir
                        if 0 <= new.r < 8 and 0 <= new.c < 8:
                            if self.board[new.r][new.c] is None:
                                self.board[new.r][new.c] = "lilypad"