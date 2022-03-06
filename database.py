from core import Champion

from socket import socket, SOL_SOCKET, SO_REUSEADDR
import pickle

# Functions that fetch and parses list of champions
def _parse_champ(champ_text: str) -> Champion:
    name, rock, paper, scissors = champ_text.split(sep=',')
    return Champion(name, float(rock), float(paper), float(scissors))

def from_csv(filename: str) -> dict[str, Champion]:
    champions = {}
    with open(filename, 'r') as f:
        for line in f.readlines():
            champ = _parse_champ(line)
            champions[champ.name] = champ
    return champions

# Pickle and send whatever to client or database. Yeah, bad name for the function.
def send_client(sock,conn,_,load):
    pickled = pickle.dumps(load) #always pickle
    conn.send(pickled)
    print(f'Sent data to {_}, showing the unpickled format:\n{load}\n')

# Listen to and return champions in pickled format when requested
def load_some_champs():
    with socket() as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(('localhost', 5556))
        sock.listen() # Should this be inside the loop?
        print('TNT Database online.')
        print(f'Listening at {sock.getsockname()}\n')

        while True: # Network loop
            conn, _ = sock.accept()
            print(f'Peer {_} connected\n')
            print(f'Listening at {sock.getsockname()}\n')
            # Get command and forward to server_command
            # Data will always be sent as an array consisting of command,data
            received = pickle.loads(conn.recv(1024))
            print(f'Received request from {_}:\n{received}\n')
            command = received[0]
            load = received[1]
            print(command)
            # Quit and shut down server if requested, else handle command
            if command == "GET_CHAMPS":
                champions = from_csv('some_champs.txt')
                send_client(sock,conn,_,champions)                
                print("Sent champions")
                conn.close()
            elif command == "QUIT": #TODO quit command
                pass

def main():
    print("Database loading")
    load_some_champs()

if __name__ == '__main__':
    main()