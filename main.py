import sys
from queue import LifoQueue, Queue
import API
import location
import state
import time
import os

MAZE_WIDTH = 16
MAZE_HEIGHT = 16
cur_direction = 0
cur_position = [0, 0]
maze = [[location.Location([i, j]) for j in range(0, MAZE_WIDTH)] for i in range(0, MAZE_HEIGHT)]
loc_stack = LifoQueue()
dir_stack = LifoQueue()
act_stack = LifoQueue()
frontier = Queue()
def pos_update(move_direction=1):
    global cur_position
    if cur_direction == 0: 
        cur_position[1] = cur_position[1] + move_direction
    elif cur_direction == 1: 
        cur_position[0] = cur_position[0] + move_direction
    elif cur_direction == 2: 
        cur_position[1] = cur_position[1] - move_direction
    elif cur_direction == 3:
        cur_position[0] = cur_position[0] - move_direction

def direction_update(turn_direction):
    global cur_direction 
    cur_direction = (cur_direction + turn_direction) % 4

def wall_check():
    walls = [False, False, False, False]
    walls[cur_direction] = API.wallFront() 
    walls[(cur_direction + 1) % 4] = API.wallRight() 
    walls[(cur_direction + 2) % 4] = False  
    walls[(cur_direction + 3) % 4] = API.wallLeft()  
    if cur_position == [0, 0]: 
        walls[2] = True
    return walls



def spoted_maze(pos=None):
    if pos is None:
        pos = cur_position
    API.setColor(pos[0], pos[1], "k")
    API.setText(pos[0], pos[1], "RUN")  

def mark_solution_api(pos=None):
    if pos is None:
        pos = cur_position
    API.setColor(pos[0], pos[1], "b")
    API.setText(pos[0], pos[1], "SOL")

def maze_runner(pos=None):
    if pos is None:
        pos = cur_position
    API.setColor(pos[0], pos[1], "c")
    API.setText(pos[0], pos[1], "NUL")

def blank(pos=None):
    if pos is None:
        pos = cur_position
    API.setColor(pos[0], pos[1], "o")
    API.setText(pos[0], pos[1], "BLN")

def log(string):
    sys.stderr.write("{}\n".format(string))
    sys.stderr.flush()

def move_forward():
    API.moveForward()  
    pos_update(+1)  

def turn_left():
    API.turnLeft()
    direction_update(-1)  

def turn_right():
    API.turnRight()
    direction_update(+1)  

def turn_around():
    turn_right()
    turn_right()

def set_dir(_dir):
    if _dir == cur_direction:  
        return
    if _dir == (cur_direction + 1) % 4:  
        turn_right()
        return
    if _dir == (cur_direction + 2) % 4:  
        turn_right()
        turn_right()
        return
    turn_left()  
    return

def turn_toward(loc):
    _dir = cur_direction
    
    if cur_position[0] == loc.position[0]:  
        if cur_position[1] - loc.position[1] == 1:  
            _dir = 2
        else:  
            _dir = 0
    else:  
        if cur_position[0] - loc.position[0] == 1:  
            _dir = 3
        else:  
            _dir = 1
    set_dir(_dir)

def GPS():
    cur_loc = maze[cur_position[0]][cur_position[1]]  
    if not cur_loc.visited:  
        cur_loc.set_visited(True)  
        cur_loc.set_walls(wall_check())  
        spoted_maze(cur_position)  
        
        if not cur_loc.walls[0] and not maze[cur_position[0]][cur_position[1] + 1].visited:
            loc_stack.put(maze[cur_position[0]][cur_position[1] + 1])
        
        if not cur_loc.walls[1] and not maze[cur_position[0] + 1][cur_position[1]].visited:
            loc_stack.put(maze[cur_position[0] + 1][cur_position[1]])
        
        if not cur_loc.walls[2] and not maze[cur_position[0]][cur_position[1] - 1].visited:
            loc_stack.put(maze[cur_position[0]][cur_position[1] - 1])

        if not cur_loc.walls[3] and not maze[cur_position[0] - 1][cur_position[1]].visited:
            loc_stack.put(maze[cur_position[0] - 1][cur_position[1]])

    while True:  
        if loc_stack.empty():  
            if not cur_position == [0, 0]:
                set_dir((dir_stack.get() + 2) % 4)  
                move_forward()
                GPS()  
            return
        next_loc = loc_stack.get()  
        if not next_loc.visited:
            break

    if cur_loc.can_move_to(next_loc):
        turn_toward(next_loc)
        dir_stack.put(cur_direction)  
        move_forward()
    else:   
        loc_stack.put(next_loc)
        set_dir((dir_stack.get() + 2) % 4)  
        move_forward()
    GPS()  

