import time
import curses
import os
from random import shuffle
import RPi.GPIO as GPIO 

def main():
    pieces = [
        [
            [False, False, False, False],
            [True, True, True, True],
            [False, False, False, False],
            [False, False, False, False],
        ],
        [
            [False, False, False, False],
            [False, True, True, False],
            [False, True, True, False],
            [False, False, False, False],
        ],
        [
            [True, False, False],
            [True, True, True],
            [False, False, False]
        ],
        [
            [False, False, True],
            [True, True, True],
            [False, False, False]
        ],
        [
            [False, True, True],
            [True, True, False],
            [False, False, False]
        ],
        [
            [True, True, False],
            [False, True, True],
            [False, False, False]
        ],
        [
            [False, True, False],
            [True, True, True],
            [False, False, False]
        ]
    ]

    pieceNames = [
        "i",
        "o",
        "j",
        "l",
        "s",
        "z",
        "t"
    ]
    
    leftKey = 22
    leftKeyLast = True
    
    rightKey = 27
    rightKeyLast = True
    
    CWKey = 10
    CWKeyLast = True
    
    CCWKey = 9
    CCWKeyLast = True
    
    dropKey = 11
    
    playing = True
    frame = 0

    piece = []
    preview = -1
    bag = []

    grid = []

    curX = 3
    curY = 0

    dropDelay = 0

    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()

    
    GPIO.setwarnings(False) 
    GPIO.setmode(GPIO.BCM) 
    GPIO.setup(rightKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(leftKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CWKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CCWKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(dropKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    for i in range(20):
        grid.append([])
        for j in range(10):
            grid[i].append(False)

    def place(matrix):
        for y in range(len(matrix)):
            for x in range(len(matrix)):
                if matrix[y][x] == True:
                    grid[y + curY][x + curX] = True
        clearLines()
        
    def clearLines():
        for y in range(20):
            full = True
            for x in range(10):
                if grid[y][x] == False:
                    full = False
                    break
            if full == True:
                for x in range(10):
                    grid[y][x] = False
                for y2 in range(y,0,-1):
                    for x in range(10):
                        grid[y2][x] = grid[y2-1][x]
    
    def fillBag():
        for i in range(7):
            bag.append(i)
        shuffle(bag)

    def rotCW(matrix, n):
        ret = []
        for i in range(n):
            ret.append([])
            for j in range(n):
                ret[i].append(False)
        for i in range(n):
            for j in range(n):
                ret[i][j] = matrix[n - j - 1][i]

        return ret

    def rotCCW(matrix, n):
        ret = []
        for i in range(n):
            ret.append([])
            for j in range(n):
                ret[i].append(False)
        for i in range(n):
            for j in range(n):
                ret[i][j] = matrix[j][n - i - 1]
        return ret
    
    def colliding():
        for y in range(len(piece)):
            for x in range(len(piece)):
                if piece[y][x] == True:
                    if y + curY < 0 or y + curY > 19 or x + curX < 0 or x + curX > 9:
                        return True
                    if grid[y + curY][x + curX] == True:
                        return True
    fillBag()
    preview = bag.pop()
    while playing:
        time.sleep(0.016)
        frame += 1
        if frame % 60 == 0:
            curY += 1
            if colliding():
                curY -= 1
                place(piece)
                piece = []
                curX = 3
                curY = 0
                dropDelay = 20

        if len(piece) == 0:
            piece = pieces[preview]
            if len(bag) > 0:
                preview = bag.pop()
            else:
                fillBag()
                preview = bag.pop()

        if GPIO.input(rightKey) == False:
            if rightKeyLast == True:
                curX += 1
                if colliding():
                    curX -= 1
                rightKeyLast = False
        else:
            rightKeyLast = True
            
        if GPIO.input(leftKey) == False:
            if leftKeyLast == True:
                curX -= 1
                if colliding():
                    curX += 1
                leftKeyLast = False
        else:
            leftKeyLast = True
            
        if GPIO.input(CWKey) == False:
            if CWKeyLast == True:
                piece = rotCW(piece, len(piece))
                if colliding():
                    piece = rotCCW(piece, len(piece))
                CWKeyLast = False
        else:
            CWKeyLast = True
            
        if GPIO.input(CCWKey) == False:
            if CCWKeyLast == True:
                piece = rotCCW(piece, len(piece))
                if colliding():
                    piece = rotCW(piece, len(piece))
                CCWKeyLast = False
        else:
            CCWKeyLast = True
            
        if GPIO.input(dropKey) == False and dropDelay <= 0:
            curY += 1
            if colliding():
                curY -= 1
                place(piece)
                piece = []
                curX = 3
                curY = 0
                dropDelay = 20
        else:
            dropDelay -= 1
        # print    
        lines = []
        for y in range(20):
            lines.append([])
            lines[y].append("| ")
            for x in range(10):
                if grid[y][x] == True:
                    lines[y].append("# ")
                else:
                    lines[y].append("` ")
            lines[y].append("|")
        for y in range(len(piece)):
            for x in range(len(piece)):
                if piece[y][x]:
                    if y+curY > -1 and y+curY < 20 and (x+curX) + 1 > 0 and (x+curX) + 1 < 11:
                        lines[y+curY][(x+curX) + 1] = "# "
        if len(bag) > 0:
            pre = pieces[preview]
            for y in range(len(pre)):
                for x in range(len(pre)):
                    if pre[y][x] == True:
                        lines[y+1].append(" #")
                    else:
                        lines[y+1].append("  ")
                
        for y in range(20):
            line = ""
            for x in lines[y]:
                line += x
                stdscr.addstr(y, 0, line + "  ")
        stdscr.refresh()
    input("lol")


main()
