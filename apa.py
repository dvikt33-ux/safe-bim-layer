"""ArchiCAD Project Accelerator command line."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    payload = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(payload)


def doctor():
    packages = {}
    for row in (ROOT / "requirements-apa.lock").read_text(encoding="utf-8").splitlines():
        if not row or row.startswith("#"):
            continue
        name, required = row.split("==", 1)
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            installed = None
        packages[name] = {"required": required, "installed": installed, "match": installed == required}
    supported = (sys.version_info[:2] == (3, 11) and platform.system() == "Windows"
                 and sys.maxsize > 2**32)
    return {"status": "LOCAL_ENV_READY" if supported and all(p["match"] for p in packages.values())
            else "LOCAL_ENV_INCOMPLETE", "python": sys.version.split()[0],
            "supportedPython": supported, "platform": platform.system(), "packages": packages,
            "archicadRuntime": "NOT_PROBED", "semanticModels": "OPTIONAL_OPERATOR_PROFILE"}


def load_router(semantic_profile=None):
    import apa_ac29_installed_group_provider as group
    import apa_file_providers as files
    import archicad_project_accelerator as core

    if semantic_profile:
        semantic_profile = semantic_profile.resolve(strict=True)
        if read_json(semantic_profile).get("schema") != "APA_SEMANTIC_ML_VENDOR_CONFIG_V1":
            raise ValueError("APA_SEMANTIC_PROFILE_SCHEMA_INVALID")
    router = core.native_command_router(core.RUN.DEFAULT_SCENE_SCHEMA)
    group.attach(router)
    files.attach(router, semantic_profile=semantic_profile)
    return router


def catalog(router, query, contracts):
    matches = {}
    for name, command in sorted(router.catalog["commands"].items()):
        if query.casefold() in name.casefold():
            matches[name] = {"api": command["api"], "kind": router.operation_kind(name),
                             "contractHash": router.contract_hash(name)}
            if contracts:
                matches[name].update(parameters=command["parameters"], returns=command["returns"])
    return {"status": "SOURCE_CATALOG", "catalogHash": router.fingerprint,
            "nativeRuntime": "NOT_PROBED", "count": len(matches), "commands": matches}


def compile_plan(router, intent):
    import archicad_project_accelerator as core

    schema = intent.get("schemaVersion")
    if schema in {"archicad-project-intent/1", "apa-native-task/1"}:
        return core.compile_intent(intent, core.RUN.DEFAULT_SCENE_SCHEMA, router)
    if schema == "apa-native-optimizer/1":
        return core.prepare_optimized_native_task(router, intent)
    return core.prepare_auto_optimized_native_task(router, intent)


def check_local(router, command):
    entry = router.catalog["commands"].get(command)
    if not entry or entry["api"] != "local-python" or router.operation_kind(command) != "READ_ONLY":
        raise ValueError("APA_LOCAL_READ_COMMAND_REQUIRED:" + command)


def run_local(router, command, parameters):
    check_local(router, command)
    return router.read(None, router.prepare(command, parameters), reviewed_read_only=True)


def run_read_workflow(router, graph):
    for step in graph["operations"]:
        check_local(router, step["command"])
    return router.run_workflow(None, router.prepare_workflow(graph))


def exchange(router, source, destination, page):
    import apa_dxf_source_preflight as dxf
    from apa_high_density_readonly_v2 import digest

    source = source.resolve(strict=True)
    suffix = source.suffix.lower()
    if not source.is_file() or suffix not in {".dxf", ".ifc", ".pdf"}:
        raise ValueError("APA_EXCHANGE_REQUIRES_DXF_IFC_OR_PDF")
    destination = destination.resolve()
    destination.mkdir()
    before = digest(source)

    commands = {
        ".dxf": ("AddOn.APAHighDensityReadOnlyV2.DXFLayerInventory",
                 "AddOn.APAHighDensityReadOnlyV2.DXFBlockInsertions"),
        ".ifc": ("AddOn.APAHighDensityReadOnlyV2.IFCSchemaInventory",
                 "AddOn.APAExternalReadOnly.IFCQuantities"),
        ".pdf": ("AddOn.APASemantic.PDFPaths", "AddOn.APASemantic.PDFPageRaster"),
    }
    report = {"schema": "APA_EXCHANGE_WORKFLOW_V1", "source": str(source), "sourceSha256": before,
              "modelWrites": 0, "nativeCalls": 0}
    try:
        if suffix == ".dxf":
            report["preflight"] = run_local(router, dxf.CMD,
                                            {"a": str(source), "output": str(destination / "preflight.json")})
            if not report["preflight"]["result"]["readyForFurtherSourceAnalysis"]:
                report["status"] = "DXF_PREFLIGHT_REVIEW_REQUIRED"
                write_json(destination / "report.json", report)
                return report
        operations = []
        for command in commands[suffix]:
            name = command.rsplit(".", 1)[-1]
            parameters = {"a": str(source), "output": str(destination / (name + ".json"))}
            if suffix == ".pdf":
                parameters["page"] = page
            operations.append({"id": name, "command": command, "params": parameters})
        workflow = run_read_workflow(router, {"operations": operations})
        if digest(source) != before:
            raise ValueError("APA_EXCHANGE_SOURCE_CHANGED")
        report.update(status="LOCAL_EXCHANGE_VERIFIED", workflow={
            key: workflow[key] for key in ("status", "sourcePlanHash", "trace", "automaticRetry")})
    except (ValueError, OSError, ImportError, RuntimeError) as exc:
        report.update(status="EXCHANGE_BLOCKED", reason=str(exc))
        write_json(destination / "report.json", report)
        raise
    write_json(destination / "report.json", report)
    return report


def parser():
    cli = argparse.ArgumentParser(description="ArchiCAD Project Accelerator")
    cli.add_argument("--semantic-profile", type=Path, help="Локальный профиль доверенных ML-моделей")
    commands = cli.add_subparsers(dest="mode", required=True)
    commands.add_parser("doctor", help="Проверить версии Python и зависимостей")
    cmd = commands.add_parser("catalog", help="Найти команду и получить её контракт")
    cmd.add_argument("query", nargs="?", default="")
    cmd.add_argument("--contracts", action="store_true")
    cmd = commands.add_parser("plan", help="Подготовить BIM Graph или нативное задание")
    cmd.add_argument("--intent", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("run-local", help="Выполнить локальную аналитическую команду")
    cmd.add_argument("command")
    cmd.add_argument("--params", type=Path, required=True)
    cmd = commands.add_parser("run-read-workflow", help="Выполнить граф локальных аналитических команд")
    cmd.add_argument("--graph", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("exchange", help="Проверить исходный DXF, IFC или PDF и сохранить отчёт")
    cmd.add_argument("source", type=Path)
    cmd.add_argument("--output", type=Path, required=True)
    cmd.add_argument("--page", type=int, default=1)
    cmd = commands.add_parser("documentation", help="Собрать документацию по снимку модели")
    cmd.add_argument("--native-dump", type=Path, required=True)
    cmd.add_argument("--guids", type=Path, required=True)
    cmd.add_argument("--story", type=int, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    commands.add_parser("template-check", help="Проверить локальные спецификации шаблона")
    commands.add_parser("project-runtime", help="Действующий интерфейс SceneWriter для проекта")
    commands.add_parser("group-runtime", help="Действующий протокол нативных групп и сверки PLN")
    return cli


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv and argv[0] == "project-runtime":
            from archicad_project_accelerator import main as project_main

            return project_main(argv[1:])
        if argv and argv[0] == "group-runtime":
            from apa_ac29_group_batch_oneshot import main as group_main

            return group_main(argv[1:])
        args = parser().parse_args(argv)
        code = 0
        if args.mode == "doctor":
            result = doctor()
            code = 0 if result["status"] == "LOCAL_ENV_READY" else 2
        elif args.mode == "template-check":
            from archicad_template_builder import validate_specs

            result = validate_specs()
            code = 0 if result["status"] == "PASS" else 2
        else:
            router = load_router(args.semantic_profile)
            if args.mode == "catalog":
                result = catalog(router, args.query, args.contracts)
            elif args.mode == "plan":
                raw = args.intent.read_bytes()
                result = compile_plan(router, json.loads(raw.decode("utf-8-sig")))
                result = dict(result, inputSha256=hashlib.sha256(raw).hexdigest(), executionPermission=False)
                write_json(args.output, result)
            elif args.mode == "run-local":
                result = run_local(router, args.command, read_json(args.params))
            elif args.mode == "run-read-workflow":
                if args.output.exists():
                    raise FileExistsError(args.output)
                result = run_read_workflow(router, read_json(args.graph))
                write_json(args.output, result)
            elif args.mode == "exchange":
                result = exchange(router, args.source, args.output, args.page)
                code = 0 if result["status"] == "LOCAL_EXCHANGE_VERIFIED" else 2
            else:
                from apa_file_providers import DOCUMENTATION

                result = run_local(router, DOCUMENTATION, {
                    "a": str(args.native_dump), "guids": read_json(args.guids),
                    "story": args.story, "output": str(args.output),
                })
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return code
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "type": type(exc).__name__, "reason": str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
