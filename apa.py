"""ArchiCAD Project Accelerator command line."""

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
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
    if schema == "apa-semantic-project-brief/1":
        return core.compile_project_brief(intent)
    if schema == "apa-project-design/1":
        from apa_project_design import compile_design

        return compile_design(intent)
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
    cmd = commands.add_parser("design-request", help="Подготовить исходное текстовое задание для GPT")
    cmd.add_argument("--source", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("design-select", help="Выбрать проверенный проектный вариант для предконтроля")
    cmd.add_argument("--intent", type=Path, required=True)
    cmd.add_argument("--variant", required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("design-diff", help="Определить, что требует сверки после изменения проектного варианта")
    cmd.add_argument("--previous", type=Path, required=True)
    cmd.add_argument("--current", type=Path, required=True)
    cmd.add_argument("--variant", required=True)
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
    selection = cmd.add_mutually_exclusive_group(required=True)
    selection.add_argument("--guids", type=Path)
    selection.add_argument("--all-dump-elements", action="store_true")
    cmd.add_argument("--story", type=int, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    commands.add_parser("template-check", help="Проверить локальные спецификации шаблона")
    commands.add_parser("template-runtime", help="Действующий интерфейс инвентаризации и настройки шаблона")
    commands.add_parser("project-runtime", help="Действующий интерфейс SceneWriter для проекта")
    commands.add_parser("connected-runtime", help="Существующие связные операции крыши и MEP через SceneWriter")
    cmd = commands.add_parser("architecture-stage", help="Подготовить свежую тестовую копию для оболочки или выбранного варианта")
    cmd.add_argument("--job", type=Path, required=True)
    cmd.add_argument("--intent", type=Path, required=True)
    cmd.add_argument("--donor", type=Path, required=True)
    cmd.add_argument("--donor-sha256", required=True)
    cmd.add_argument("--baseline-trace", type=Path, required=True)
    cmd.add_argument("--port", type=int, default=19723)
    cmd = commands.add_parser("architecture-runtime", help="Операции на подготовленной изолированной копии")
    cmd.add_argument("phase", choices=("status", "native-read", "preflight", "execute", "check-closed", "verify-reopen"))
    cmd.add_argument("--job", type=Path, required=True)
    cmd.add_argument("--port", type=int)
    cmd.add_argument("--output", type=Path, help="Новый файл инвентаря для native-read")
    cmd.add_argument("--shared-native-lock", action="store_true", help=argparse.SUPPRESS)
    cmd.add_argument("--discover-test-port", action="store_true", help=argparse.SUPPRESS)
    cmd.add_argument("--expected-stage-sha", help=argparse.SUPPRESS)
    cmd.add_argument("--confirm-preflight", help="SHA-256 approved-preflight.json для записи авторского варианта")
    commands.add_parser("group-runtime", help="Действующий протокол нативных групп и сверки PLN")
    commands.add_parser("archicad-startup", help="Диагностика запуска проверенной тестовой копии Archicad")
    commands.add_parser("mcp-control", help="Приватный MCP для типизированных операций APA")
    commands.add_parser("source-batch", help="Существующий протокол пакетного создания по подтверждённым источникам")
    commands.add_parser("source-batch-reconcile", help="Сверка прерванного пакетного создания по источникам")
    commands.add_parser("mailbox", help="Приёмник APA с квитанциями и профилем чтения")
    commands.add_parser("bureau", help="Очередь и существующий диспетчер бюро")
    commands.add_parser("knowledge", help="Запросы, пересборка индекса и MCP для настроенного источника")
    cmd = commands.add_parser("mailbox-profile", help="Связать приёмник чтения с проверенной копией PLN")
    cmd.add_argument("--state", type=Path, required=True)
    cmd.add_argument("--port", type=int, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("bureau-profile", help="Подготовить отдельную конфигурацию бюро для этой сборки")
    cmd.add_argument("--config", type=Path, required=True)
    cmd.add_argument("--profile", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("tdk-wall", help="Подготовить или сверить Wall.Ensure")
    cmd.add_argument("--payload", type=Path, required=True)
    cmd.add_argument("--profile", type=Path)
    cmd.add_argument("--journal", type=Path)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("tdk-trace-stage", help="Подготовить новую копию PLN для испытания AI_TRACE")
    cmd.add_argument("--source", type=Path, required=True)
    cmd.add_argument("--payload", type=Path, required=True)
    cmd.add_argument("--job", type=Path, required=True)
    cmd = commands.add_parser("tdk-trace", help="Сверить или применить изменение AI_TRACE в тестовой копии")
    cmd.add_argument("--job", type=Path, required=True)
    cmd.add_argument("--port", type=int, required=True)
    cmd.add_argument("--confirm-preflight", help="SHA-256 проверенного предконтроля для одной записи")
    cmd = commands.add_parser("library-pack", help="Подготовить привязанный к источнику комплект проекта")
    cmd.add_argument("--brief", type=Path, required=True)
    cmd.add_argument("--candidate", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("knowledge-query", help="Запрос к включённому снимку реестра APA")
    cmd.add_argument("--query", required=True)
    cmd.add_argument("--mode", dest="knowledge_mode", choices=("plan", "research"), default="plan")
    cmd.add_argument("--cache", type=Path, required=True)
    cmd.add_argument("--output", type=Path, required=True)
    cmd = commands.add_parser("arena-receipt", help="Прочитать локальную квитанцию завершения Arena")
    cmd.add_argument("--receipt", type=Path, required=True)
    cmd.add_argument("--intent", type=Path, help="Отдельный типизированный вход APA для подготовки плана")
    cmd.add_argument("--output", type=Path, required=True)
    return cli


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        routes = {"project-runtime": ("archicad_project_accelerator", "main"),
                  "connected-runtime": ("archicad_connected_components", "main"),
                  "group-runtime": ("apa_ac29_group_batch_oneshot", "main"),
                  "archicad-startup": ("apa_archicad_startup", "main"),
                  "mcp-control": ("apa_control_mcp", "main"),
                  "template-runtime": ("archicad_template_builder", "main"),
                  "source-batch": ("apa_source_qualified_native_batch", "cli"),
                  "source-batch-reconcile": ("apa_reconcile_source_batch_save", "cli"),
                  "mailbox": ("apa_ac29_autonomous_job_bridge", "main"),
                  "bureau": ("bureau_unified_service", "main"),
                  "knowledge": ("archicad_knowledge_access", "main")}
        if argv and argv[0] in routes:
            from importlib import import_module

            module, entry = routes[argv[0]]
            return getattr(import_module(module), entry)(argv[1:])
        args = parser().parse_args(argv)
        code = 0
        if args.mode == "doctor":
            result = doctor()
            code = 0 if result["status"] == "LOCAL_ENV_READY" else 2
        elif args.mode == "design-request":
            from apa_project_design import read_request

            result = read_request(args.source, ROOT / "examples/accelerator/r04-project-design.json")
            write_json(args.output, result)
        elif args.mode == "design-select":
            from apa_project_design import select_variant

            selected = select_variant(read_json(args.intent), args.variant)
            write_json(args.output, selected)
            result = dict(status="AUTHORED_INPUT_FOR_NATIVE_PREFLIGHT", variant=args.variant,
                          executionPermission=False, output=str(args.output))
        elif args.mode == "design-diff":
            from apa_project_design import changes_between

            result = changes_between(read_json(args.previous), read_json(args.current), args.variant)
            write_json(args.output, result)
        elif args.mode == "template-check":
            from archicad_template_builder import validate_specs

            result = validate_specs()
            code = 0 if result["status"] == "PASS" else 2
        elif args.mode == "mailbox-profile":
            from apa_mailbox_profile import make_profile

            result = make_profile(ROOT, args.state, args.port)
            write_json(args.output, result)
        elif args.mode == "bureau-profile":
            from apa_mailbox_profile import PackageProfile
            from bureau_unified_service import validate_config

            profile_path = args.profile.resolve(strict=True)
            profile = PackageProfile(ROOT, profile_path)
            config = validate_config(dict(read_json(args.config), apaEnabled=True,
                                          apaProfile=str(profile_path), dispatchArmed=False))
            write_json(args.output, config)
            result = {"status": "BUREAU_CONFIGURATION_PREPARED", "revision": profile.release["revision"],
                      "configuration": str(args.output.resolve()), "targets": len(config["targets"]),
                      "dispatchArmed": False, "nativeCalls": 0}
        elif args.mode == "tdk-wall":
            from apa_tdk_wall import inspect_wall

            if args.output.exists():
                raise FileExistsError(args.output)
            result = inspect_wall(ROOT, args.payload, args.profile, args.journal,
                                  args.output.with_suffix(".evidence"))
            write_json(args.output, result)
        elif args.mode == "tdk-trace-stage":
            from apa_tdk_wall import stage_trace

            result = stage_trace(ROOT, args.job, args.source, args.payload)
        elif args.mode == "tdk-trace":
            from apa_tdk_wall import run_trace

            result = run_trace(ROOT, args.job, args.port, confirm=args.confirm_preflight)
            code = 2 if result["status"] == "STOPPED_RECONCILE_NO_AUTORETRY" else 0
        elif args.mode == "library-pack":
            from archicad_project_library_pack import compile_pack

            result = compile_pack(read_json(args.brief), read_json(args.candidate))
            write_json(args.output, result)
        elif args.mode == "architecture-stage":
            from apa_r03_architecture import stage

            result = stage(args.job.resolve(), args.intent.resolve(strict=True), args.port,
                           args.donor.resolve(strict=True), args.donor_sha256, args.baseline_trace.resolve(strict=True))
        elif args.mode == "architecture-runtime":
            from contextlib import nullcontext
            from apa_ac29_autonomous_job_bridge import acquire_singleton
            from apa_integrated_services import architecture_phase

            if (args.output is not None) != (args.phase == "native-read"):
                raise ValueError("APA_ARCHITECTURE_OUTPUT_ONLY_FOR_NATIVE_READ")
            with acquire_singleton(shared=True) if args.shared_native_lock else nullcontext():
                result = architecture_phase(ROOT, args.job, args.phase, args.port,
                                            confirm_preflight=args.confirm_preflight, output=args.output,
                                            discover_port=args.discover_test_port,
                                            expected_stage_sha=args.expected_stage_sha)
            if args.phase == "preflight" and result.get("status") != "READY_FOR_EXPLICIT_TEST_RUN":
                code = 2
        elif args.mode == "knowledge-query":
            from apa_integrated_services import knowledge_query

            result = knowledge_query(ROOT, args.cache, args.query, args.knowledge_mode)
            write_json(args.output, result)
            code = 0 if result["status"] == "OK" else 2
        elif args.mode == "arena-receipt":
            from apa_integrated_services import arena_receipt

            result = arena_receipt(args.receipt, args.intent)
            write_json(args.output, result)
        else:
            router = load_router(args.semantic_profile)
            if args.mode == "catalog":
                result = catalog(router, args.query, args.contracts)
            elif args.mode == "plan":
                raw = args.intent.read_bytes()
                try:
                    intent = json.loads(raw.decode("utf-8-sig"))
                except json.JSONDecodeError as exc:
                    raise ValueError("Текстовое задание подайте через apa design-request") from exc
                if not isinstance(intent, dict):
                    raise ValueError("APA_PLAN_REQUIRES_JSON_OBJECT")
                result = compile_plan(router, intent)
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
                    "a": str(args.native_dump), "guids": None if args.all_dump_elements else read_json(args.guids),
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
