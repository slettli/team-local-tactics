from core import Champion

# Functions that fetch and parses list of champions
# Originally in a separate file but due to circular imports I just put them here for now...
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

def load_some_champs():
    return from_csv('some_champs.txt')