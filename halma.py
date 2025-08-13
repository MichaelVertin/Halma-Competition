import tkinter
import pdb
import time
import random


# AESTHETICS
PLAYER_LIST = [ "blue", "green" ]#, "pink", "purple" ]
AI_LIST = [ "green" ]
    # NOTE: does not support more than two players when ai_list is set
    #               after implementation of alternating players in alpha-beta

# BOARD PROPERTIES
BOARD_LENGTH = 8
YARD_DEPTH = 4
CANVAS_DIM = 60
REVERSE_YARD_INDEX = 3
YARD_INDEX_CONVERSION = 3

# ALGORITHM CONTANTS
REC_DEPTH = 4 # depth of recursion for ai
CURRENT_PRIORITY = 1.01 # prioirize moves that will occur sooner
                        # main use for gameEnd case
MIN_REC_INCREMENT = -4
MAX_SELF_PENALTY = 6
ALPHA_START = float("-inf")
BETA_START = float("inf")

# TIME_MANAGEMENT CONSTANTS
    # modifies REC_DEPTH based on time to perform previous iterations
TARGET_TIME_MULTIPLIER = .8
APPLY_TIME_MANAGEMENT = True

# TIME CONSTANTS
MAX_TIME = 20
TIME_TO_EXIT = .1
AI_DELAY = 0 # delay between ai turns

ADJACENT_DIM_RANGE = (-1,0,1)
# all adjacent relatives (excludes self)
ADJACENT_POS_LIST = [ (rel_x,rel_y) for rel_x in ADJACENT_DIM_RANGE \
                                    for rel_y in ADJACENT_DIM_RANGE \
                                        if not ( rel_x == 0 and rel_y == 0 ) ]
BOARD_COORS = [ (coor_x,coor_y) for coor_x in range(BOARD_LENGTH)\
                                      for coor_y in range(BOARD_LENGTH) ]



####### create score grid
def getYardIndex( piece_type, reverse = False ):
    # get index from list
    yard_ind = PLAYER_LIST.index( piece_type )

    # apply conversion (only last 2 bits are significant)
    return ( yard_ind * YARD_INDEX_CONVERSION ) ^ ( REVERSE_YARD_INDEX * reverse )

def distanceToYard( piece_type, x_coor, y_coor ):
    yard_ind = getYardIndex( piece_type, reverse = True )
    x_compare = ( yard_ind & 1 > 0 ) * ( BOARD_LENGTH - 1 )
    y_compare = ( yard_ind & 2 > 0 ) * ( BOARD_LENGTH - 1 )
    DEPTH_IGNORANCE_FACTOR = 0#YARD_DEPTH + 1
    return max( abs( x_coor-x_compare ) + \
                  abs( y_coor-y_compare ) - \
                            DEPTH_IGNORANCE_FACTOR, 0 )

def createScoreGrid():
    grid_list = []
    for x_coor in range(BOARD_LENGTH):
        sub_list = []
        for y_coor in range(BOARD_LENGTH):
            sub_list.append( {} )
        grid_list.append( sub_list )

    for player in PLAYER_LIST:
        for x_coor,y_coor in BOARD_COORS:
            grid_list[x_coor][y_coor][ player ] = \
                        distanceToYard( player, x_coor, y_coor )
    return grid_list

SCORE_GRID = createScoreGrid()

def getGridSquareScore( coor, piece_type ):
    return SCORE_GRID[ coor[0] ][ coor[1] ][ piece_type ]



