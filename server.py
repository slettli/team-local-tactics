from logging import exception
from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
import selectors
import pickle

from core import Champion, Match, Shape, Team

sel = selectors.DefaultSelector()

# Used to prevent more than two clients connecting. Possibly shouldn't be global, or two bools.
P1_CONNECTED = False
P2_CONNECTED = False
# Adresses of clients
P1_ADR = "0.0.0.0:1111"
P2_ADR = "0.0.0.0:2222"

# Store connected clients, mainly for add_team()
CLIENTS = [] 

P1_READY = False
P2_READY = False

MATCH = ""

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
    Forwards commands and/or data to database in pickled form using send_command().
    Returns unpickled reply.

    Parameters
    ----------
    command : str
        Command telling server what to do with sent data
    data : anything
        Payload / data relevant to the command if any, like champion choices
    """

    with socket() as sock:
        DB_ADDRESS = ("localhost", 5556)
        sock.connect(DB_ADDRESS)
        print(f'Connected to server {sock.getpeername()}')
        result = send_command(sock,command,data)

    return result 

def send_command(sock,command,data=''):
    """
    Sends commands and data (pickled) to a destination when server acts as a client.
    Returns unpickled reply.

    Parameters
    ----------
    sock : socket
        Connection to send data through
    command : str
        Command telling server what to do with sent data
    data : any
        Payload / data if any, like champion choices
    """

    sock.send(pickle.dumps((command,data))) # Always pickle
    try:
        return pickle.loads(sock.recv(1024)) # Return reply
    except:
        return

def send_client(conn,data):
    """
    Sends commands and data (pickled) to a player client.

    Parameters
    ----------
    conn : socket
        Established connection with client
    data : any
        Payload / data if any, like champion choices
    """
    _ = conn.getpeername()

    pickled = pickle.dumps(data) #always pickle
    conn.send(pickled)
    print(f'Sent data to {_}, showing the unpickled format:\n{data}\n')

def add_to_team(load):
    global P1_TEAM, P2_TEAM, CLIENTS
    """
    Adds champion choices to respetive teams, in order.
    Pokes clients when it's their turn to pick again.

    Parameters
    ----------
    load : tuple containing str
        Data from clients invoking function, usually containing champion choice or player ID.
    """
    p1Pick = len(P1_TEAM)
    p2Pick = len(P2_TEAM)

    if p1Pick == 0:
        send_client(CLIENTS[0],"P1") # Tell P2 it's their turn again
        P1_TEAM.append(load[1]) # Add chosen champion to team
    elif p2Pick == 0:
        send_client(CLIENTS[1],"P2") # Tell P2 it's their turn again
        P2_TEAM.append(load[1])
    elif p1Pick == 1:
        send_client(CLIENTS[0],"P1") # Tell P1 it's their turn again
        P1_TEAM.append(load[1])
    elif p2Pick == 1:
        send_client(CLIENTS[1],"P2") # Tell P2 it's their turn again
        P2_TEAM.append(load[1])
    elif p1Pick == 2:
        send_client(CLIENTS[0],"P1") # Tell P1 it's their turn again
        P1_TEAM.append(load[1])
    else:
        send_client(CLIENTS[1],"P2") # Tell P2 it's their turn again
        P2_TEAM.append(load[1])
    
def server_command(conn,_,command,load):
    """
    Beeg function that handles all incoming commands and calls appopriate functions.

    Paramteres
    ----------
    conn : socket
        Connection/socket that the request arrived through
    _ : tuple
        Address of who/whatever sent the request
    command : str
        Command telling server what to do with sent data
    data : any
        Payload / data if any, like champion choices
    """
    global P1_TEAM, P2_TEAM, P1_READY, P2_READY, MATCH

    match (command):
        case 'disconnect': # Mark player slot as open, wipe corresponding player's team
            if load == "Player 1":
                P1_TEAM = []
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
            elif load == "Player 2":
                P2_TEAM = [] # Player 2's team
                print(f"Disconnect request received from {_}, wiping {load}'s team.")
        case 'champions': # Get champions from db and send to client
            print('Champion list requested')
            send_client(conn,send_database("GET_CHAMPS"))
        case 'teams': # Get list of current teams - player1 and player2 arrays
            print('Team lists requested')
            send_client(conn,(P1_TEAM,P2_TEAM)) # Return pickled tuple of player teams
        case 'select':  
            print('Adding to team requested')
            add_to_team(load)
            if len(P1_TEAM) == 3 and len(P2_TEAM) == 3:
                print("playing")
                MATCH = play_match()
                for c in CLIENTS:
                    send_client(c,MATCH)
                    print("sent match")
                P1_TEAM = [] # Reset teams
                P2_TEAM = []
                MATCH = ""
                print("reset match data")
        case 'PLAY': # Return result to client
            send_client(conn,_,MATCH)
        case 'SAVE_MATCH': # Send match result to db
            send_database("SAVE_MATCH",load)
        case 'MATCH_HISTORY': # Get match history from db, return resulting dict to client
            send_client(conn,send_database("MATCH_HISTORY"))
        case 'teamreset': # Reset teams 
            P1_TEAM = []
            P2_TEAM = []
            send_client(conn,"OK") # Use 200 instead?
        case 'playerreset': # Will reset connected players
            pass

def conn_new_handler(sock):
    """
    Handles new clients connecting.
    Will grant either P1 or P2 ID to the user, depending on which is available. Replies with FULL if both player slots are taken.
    This is to keep track of which player is which.

    Parameters
    ----------
    sock : socket
        Connection to send data through
    """
    global P1_CONNECTED, P2_CONNECTED, P1_ADR, P2_ADR
    # Client sends player ID if any on initial connection. If no provided, check if slots available and return ID
    conn, _ = sock.accept()
    print(f'New peer {_} connected\n')
    conn.setblocking(False)

    if P1_CONNECTED == False: # Check if there are available player slots, return to client
        pID = "P1"
        print(f"Gave new ID {pID} to {_}")
        P1_CONNECTED = True # Note connected player. This could be done with more verification.
        P1_ADR = _
        CLIENTS.append(conn)
    elif P2_CONNECTED == False:
        pID = "P2"
        print(f"Gave new ID {pID} to {_}")
        P2_CONNECTED = True
        P2_ADR = _
        CLIENTS.append(conn)
    else: 
        pID = "FULL"
        print("no available id")

    print(P1_CONNECTED)
    print(P2_CONNECTED)
    sel.register(conn, selectors.EVENT_READ | selectors.EVENT_WRITE, data=pID) # Register new connection selector
    send_client(conn,pID) # Give client its ID

def conn_handler(key,_):
    """
    Handles requests from already registered clients. Either quits if requested or forwards the request to server_command().

    Parameters
    ----------
    key : SelectorKey
        Key to get data from selector event
    _ : tuple
        Address of who/whatever sent the request
    """
    sock = key.fileobj
    data = key.data
    adr = sock.getpeername()
    if (_ & selectors.EVENT_READ):
        try:
            # Extract data
            received = pickle.loads(sock.recv(1024))
            print(f'Received request from {adr}:\n{received}\n')
            command = received[0]
            load = received[1]

            # Quit and shut down server if requested, else handle command
            if command == 'quit': 
                print('Shutdown request received.')
                send_database("QUIT") # Tell database to shut down as well
                print('Database shut down.')
                print('Connection closed. Shutting down.')
                sel.unregister(sock)
                sock.close()
                return
            else:
                server_command(sock,adr,command,load)
        except:
            pass
            """print(f"Something went wrong with request from {adr}, aborting\n") # Break loop and listen for new connections
            sel.unregister(sock)
            sock.close()
            return"""

def main():
    """
    Main function that sets up server and loops over incoming requests.
    """
    # Initialize TCP listener socket and listen for incoming connections
    print('Welcome to the TNT super early access indiegogo crowdfund server.')
    listensock = socket() # Listener socket
    listensock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    listensock.bind(('localhost', 5555))
    listensock.listen() 
    listensock.setblocking(False)
    sel.register(listensock, selectors.EVENT_READ, data=None) # Let selectors monitor socket
    print(f'Listening at {listensock.getsockname()}\n')
    
    # Listen for connections, register new clients or handle commands
    try:
        while True: # Loop over selector events (incoming requests)
            events = sel.select(timeout=None)
            for key, _ in events:
                if key.data is None: # Incoming new client
                    conn_new_handler(key.fileobj)
                else: # Already connected client
                    conn_handler(key, _)
    except:
        print("Uh oh")
    finally:
        sel.close() # Properly detach from selector when finished

if __name__ == '__main__':
    main()