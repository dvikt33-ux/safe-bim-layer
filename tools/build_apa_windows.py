"""Build a verified Windows package from a Git revision, wheels and the existing APX."""

import argparse
from email.parser import BytesParser
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE = "docs/research/apa-results"
TDK_SOURCE = "03_Archicad_Template/External_Runtime/tdk_wall_ensure.py"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def hash_bytes(data):
    return hashlib.sha256(data).hexdigest()


def name_key(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def wheel_requirements(lock, wheelhouse):
    packages = {}
    for line in lock.decode("utf-8").splitlines():
        if line and not line.startswith("#"):
            name, version = line.split("==", 1)
            if name_key(name) in packages:
                raise ValueError(f"Duplicate locked distribution: {name}")
            packages[name_key(name)] = (name, version)
    wheels = {}
    for path in sorted(wheelhouse.glob("*.whl")):
        with zipfile.ZipFile(path) as archive:
            metadata_path, = [p for p in archive.namelist() if p.count("/") == 1 and p.endswith(".dist-info/METADATA")]
            metadata = BytesParser().parsebytes(archive.read(metadata_path), headersonly=True)
        name, version = name_key(metadata["Name"]), metadata["Version"]
        if name not in packages or packages[name][1] != version or name in wheels:
            raise ValueError(f"Wheel does not match the unique locked distribution: {path.name}")
        wheels[name] = path
    if set(packages) != set(wheels):
        raise ValueError("Missing wheels: " + ", ".join(sorted(set(packages) - set(wheels))))
    return [(packages[name][0], packages[name][1], wheels[name]) for name in sorted(packages)]


def archive_files(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for entry in archive.infolist():
            if not entry.is_dir():
                yield entry.filename, archive.read(entry)


def native_receipt(revision, path, receipt):
    binary = path.read_bytes()
    if (receipt["status"] != "BUILD_PASS_BINARY_IDENTITY_VERIFIED_NOT_INSTALLED"
            or len(binary) != receipt["bytes"] or hash_bytes(binary) != receipt["apxSHA256"]
            or receipt["buildIdentity"].encode("ascii") not in binary
            or receipt["sourceRevision"].encode("ascii") not in binary):
        raise ValueError("APX does not match the build receipt")
    pe = struct.unpack_from("<I", binary, 0x3C)[0]
    if binary[pe:pe + 4] != b"PE\0\0" or struct.unpack_from("<H", binary, pe + 4)[0] != 0x8664:
        raise ValueError("APX is not a Windows x64 binary")
    subprocess.run(["git", "diff", "--quiet", receipt["sourceRevision"], revision, "--", "archicad-addon"],
                   cwd=ROOT, check=True)
    return binary


def build(args):
    revision = git("rev-parse", args.revision + "^{commit}").decode("ascii").strip()
    knowledge = git("rev-parse", args.knowledge_revision + "^{commit}").decode("ascii").strip()
    lock = git("show", f"{revision}:requirements-apa.lock")
    wheels = wheel_requirements(lock, args.wheelhouse)
    receipt = json.loads(args.apx_receipt.read_text(encoding="utf-8-sig"))
    binary = native_receipt(revision, args.apx, receipt)
    sources = git("archive", "--format=zip", revision)
    knowledge_zip = git("archive", "--format=zip", knowledge, KNOWLEDGE)
    manifest = {"schema": "APA_WINDOWS_RELEASE_V1", "revision": revision, "knowledgeRevision": knowledge,
                "python": "CPython 3.11 x64", "buildStatus": "BUILD_SUCCESS",
                "runtimeVerification": "DEFERRED", "productionAcceptance": "PENDING",
                "wheelCount": len(wheels), "files": {}}
    args.output = args.output.resolve()
    temporary = args.output.with_suffix(".building.zip")
    if args.output.exists():
        raise FileExistsError(args.output)
    prefix = "APA-Windows/"
    with zipfile.ZipFile(temporary, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as archive:
        names = set()

        def write_member(name, data):
            entry = zipfile.ZipInfo(prefix + name)
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=5)

        def add(name, data):
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or name.casefold() in names:
                raise ValueError(f"Unsafe or repeated package member: {name}")
            names.add(name.casefold())
            write_member(name, data)
            manifest["files"][name] = {"bytes": len(data), "sha256": hash_bytes(data)}

        for name, data in archive_files(sources):
            add(name, data)
        for name, data in archive_files(knowledge_zip):
            add("knowledge/" + name, data)
        requirements = []
        for name, version, path in wheels:
            member = "wheels/" + path.name
            add(member, path.read_bytes())
            requirements.append(f"{name}=={version} --hash=sha256:{manifest['files'][member]['sha256']}")
        add("requirements-offline.txt", ("\n".join(requirements) + "\n").encode("ascii"))
        add("native/TapirAddOn_AC29_Win.apx", binary)
        add("native/binary-receipt.json", json.dumps({"binary": receipt}, indent=2).encode("utf-8"))
        if args.tdk_mirror:
            ref = git(f"--git-dir={args.tdk_mirror}", "rev-parse", args.tdk_revision + "^{commit}").decode("ascii").strip()
            source = git(f"--git-dir={args.tdk_mirror}", "show", f"{ref}:{TDK_SOURCE}")
            compile(source, "tdk_wall_ensure.py", "exec")
            add("local-components/tdk_wall_ensure.py", source)
            manifest["tdkRevision"] = ref
            manifest["deliveryScope"] = "LOCAL_WITH_PRIVATE_COMPONENT"
        write_member("apa-release.json", json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))
        archive.comment = revision.encode("ascii")

    with zipfile.ZipFile(temporary) as readback:
        if readback.testzip() is not None:
            raise ValueError("Archive CRC verification failed")
        actual_manifest = json.loads(readback.read(prefix + "apa-release.json"))
        if actual_manifest != manifest:
            raise ValueError("Archive manifest readback differs")
        for name, expected in manifest["files"].items():
            if hash_bytes(readback.read(prefix + name)) != expected["sha256"]:
                raise ValueError(f"Archive readback SHA-256 mismatch: {name}")
    temporary.rename(args.output)
    with args.output.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    with args.output.with_suffix(".sha256").open("x", encoding="ascii") as stream:
        stream.write(f"{digest}  {args.output.name}\n")
    return {"status": "BUILD_SUCCESS", "revision": revision, "archive": str(args.output),
            "archiveSha256": digest, "archiveBytes": args.output.stat().st_size,
            "filesVerified": len(manifest["files"]), "wheelCount": len(wheels),
            "knowledgeRevision": knowledge, "tdkRevision": manifest.get("tdkRevision"),
            "apxSha256": receipt["apxSHA256"], "runtimeVerification": "DEFERRED"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--knowledge-revision", required=True)
    parser.add_argument("--wheelhouse", type=Path, required=True)
    parser.add_argument("--apx", type=Path, required=True)
    parser.add_argument("--apx-receipt", type=Path, required=True)
    parser.add_argument("--tdk-mirror", type=Path)
    parser.add_argument("--tdk-revision")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if bool(args.tdk_mirror) != bool(args.tdk_revision):
        parser.error("--tdk-mirror and --tdk-revision must be supplied together")
    print(json.dumps(build(args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
