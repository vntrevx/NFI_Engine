from __future__ import annotations

import ast
import hashlib
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, override

TIMEFRAME_PATTERN: Final[re.Pattern[str]] = re.compile(r"^(?P<count>[1-9][0-9]*)(?P<unit>[mhd])$")
EXPECTED_CLASS_NAME: Final = "NostalgiaForInfinityX7"
REQUIRED_ARG_COUNT: Final = 10
USAGE: Final = (
    "usage: uv run scripts/x7_provenance.py --source <NostalgiaForInfinityX7.py> "
    "--commit <upstream-commit> --source-url <raw-url> --observed-at <YYYY-MM-DD> "
    "--output <artifact.md>\n"
)


@dataclass(frozen=True, slots=True)
class X7ProvenanceInputs:
    source_path: Path
    upstream_commit: str
    source_url: str
    observed_at: str
    output_path: Path


@dataclass(frozen=True, slots=True)
class X7Provenance:
    source_path: Path
    source_url: str
    observed_at: str
    upstream_commit: str
    raw_sha256: str
    byte_count: int
    strategy_class_name: str
    interface_version: int
    strategy_version: str
    base_timeframe: str
    informative_timeframes: tuple[str, ...]
    import_roots: tuple[str, ...]
    method_names: tuple[str, ...]

    @property
    def method_count(self) -> int:
        return len(self.method_names)


@dataclass(frozen=True, slots=True)
class X7ProvenanceError(Exception):
    code: str
    detail: str

    @override
    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


def build_x7_provenance(inputs: X7ProvenanceInputs) -> X7Provenance:
    source = inputs.source_path.read_text(encoding="utf-8")
    source_bytes = source.encode("utf-8")
    module = ast.parse(source, filename=inputs.source_path.as_posix())
    strategy_class = _find_strategy_class(module)
    base_timeframe = _class_string_assignment(strategy_class, "timeframe")
    return X7Provenance(
        source_path=inputs.source_path,
        source_url=inputs.source_url,
        observed_at=inputs.observed_at,
        upstream_commit=inputs.upstream_commit,
        raw_sha256=hashlib.sha256(source_bytes).hexdigest(),
        byte_count=len(source_bytes),
        strategy_class_name=strategy_class.name,
        interface_version=_class_int_assignment(strategy_class, "INTERFACE_VERSION"),
        strategy_version=_strategy_version(strategy_class),
        base_timeframe=base_timeframe,
        informative_timeframes=_informative_timeframes(strategy_class, base_timeframe),
        import_roots=_import_roots(module),
        method_names=_method_names(strategy_class),
    )


def render_markdown_report(provenance: X7Provenance) -> str:
    imports = ", ".join(f"`{name}`" for name in provenance.import_roots)
    timeframes = ", ".join(f"`{timeframe}`" for timeframe in provenance.informative_timeframes)
    methods = "\n".join(f"- `{name}`" for name in provenance.method_names)
    return (
        "# NFI X7 Provenance Artifact\n\n"
        "## Observation\n\n"
        f"- observed_at: `{provenance.observed_at}`\n"
        f"- source_url: `{provenance.source_url}`\n"
        f"- source_path: `{provenance.source_path.as_posix()}`\n"
        f"- upstream_commit: `{provenance.upstream_commit}`\n"
        f"- raw_sha256: `{provenance.raw_sha256}`\n"
        f"- byte_count: `{provenance.byte_count}`\n\n"
        "## Parsed Target Facts\n\n"
        f"- strategy_class: `{provenance.strategy_class_name}`\n"
        f"- interface_version: `{provenance.interface_version}`\n"
        f"- strategy_version: `{provenance.strategy_version}`\n"
        f"- base_timeframe: `{provenance.base_timeframe}`\n"
        f"- informative_timeframes: {timeframes}\n"
        f"- import_roots: {imports}\n"
        f"- method_count: `{provenance.method_count}`\n\n"
        "## Method Inventory\n\n"
        f"{methods}\n\n"
        "## Clean-room Boundary\n\n"
        "- This artifact records public provenance and structural metadata only.\n"
        "- It does not vendor, paste, translate, or summarize upstream strategy code bodies.\n"
        "- NFI Engine may use these facts as a behavior target for native typed modules.\n"
    )


