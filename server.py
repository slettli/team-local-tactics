from logging import exception
from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
import pickle

from core import Champion, Match, Shape, Team

# Used to prevent more than two clients connecting. Possibly shouldn't be global, or two bools.
P1_CONNECTED = False
P2_CONNECTED = False

P1_TEAM = [] # Player 1's team
P2_TEAM = [] # Player 2's team

def play_match():
    """
    Generates a match object and "plays" the match.
    Sends result to database.
    Returns match object.
    """

    # Match - Should be moved to server.py, with server only returning results.
    champs = send_database("GET_CHAMPS")
    match = Match(
        Team([champs[name] for name in P1_TEAM]),
        Team([champs[name] for name in P2_TEAM])
    )
    match.play() # Play the match
    send_database("SAVE_MATCH",match.score) # Tell database to store results
    return match # Return match object to send back to clients TODO change to only reuturning results to clients

# Send stuff to database. Request champions, send match result
def send_database(command,data=''):
    """
    Establishes TCP connection to database server.
    Forwards commands and/or data to database in pickled form.
        Using send_command()
    Returns unpickled reply 

    Parameters
    ----------
    command : str
        Command telling server what to do with sent data
    data : str
        Payload / data relevant to the command if any, like champion choices
    """

    with socket() as sock:
        DB_ADDRESS = ("localhost", 5556)
        sock.connect(DB_ADDRESS)
        print(f'Connected to server {sock.getpeername()}')
        result = send_command(sock,command,data)

    return result # Return reply, HOPEFULLY CHAMPS

# Used to send command when server acts as client, like with database
def send_command(sock,command,data=''):
    """
    Sends commands and data (pickled) to a destination when server acts as a client.
    Returns unpickled reply.

    Parameters
    ----------
    sock : socket
        Currently used socket containing connection to server 
    command : str
        Command telling server what to do with sent data
    data : anything
        Payload / data relevant to the command if any, like champion choices
    """

    sock.send(pickle.dumps((command,data))) # Always pickle
    try:
        return pickle.loads(sock.recv(1024)) # Return reply
    except:
        return

# Pickle and send whatever to client or database. Yeah, bad name for the function.
def send_client(conn,_,data):
    """
    Sends commands and data (pickled) to a player client.
    Returns unpickled reply.

    Parameters
    ----------
    conn : tcp connection
        Established TCP connection with client
    _ : tuple 
        Address of client
    data : anything
        Payload / data relevant to the command if any, like champion choices
    """

    pickled = pickle.dumps(data) #always pickle
    conn.send(pickled)
    print(f'Sent data to {_}, showing the unpickled format:\n{data}\n')

# Add selected champion to a player's team
def add_to_team(player,champion):
    """
    Adds player champion pick to list of team.

    Parameters
    ----------
    player : str
        Player ID
    champion : str
        Champion name
    """

    if player == 'Player 1':
        P1_TEAM.append(champion)
    else:
        P2_TEAM.append(champion)
    print(f"Added {champion} to {player}'s team\n")

# Receive input from clients and call appropriate methods
# Send reply to client
def server_command(sock,conn,_,command,load):
    global P1_TEAM, P2_TEAM

    match (command):
        case 'connect': # New client connects. Check if player slot available, return error or player ID to client
            if P1_CONNECTED == False:
                send_client(conn,_,"Player 1")
            elif P2_CONNECTED == False:
                send_client(conn,_,"Player 2")
            else:
                send_client(conn,_,"FULL") # Tell client server is full
        case 'disconnect': # Mark player slot as open, wipe corresponding player's team
            if load == "Player 1":
                P1_TEAM = []
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
            elif load == "Player 2":
                P2_TEAM = [] # Player 2's team
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
        case 'champions': # Get champions from db and send to client
            print('Champion list requested')
            send_client(conn,_,send_database("GET_CHAMPS"))
        case 'teams': # Get list of current teams - player1 and player2 arrays
            print('Team lists requested')
            send_client(conn,_,(P1_TEAM,P2_TEAM)) # Return pickled tuple of player teams
        case 'select':
            print('Adding to team requested')
            add_to_team(load[0],load[1])
            send_client(conn,_,"OK") # Use 200 instead?
        case 'PLAY': # Play match, return result to client
            send_client(conn,_,play_match())
        case 'SAVE_MATCH': # Send match result to db
            send_database("SAVE_MATCH",load)
        case 'MATCH_HISTORY': # Get match history from db, return resulting dict to client
            send_client(conn,_,send_database("MATCH_HISTORY"))
        case 'teamreset': # Reset teams 
            P1_TEAM = []
            P2_TEAM = []
            send_client(conn,_,"OK") # Use 200 instead?
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
        
        while True: # Connection loop with client. TODO spin this off into separate thread for each conn
            conn, _ = sock.accept()
            with conn:
                print(f'Peer {_} connected\n')
                while True: # Network loop
                    # Get command and forward to server_command
                    # Data will always be sent as an array consisting of command,data
                    try:
                        received = pickle.loads(conn.recv(1024))
                    except:
                        print(f"Lost connection to {_}\n") # Break loop and listen for new connections
                        break
                    print(f'Received request from {_}:\n{received}\n')
                    command = received[0]
                    load = received[1]

                    # Quit and shut down server if requested, else handle command
                    if command == 'quit': 
                        print('Shutdown request received.')
                        send_database("QUIT") # Tell database to shut down as well
                        print('Database shut down.')
                        send_client(conn,_,"Bye") # Change to appropriate code
                        print('Connection closed. Shutting down.')
                        return
                    else:
                        server_command(sock,conn,_,command,load)

if __name__ == '__main__':
    main()