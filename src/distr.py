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
