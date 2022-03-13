from __future__ import annotations

from typing import Dict, Generic, Iterable, List, Set, TypeVar

T = TypeVar('T')


class TopologicNode:
    def __init__(self, name: str):
        self.name = name
        self.depends_on: List[TopologicNode] = []
        self.depended_by: List[TopologicNode] = []

    def dependencies(self, reverse: bool) -> Iterable[TopologicNode]:
        return self.depends_on if not reverse else self.depended_by

    def dependants(self, reverse: bool) -> Iterable[TopologicNode]:
        return self.dependencies(not reverse)


class Topology:
    def __init__(self):
        self.nodes: Dict[str, TopologicNode] = {}

    def add_node(self, key):
        self.nodes[key] = TopologicNode(key)

    def keys(self):
        return self.nodes.keys()

    def add_dependency(self, parent: str, child: str):
        parent_node = self.nodes[parent]
        child_node = self.nodes[child]

        parent_node.depended_by.append(child_node)
        child_node.depends_on.append(parent_node)

    def execution(self, include_only: Set[str], reverse: bool = False, ):
        return TopologicalExecution(self, include_only, reverse)

    def get_ancestors(self, children: Iterable[str], reverse) -> Set[str]:
        ret = set()
        unvisited = {self.nodes[child] for child in children}
        while unvisited:
            node = unvisited.pop()
            ret.add(node)
            for dep in node.dependencies(reverse):
                if dep in ret:
                    continue
                unvisited.add(dep)
        return {node.name for node in ret}


class TopologicalExecution(Generic[T]):
    def __init__(self, topology: Topology, include_only: Set[str], reverse: bool = False):
        self.topology = topology

        self.pending: Dict[TopologicNode, Set[str]] = {}
        self.ready: Set[TopologicNode] = set()

        include_only = topology.get_ancestors(include_only, reverse)

        for node in topology.nodes.values():
            if node.name not in include_only:
                continue
            dependencies = {d.name for d in node.dependencies(reverse)} & include_only

            if not dependencies:
                self.ready.add(node)
            else:
                self.pending[node] = dependencies

        self.submitted: Set[TopologicNode] = set()
        self.completed: Set[TopologicNode] = set()

        self.reverse = reverse
        self.cancelled = False

    def cancel_all_unsubmitted(self):
        self.pending.clear()
        self.ready.clear()
        self.cancelled = True

    def submit_ready(self) -> Iterable[str]:
        ret = [r.name for r in self.ready]

        self.submitted.update(self.ready)
        self.ready.clear()

        return ret

    def complete(self, name: str):
        node = self.topology.nodes[name]

        self.completed.add(node)
        self.submitted.remove(node)

        if self.cancelled:
            # if we cancelled than all pending nodes have been removed
            return

        to_ready = []

        for dependant in node.dependants(self.reverse):
            self.pending[dependant].remove(name)
            if not self.pending[dependant]:
                to_ready.append(dependant)
                self.ready.add(dependant)

        for ready in to_ready:
            self.pending.pop(ready)

    def __bool__(self) -> bool:
        if self.pending and not (self.ready or self.submitted):
            raise RuntimeError(f'Circular dependency detected: {[(p.name, w) for (p, w) in self.pending.items()]}')
        return bool(self.pending or self.ready or self.submitted)
