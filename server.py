from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
import pickle

from core import Champion, Match, Shape, Team
from champlistloader import load_some_champs

player1 = [] 
player2 = []

# Handle playing the match using core, return result
def play_match():
    pass

# Pickle and send whatever to client
def send_client(sock,conn,load):
    load = pickle.dumps(load) #always pickle
    conn.send(load)
    print(f'Sent response to client:\n{load}')

# Receive input from clients and call appropriate methods, return formatted reply to main()
def server_command(sock,conn,command):
    match (command):
        case 'champions': # Get dict of champions and encode with pickle
            print('Champion list requested')
            send_client(sock,conn,load_some_champs())
        case 'teams':
            print('Team lists requested')
            send_client(sock,conn,(player1,player2)) # Return pickled tuple of player teams
        case 'play': # Play match, return result
            pass

# Add selected champion to a player's team
def add_to_team(player,champion):
    if player == 'Player 1':
        player1.append(champion)
    else:
        player2.append(champion)

# Main thread to manage functionality
# TODO make it loop until asked to exit
def main():
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(('localhost', 6666))
    sock.listen() # Should this be inside the loop?

    while True: # Network loop

        # Initialize TCP socket and listen
        print("Listening...")
        # Get command and forward to server_command
        # Data will always be sent as an array consisting of command,data
        conn, _ = sock.accept()
        received = pickle.loads(conn.recv(1024))
        print(received)
        command = received[0]
        print(command)
        load = received[1]
        print(load)

        # Quit if desired, will shut down server
        if command == 'quit': 
            print('Server shutting down...')
            conn.close()
            print('Connection closed. Quitting.')
            break
        elif command == 'teams' or command == 'champions': # Simply return teams
            server_command(sock,conn,command)
        elif command == 'select': # Add player selection to array
            add_to_team(load[0],load[1])



if __name__ == '__main__':
    main()