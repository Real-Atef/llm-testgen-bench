"""``pymutant`` - a small, pure-stdlib AST mutation backend.

Each mutant is the original source with exactly ONE mutation applied. Mutants
are produced in a deterministic order (``ast.walk`` order), deduplicated by
unparsed source, capped, and only kept if they compile.

Operator set (as specified):
  comparison : <->  <= , > <-> >= , == <-> !=
  arithmetic : +  <-> - , * <-> //
  boolean    : and <-> or , not X -> X
  constant   : int n -> n+1 , True <-> False
  boundary   : slice/range integer arg n -> n+1   (a labelled subset of the
               constant operator: the +1 mutation on an int inside a slice or a
               range() call is reported as ``boundary`` rather than ``constant``)
  return     : return X -> return None
"""

from __future__ import annotations

import ast
import copy
from dataclasses import dataclass
from typing import Protocol

from .config import settings

_COMPARE_SWAP: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Lt: ast.LtE,
    ast.LtE: ast.Lt,
    ast.Gt: ast.GtE,
    ast.GtE: ast.Gt,
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
}
_ARITH_SWAP: dict[type[ast.operator], type[ast.operator]] = {
    ast.Add: ast.Sub,
    ast.Sub: ast.Add,
    ast.Mult: ast.FloorDiv,
    ast.FloorDiv: ast.Mult,
}


@dataclass(frozen=True)
class Mutant:
    index: int
    operator: str  # e.g. "comparison", "arithmetic", "constant", "boundary"
    mutation: str  # human label, e.g. "Lt->LtE", "int 3->4"
    lineno: int
    source: str


@dataclass(frozen=True)
class _Site:
    node_id: int
    kind: str
    sub: int
    operator: str
    mutation: str
    lineno: int


class MutationBackend(Protocol):
    def generate(self, source: str) -> list[Mutant]: ...


def _parents(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _is_boundary(node: ast.AST, parents: dict[int, ast.AST]) -> bool:
    cur = parents.get(id(node))
    while cur is not None:
        if isinstance(cur, ast.Slice):
            return True
        if isinstance(cur, ast.Call) and isinstance(cur.func, ast.Name) and cur.func.id == "range":
            return True
        cur = parents.get(id(cur))
    return False


class PyMutant:
    """The required, pure-stdlib mutation backend."""

    name = "pymutant"

    def _sites(self, tree: ast.AST) -> list[_Site]:
        parents = _parents(tree)
        sites: list[_Site] = []
        for node in ast.walk(tree):  # deterministic BFS order
            nid = getattr(node, "_mut_id")
            line = getattr(node, "lineno", 0)
            if isinstance(node, ast.Compare):
                for i, op in enumerate(node.ops):
                    if type(op) in _COMPARE_SWAP:
                        dst = _COMPARE_SWAP[type(op)].__name__
                        sites.append(_Site(nid, "compare_op", i, "comparison",
                                           f"{type(op).__name__}->{dst}", line))
            elif isinstance(node, ast.BinOp) and type(node.op) in _ARITH_SWAP:
                dst = _ARITH_SWAP[type(node.op)].__name__
                sites.append(_Site(nid, "binop", 0, "arithmetic",
                                   f"{type(node.op).__name__}->{dst}", line))
            elif isinstance(node, ast.BoolOp):
                dst = "Or" if isinstance(node.op, ast.And) else "And"
                sites.append(_Site(nid, "boolop", 0, "boolean",
                                   f"{type(node.op).__name__}->{dst}", line))
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                sites.append(_Site(nid, "not_unary", 0, "boolean", "drop-not", line))
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, bool):
                    sites.append(_Site(nid, "bool_const", 0, "constant",
                                       f"{node.value}->{not node.value}", line))
                elif isinstance(node.value, int):
                    boundary = _is_boundary(node, parents)
                    op = "boundary" if boundary else "constant"
                    sites.append(_Site(nid, "int_const", 0, op,
                                       f"int {node.value}->{node.value + 1}", line))
            elif isinstance(node, ast.Return) and node.value is not None:
                if not (isinstance(node.value, ast.Constant) and node.value.value is None):
                    sites.append(_Site(nid, "return_none", 0, "return",
                                       "return X->return None", line))
        return sites

    def generate(self, source: str) -> list[Mutant]:
        tree = ast.parse(source)
        for i, node in enumerate(ast.walk(tree)):
            node._mut_id = i  # type: ignore[attr-defined]

        original = ast.unparse(tree)
        sites = self._sites(tree)

        mutants: list[Mutant] = []
        seen: set[str] = {original}
        for site in sites:
            if len(mutants) >= settings.max_mutants:
                break
            mutated_tree = _apply(copy.deepcopy(tree), site)
            ast.fix_missing_locations(mutated_tree)
            try:
                mutant_src = ast.unparse(mutated_tree)
                compile(mutant_src, "<mutant>", "exec")
            except (SyntaxError, ValueError):
                continue
            if mutant_src in seen:  # equivalent / duplicate
                continue
            seen.add(mutant_src)
            mutants.append(
                Mutant(
                    index=len(mutants),
                    operator=site.operator,
                    mutation=site.mutation,
                    lineno=site.lineno,
                    source=mutant_src,
                )
            )
        return mutants

    def count_mutable_operators(self, source: str) -> int:
        """Distinct mutation sites (before dedup/cap). Used by the corpus check
        that guarantees every impl carries enough mutable structure."""
        tree = ast.parse(source)
        for i, node in enumerate(ast.walk(tree)):
            node._mut_id = i  # type: ignore[attr-defined]
        return len(self._sites(tree))


class _Applier(ast.NodeTransformer):
    def __init__(self, site: _Site):
        self.site = site

    def visit(self, node: ast.AST) -> ast.AST:
        node = self.generic_visit(node)  # recurse into children first
        if getattr(node, "_mut_id", None) != self.site.node_id:
            return node
        s = self.site
        if s.kind == "compare_op":
            assert isinstance(node, ast.Compare)
            node.ops[s.sub] = _COMPARE_SWAP[type(node.ops[s.sub])]()
            return node
        if s.kind == "binop":
            assert isinstance(node, ast.BinOp)
            node.op = _ARITH_SWAP[type(node.op)]()
            return node
        if s.kind == "boolop":
            assert isinstance(node, ast.BoolOp)
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
            return node
        if s.kind == "not_unary":
            assert isinstance(node, ast.UnaryOp)
            return node.operand
        if s.kind == "int_const":
            assert isinstance(node, ast.Constant)
            return ast.copy_location(ast.Constant(value=node.value + 1), node)
        if s.kind == "bool_const":
            assert isinstance(node, ast.Constant)
            return ast.copy_location(ast.Constant(value=not node.value), node)
        if s.kind == "return_none":
            return ast.copy_location(ast.Return(value=ast.Constant(value=None)), node)
        return node


def _apply(tree: ast.AST, site: _Site) -> ast.AST:
    return _Applier(site).visit(tree)


# Default backend instance used across the harness.
default_backend = PyMutant()
