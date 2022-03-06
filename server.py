from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
from database import load_some_champs

from core import Champion, Match, Shape, Team

# Used to prevent more than two clients connecting. Possibly shouldn't be global, or two bools.
P1_CONNECTED = False
P2_CONNECTED = False

P1_TEAM = [] # Player 1's team
P2_TEAM = [] # Player 2's team

# TODO Handle playing the match using core, return result
def play_match():
    pass

# Helper function for getting champions specifically. Returns champions
def load_some_champs():
    with socket() as sock:
        DB_ADDRESS = ("localhost", 5556)
        sock.connect(DB_ADDRESS)
        print(f'Connected to server {sock.getpeername()}')
        champs= send_command(sock,"GET_CHAMPS")

    return champs # Return reply, HOPEFULLY CHAMPS

# Used to send command when server acts as client, like with database
def send_command(sock,command,data=''):
    sock.send(pickle.dumps((command,data))) # Always pickle
    return pickle.loads(sock.recv(1024)) # Return reply

# Pickle and send whatever to client or database. Yeah, bad name for the function.
def send_client(sock,conn,_,load):
    pickled = pickle.dumps(load) #always pickle
    conn.send(pickled)
    print(f'Sent data to {_}, showing the unpickled format:\n{load}\n')

# Add selected champion to a player's team
def add_to_team(player,champion):
    if player == 'Player 1':
        P1_TEAM.append(champion)
    else:
        P2_TEAM.append(champion)
    print(f"Added {champion} to {player}'s team\n")

# Receive input from clients and call appropriate methods
# Send reply to client
def server_command(sock,conn,_,command,load):
    global NUM_PLAYERS, MAX_PLAYERS, P1_TEAM, P2_TEAM

    match (command):
        case 'connect': # New client connects. Check if player slot available, return error or player ID to client
            if P1_CONNECTED == False:
                send_client(sock,conn,_,"Player 1")
            elif P2_CONNECTED == False:
                send_client(sock,conn,_,"Player 2")
            else:
                send_client(sock,conn,_,"FULL") # Tell client server is full
        case 'disconnect': # Mark player slot as open, wipe corresponding player's team
            if load == "Player 1":
                P1_TEAM = []
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
            elif load == "Player 2":
                P2_TEAM = [] # Player 2's team
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
        case 'champions': # Get dict of champions and encode with pickle
            print('Champion list requested')
            send_client(sock,conn,_,load_some_champs())
        case 'teams': # Get list of current teams - player1 and player2 arrays
            print('Team lists requested')
            send_client(sock,conn,_,(P1_TEAM,P2_TEAM)) # Return pickled tuple of player teams
        case 'select':
            print('Adding to team requested')
            add_to_team(load[0],load[1])
            send_client(sock,conn,_,"OK") # Use 200 instead?
        case 'play': # Play match, return result
            pass
        case 'teamreset': # Reset teams 
            P1_TEAM = []
            P2_TEAM = []
            send_client(sock,conn,_,"OK") # Use 200 instead?
        case 'playerreset': # Will reset connected players
            pass

# Main thread to manage functionality
def main():
    # Initialize TCP socket and listen
    with socket() as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('localhost', 5555))
        sock.listen() # Should this be inside the loop?
        print('Welcome to the TNT super early access indiegogo crowdfund server.')
        print(f'Listening at {sock.getsockname()}\n')
        conn, _ = sock.accept()

        while True: # Network loop
            print(f'Peer {_} connected\n')
            print(f'Listening at {sock.getsockname()}\n')
            # Get command and forward to server_command
            # Data will always be sent as an array consisting of command,data
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