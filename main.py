import socket
import sys
import curses
import time
import logging

logging.basicConfig(filename='debug.log', level=logging.DEBUG)
logging.info('---------------------')

MAX_COL = 7
MAX_ROW = 6
HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

network = True
board = [['-' for _ in range(MAX_ROW)] for _ in range(MAX_COL)]
heights = [0 for _ in range(MAX_COL)]

logging.info(board)
logging.info(heights)

def print_board(screen, selected_col=None):
    screen.clear()
    for row in range(MAX_ROW):
        for col in range(MAX_COL):
            screen.addch(MAX_ROW - row, col * 2, curses.ACS_VLINE)
            screen.addch(MAX_ROW - row, col * 2 + 1, board[col][row])
        screen.addch(MAX_ROW - row, MAX_COL * 2, curses.ACS_VLINE)
    if selected_col is not None:
        screen.addch(MAX_ROW + 1, selected_col * 2 + 1, '^')
    screen.refresh()


def is_aligned(played_col, played_row):
    logging.info(f'{played_col} {played_row}')
    win_chain = board[played_col][played_row] * 4
    logging.info(f'win chain: {win_chain}')
    
    def is_horizontally_aligned():
        row_chain = ''.join([board[col][played_row] for col in range(MAX_COL)])
        logging.info(f'row chain: {row_chain}')
        return win_chain in row_chain

    def is_vertically_aligned():
        col_chain = ''.join([board[played_col][row] for row in range(played_row + 1)])
        logging.info(f'col chain: {col_chain}')
        return win_chain in col_chain

    def is_diagonally_aligned():
        start_row, start_col = max(0, played_row - played_col), max(0, played_col - played_row)
        logging.info(f'diag right: start_row={start_row}, start_col={start_col}')
        diag_righ_chain = ''.join([board[start_col + i][row] for i, row in enumerate(range(start_row, MAX_ROW)) if start_col + i < MAX_COL])
        logging.info(f'diag right chain: {diag_righ_chain}')
        start_col = min(MAX_COL - 1, played_col + played_row)
        start_row = max(0, played_row - (played_col - start_col))
        diag_left_chain = ''.join([board[start_col - i][row] for i, row in enumerate(range(start_row, MAX_ROW)) if start_col - i >= 0])
        logging.info(f'diag left chain: {diag_left_chain}')
        return win_chain in diag_righ_chain or win_chain in diag_left_chain

    return is_horizontally_aligned() or is_vertically_aligned() or is_diagonally_aligned()


def add_disc_to_board(player, col):
    board[col][heights[col]] = 'x' if player == 1 else 'o'
    heights[col] += 1
    return is_aligned(col, heights[col] - 1)


def select_col(screen):
    col = 1
    while True:
        cmd = screen.getch()
        if cmd == curses.KEY_ENTER or cmd == 10:
            break
        if cmd == curses.KEY_RIGHT and col < MAX_COL - 1:
            col += 1
        elif cmd == curses.KEY_LEFT and col > 0:
            col -= 1
        print_board(screen, col)
    return col


def game(screen):
    curses.curs_set(0)
    print_board(screen)

    if len(sys.argv) > 1:
        server = sys.argv[1] == 'server'
        if not server:
            ip_to_join = sys.argv[2]
            port_to_join = int(sys.argv[3])

    if network:
        if server:
            player = 1
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # IPv4 TCP socket
                s.bind((HOST, PORT))  # associate the socket with a network interface and port to listen on
                s.listen()  # enable the server to accept connections
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    while True:
                        selected_col = select_col(screen)
                        conn.sendall(bytes(str(selected_col).encode('utf8')))
                        end = add_disc_to_board(player, selected_col)
                        print_board(screen)
                        if end:
                            logging.info(f'Player {player} win')
                            screen.addstr(f'Player {player} win')
                            break
                        data = conn.recv(1024)
                        if not data:
                            break
                        else:
                            played_col = int(data.decode('utf8'))
                            add_disc_to_board(2, played_col)
                            print_board(screen)
                        # conn.sendall(data)
        else:
            player = 2
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((ip_to_join, port_to_join))
                while True:
                    data = s.recv(1024)
                    played_col = int(data.decode('utf8'))
                    add_disc_to_board(1, played_col)
                    print_board(screen)
                    selected_col = select_col(screen)
                    s.sendall(bytes(str(selected_col).encode('utf8')))
                    end = add_disc_to_board(player, selected_col)
                    print_board(screen)
                    if end:
                        logging.info(f'Player {player} win')
                        screen.addstr(f'Player {player} win')
                        break


curses.wrapper(game)
print(board)
