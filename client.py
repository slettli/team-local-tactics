from turtle import forward
from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket
import pickle

from core import Champion, Match, Shape, Team

# Can stay in client
def print_available_champs(champions: dict[Champion]) -> None:

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
        available_champs.add_row(*champion.str_tuple)

    print(available_champs)

# Checks if champion is available, forwards choice if accepted to server.
# Should be moved server side.
def input_champion(sock,
                   prompt: str,
                   color: str,
                   champions: dict[Champion],
                   player1: list[str],
                   player2: list[str]) -> None:

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
                send_command(sock,'select',(prompt,name))
                break


def print_match_summary(match: Match) -> None:

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

# Forwards champion selection to server
def send_team_selection(sock,command):
    pass

# Used for forwarding a simple text based command, return reply
def send_command(sock,command,data):
    sock.send(pickle.dumps((command,data))) # Always pickle

    return pickle.loads(sock.recv(1024)) # Return reply

# Takes server command from main() and forwards to appropriate method
def server_command(sock,command):
    match (command):
        case 'champions':
            return send_command(sock,command, '')
        case 'teams':
            return send_command(sock,command, '')
        case 'quit':
            send_command(sock, command, '')
        

# Fetch list of champions: db > server > client 
def play(sock):
    print("Asking server for champions...")
    champions = server_command(sock,"champions")
    print(f"Received reply: {champions}")

    print('\n'
        'Welcome to [bold yellow]Team Local Tactics[/bold yellow]!'
        '\n'
        'Each player choose a champion each time.'
        '\n')

    print_available_champs(champions)
    print('\n')

    # TODO make below stuff networked. 
    # TODO move parsing to server
    # TODO move keeping track of champions to server

    teams = send_command('teams') # Initial team fetch

    # Champion selection. Ask server for teams before each player picks again.
    for _ in range(2): 
        teams = send_command('teams')
        print(teams[1])
        print(teams[2])
        input_champion(sock,'Player 1', 'red', champions, teams[1], teams[2])
        teams = send_command('teams')
        input_champion(sock,'Player 2', 'blue', champions, teams[2], teams[1])

    print('\n')



    teams = send_command('teams')
    # Match
    match = Match(
        Team([champions[name] for name in teams[1]]),
        Team([champions[name] for name in teams[2]])
    )
    match.play()

    # Print a summary
    print_match_summary(match)

def main() -> None:
    # Initialize TCP connection to server
    sock = socket()
    server_address = ("localhost", 6666)
    sock.connect(server_address)

    while True: #network loop      
        # Connection established, ask for command
        command = input("Welcome to TNT. Commands:\nplay - play\nquit - quit the game and shut down server\n")

        # Client commands 
        match (command):
            case ('quit'):
                print("Thanks for playing.")
                break
            case ('play'): 
                play(sock)
        
    sock.close() # Close socket and let function exit if loop broken by player

if __name__ == '__main__':
    main()
