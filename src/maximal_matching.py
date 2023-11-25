#!/usr/bin/env python
from distr import Computer, Port, Network, ER_bipartite
from enum import Enum
from typing import Set
from math import ceil


class Color(Enum):
    WHITE = 1
    BLACK = 2


class State(Enum):
    UR = 0
    MR = 1
    US = 2
    MS = 3


"""
sending:
    round 2k - 1, white, UR, k <= deg, port == k:
        send 'proposal'
    round 2k - 1, white, MR(i): 
        send 'matched'
    round 2k, black, UR, M not empty, port == min(M):
        send 'accept'
        switch to MS(i)

receive:
    round 2k - 1, black, UR:
        case 'matched': X.remove(port)
        case 'proposal': M.add(port)
    round 2k, white:
        case 'accept': switch to MR(i)

compute:
    round 2k - 1, white, UR, k > deg:
        switch to US
    round 2k - 1, white, MR(i):
        switch to MS(i)
    round 2k, black, UR, X empty:
        switch to US
"""


# Bipartite maximal matching
class MaximalMatcherComputer(Computer):
    def __init__(self, degree: int, input_data: Color):
        super().__init__(degree, input_data)
        self.degree = degree
        self.color = input_data
        self.state: State = State.UR
        self.round = 1
        self.M: Set[int] = set()
        self.X: Set[Port] = set(range(1, degree + 1))

    def __repr__(self) -> str:
        return (
            f"MaxMatcher[{self.color}](d={self.degree},state={self.state})"
        )

    def k(self) -> int:
        return ceil(self.round / 2)

    def modulus(self) -> int:
        return self.round % 2

    def set_US(self):
        self.state = State.US
        self.output = "unmatched"

    def set_MR(self, port: int):
        self.state = State.MR
        self.output = f"matched to port {port}"

    def set_MS(self, port: int | None = None):
        self.state = State.MS
        if port:
            self.output = f"matched to p:{port}"
        elif self.output is None:
            raise Exception("You need to set output port")

    def send(self, port: int) -> str:
        match (self.color, self.modulus(), self.state, self.k()):
            case (Color.WHITE, 1, State.UR, port):
                return "proposal"
            case (Color.WHITE, 1, State.MR, _):
                return "matched"
            case (Color.BLACK, 0, State.UR, _) if len(self.M) > 0 and port == min(
                self.M
            ):
                self.set_MR(port)
                return "accept"
        return ""

    def receive(self, port: int, message: str) -> None:
        match (self.color, self.modulus(), self.state):
            case (Color.BLACK, 1, State.UR):
                match message:
                    case "matched":
                        self.X.remove(port)
                    case "proposal":
                        self.M.add(port)
            case (Color.WHITE, 0, State.UR):
                if message == "accept":
                    self.set_MR(port)

    def compute(self) -> None:
        match (self.color, self.modulus(), self.state):
            case (Color.WHITE, 1, State.UR) if self.k() > self.degree:
                self.set_US()
            case (Color.WHITE, 1, State.MR):
                self.set_MS()
            case (Color.BLACK, 0, State.UR) if len(self.X) == 0:
                self.set_US()
        self.round += 1


if __name__ == "__main__":
    ((A, B), E) = ER_bipartite(7, 11, 0.9)
    V = [Color.WHITE for _ in A] + [Color.BLACK for _ in B]
    network = Network(V, E, MaximalMatcherComputer)
    print(network)

    network.run_until_done()