####################### Position object in Halma board #########################
class Position:
    def __init__( self, row, column, board ):
        self.row = row
        self.column = column
        self.board = board
        if self.board.root != None:
            self.canvas_instance = tkinter.Canvas( \
                                self.board.root, width=CANVAS_DIM, \
                                heigh=CANVAS_DIM, bg = "white" )
            self.canvas_instance.grid( row = row, column = column )
        self.piece_type = None

    def createPiece( self, piece_type ):
        self.piece_type = piece_type
        if self.board.root != None:
            self.oval_id = self.canvas_instance.create_oval( \
                0, 0, CANVAS_DIM, CANVAS_DIM, fill = self.piece_type, \
                tags = "pieceButton" )
            self.canvas_instance.tag_bind( self.oval_id, "<Button-1>", \
                                           self.clickPiece )

    def clickPiece( self, event ):
        # do not allow non-turn pieces to be selected
        if self.piece_type != self.board.piece_type_turn:
            return False
        prev = self.board.PREV_HILITE
        # do not allow a player to click an AI's piece
        if self.piece_type in AI_LIST:
            return False
        if prev is not None:
            prev.canvas_instance.itemconfig( prev.oval_id, \
                                             fill = prev.piece_type )
        self.canvas_instance.itemconfig( self.oval_id, fill = "red" )
        self.possibleMoves = self.board.getPossibleMoves( \
                                ( self.column, self.row ) )
        self.board.PREV_HILITE = self

        # clear all board options
        self.board.clearOptions()
        for move_coor in self.possibleMoves:
            new_pos_obj = self.board.position_dict[ move_coor ]
            new_oval_id = new_pos_obj.canvas_instance.create_rectangle( \
                            0, 0, CANVAS_DIM, CANVAS_DIM, \
                            fill = "yellow", tags = "next_move_button" )
            new_pos_obj.canvas_instance.tag_bind( \
                new_oval_id, "<Button-1>", \
                lambda event,new_pos_obj=new_pos_obj: \
                            self.movePiece( new_pos_obj ) )
            self.board.move_options.append( new_pos_obj )
            
    def movePiece( self, new_pos_obj ):
        if not self.board.isAvailable( (new_pos_obj.column,new_pos_obj.row ) ):
            print( "Attempting an illegal move" )
        else:
            self.board.total_plies += 1
            # clear all options
            self.board.clearOptions()
            # create new
            new_pos_obj.createPiece( piece_type = self.piece_type )

            # update score
            self.board.score_dict[ self.piece_type ] -= \
                                   self.getGridSquareScore( self.piece_type ) - \
                                   new_pos_obj.getGridSquareScore( self.piece_type )

            # delete oringal
            self.deletePiece()
            # get next turn
            self.board.nextTurn()

    def deletePiece( self ):
        if self.board.root != None:
            self.canvas_instance.delete( "pieceButton" )
        self.piece_type = None

    def deepCopy( self,new_board ):
        result = Position( self.row,self.column,new_board )
        result.piece_type = self.piece_type
        return result

    def getGridSquareScore( self, piece_type ):
        return getGridSquareScore( (self.column, self.row),piece_type )

