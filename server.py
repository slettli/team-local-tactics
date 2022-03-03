from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
import pickle

from core import Champion, Match, Shape, Team
from champlistloader import load_some_champs

player1 = [] # Player 1's team
player2 = [] # Player 2's team

# TODO Handle playing the match using core, return result
def play_match():
    pass

# Pickle and send whatever to client
def send_client(sock,conn,_,load):
    pickled = pickle.dumps(load) #always pickle
    conn.send(pickled)
    print(f'Sent response to client {_}, showing the unpickled format:\n{load}\n')

# Add selected champion to a player's team
def add_to_team(player,champion):
    if player == 'Player 1':
        player1.append(champion)
    else:
        player2.append(champion)
    print(f"Added {champion} to {player}'s team\n")

# Receive input from clients and call appropriate methods
# Send reply to client
def server_command(sock,conn,_,command,load):
    match (command):
        case 'champions': # Get dict of champions and encode with pickle
            print('Champion list requested')
            send_client(sock,conn,_,load_some_champs())
        case 'teams': # Get list of current teams - player1 and player2 arrays
            print('Team lists requested')
            send_client(sock,conn,_,(player1,player2)) # Return pickled tuple of player teams
        case 'select':
            print('Adding to team requested')
            add_to_team(load[0],load[1])
            send_client(sock,conn,_,"OK") # Use 200 instead?
        case 'play': # Play match, return result
            pass

# Main thread to manage functionality
def main():
    # Initialize TCP socket and listen
    with socket() as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('localhost', 6666))
        sock.listen() # Should this be inside the loop?
        print('Welcome to the TNT super early access indiegogo crowdfund server.\n')

        while True: # Network loop
            print(f'Listening at {sock.getsockname()}\n')
            # Get command and forward to server_command
            # Data will always be sent as an array consisting of command,data
            conn, _ = sock.accept()
            received = pickle.loads(conn.recv(1024))
            print(f'Received request from {_}:\n{received}\n')
            command = received[0]
            load = received[1]

            # Quit and shut down server if requested, else handle command
            if command == 'quit': 
                print('Shutdown request received.')
                send_client(sock,conn,_,"Bye") # Change to appropriate code
                conn.close()
                print('Connection closed. Shutting down.')
                break
            else:
                server_command(sock,conn,_,command,load)

if __name__ == '__main__':
    main()