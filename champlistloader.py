from core import Champion

from socket import socket, AF_INET, SOCK_DGRAM, SOL_SOCKET, SO_REUSEADDR
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

# Listen to and return champions in pickled format when requested
# Uses UDP for now
def load_some_champs():
    with socket(AF_INET, SOCK_DGRAM) as sock:
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        sock.bind(("localhost", 6667))
        while True: # Listen for requests constantly, pickle and send when requested
            received,address = pickle.loads(sock.recv(1))
            command = received[0]
            if command == "GET_CHAMPIONS":
                champions = pickle.dumps(from_csv('some_champs.txt')) 
                sock.sendto(bytes(received), address)