import time
import curses
import os
from random import shuffle
import RPi.GPIO as GPIO


def main():

    # 7 tetraminos
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

    # input pins, and last input states
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

    # current piece
    piece = []
    # piece index of upcoming piece
    preview = -1
    # "bag" for bag randomizer, one of each 7 pieces are put in the bag, then everytime the player needs a new piece, it is taken out of the bag.
    # When the bag is empty, it is filled again. This is the modern standard for making more fair random piece generation in tetris
    bag = []

    # game grid
    grid = []

    # current piece offset
    curX = 3
    curY = 0

    # delay before piece can be manually dropped again
    dropDelay = 0

    # initialize printing
    stdscr = curses.initscr()
    curses.noecho()
    curses.cbreak()

    # setup GPIO
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(rightKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(leftKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CWKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(CCWKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(dropKey, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # create empty grid
    for i in range(20):
        grid.append([])
        for j in range(10):
            grid[i].append(False)

    # places the current piece in the grid, and tries to clear lines
    def place(matrix):
        for y in range(len(matrix)):
            for x in range(len(matrix)):
                if matrix[y][x] == True:
                    grid[y + curY][x + curX] = True
        clearLines()

    # clears any complete rows
    def clearLines():
        for y in range(20):
            full = True
            # stop if row isn't complete
            for x in range(10):
                if grid[y][x] == False:
                    full = False
                    break
            # if it is complete, shift above rows down by one
            if full == True:
                for x in range(10):
                    grid[y][x] = False
                for y2 in range(y, 0, -1):
                    for x in range(10):
                        grid[y2][x] = grid[y2-1][x]

    # refills the bag for randomizing pieces
    def fillBag():
        for i in range(7):
            bag.append(i)
        shuffle(bag)

    # returns a matrix with side length n rotated clockwise
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

    # returns a matrix with side length n rotated counter clockwise
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

    # returns true if piece is out of bounds, or touching blocks in the grid
    def colliding():
        for y in range(len(piece)):
            for x in range(len(piece)):
                if piece[y][x] == True:
                    if y + curY < 0 or y + curY > 19 or x + curX < 0 or x + curX > 9:
                        return True
                    if grid[y + curY][x + curX] == True:
                        return True

    # initialize pieces
    fillBag()
    preview = bag.pop()

    # main game loop
    while playing:
        time.sleep(0.016)
        frame += 1

        # gravity
        if frame % 60 == 0:
            curY += 1
            if colliding():
                curY -= 1
                place(piece)
                piece = []
                curX = 3
                curY = 0
                dropDelay = 20

        # use next piece if current one has been placed
        if len(piece) == 0:
            piece = pieces[preview]
            if len(bag) > 0:
                preview = bag.pop()
            else:
                fillBag()
                preview = bag.pop()

        # move right
        if GPIO.input(rightKey) == False:
            if rightKeyLast == True:
                curX += 1
                if colliding():
                    curX -= 1
                rightKeyLast = False
        else:
            rightKeyLast = True

        # move left
        if GPIO.input(leftKey) == False:
            if leftKeyLast == True:
                curX -= 1
                if colliding():
                    curX += 1
                leftKeyLast = False
        else:
            leftKeyLast = True

        # rotate clockwise
        if GPIO.input(CWKey) == False:
            if CWKeyLast == True:
                piece = rotCW(piece, len(piece))
                if colliding():
                    piece = rotCCW(piece, len(piece))
                CWKeyLast = False
        else:
            CWKeyLast = True

        # rotate counter clockwise
        if GPIO.input(CCWKey) == False:
            if CCWKeyLast == True:
                piece = rotCCW(piece, len(piece))
                if colliding():
                    piece = rotCW(piece, len(piece))
                CCWKeyLast = False
        else:
            CCWKeyLast = True

        # drop piece quicker
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

        # print game
        lines = []
        for y in range(20):
            lines.append([])
            # left wall
            lines[y].append("| ")
            # grid
            for x in range(10):
                if grid[y][x] == True:
                    lines[y].append("# ")
                else:
                    lines[y].append("` ")
            # right wall
            lines[y].append("|")
        # draw piece
        for y in range(len(piece)):
            for x in range(len(piece)):
                if piece[y][x]:
                    if y+curY > -1 and y+curY < 20 and (x+curX) + 1 > 0 and (x+curX) + 1 < 11:
                        lines[y+curY][(x+curX) + 1] = "# "
        # draw preview
        if len(bag) > 0:
            pre = pieces[preview]
            for y in range(len(pre)):
                for x in range(len(pre)):
                    if pre[y][x] == True:
                        lines[y+1].append(" #")
                    else:
                        lines[y+1].append("  ")

        # render to console
        for y in range(20):
            line = ""
            for x in lines[y]:
                line += x
                stdscr.addstr(y, 0, line + "  ")
        stdscr.refresh()

    input("I dont think this does anything but I dont want to delete it")


# do the game
main()
