from dataclasses import dataclass
from enum import Enum
from random import random, shuffle

_BEATS = {
    (1, 3),
    (3, 2),
    (2, 1)
}


class Shape(Enum):
    """
    Hand shapes for the Rock paper scissors game.

    Support the comparisson of two shapes to infer the one that wins.

    Example
    -------
    >>> Shape.ROCK > Shape.PAPER 
    False
    >>> Shape.ROCK < Shape.PAPER
    True
    """
    ROCK = 1
    PAPER = 2
    SCISSORS = 3

    def __gt__(self, other):
        return (self.value, other.value) in _BEATS


@dataclass
class PairThrow:
    """
    Store the pair of shapes in a throw.
    """
    red: Shape
    blue: Shape


class Champion:
    """
    Champion for the game Rock paper scissors. Store the name and the
    probabilities of throwing each shape.

    Parameters
    ----------
    name : str
        The name of the champion.
    rock : float
        The probability of throwing rock. Must be between 0 and 1. 
    paper : float
        The probability of throwing paper. Must be between 0 and 1.
    scissors : float
        The probability of throwing scissors. Must be between 0 and 1.

    Note
    ----
    Probabilities are stored after dividing by the sum of them.
    """

    def __init__(self,
                 name: str,
                 rock: float = 1,
                 paper: float = 1,
                 scissors: float = 1) -> None:
        self._name = name
        total = rock + paper + scissors
        self._rock = rock / total
        self._paper = paper / total

    @property
    def name(self) -> str:
        return self._name

    def throw(self) -> Shape:
        """
        Throw a hand shape at random following the stored probabilities.

        Returns
        -------
        Shape

        Example
        -------
        >>> Champion("John").throw()
        Shape.ROCK
        """
        r = random()
        if r < self._rock:
            return Shape.ROCK
        if r < self._paper+self._rock:
            return Shape.PAPER
        return Shape.SCISSORS

    @property
    def str_tuple(self) -> tuple[str, str, str, str]:
        """
        A tuple with strings describing the champion.

        Returns
        -------
        tuple

        Example
        -------
        >>> Champion("John").str_tuple
        ('John','0.33','0.33','0.33')
        """
        return (self.name,
                f'{self._rock:.2f}',
                f'{self._paper:.2f}',
                f'{(1-self._rock-self._paper):.2f}')

    def __repr__(self) -> str:
        return (f'{self._name:10}|   {self._rock:.2f}   |   '
                f'{self._paper:.2f}   |   {(1-self._rock-self._paper):.2f}')


def pair_throw(red_champ: Champion,
               blue_champ: Champion,
               max_iter: int = 100) -> PairThrow:
    """
    Red and blue champions throw at the same time.

    Parameters
    ----------
    red_champ : Champion
        Red champion.
    blue_champ : Champion
        Blue champion.
    max_iter : int, default 100
        Maximun number of interations before calling a draw.
    """

    for _ in range(max_iter):
        red_throw = red_champ.throw()
        blue_throw = blue_champ.throw()
        if red_throw != blue_throw:
            break
    return PairThrow(red_throw, blue_throw)


@dataclass
class Team:
    """
    Team consisting in a list of champions.

    Support interating over the team. Each time the iteration begins 
    the list of champions is shuffled.
    """

    champions: list[Champion]

    def __iter__(self) -> list[Champion]:
        shuffle(self.champions)
        return iter(self.champions)


@dataclass
class Match:
    """
    Match results between two teams.

    Parameters
    ----------
    red_team: Team
        The red team.
    blue_team: Team
        The blue team.
    n_rounds: int, default 3
        Number of rounds to be played.
    """
    red_team: Team
    blue_team: Team
    n_rounds: int = 3

    def play(self):
        """
        Play a match.
        """
        self._red_score = 0
        self._blue_score = 0
        self._rounds = [{} for _ in range(self.n_rounds)]
        for round in self._rounds:
            for red_champ, blue_champ in zip(self.red_team, self.blue_team):
                champ_names = red_champ.name + ', ' + blue_champ.name
                pair = pair_throw(red_champ, blue_champ)
                if pair.red > pair.blue:
                    self._red_score += 1
                elif pair.red < pair.blue:
                    self._blue_score += 1
                round[champ_names] = pair

    @property
    def score(self) -> tuple[int, int]:
        return (self._red_score, self._blue_score)

    @property
    def rounds(self) -> list[dict[str, PairThrow]]:
        return self._rounds