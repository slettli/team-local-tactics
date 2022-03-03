from rich import print
from rich.prompt import Prompt
from rich.table import Table
from socket import socket, SOL_SOCKET, SO_REUSEADDR
import pickle

from core import Champion, Match, Shape, Team
from champlistloader import load_some_champs

# Handle playing the match using core, return result
def play_match():
    pass

# Receive input from clients and call appropriate methods, return formatted reply to main()
def server_command(command):
    match (command):
        case "champions": # Get dict of champions and encode with pickle
            return pickle.dumps(load_some_champs())
        case "play": # Play match, return result
            pass

# Main thread to manage functionality
# TODO make it loop until asked to exit
def main():
    # Initialize TCP socket and listen
    sock = socket()
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(("localhost", 6666))
    sock.listen()
    print("Server ready to receive input")
    # Get command and forward to server_command
    conn, _ = sock.accept()
    command = conn.recv(1024).decode()
    response = server_command(command) # Reply with returned answer from server_command
    print(response)
    conn.send(response)
    conn.close()


if __name__ == '__main__':
    main()