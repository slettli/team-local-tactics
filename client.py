from logging import exception
from re import S
from turtle import forward
from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket
import pickle

from core import Champion, Match, Shape, Team

def print_available_champs(champions: dict[Champion]) -> None:
    """
    Prints available champions in a nice table.
    Takes input in the form of a Champion dict, requested from server by the client.

    Parameters
    ----------
    champions : dict
        A dict containing champions available in the game, and corresponding stats.
    """

    # Create a table containing available champions
    available_champs = Table(title='Available champions')

    # Add the columns Name, probability of rock, probability of paper and
    # probability of scissors
    available_champs.add_column("Name", style="cyan", no_wrap=True)
    available_champs.add_column("prob(:raised_fist-emoji:)", justify="center")
    available_champs.add_column("prob(:raised_hand-emoji:)", justify="center")
    available_champs.add_column("prob(:victory_hand-emoji:)", justify="center")

    # Populate the table
    for champion in champions.values():
        print(champion)
        available_champs.add_row(*champion.str_tuple)

    print(available_champs)

def input_champion(sock,
                   prompt: str,
                   color: str,
                   champions: dict[Champion],
                   player1: list[str],
                   player2: list[str]) -> None:
    """
    Takes input from player when selecting champions and forwards to server.
    Parses input and prints an error message if the champion is unavailable or already taken.   
    It then calls send_command() to forward the choice to the server. 

    Parameters
    ----------
    sock : socket
        Currently used socket containing connection to server
    prompt : str
        What to prompt the player with
    color : str
        Which player to ask ( blue or red)
    champions : dict
        Dict with champions
    player1 : list
        Team for player 1
    player2 : list
        Team for player 2
    """

    # Prompt the player to choose a champion and provide the reason why
    # certain champion cannot be selected
    while True:
        match Prompt.ask(f'[{color}]{prompt}'):
            case name if name not in champions:
                print(f'The champion {name} is not available. Try again.')
            case name if name in player1:
                print(f'{name} is already in your team. Try again.')
            case name if name in player2:
                print(f'{name} is in the enemy team. Try again.')
            case _: # send champion selection to server in form of tuple playername, champ name
                a = send_command(sock,'select',(prompt,name))
                break


def print_match_summary(match: Match) -> None:
    """
    Takes a Match object as input, extracts relevant info,
    and finally prints a nice stylized representation of the results.

    Parameters
    ----------
    match: Match object
        A match object of Match class, containing all info about the played match
    """

    EMOJI = {
        Shape.ROCK: ':raised_fist-emoji:',
        Shape.PAPER: ':raised_hand-emoji:',
        Shape.SCISSORS: ':victory_hand-emoji:'
    }

    # For each round print a table with the results
    for index, round in enumerate(match.rounds):

        # Create a table containing the results of the round
        round_summary = Table(title=f'Round {index+1}')

        # Add columns for each team
        round_summary.add_column("Red",
                                 style="red",
                                 no_wrap=True)
        round_summary.add_column("Blue",
                                 style="blue",
                                 no_wrap=True)

        # Populate the table
        for key in round:
            red, blue = key.split(', ')
            round_summary.add_row(f'{red} {EMOJI[round[key].red]}',
                                  f'{blue} {EMOJI[round[key].blue]}')
        print(round_summary) 
        print('\n')

    # Print the score
    red_score, blue_score = match.score
    print(f'Red: {red_score}\n'
          f'Blue: {blue_score}')

    # Print the winner
    if red_score > blue_score:
        print('\n[red]Red victory! :grin:')
    elif red_score < blue_score:
        print('\n[blue]Blue victory! :grin:')
    else:
        print('\nDraw :expressionless:')

# Prints out a table of all matches
def print_match_history(history):
    # Create a table containing match history
    match_history = Table(title='Match history')

    # Add coluns for match no., winner, scores
    match_history.add_column("Match no.", style="cyan", no_wrap=True, justify="center")
    match_history.add_column("Winner", no_wrap=True, justify="center")
    match_history.add_column("P1 Score", style ="red", no_wrap=True, justify="center")
    match_history.add_column("P2 Score", style ="blue", no_wrap=True, justify="center")

    for match in history:
        m = str(match[1])
        if m  == str(0):
            match[1] = 'Draw'
        elif m  == str(1):
            match[1] = 'Player 1'
        elif m == str(2):
            match[1] = 'Player 2'   
        match_history.add_row(*match)

    print(match_history)

