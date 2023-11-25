# $\star$ Exercise 3.6 (implementation).

_Using your favorite programming language, implement a simulator that lets you play with distributed algorithms in the port-numbering model. Implement the algorithms for bipartite maximal matching and minimum vertex cover 3-approximation and try them out in the simulator._

Here is a concatenation of the source code to my simulator, an implementation of the algorithm for _bipartite maximal matching_ from section 3.5, and an implementation of the algorithm for a 3-approximation of a minimum vertex cover from section 3.6.

You can probably have an easier time reading this source at GitHub or locally instead: [peik-etzell/distributed-computing-simulator](https://github.com/peik-etzell/distributed-computing-simulator).

## src/distr.py

```python
from abc import ABC, abstractmethod
from random import random
from typing import Any, Dict, List, Tuple, Type, TypeVar


class Computer(ABC):
    """
    An abstract base class to inherit, defines the interface for
    distributed algorithms
    """

    @abstractmethod
    def __init__(self, degree: int, input_data):
        self.output: str | None = None

    @abstractmethod
    def send(self, port: int) -> str:
        pass

    @abstractmethod
    def receive(self, port: int, message: str) -> None:
        pass

    @abstractmethod
    def compute(self) -> None:
        pass


# Basic graph types
Vertex = int
Edge = Tuple[Vertex, Vertex]

# Distributed computing types
BaseComputer = TypeVar("BaseComputer", bound=Computer)
Port = int
PortBinding = Tuple[BaseComputer, Port]
Link = Tuple[PortBinding, PortBinding]


def ER(size: int, p: float) -> Tuple[List[Vertex], List[Edge]]:
    """
    Erdos Renyi random graph
    """
    V: List[Vertex] = list(range(size))
    E: List[Edge] = []

    for i, u in enumerate(V):
        for v in V[i + 1 : :]:
            if random() <= p:
                E.append((u, v))
    return (V, E)


def ER_bipartite(
    size_a: int, size_b: int, p: float
) -> Tuple[Tuple[List[Vertex], List[Vertex]], List[Edge]]:
    """
    Bipartite Erdos Renyi random graph
    """
    A: List[Vertex] = list(range(size_a))
    B: List[Vertex] = list(range(size_a, size_a + size_b))
    E: List[Edge] = []

    for a, b in [(a, b) for a in A for b in B]:
        if random() <= p:
            E.append((a, b))
    return ((A, B), E)


class Network:
    """
    A collection of generic computers which runs them synchronously in the order:
        send()
        receive()
        compute()
    until they are all done.
    """

    def __init__(self, V: List[Any], E: List[Edge], type: Type[BaseComputer]):
        degrees: List[int] = [0 for _ in V]
        for u, v in E:
            degrees[u] += 1
            degrees[v] += 1
        self.computers: List[BaseComputer] = [
            type(degrees[i], v) for i, v in enumerate(V)
        ]
        port_counts: List[int] = [0 for _ in self.computers]

        def new_port(v: Vertex) -> PortBinding:
            port_counts[v] += 1
            return (self.computers[v], port_counts[v])

        self.links: List[Link] = [(new_port(u), new_port(v)) for u, v in E]

    def __repr__(self) -> str:
        return f"Network: {len(self.computers)} computers, {len(self.links)} links:\n{self.computers}"

    def run_iteration(self):
        # Keep messages waiting such that they are received only in the
        # receive step
        mailbox: Dict[PortBinding, str] = {}

        # Send
        for (c1, port1), (c2, port2) in self.links:
            mailbox[(c1, port1)] = c2.send(port2)
            mailbox[(c2, port2)] = c1.send(port1)

        # Receive
        for (computer, port), msg in mailbox.items():
            computer.receive(port, msg)

        # Compute
        for computer in self.computers:
            computer.compute()

    def run_until_done(self, round_limit=50):
        iter = 0
        while (
            None in [computer.output for computer in self.computers]
            and iter < round_limit
        ):
            print(f">>> Iteration {iter} >>>")
            self.run_iteration()
            iter += 1
        if iter == round_limit:
            print(">>> Round limit reached")
            return
        print(">>> All done:")
        for idx, computer in enumerate(self.computers):
            print(f"\tComputer{idx}: {computer.output}")
```

## src/maximal_matching.py

```python
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
```

## src/maximal_matching.py

```python
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
                self.output = "0 (not in the cover)"
            case _:
                self.output = "1 (part of the cover)"


if __name__ == "__main__":
    (V, E) = ER(10, 0.2)
    network = Network(V, E, VertexCoverApproximatingComputer)
    print(network)

    network.run_until_done(10)
```