def solve():
    
    for i in range(0, MAZE_HEIGHT):
        for j in range(0, MAZE_WIDTH):
            maze[i][j].visited = False;
    first_state = state.State(maze[0][0])  
    frontier.put(first_state)   
    
    while not frontier.empty():
        next_state = frontier.get()          
        maze[next_state.location.position[0]][next_state.location.position[1]].set_visited(True)
        maze_runner(next_state.location.position)  
        if next_state.is_goal():  
            return next_state    
        
        my_loc = next_state.location
        if not my_loc.walls[0]:
            north_loc = maze[my_loc.position[0]][my_loc.position[1] + 1]
        if not my_loc.walls[1]:
            east_loc  = maze[my_loc.position[0] + 1][my_loc.position[1]]
        if not my_loc.walls[2]:
            south_loc = maze[my_loc.position[0]][my_loc.position[1] - 1]
        if not my_loc.walls[3]:
            west_loc  = maze[my_loc.position[0] - 1][my_loc.position[1]]
        
        if not my_loc.walls[0] and my_loc.can_move_to(north_loc) and not north_loc.visited:
            
            north_state = state.State(north_loc, next_state, (0 - next_state.cur_dir) % 4, 0)
            frontier.put(north_state)  
        
        if not my_loc.walls[1] and my_loc.can_move_to(east_loc) and not east_loc.visited:
            
            east_state = state.State(east_loc, next_state, (1 - next_state.cur_dir) % 4, 1)
            frontier.put(east_state)  
    
        if not my_loc.walls[2] and my_loc.can_move_to(south_loc) and not south_loc.visited:
            
            south_state = state.State(south_loc, next_state, (2 - next_state.cur_dir) % 4, 2)
            frontier.put(south_state)  
    
        if not my_loc.walls[3] and my_loc.can_move_to(west_loc) and not west_loc.visited:
            
            west_state = state.State(west_loc, next_state, (3 - next_state.cur_dir) % 4, 3)
            frontier.put(west_state)  


def load_solved(sol):
    while sol.parent is not sol:    
        act_stack.put(sol.action)   
        blank(sol.location.position)  
        sol = sol.parent    
    while not act_stack.empty():    
        act = act_stack.get()
        mark_solution_api()  
        if act == 1:
            turn_right()
        elif act == 3:
            turn_left()
        move_forward()

def banner():
        os.system('clear')
        banner = r'''                                                
 ____        _         _____         _           
|    \ ___ _| |___ ___|     |___ ___| |_ ___ _ _ 
|  |  | . | . | . | -_| | | | . |   | '_| -_| | |
|____/|___|___|_  |___|_|_|_|___|_|_|_,_|___|_  |
              |___|                         |___|                                                                                                                                     
'''

def main():
    log(" ____        _         _____         _ ")
    log("|    \ ___ _| |___ ___|     |___ ___| |_ ___ _ _ ")
    log("|  |  | . | . | . | -_| | | | . |   | '_| -_| | |")
    log("|____/|___|___|_  |___|_|_|_|___|_|_|_,_|___|_  |")
    log("              |___|                         |___|")
    log("Running..." )
    start = time.time()
    GPS()  
    set_dir(0) 
    end = time.time() 
    log("Maze Solved within "+ str(end-start) + " seconds" )    
    end = time.time()  
    solution = solve()  
    load_solved(solution) 
    end1 = time.time()  
    log("Exit Path Travelled within "+ str(end1-end) + " seconds" ) 


if __name__ == "__main__":
    main()