def write_markdown_report(provenance: X7Provenance, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_markdown_report(provenance), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    try:
        inputs = _parse_args(args)
        provenance = build_x7_provenance(inputs)
        write_markdown_report(provenance, inputs.output_path)
    except X7ProvenanceError as exc:
        sys.stderr.write(f"X7_PROVENANCE_ERROR {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"X7_PROVENANCE_FILE_ERROR {exc}\n")
        return 1
    except SyntaxError as exc:
        sys.stderr.write(f"X7_PROVENANCE_SYNTAX_ERROR {exc.msg}\n")
        return 1
    sys.stdout.write(f"X7_PROVENANCE_OK {inputs.output_path.as_posix()}\n")
    return 0


def _parse_args(args: Sequence[str]) -> X7ProvenanceInputs:
    if len(args) != REQUIRED_ARG_COUNT:
        raise X7ProvenanceError(code="invalid_arg_count", detail=USAGE.strip())
    source = _arg_value(args, "--source")
    commit = _arg_value(args, "--commit")
    source_url = _arg_value(args, "--source-url")
    observed_at = _arg_value(args, "--observed-at")
    output = _arg_value(args, "--output")
    return X7ProvenanceInputs(
        source_path=Path(source),
        upstream_commit=commit,
        source_url=source_url,
        observed_at=observed_at,
        output_path=Path(output),
    )


def _arg_value(args: Sequence[str], flag: str) -> str:
    for index, value in enumerate(args):
        if value != flag:
            continue
        value_index = index + 1
        if value_index >= len(args):
            raise X7ProvenanceError(code="missing_arg_value", detail=flag)
        return args[value_index]
    raise X7ProvenanceError(code="missing_arg", detail=flag)


def _find_strategy_class(module: ast.Module) -> ast.ClassDef:
    for node in module.body:
        match node:
            case ast.ClassDef(name=name) if name == EXPECTED_CLASS_NAME:
                return node
            case _:
                continue
    raise X7ProvenanceError(code="missing_strategy_class", detail=EXPECTED_CLASS_NAME)


def _class_string_assignment(strategy_class: ast.ClassDef, name: str) -> str:
    for node in strategy_class.body:
        match node:
            case ast.Assign(targets=targets, value=ast.Constant(value=str(value))):
                if _assigns_name(targets, name):
                    return value
            case _:
                continue
    raise X7ProvenanceError(code="missing_string_assignment", detail=name)


def _class_int_assignment(strategy_class: ast.ClassDef, name: str) -> int:
    for node in strategy_class.body:
        match node:
            case ast.Assign(targets=targets, value=ast.Constant(value=int(value))):
                if _assigns_name(targets, name):
                    return value
            case _:
                continue
    raise X7ProvenanceError(code="missing_int_assignment", detail=name)


def _strategy_version(strategy_class: ast.ClassDef) -> str:
    for node in strategy_class.body:
        match node:
            case ast.FunctionDef(name="version") as version_function:
                for child in ast.walk(version_function):
                    match child:
                        case ast.Return(value=ast.Constant(value=str(version))):
                            return version
                        case _:
                            continue
            case _:
                continue
    raise X7ProvenanceError(code="missing_strategy_version", detail="version")


def _informative_timeframes(strategy_class: ast.ClassDef, base_timeframe: str) -> tuple[str, ...]:
    observed: set[str] = set()
    for node in ast.walk(strategy_class):
        match node:
            case ast.Constant(value=str(value)):
                if _is_timeframe(value) and value != base_timeframe:
                    observed.add(value)
            case _:
                continue
    return tuple(sorted(observed, key=_timeframe_minutes))


def _import_roots(module: ast.Module) -> tuple[str, ...]:
    roots: set[str] = set()
    for node in module.body:
        match node:
            case ast.Import(names=names):
                roots.update(alias.name.split(".", maxsplit=1)[0] for alias in names)
            case ast.ImportFrom(module=str(module_name)):
                roots.add(module_name.split(".", maxsplit=1)[0])
            case _:
                continue
    return tuple(sorted(roots))


def _method_names(strategy_class: ast.ClassDef) -> tuple[str, ...]:
    names: list[str] = []
    for node in strategy_class.body:
        match node:
            case ast.FunctionDef(name=name):
                names.append(name)
            case _:
                continue
    return tuple(names)


def _assigns_name(targets: Sequence[ast.expr], name: str) -> bool:
    for target in targets:
        match target:
            case ast.Name(id=target_name):
                if target_name == name:
                    return True
            case _:
                continue
    return False


def _is_timeframe(value: str) -> bool:
    return TIMEFRAME_PATTERN.fullmatch(value) is not None


def _timeframe_minutes(timeframe: str) -> int:
    match = TIMEFRAME_PATTERN.fullmatch(timeframe)
    if match is None:
        raise X7ProvenanceError(code="invalid_timeframe", detail=timeframe)
    count = int(match.group("count"))
    unit = match.group("unit")
    match unit:
        case "m":
            return count
        case "h":
            return count * 60
        case "d":
            return count * 60 * 24
        case unreachable:
            raise X7ProvenanceError(code="invalid_timeframe_unit", detail=unreachable)


if __name__ == "__main__":
    raise SystemExit(main())