# Used for forwarding commands, return reply. Pickles and unpickles
def send_command(sock,command,data=''):
    """
    Forwards commands and/or data to destination in pickled form.
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

    return pickle.loads(sock.recv(1024)) # Return reply
        
def play(sock,player_id):
    """
    Performs one loop/round of the game from the client side:
        1. Retrieves champions from server
            db > server > client
        2. Prints and lets players pick champions
        3. Forward chosen teams to server
        4. Tell server to start match
        5. Format and print match results when returned from server
        6. Tell server to reset teams for the next round.
    
    Parameters
    ----------
    sock : socket
        Currently used socket containing connection to server 
    player_id : int
        Number representing whether this client is Player 1 or 2. Currently not used.
    """

    print("Asking server for champions...")
    champions = send_command(sock,"champions")
    print(f"Received reply: {champions}")

    print_available_champs(champions)
    print('\n')

    teams = send_command(sock,'teams') # Initial team fetch
    print(teams)

    # Champion selection. Ask server for teams before each player picks again.
    for _ in range(2): 
        teams = send_command(sock,'teams')
        print(teams[0])
        print(teams[1])
        input_champion(sock,'Player 1', 'red', champions, teams[0], teams[1])
        teams = send_command(sock,'teams')
        input_champion(sock,'Player 2', 'blue', champions, teams[1], teams[0])

    print('\n')

    # Tell server to play match, retrieve resulting match object
    match = send_command(sock,'PLAY') # Initial call to play match when using one client only, will be changed
    # Print a summary
    print_match_summary(match)
    send_command(sock,"teamreset") # Tell server to wipe teams so you can play again without restarting server. This will be moved to server later

# Handles initial connection, calls other methods based on player input
def main() -> None:
    """
    Client loop that performs the client side of the game:
        1. Establishes a socket and connects to server over TCP
        2. Presents a menu of commands
        3. Acts in requested manner from there    

    Example
    -------
    >>> Connect
    Attempt to establish TCP connection with server -- NOT IMPLEMENTED
    >>> Disconnect
    Disconnect from server if connected -- NOT IMPLEMENTED
    >>> Play
    Calls other appropriate functions within this script to play game
    >>> Match history
    Retreive and show match history. -- NOT IMPLEMENTED 
    >>> Quit
    Tells server to shut down (server tells database to shut down),
    and shuts down client.
    """

    playerID = ''
    # Initialize TCP connection to server
    with socket() as sock:
        # TODO make client not crash if server not found
        # Connect to server
        SERVER_ADDRESS = ("localhost", 5555)
        sock.connect(SERVER_ADDRESS)
        print(f'Client address {sock.getsockname()}')
        print(f'Connected to server {sock.getpeername()}')

        # Welcome message and table of commands
        print('\n'
                'Welcome to [bold yellow]Team Network Tactics[/bold yellow] alpha early access crowdfunded edition (final name pending)!'
                '\n')

        initial_info_table = Table(title='Commands')
        initial_info_table.add_column("Command", style="cyan", no_wrap=True)
        initial_info_table.add_column("Function", no_wrap=True)
        initial_info_table.add_row(*("Play","Starts the game"))
        initial_info_table.add_row(*("History","Match History"))
        #initial_info_table.add_row(*("Connect","Connect to the server and get Player ID [PLACEHOLDER]"))
        #initial_info_table.add_row(*("Disconnect","Disconnect and wipe team"))
        initial_info_table.add_row(*("Quit","Shut down the server and client"))
        #initial_info_table.add_row(*("Debug","Show (very) secret debug commands [PLACEHOLDER]"))

        # Command loop     
        while True: 
            print(initial_info_table)

            command = input('\nEnter command: ')
            command = command.lower()

            # Client commands 
            match (command):
                case ('connect'): # Connect and get assigned playerID if available - Not fully implemented
                    sock.connect(SERVER_ADDRESS)
                    print(f'Client address {sock.getsockname()}')
                    print(f'Connected to server {sock.getpeername()}')
                    '''if playerID == '': # Don't attempt to connect if already assigned
                        playerID = send_command(sock,'connect') # Assign player ID
                        if playerID == 'FULL':
                            print('Sorry, the TNT servers are full at the moment. Please try again later.\n')
                            playerID = ''
                        else:
                            print(f'Welcome, {playerID}. Please pick the play option.')'''
                case ('play'): # Start playing the game
                    '''if playerID == '':
                        print("Error - Not assigned Player ID.")
                    else:
                        play(sock,playerID)'''
                    play(sock,playerID)
                case 'history': # Request match history from server > db and show
                    history = send_command(sock,'MATCH_HISTORY')
                    print_match_history(history)
                case ('disconnect'): # Tell server to disconnect and wipe team. TODO make client actually disconnect on network level. Make quit client?
                    send_command(sock,'disconnect',playerID)
                    print('Disconnected. Thanks for playing.')
                    break
                case ('quit'): # Tell server to shut down, quit client. Make shut down server and quit client separate?
                    send_command(sock,'quit')
                    print('Server shutting down. Thanks for playing.')
                    break

        
if __name__ == '__main__':
    main()
