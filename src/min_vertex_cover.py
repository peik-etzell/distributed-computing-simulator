#!/usr/bin/env python
from typing import Any
from distr import Computer, Network, ER
from maximal_matching import MaximalMatcherComputer, Color




class VertexCoverApproximatingComputer(Computer):
    """
    Computer which simulates two internal MaximalMatcherComputer's internally,
    which outputs a 3-approximation of a vertex cover on a generic graph.
    """
    def __init__(self, degree: int, input_data: Any = None):
        super().__init__(degree, input_data)
        self.degree = degree  # not needed other than in __repr__
        self.input_data = input_data  # not needed other than in __repr__
        self.v1 = MaximalMatcherComputer(degree, Color.WHITE)
        self.v2 = MaximalMatcherComputer(degree, Color.BLACK)

    def __repr__(self) -> str:
        return f"VCApproxComputer{self.input_data}(deg={self.degree})"

    def send(self, port: int) -> str:
        """
        (a) If v1 sends a message m1 to port (v1, i) and v2 sends a message
            m2 to port (v2, i) in the simulation, then v sends the pair (m1, m2)
            to port (v, i) in the physical network.
        """
        m1 = self.v1.send(port)
        m2 = self.v2.send(port)
        message = f"{m1};{m2}"
        # print(f"sending {message}")
        return message

    def receive(self, port: int, message: str) -> None:
        """
        (b) If v receives a pair (m1, m2) from port (v, i) in the physical network,
            then v1 receives message m2 from port (v1, i) in the simulation,
            and v2 receives message m1 from port (v2, i) in the simulation.
            Note that we have here reversed the messages: what came from a
            white node is received by a black node and vice versa.
        """
        # print(f"received {message}")
        [m1, m2] = message.split(";")
        self.v2.receive(port, m1)
        self.v1.receive(port, m2)

    def compute(self) -> None:
        """
        (a) Simulate the bipartite maximal matching algorithm in the virtual network N'.
            Each node v waits until both of its copies, v1 and v2, have stopped.

        (b) Node v outputs 1 if at least one of its copies v1 or v2 becomes matched.
        """
        self.v1.compute()
        self.v2.compute()
        # print(f"v1: {self.v1.output}; v2: {self.v2.output}")
        match (self.v1.output, self.v2.output):
            case (None, None):
                pass
            case ("unmatched", "unmatched"):
                self.output = f"{0} (not in the cover)"
            case _:
                self.output = f"{1} (part of the cover)"


if __name__ == "__main__":
    (V, E) = ER(10, 0.2)
    network = Network(V, E, VertexCoverApproximatingComputer)
    print(network)

    network.run_until_done(10)