############################## Board for halma game ############################
class Board:
    def __init__(self, N_POSITIONS=BOARD_LENGTH, set_root = True, \
                                                 add_agents = True ):
        self.total_plies = 0

        # skip initialization if not setting root
        if not set_root:
            self.root = None
            return None
        
        self.root = tkinter.Tk()        
        self.PREV_HILITE = None
        self.piece_type_turn = PLAYER_LIST[ 0 ] # start with first player
        self.move_options = []
        self.running_ai = False
        self.create_score_canvas()

        self.position_dict = dict()
        # create position in every row/column
        for row,column in BOARD_COORS:
            self.position_dict[ ( column, row ) ] \
                         = Position( row = row, column = column, board = self )

        for piece_type in PLAYER_LIST:
            # generate pieces in each yard corresponding to the piece_type
            for yard_coor in self.getYardList( piece_type ):
                self.position_dict[ yard_coor ].createPiece( piece_type )

        self.setScore()

        self.displayScore()
        self.ai_agents = [AI_Agent(self,piece_type) \
                                 for piece_type in AI_LIST]

        # create AI start button if start turn is an ai_agent
        if self.piece_type_turn in AI_LIST:
            self.createAIStartButton()
    
    def create_score_canvas( self ):
        self.score_canvas = tkinter.Canvas( \
                                self.root, width=CANVAS_DIM*BOARD_LENGTH, \
                                height=CANVAS_DIM, bg = "white" )
        self.score_canvas.grid( row = BOARD_LENGTH + 1, column = 0, \
                                columnspan = BOARD_LENGTH )

    # create button to begin game, starts in center of screen
    def createAIStartButton( self ):
        button_canvas = self.position_dict[ 
                        (BOARD_LENGTH//2,BOARD_LENGTH//2)].canvas_instance
        button_id = button_canvas.create_oval( \
                0, 0, CANVAS_DIM, CANVAS_DIM, fill = "grey", \
                tags = "startButton" )
        button_canvas.tag_bind( button_id, "<Button-1>", \
                                           self.startAI )

    # only call at beginning of game if fist player is AI_Agent
    def startAI( self, event ):
        button_canvas = self.position_dict[
                        (BOARD_LENGTH//2,BOARD_LENGTH//2 ) ].canvas_instance
        button_canvas.delete( "startButton" )
        # set turn to last player, move to next turn to initialize ai
        self.piece_type_turn = PLAYER_LIST[-1]
        self.nextTurn()

    # returns all possible moves given a start coordinate
    def getPossibleMoves( self, start_coor ):
        visited = set()
        self.getPossibleMovesHelper( start_coor, visited, jumping = False )
        return visited

    def getPossibleMovesHelper( self, wkg_coor, visited, jumping = False ):
        wkg_x,wkg_y = wkg_coor
        # skip if already visited
        for rel_x,rel_y in ADJACENT_POS_LIST:
            adj_coor = (wkg_x+rel_x,wkg_y+rel_y)
            if self.isAvailable( adj_coor ):
                if not jumping:
                    visited.add( adj_coor )
            else:
                jump_coor = (wkg_x+rel_x*2,wkg_y+rel_y*2)
                if jump_coor not in visited and self.isAvailable( jump_coor ):
                    visited.add( jump_coor )
                    self.getPossibleMovesHelper( jump_coor, visited, \
                                                 jumping = True )

    # returns false if position is filled, or position is not in boundaries
    def isAvailable( self, abs_coor ):
        pos_obj = self.position_dict.get( abs_coor )
        if pos_obj == None:
            return False
        return pos_obj.piece_type == None

    # checks a location contains a certain piece
    def containsType( self, test_coor, piece_type ):
        pos_obj = self.position_dict[ test_coor ]
        # return position object is not piece type
        return pos_obj.piece_type == piece_type

    # remove all options from the board
    def clearOptions( self ):
        if self.root != None:
            for pos_obj in self.move_options:
                pos_obj.canvas_instance.delete( "next_move_button" )
        self.moves_options = []

    def gameEnd( self ):
        for piece_type in PLAYER_LIST:
            # assume win until proven not
            piece_win = True
            for yard_coor in self.getYardList( piece_type, opposing = True ):
                # return false if incorrect piece
                if not self.containsType( yard_coor, piece_type ):
                    piece_win = False
                    break
            if piece_win:
                return piece_type
        return False

    # returns list of yard of the section_type
    # get opposing yard instead if opposing set to True
    #  yard_ind:
        # two bits: first bit sets x to right, second bit sets y to bottom
        #   ex: 01 -> left-bottom, 00 -> left-top
    def getYardList( self, section_type, opposing = False ):
        # get yard index, reversed if opposing
        yard_ind = self.getYardIndex( section_type, reverse = opposing )
        # x-range: YARD_DEPTH
        # y-range: 0 to ( yard_x + yard_y less than YARD_DEPTH )
        yard_list = [ ( yard_x, yard_y ) for yard_x in range( YARD_DEPTH + 1 ) \
                                for yard_y in range( 0, YARD_DEPTH - yard_x ) ]

        # flip x if last bit is set
        if yard_ind & 1:
            yard_list = [ ( BOARD_LENGTH - 1 - yard_x, yard_y ) \
                          for yard_x, yard_y in yard_list ]

        # flip y if second to last bit is set
        if yard_ind & 2:
            yard_list = [ ( yard_x, BOARD_LENGTH - 1 - yard_y ) \
                          for yard_x, yard_y in yard_list ]
            
        return yard_list

    # finds yardIndex based on the type of piece
    # converts player_list index to yard_index:
        # only last two bits are significant
        # index 0 -> yard 00        -> top left
        # index 1 -> yard 11        -> bottom right
        # index 2 -> yard (1)10     -> bottom left
        # index 3 -> yard (10)01    -> top right
    def getYardIndex( self, piece_type, reverse = False ):
        # get index from list
        yard_ind = PLAYER_LIST.index( piece_type )

        # apply conversion (only last 2 bits are significant)
        return ( yard_ind * YARD_INDEX_CONVERSION ) ^ \
                                   ( REVERSE_YARD_INDEX * reverse )

    def nextTurn( self ):
        newInd = ( PLAYER_LIST.index( self.piece_type_turn ) + 1 ) % \
                 len( PLAYER_LIST )
        self.piece_type_turn = PLAYER_LIST[ newInd ]
        if self.root != None:
            self.displayScore() # temporary
        # return false if running ai program
        if self.root == None or self.running_ai:
            return False

        self.running_ai = True
        while not self.gameEnd() and self.piece_type_turn in AI_LIST:
            self.perform_ai_turn()
        self.running_ai = False
        winner = self.gameEnd()
        if winner:
            print( f"Game end: winner = {winner}" )

    def perform_ai_turn( self ):
        if self.root == None:
            return False
        if self.piece_type_turn not in AI_LIST:
            return False

        # clear options and update before perrforming next turn
        self.clearOptions()
        self.root.update()
        ai_index = AI_LIST.index(self.piece_type_turn)
        ai_result = self.ai_agents[ai_index].getMove()
        try:
            best_start_coor,best_end_coor = ai_result
        except TypeError:
            print( "ai agent unable to find a move" )
            pdb.set_trace()
        best_start_obj = self.position_dict[ best_start_coor ]
        best_end_obj = self.position_dict[ best_end_coor ]
        best_start_obj.movePiece( best_end_obj )
        time.sleep(AI_DELAY)
        
    # linearly compare coordinates
    def linearCoorComp( self, start_coor, end_coor ):
        start_x,start_y = start_coor
        end_x,end_y = end_coor
        yard_ind = self.getYardIndex( self.piece_type_turn )
        # determine if maximizing x or y is beneficial
        max_x = yard_ind&1 == 0
        max_y = yard_ind&2 == 0
        # find differences
        x_dif = end_x - start_x
        y_dif = end_y - start_y
        # add results dependent on which values should be maximized
        result = 0
        if not max_y:
            y_dif *= -1
        if not max_x:
            x_dif *= -1
        return x_dif + y_dif

    def linearMoveComp( self, move_pair ):
        start_coor,end_coor = move_pair
        return self.linearCoorComp( start_coor, end_coor )

    def compareCoordinates( self, start_coor, end_coor, piece_type ):
        return self.minDistanceToYard( start_coor, piece_type ) - \
               self.minDistanceToYard( end_coor, piece_type )

    def minDistanceToYard( self, start_coor, piece_type ):
        min_distance = float("inf")
        yard_list = self.getYardList( piece_type, opposing = True )
        for test_yard_coor in yard_list:
            test_yard_pos = self.position_dict[ test_yard_coor ]
            if test_yard_pos.piece_type != piece_type:
                test_dist = distanceHeuristic( start_coor, test_yard_coor )
                if test_dist < min_distance:
                    min_distance = test_dist
        return min_distance

    def deepCopy( self ):
        result = Board( set_root = False, add_agents = False )
        result.piece_type_turn = self.piece_type_turn
        result.position_dict = dict()
        result.score_dict = self.score_dict.copy()
        for pos_coor,pos_obj in self.position_dict.items():
            result.position_dict[ pos_coor ] = pos_obj.deepCopy( result )
        return result

    def displayScore( self ):
        to_print = str()
        winner = self.gameEnd()
        for piece_type in PLAYER_LIST:
            #score = self.getBruteForceScore( piece_type )
            score = round(self.getBruteForceScore( piece_type ),2)
# test
            to_print += f" {piece_type}"
            if piece_type == self.piece_type_turn:
                to_print += f"(current)"
            to_print += f":{score} "
            if winner == piece_type:
                to_print += f" (winner) "
        # also display plies
        to_print += f" plies = {self.total_plies} "
        self.score_canvas.delete( "all" )
        self.score_canvas.create_text(CANVAS_DIM*BOARD_LENGTH/2,CANVAS_DIM/2, \
                                      text=to_print, \
                                      font=('Helvetica 15'), \
                                      justify = tkinter.CENTER )

    # reverse = None -> no sort
    # reverse = False -> low to high sort
    # reverse = True -> high to low sort
    def getAllPossibleMoves( self, reverse = None ):
        return_list = [ (start_coor,possible_move) \
                 for start_coor,start_obj in self.position_dict.items() \
                 if start_obj.piece_type == self.piece_type_turn \
                 for possible_move in self.getPossibleMoves( start_coor ) ]
        if reverse != None:
            return_list.sort( key = lambda coor_pair: \
                                self.linearMoveComp( \
                                    coor_pair ) ,reverse = reverse )
        return return_list

    def setScore( self ):
        self.score_dict = {}
        for player in PLAYER_LIST:
            player_score = 0
            for (x_coor,y_coor),pos_obj in self.position_dict.items():
                if pos_obj.piece_type == player:
                    player_score += SCORE_GRID[x_coor][y_coor][ player ]
            self.score_dict[ player ] = player_score

    def currentPlayerScore( self ):
        current_turn_score = self.score_dict[ self.piece_type_turn ]
        opposing_turn_score = 0
        for player in PLAYER_LIST:
            if player != self.piece_type_turn:
                opposing_turn_score += self.score_dict[ self.piece_turn ]
        return opposing_turn_score - current_turn_score

    def score( self, piece_type ):
        current_turn_score = self.score_dict[ piece_type ]
        opposing_turn_score = 0
        for player in PLAYER_LIST:
            if player != piece_type:
                opposing_turn_score += self.score_dict[ player ]
        return opposing_turn_score - current_turn_score


    # brute force algorithm to get score
        # ai algorithm instead uses relative positioning to determine score
    def getBruteForceScore( self, piece_type ):
        # get opposing yard_index
        yard_ind = self.getYardIndex( piece_type, reverse = True )
        total_score = 0
        # set comparison based on yard_index, 0 or BOARD_LENGTH
        x_compare = ( yard_ind & 1 > 0 ) * ( BOARD_LENGTH - 1 )
        y_compare = ( yard_ind & 2 > 0 ) * ( BOARD_LENGTH - 1 )
        for pos_x,pos_y in BOARD_COORS:
            pos_obj = self.position_dict[ (pos_x,pos_y) ]
            if pos_obj.piece_type == piece_type:
                total_score += max( ( abs( pos_x-x_compare ) ** 2 + \
                                abs( pos_y-y_compare ) ** 2 ) ** .5, 0 )
        return total_score

# heuristic function for distance between two coordinates
    # assumes grid-style layout, able to move one adjacent, including diagonal
    # both coordinates must have equal size
def distanceHeuristic( one_coor, other_coor ):
    coor_zip = zip( one_coor, other_coor )
    #return sum( abs( one_dim - other_dim ) for one_dim, other_dim in coor_zip )
    return max( abs( one_dim - other_dim ) for one_dim, other_dim in coor_zip )


######################## ai agent for halma game ###############################
class AI_Agent:
    def __init__( self, board, piece_type, recDepth = REC_DEPTH, \
                  minRecInc = MIN_REC_INCREMENT, \
                  applyTimeManagement = APPLY_TIME_MANAGEMENT ):
        self.piece_type = piece_type
        self.orig_board = board # reference
        self.resetsimulation()
        self.time_list = []
        self.REC_DEPTH = recDepth
        self.MIN_REC_INCREMENT = minRecInc
        self.APPLY_TIME_MANAGEMENT = applyTimeManagement

    def resetsimulation( self ):
        self.sim_board = self.orig_board.deepCopy()

    def getMove( self ):
        self.start_time = time.time()
        self.resetsimulation()
        self.iterationCountList = []
        self.last_iter_count = 0
        self.alphabeta_mode = True
        #best_score,best_move = self.alphabeta( self.sim_board, self.REC_DEPTH, \
        #                                       alphabeta_mode = self.alphabeta_mode )
        best_board,best_move = self.alphabeta( self.sim_board, self.REC_DEPTH )
        self.time_list.append( time.time() - self.start_time )
        self.displayTimeResults()
        
        # time management: modifies REC_DEPTH based on previous iteration's time
        if self.APPLY_TIME_MANAGEMENT:
            self.REC_DEPTH = getDepthFromTimes( self.time_list[-1], \
                                    MAX_TIME, self.REC_DEPTH, \
                                    self.last_iter_count, \
                                    self.last_total_children )
        return best_move

    def week_3_implementation_display( self ):
        print( f"\n{self.piece_type} with" + "out"*(not self.alphabeta_mode) + \
                                                " alphabeta mode ", end = "" )
        print( f"and depth {self.REC_DEPTH}: " )
        self.displayTimeResults()
        self.displayIterationTrackerResults()

    def displayTimeResults( self ):
        print( f"  Time: ", end = "" )
        print( f"Last={round(self.time_list[-1],3)}", end = ", " )
        print( f"Max={round(max( self.time_list),3)}", end=", " )
        #print( f"Min: {round(min( self.time_list),3 )}", end = ", " )
        total_time = sum( self.time_list )
        print( f"Total={round( total_time,3 )}", end = ", " )
        print( f"Average={round( total_time/len( self.time_list ),3)}" )

    def displayIterationTrackerResults( self ):
        print( f"  Iterations: ", end = "" )
        total_iter = sum( self.iterationCountList )
        print( f"Total={round( total_iter,3 )}", end = ", " )
        print( f"Average={round( total_iter/len( self.iterationCountList ),3)}" )

    
    def updateBoard( self, to_update, new_board ):
        to_update.piece_type_turn = new_board.piece_type_turn
        to_update.score_dict = new_board.score_dict.copy()
        to_update_dict = to_update.position_dict
        new_board_dict = new_board.position_dict
        for pos_coor in BOARD_COORS:
            # deep copy position if piece_types are not equal
            if to_update_dict[ pos_coor ].piece_type != \
                        new_board_dict[ pos_coor ].piece_type:
                to_update_dict[ pos_coor ] = \
                                new_board_dict[ pos_coor ].deepCopy( to_update )
            else:
                # always update position's parent board
                to_update_dict[ pos_coor ].board = to_update

    def getMovementScore( self, current_board, start_coor, end_coor ):
        score_mod = current_board.linearCoorComp( start_coor, end_coor )
        # reverse score if opponent
        if current_board.piece_type_turn != self.piece_type:
            score_mod *= -1
        return score_mod


    def alphabeta( self, parent_board, remaining_depth, \
                   alpha = ALPHA_START, beta = BETA_START, \
                   player_sign = 1 ):
        iterationCount = 0
        best_score = float("-inf") * player_sign
        best_move = None
        agent_turn = player_sign == 1
        
        if parent_board.gameEnd():
            return -player_sign * self.maxScore( remaining_depth ),None

        if remaining_depth <= random.random():
            return parent_board.score( self.piece_type ),None

        child_board = parent_board.deepCopy()

        all_moves = parent_board.getAllPossibleMoves( reverse = True )

        if remaining_depth == self.REC_DEPTH:
            self.last_total_children = len( all_moves )

        if remaining_depth <= 1 + random.random():
            best_start,best_end = all_moves[0]
            child_board.position_dict[ best_start ].movePiece( \
                child_board.position_dict[ best_end ] )
            return child_board.score( self.piece_type ), (best_start,best_end)
        
        for start_coor,end_coor in all_moves:
            if remaining_depth == self.REC_DEPTH:
                self.last_iter_count += 1
            iterationCount += 1

            self.updateBoard( child_board, parent_board )
            child_start_pos_obj = child_board.position_dict[ start_coor ]
            child_end_pos_obj = child_board.position_dict[ end_coor ]
            child_start_pos_obj.movePiece( child_end_pos_obj )

            if time.time() + TIME_TO_EXIT > self.start_time + MAX_TIME:
                print( f"ran out of time at {time.time() - self.start_time}" )
                return best_score,best_move

            if parent_board.score_dict[ parent_board.piece_type_turn ] - \
                child_board.score_dict[ parent_board.piece_type_turn ] < \
                                       MIN_REC_INCREMENT:
                continue
                    
            test_score,test_move = self.alphabeta( child_board, \
                                                    remaining_depth - 1, \
                                                    alpha = alpha, \
                                                    beta = beta, \
                                                    player_sign = -player_sign \
                                                    )
            if test_score == float("inf") or test_score == float("-inf"):
                continue


            if agent_turn:
                if test_score > best_score:
                    best_score = test_score
                    best_move = (start_coor,end_coor)
                if best_score >= beta:
                    break
                alpha = max( alpha, best_score )
            else:
                if test_score < best_score:
                    best_score = test_score
                    best_move = (start_coor,end_coor)
                if best_score <= alpha:
                    break
                beta = min( beta, best_score )

        return best_score,best_move    

    # max possible score based on remaining recursion depth
    def maxScore( self, remaining_depth ):
        return BOARD_LENGTH ** 2 * CURRENT_PRIORITY ** remaining_depth








################################### TIME_MANAGEMENT ############################
# get depth due to time and node completion
def getDepthFromTimes( used_time, target_time, old_depth, \
                               attempted_children, total_children, \
                               verbose = True ):
    if verbose:
        print( f"\noriginal depth = {old_depth}" )
        print( f"  used_time: {used_time}" )
        print( f"  attempted_children: {attempted_children}" )
        print( f"  total_children: {total_children}" )
    target_time *= TARGET_TIME_MULTIPLIER
    old_depth_base = int( old_depth )
    old_depth_excess = old_depth - old_depth_base
    
    # case did not attempt all children
    if attempted_children < total_children:
        children_ratio = attempted_children / total_children
        actual_depth_excess = children_ratio * old_depth_excess
        actual_depth = old_depth_base + actual_depth_excess
    else:
        actual_depth = old_depth
    # end identification of actual_depth:
    #   all variables are independent of above depths (excluding actual_depth)
    
    # convert depth_value to linear
    linear_depth = expDepthToLineDepth( actual_depth, total_children )

    # linear decrease if attempted_children requirements are not met
    if attempted_children < total_children:
        linear_depth *= attempted_children / total_children

    # find target_linear_depth
    target_used_time_ratio = target_time / used_time
    linear_target = linear_depth * target_used_time_ratio

    # convert linear target to exponential
    exp_target = lineDepthToExpDepth( linear_target, total_children )
    if verbose:
        print( f"modified depth = {exp_target}" )
    return exp_target

# converts exponential depth to linear depth
def expDepthToLineDepth( exp_depth, expand_rate ):
    line_depth = 0
    wkg_converter = 1.0
    while exp_depth > 1:
        line_depth += wkg_converter
        exp_depth -= 1
        wkg_converter *= expand_rate
    # multiply remaining depth by wkg_converter
    line_depth += exp_depth * wkg_converter
    return line_depth

# converts linear depth to exponential depth
def lineDepthToExpDepth( line_depth, expand_rate ):
    exp_depth = 0
    wkg_converter = 1.0
    while line_depth > wkg_converter:
        line_depth -= wkg_converter
        exp_depth += 1
        wkg_converter *= expand_rate
    # add remaining ratio to exp_depth
    exp_depth += line_depth / wkg_converter
    return exp_depth
        

if __name__ == "__main__":
    board_instance = Board( set_root = True )
    board_instance.root.mainloop()















