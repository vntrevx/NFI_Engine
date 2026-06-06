from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import override

from nfi_engine.sandbox.errors import SandboxError, SandboxErrorCode
from nfi_engine.sandbox.models import SandboxViolation, SandboxViolationKind

ENV_READ_CALLS = ("os.environ", "os.getenv")
FILESYSTEM_WRITE_CALLS = (
    "open",
    "Path.write_text",
    "Path.write_bytes",
    "Path.unlink",
    "Path.mkdir",
    "Path.rename",
    "Path.replace",
    "Path.rmdir",
)
NETWORK_IMPORTS = ("socket", "httpx", "requests", "urllib", "urllib.request")
NETWORK_CALLS = (
    "socket.create_connection",
    "socket.socket",
    "httpx.Client",
    "httpx.AsyncClient",
    "requests.get",
    "requests.post",
    "urllib.request.urlopen",
)
SUBPROCESS_IMPORTS = ("subprocess",)
SUBPROCESS_CALLS = (
    "subprocess.run",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
)
DIRECT_EXCHANGE_IMPORT_PREFIX = "nfi_engine.exchange"
DIRECT_EXCHANGE_CALLS = ("exchange.create_order", "create_order")
DIRECT_EXCHANGE_NAMES = ("ExchangeOrderRequest", "BybitTestnetAdapter")


def scan_strategy_source(path: Path, *, class_name: str) -> tuple[SandboxViolation, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    class_node = _find_class(tree=tree, class_name=class_name, path=path)
    visitor = SandboxVisitor()
    visitor.visit(class_node)
    return tuple(visitor.violations)


def _find_class(*, tree: ast.Module, class_name: str, path: Path) -> ast.ClassDef:
    for node in tree.body:
        match node:
            case ast.ClassDef(name=name) if name == class_name:
                return node
            case _:
                continue
    raise SandboxError(
        code=SandboxErrorCode.SANDBOX_STRATEGY_LOAD_ERROR,
        message=f"strategy class not found in source before import: {path}:{class_name}",
    )


@dataclass(slots=True)
class SandboxVisitor(ast.NodeVisitor):
    violations: list[SandboxViolation] = field(default_factory=list)

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self._check_import(alias.name, line=node.lineno)
        self.generic_visit(node)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module_name = "" if node.module is None else node.module
        self._check_import(module_name, line=node.lineno)
        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        name = _expression_name(node.func)
        if name is not None:
            self._check_call(name, line=node.lineno)
        self.generic_visit(node)

    @override
    def visit_Name(self, node: ast.Name) -> None:
        if node.id in DIRECT_EXCHANGE_NAMES:
            self._add(
                SandboxViolationKind.DIRECT_EXCHANGE_ACCESS,
                "direct exchange type access is not allowed",
                node.lineno,
            )
        self.generic_visit(node)

    def _check_import(self, module_name: str, *, line: int) -> None:
        if module_name in SUBPROCESS_IMPORTS:
            self._add(SandboxViolationKind.SUBPROCESS, "subprocess access is not allowed", line)
        if module_name in NETWORK_IMPORTS:
            self._add(SandboxViolationKind.NETWORK, "direct network access is not allowed", line)
        if module_name.startswith(DIRECT_EXCHANGE_IMPORT_PREFIX):
            self._add(
                SandboxViolationKind.DIRECT_EXCHANGE_ACCESS,
                "direct exchange access is not allowed",
                line,
            )

    def _check_call(self, name: str, *, line: int) -> None:
        if _starts_with_any(name, ENV_READ_CALLS):
            self._add(
                SandboxViolationKind.ENV_READ,
                "environment reads must go through typed config views",
                line,
            )
        if name in FILESYSTEM_WRITE_CALLS:
            self._add(
                SandboxViolationKind.FILESYSTEM_WRITE,
                "filesystem writes are not allowed from strategies",
                line,
            )
        if name in SUBPROCESS_CALLS:
            self._add(SandboxViolationKind.SUBPROCESS, "subprocess access is not allowed", line)
        if name in NETWORK_CALLS:
            self._add(SandboxViolationKind.NETWORK, "direct network access is not allowed", line)
        if name in DIRECT_EXCHANGE_CALLS:
            self._add(
                SandboxViolationKind.DIRECT_EXCHANGE_ACCESS,
                "direct exchange order access is not allowed",
                line,
            )

    def _add(self, kind: SandboxViolationKind, message: str, line: int) -> None:
        self.violations.append(SandboxViolation(kind=kind, message=message, line=line))


def _expression_name(node: ast.expr) -> str | None:
    match node:
        case ast.Name(id=name):
            return name
        case ast.Attribute(value=value, attr=attr):
            parent = _expression_name(value)
            if parent is None:
                return attr
            return f"{parent}.{attr}"
        case ast.Call(func=func):
            return _expression_name(func)
        case _:
            return None


def _starts_with_any(value: str, prefixes: tuple[str, ...]) -> bool:
    return any(value.startswith(prefix) for prefix in prefixes)
