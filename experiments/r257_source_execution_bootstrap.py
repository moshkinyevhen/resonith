import sys, os, ntpath; ROOT_TEXT = ntpath.dirname(ntpath.dirname(ntpath.abspath(__file__))); PREFIX_ROOT_TEXT = ntpath.join(ROOT_TEXT, "artifacts"); MARKER, VOLUME, FILE_ID, FINAL_PATH = "RESONITH_R257_STAGE1", "RESONITH_R257_PREFIX_VOLUME", "RESONITH_R257_PREFIX_FILE_ID", "RESONITH_R257_PREFIX_FINAL_PATH"; HASH_PROBE, REPARSE = -8560892508303650147, 0x400
def _arg(name: str) -> str: index = sys.argv.index(name) if sys.argv.count(name) == 1 else -1; _require(index >= 0 and index + 1 < len(sys.argv), RuntimeError(f"R-257 duplicate or missing {name}")); return sys.argv[index + 1]
def _same(left, right) -> bool: return ntpath.normcase(ntpath.abspath(str(left))) == ntpath.normcase(ntpath.abspath(str(right)))
def _require(ok, error) -> None: ok or (_ for _ in ()).throw(error)
def _plain_directory(path: str) -> bool:
    try: state = os.lstat(path)
    except OSError: return False
    return os.path.isdir(path) and not (getattr(state, "st_file_attributes", 0) & REPARSE)
def _prologue() -> tuple[bool, str]:
    stage1, prefix = "--stage1" in sys.argv, _arg("--stage0-prefix")
    _require(ntpath.isabs(prefix) and _same(ntpath.dirname(prefix), PREFIX_ROOT_TEXT), RuntimeError("R-257 prefix escaped its frozen root")); ancestors = (ntpath.splitdrive(ROOT_TEXT)[0] + "\\", ntpath.dirname(ROOT_TEXT), ROOT_TEXT, PREFIX_ROOT_TEXT); _require(_same(sys.pycache_prefix or "", prefix) and all(_plain_directory(path) for path in ancestors), RuntimeError("R-257 startup prefix or root mismatch"))
    _require(not stage1 or os.environ.get(MARKER) == "1" and _plain_directory(prefix), RuntimeError("R-257 unauthenticated Stage-1 entry")); _require(stage1 or os.environ.get(MARKER) is None and not os.path.exists(prefix), RuntimeError("R-257 Stage-0 prefix was not fresh")); stage1 or os.mkdir(prefix); return stage1, prefix
IS_STAGE1, PREFIX_TEXT = _prologue(); STARTUP_CACHES = tuple(sorted(getattr(module, "__cached__") for name, module in sys.modules.items() if (name == "encodings" or name.startswith("encodings.")) and getattr(module, "__cached__", None)))
import argparse, ast, ctypes, hashlib, importlib, importlib.abc, importlib.machinery, importlib.util, io, json, subprocess, threading, unittest; from ctypes import wintypes; from pathlib import Path; NAMESPACE_PATH = importlib._bootstrap_external._NamespacePath
class _Info(ctypes.Structure): _fields_ = [(name, wintypes.DWORD) for name in ("attributes", "created_low", "created_high", "access_low", "access_high", "write_low", "write_high", "volume_serial", "size_high", "size_low", "links", "file_index_high", "file_index_low")]
KERNEL = ctypes.WinDLL("kernel32", use_last_error=True)
KERNEL.CreateFileW.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE); KERNEL.CreateFileW.restype = wintypes.HANDLE; KERNEL.GetFileInformationByHandle.argtypes = (wintypes.HANDLE, ctypes.POINTER(_Info)); KERNEL.GetFileInformationByHandle.restype = wintypes.BOOL; KERNEL.GetFinalPathNameByHandleW.argtypes = (wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD); KERNEL.GetFinalPathNameByHandleW.restype = wintypes.DWORD; KERNEL.CloseHandle.argtypes = (wintypes.HANDLE,); KERNEL.CloseHandle.restype = wintypes.BOOL
def _sha(path: Path) -> str: return hashlib.sha256(path.read_bytes()).hexdigest()
def _under(path: Path, roots: tuple[Path, ...], resolved: bool = False) -> bool: candidate = path if resolved else path.resolve(strict=False); return any(candidate == root or root in candidate.parents for root in roots)
def _known(mapping: dict, key, grow: bool = False): return mapping[key] if key in mapping else mapping.setdefault(key,str(Path(key or os.getcwd()).resolve(strict=False))) if grow else (_ for _ in ()).throw(RuntimeError("R-257 unbound path observation"))
def _path_map(modules, extra=()) -> dict: return {value:Path(value).resolve(strict=False) for value in {value for module in modules for spec in (getattr(module,"__spec__",None),) for loader in (getattr(spec,"loader",None),) for value in (getattr(module,"__file__",None),getattr(spec,"origin",None),getattr(loader,"path",None),getattr(spec,"cached",None),*extra) if type(value) is str and value not in {"built-in","frozen"}}}
def _identity(path: Path) -> tuple[int, tuple[int, int, str]]:
    handle = KERNEL.CreateFileW(str(path), 0x80, 0x1 | 0x2, None, 3, 0x02000000, None); _require(handle != ctypes.c_void_p(-1).value, ctypes.WinError(ctypes.get_last_error()))
    info = _Info(); buffer = ctypes.create_unicode_buffer(32768)
    if not KERNEL.GetFileInformationByHandle(handle, ctypes.byref(info)) or info.attributes & REPARSE: KERNEL.CloseHandle(handle); raise RuntimeError("R-257 prefix identity is unavailable or reparse")
    size = KERNEL.GetFinalPathNameByHandleW(handle, buffer, len(buffer), 0); final = buffer.value.removeprefix("\\\\?\\")
    if not size or size >= len(buffer) or not _same(final, path): KERNEL.CloseHandle(handle); raise RuntimeError("R-257 prefix final path drift")
    return int(handle), (int(info.volume_serial), (int(info.file_index_high) << 32) | int(info.file_index_low), ntpath.normcase(ntpath.abspath(final)))
def _close(handle: int) -> None: _require(KERNEL.CloseHandle(handle), ctypes.WinError(ctypes.get_last_error()))
def _assert_prefix(path: Path, identity: tuple[int, int]) -> None:
    if not path.is_dir() or path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & REPARSE or any(path.iterdir()): raise RuntimeError("R-257 prefix is missing, nonempty, or reparse")
    handle, observed = _identity(path); _close(handle); _require(observed == identity, RuntimeError("R-257 prefix identity changed"))
def _record(record: dict, root: Path) -> Path:
    raw = Path(record["path"]); path = (raw if raw.is_absolute() else root / raw).resolve(strict=True); _require(_sha(path) == record["sha256"].lower(), RuntimeError(f"R-257 bound file drift: {record['path']}")); return path
def _tree(root: Path, caches: bool = False) -> str:
    root = Path(root); state = root.lstat(); files, stack = [], []
    if root.is_symlink() or getattr(state, "st_file_attributes", 0) & REPARSE: raise RuntimeError("R-257 runtime tree root is reparse")
    root = root.resolve(strict=True); digest = hashlib.sha256(b"resonith-r257-filtered-tree-1\0"); stack.append((root, ()))
    while stack:
        parent, parts = stack.pop()
        for entry in os.scandir(parent):
            relative, state = (*parts, entry.name), entry.stat(follow_symlinks=False); inside = "__pycache__" in relative[:-1]
            if entry.is_symlink() or getattr(state, "st_file_attributes", 0) & REPARSE: raise RuntimeError("R-257 runtime reparse entry")
            if entry.is_dir(follow_symlinks=False): (caches or entry.name != "__pycache__") and stack.append((Path(entry.path), relative))
            elif entry.is_file(follow_symlinks=False):
                accepted = caches and inside or not caches and not inside and Path(entry.name).suffix.lower() not in {".pyc", ".pyo"}
                if accepted: files.append(("/".join(relative).encode(), state.st_size, Path(entry.path)))
                elif not caches and not inside: raise RuntimeError("R-257 invalid runtime entry")
            else: raise RuntimeError("R-257 invalid runtime entry")
    for name, size, path in sorted(files): digest.update(b"F" + len(name).to_bytes(4, "little") + name + size.to_bytes(8, "little") + bytes.fromhex(_sha(path)))
    return digest.hexdigest()
def _document(path: Path, expected: str) -> dict: payload = path.resolve(strict=True).read_bytes(); _require(hashlib.sha256(payload).hexdigest() == expected.lower(), RuntimeError("R-257 authority SHA-256 mismatch")); value = json.loads(payload); _require(value.get("schema") == "resonith-r257-source-execution-authority-1", RuntimeError("R-257 authority schema mismatch")); _require(_same(value.get("prefix_root", ""), PREFIX_ROOT_TEXT), RuntimeError("R-257 authority prefix-root mismatch")); return value
def _canonical(value: dict) -> str: return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(",", ":")).encode()).hexdigest()
def _authority(path: Path, expected: str) -> dict:
    value = _document(path, expected); root, runtime = Path(ROOT_TEXT), Path(sys.executable).resolve(strict=True).parent; launcher = value["source_execution"]["r263_launcher_source"]; _require(hashlib.sha256(launcher.encode()).hexdigest() == value["source_execution"]["r263_launcher_sha256"], RuntimeError("R-263 launcher source drift")); _require(Path(value["source_execution"]["python_executable_path"]).resolve(strict=True) == Path(sys.executable).resolve(strict=True), RuntimeError("R-263 Python executable path drift")); declared = {**value["local_modules"], value["files"]["test_module"]["path"]: value["files"]["test_module"]["sha256"]}; mapped = {}
    for record in value["files"].values(): _record(record, root)
    for name, record in value["local_imports"].items():
        resolved = _record(record, root); relative = resolved.relative_to(root).as_posix(); _require(bool(name) and relative not in mapped and record.get("package") is (resolved.name == "__init__.py"), RuntimeError("R-257 local import map drift")); mapped[relative] = record["sha256"].lower()
    _require(mapped == {name: digest.lower() for name, digest in declared.items()}, RuntimeError("R-257 local source closure drift")); _require(not any(_sha((runtime / name).resolve(strict=True)) != digest.lower() for name, digest in value["runtime_files"].items()), RuntimeError("R-257 runtime file drift")); _require(not any(_tree(runtime / name) != digest.lower() for name, digest in value["runtime_trees"].items()), RuntimeError("R-257 runtime tree drift")); return value
def _binding(path: Path, expected: str, value: dict) -> tuple: return (str(path.resolve(strict=True)),expected.lower(),value,_canonical(value))
def _bound(path: Path, expected: str, binding: tuple) -> dict:
    resolved, digest, value, canonical = binding; _require((ACTIVE_AUTHORITY is None or binding is ACTIVE_AUTHORITY) and str(path.resolve(strict=True)) == resolved and expected.lower() == digest and _canonical(value) == canonical, RuntimeError("R-263 validated authority binding drift")); return value
def _finder(value, approved: tuple, paths: dict, grow: bool = False) -> tuple:
    if value is None: return ("none",)
    _require(type(value) is importlib.machinery.FileFinder, RuntimeError("R-257 unauthorized path importer")); table = tuple((suffix, loader.__module__, loader.__qualname__) for suffix, loader in value._loaders); _require(table == approved, RuntimeError("R-257 FileFinder loader-table drift")); return ("file", str(_known(paths,value.path,grow)).casefold(), id(value), tuple((*item, id(loader)) for item, (_suffix, loader) in zip(table, value._loaders)))
def _namespace(name: str, locations, site: Path) -> dict:
    if type(locations) is not NAMESPACE_PATH or len(values := tuple(locations)) != 1 or type(values[0]) is not str: raise ImportError(f"R-262 invalid namespace path: {name}")
    raw, root = values[0], Path(ntpath.abspath(str(site))); lexical = Path(ntpath.abspath(raw)); common = ntpath.normcase(ntpath.commonpath((str(root), str(lexical)))); _require(common == ntpath.normcase(str(root)), ImportError(f"R-262 namespace escaped lexical runtime: {name}"))
    parts = lexical.relative_to(root).parts; _require(bool(parts), ImportError(f"R-262 namespace equals runtime root: {name}")); chain = tuple(root.joinpath(*parts[:index]) for index in range(len(parts) + 1)); bad = next((path for path in chain if path.is_symlink() or getattr(path.lstat(), "st_file_attributes", 0) & REPARSE), None)
    _require(bad is None and (resolved := lexical.resolve(strict=True)).is_dir() and _under(resolved, (site,)), ImportError(f"R-262 invalid namespace directory: {name}")); return {"module":name,"namespace":True,"loader_type":"NamespaceLoader","raw_location":raw,"resolved_location":str(resolved)}
def _loaded_namespace(name: str, module, site: Path) -> dict:
    spec = getattr(module, "__spec__", None); loader = getattr(spec, "loader", None); locations = getattr(spec, "submodule_search_locations", None); valid = getattr(module, "__name__", None) == name and getattr(spec, "name", None) == name and type(loader) is importlib.machinery.NamespaceLoader and hasattr(module, "__file__") and module.__file__ is None and getattr(module, "__loader__", None) is loader and getattr(spec, "origin", object()) is None and getattr(module, "__path__", None) is locations; _require(valid, RuntimeError(f"R-262 loaded namespace drift: {name}")); return _namespace(name, locations, site)
class _Guard(importlib.abc.MetaPathFinder):  # Terminal source allowlist and sole owner of normal cache growth.
    def __init__(self, authority: dict) -> None:
        root, runtime, bootstrap = Path(ROOT_TEXT), Path(sys.executable).resolve().parent, _record(authority["files"]["bootstrap"], Path(ROOT_TEXT))
        self.root, self.local, self.bootstrap_path, self.bootstrap_raw = root, authority["local_imports"], bootstrap, str(bootstrap); self.bootstrap = ntpath.normcase(ntpath.abspath(self.bootstrap_raw)); self.site = Path(authority["site_packages"]).resolve(strict=True); self.runtime = (runtime, self.site); cache_values = {*sys.path_importer_cache,*(value.path for value in sys.path_importer_cache.values() if type(value) is importlib.machinery.FileFinder),self.bootstrap_raw}; self.cache_paths = {value:str(Path(value or os.getcwd()).resolve(strict=False)) for value in cache_values}; self.path_paths = {value:str(Path(value or os.getcwd()).resolve(strict=False)) for value in sys.path}; self.ledger = [{"cache_key_type":"builtins.str","cache_key":self.bootstrap_raw,"lexical_key":self.bootstrap,"resolved_target":str(self.bootstrap_path),"value_is_none":True,"finder":"none","startup":True}]; self.namespace_baseline = tuple(sorted((_loaded_namespace(name,module,self.site) for name,module in sys.modules.items() if type(getattr(getattr(module,"__spec__",None),"loader",None)) is importlib.machinery.NamespaceLoader),key=lambda item:item["module"])); self.approved = tuple(tuple(row) for row in authority["source_execution"]["file_finder_loaders"]); frozen = tuple((suffix, loader.__module__, loader.__qualname__) for loader, suffixes in ((importlib.machinery.ExtensionFileLoader, importlib.machinery.EXTENSION_SUFFIXES), (importlib.machinery.SourceFileLoader, importlib.machinery.SOURCE_SUFFIXES), (importlib.machinery.SourcelessFileLoader, importlib.machinery.BYTECODE_SUFFIXES)) for suffix in suffixes)
        if self.approved != frozen: raise RuntimeError("R-257 authority loader-table mismatch")
        self.path, self.path_value = sys.path, tuple(sys.path); self.hooks, self.hooks_value = sys.path_hooks, tuple(sys.path_hooks); self.argv, self.environment = tuple(sys.argv), tuple(sorted(os.environ.items())); self.finders = tuple(getattr(finder.find_spec, "__func__", finder.find_spec) for finder in (importlib.machinery.BuiltinImporter, importlib.machinery.FrozenImporter, importlib.machinery.PathFinder))
        self.cache, self.snapshot, self.meta = sys.path_importer_cache, self._snapshot(), None
    def _snapshot(self, grow: bool = False) -> tuple:
        if any(type(key) is not str for key in sys.path_importer_cache): raise RuntimeError("R-257 importer-cache key type drift")
        records = [(key,ntpath.normcase(ntpath.abspath(key or os.getcwd())),_known(self.cache_paths,key,grow),"builtins.str",_finder(value,self.approved,self.cache_paths,grow)) for key,value in sys.path_importer_cache.items()]; sentinel = (self.bootstrap_raw,self.bootstrap,str(self.bootstrap_path),"builtins.str",("none",))
        if records.count(sentinel) != 1 or len({lexical for _raw, lexical, _resolved, _type, _value in records}) != len(records) or any(not _under(Path(resolved),self.runtime,True) and record != sentinel for record in records for _raw,_lexical,resolved,_type,_value in (record,)) or any(type(item) is not str or item == self.bootstrap_raw or ntpath.normcase(ntpath.abspath(item or os.getcwd())) == self.bootstrap or _known(self.path_paths,item) == str(self.bootstrap_path) for item in sys.path) or _known(self.cache_paths,self.bootstrap_raw) != str(self.bootstrap_path): raise RuntimeError("R-257 importer-cache key drift")
        return tuple(sorted(records))
    def stable(self) -> None:
        if sys.path is not self.path or tuple(sys.path) != self.path_value or sys.path_hooks is not self.hooks or tuple(sys.path_hooks) != self.hooks_value or tuple(sys.argv) != self.argv or tuple(sorted(os.environ.items())) != self.environment or self.finders != tuple(getattr(finder.find_spec, "__func__", finder.find_spec) for finder in (importlib.machinery.BuiltinImporter, importlib.machinery.FrozenImporter, importlib.machinery.PathFinder)) or sys.path_importer_cache is not self.cache or self._snapshot() != self.snapshot: raise RuntimeError("R-257 launch or importer state drift")
        if self.meta is not None and tuple(sys.meta_path) != self.meta: raise RuntimeError("R-257 meta_path drift")
    def _accept(self, before: tuple) -> None:
        after = self._snapshot(True); old, new = {raw:(lexical,resolved,key_type,value) for raw,lexical,resolved,key_type,value in before}, {raw:(lexical,resolved,key_type,value) for raw,lexical,resolved,key_type,value in after}
        if any(key not in new or new[key] != value for key, value in old.items()): raise RuntimeError("R-257 importer-cache deletion or replacement")
        for key, (canonical, resolved, key_type, value) in new.items():
            if key not in old and not _under(Path(canonical), self.runtime): raise RuntimeError("R-257 importer-cache escaped runtime")
            if key not in old: self.ledger.append({"cache_key_type":key_type,"cache_key":key,"lexical_key":canonical,"resolved_target":resolved,"value_is_none":value[0] == "none","finder":value[0],"finder_path":value[1] if value[0] == "file" else None,"loaders":[list(row[:3]) for row in value[3]] if value[0] == "file" else []})
        self.snapshot = after
    def invalidate_caches(self): before = self.snapshot; importlib.machinery.PathFinder.invalidate_caches(); self._accept(before)
    def _checked(self, fullname: str, spec):
        if spec.loader is None and spec.origin is None and type(spec.submodule_search_locations) is NAMESPACE_PATH: return spec, _namespace(fullname, spec.submodule_search_locations, self.site)
        if any(raw and raw not in {"built-in", "frozen"} and not _under(Path(raw), self.runtime) for raw in [getattr(spec, "origin", None), *(spec.submodule_search_locations or ())]) or type(spec.loader) not in {importlib.machinery.SourceFileLoader, importlib.machinery.ExtensionFileLoader} or not _under(Path(spec.origin), self.runtime): raise ImportError(f"R-257 unauthorized runtime loader: {fullname}")
        return spec, None
    def find_spec(self, fullname: str, path=None, target=None):
        self.stable(); record = self.local.get(fullname); self.ledger.append({"attempt": fullname})
        if record is not None: source = _record(record, self.root); loader = importlib.machinery.SourceFileLoader(fullname, str(source)); self.ledger.append({"module": fullname, "path": str(source)}); return importlib.util.spec_from_file_location(fullname, source, loader=loader, submodule_search_locations=[str(source.parent)] if record.get("package") else None)
        spec = next((value for finder in (importlib.machinery.BuiltinImporter, importlib.machinery.FrozenImporter) if (value := finder.find_spec(fullname, path, target)) is not None), None)
        if spec is not None: return spec
        before = self.snapshot; spec = importlib.machinery.PathFinder.find_spec(fullname, path, target); self._accept(before)
        if spec is None: return None
        spec, namespace = self._checked(fullname, spec); self.ledger.append(namespace or {"module": fullname, "path": str(Path(spec.origin).resolve())}); return spec
def _ast_gate(authority: dict) -> None:
    blocked = {"path", "meta_path", "path_hooks", "path_importer_cache"}
    def flat(node): return [node] if isinstance(node, ast.Name) else sum((flat(item) for item in node.elts), []) if isinstance(node, (ast.Tuple, ast.List)) else []
    def chain(node):
        parts = []
        while isinstance(node, ast.Attribute): parts.append(node.attr); node = node.value
        return (node.id, *reversed(parts)) if isinstance(node, ast.Name) else ()
    sources = {**authority["local_modules"], authority["files"]["test_module"]["path"]: authority["files"]["test_module"]["sha256"]}
    for relative, digest in sources.items():
        path = Path(ROOT_TEXT, relative).resolve(strict=True); _require(_sha(path) == digest.lower(), RuntimeError(f"R-257 local source drift: {relative}"))
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path)); aliases = {"sys", *(alias.asname or alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names if alias.name == "sys")}
        assignments = tuple((node.value, node.targets if isinstance(node, ast.Assign) else (node.target,)) for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AnnAssign, ast.NamedExpr))); [aliases.add(target.id) for _pass in assignments for value, targets in assignments if flat(value) and any(name.id in aliases for name in flat(value)) for raw in targets for target in flat(raw)]
        if any(isinstance(node, ast.ImportFrom) and node.module == "sys" and any(alias.name in blocked for alias in node.names) for node in ast.walk(tree)): raise RuntimeError(f"R-257 import-state alias in {relative}")
        for node in ast.walk(tree):
            parts = chain(node); violation = len(parts) > 1 and parts[0] in aliases and parts[1] in blocked or isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"getattr", "setattr", "delattr", "vars"} and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id in aliases or isinstance(node, ast.Subscript) and chain(node.value)[:2] in {(alias, "__dict__") for alias in aliases} and isinstance(node.slice, ast.Constant) and node.slice.value in blocked; _require(not violation, RuntimeError(f"R-257 import-state access in {relative}"))
ACTIVE_GUARD = ACTIVE_AUTHORITY = None; PROGRESS_SEQUENCE = 0; PROGRESS_LOCK = threading.Lock()
class _Bounded(io.StringIO): write = lambda self,value: (_require(len(self.getvalue().encode()) + len(value.encode()) <= 4 << 20, RuntimeError("R-263 unittest output exceeded its bound")),io.StringIO.write(self,value))[1]
def _outer_progress(record: dict) -> None:
    global PROGRESS_SEQUENCE
    with PROGRESS_LOCK: PROGRESS_SEQUENCE += 1; payload = json.dumps({"record":record,"relay_sequence":PROGRESS_SEQUENCE,"schema":"resonith-r263-progress-relay-1"},sort_keys=True,separators=(",", ":")).encode(); os.write(2,b"R263_PROGRESS="+payload+b"\n")
def _progress(phase: str, label: str = "", completed: int = 0) -> None:
    global PROGRESS_SEQUENCE
    if os.environ.get("RESONITH_R263_PROGRESS") != "1": return
    if not IS_STAGE1: return _outer_progress({"completed":completed,"label":label,"phase":phase,"producer":"stage0","schema":"resonith-r263-progress-1","sequence":PROGRESS_SEQUENCE+1})
    with PROGRESS_LOCK: PROGRESS_SEQUENCE += 1; payload = json.dumps({"completed":completed,"label":label,"phase":phase,"producer":"stage1","schema":"resonith-r263-progress-1","sequence":PROGRESS_SEQUENCE},sort_keys=True,separators=(",", ":")).encode(); os.write(2,len(payload).to_bytes(4,"little")+payload)
def _install(authority: dict, authority_path: Path, authority_sha: str) -> _Guard:
    global ACTIVE_GUARD, ACTIVE_AUTHORITY
    site = Path(authority["site_packages"]).resolve(strict=True); runtime = Path(sys.executable).resolve().parent
    if site != (runtime / "Lib" / "site-packages").resolve(strict=True): raise RuntimeError("R-257 site-packages mismatch")
    _ast_gate(authority); sys.path.append(str(site)); guard = _Guard(authority); sys.meta_path = (guard,); guard.meta = tuple(sys.meta_path); guard.stable(); sys.addaudithook(lambda event, _args: guard.stable() if event == "import" else None); ACTIVE_GUARD = guard; ACTIVE_AUTHORITY = _binding(authority_path,authority_sha,authority); return guard
def _stage1_check(authority: dict, prefix: Path) -> tuple[int, int]:
    expected = {"MKL_NUM_THREADS":"1", "NUMEXPR_NUM_THREADS":"1", "OMP_NUM_THREADS":"1", "OPENBLAS_NUM_THREADS":"1", "PYTHONDONTWRITEBYTECODE":"1", "PYTHONHASHSEED":"0", "PYTHONPYCACHEPREFIX":str(prefix)}; flags = sys.flags.no_site and sys.flags.safe_path and sys.dont_write_bytecode and sys.flags.optimize == 0 and hash("resonith-r257") == HASH_PROBE; _require(flags and not any(os.environ.get(name) != value for name,value in expected.items()) and {name for name in os.environ if name.upper().startswith("PYTHON")} == {name for name in expected if name.startswith("PYTHON")},RuntimeError("R-257 Stage-1 flags or environment mismatch"))
    handle, identity = _identity(prefix); _close(handle); _require(identity == (int(os.environ.get(VOLUME, -1)), int(os.environ.get(FILE_ID, -1)), os.environ.get(FINAL_PATH, "")) and not any(prefix.iterdir()), RuntimeError("R-257 Stage-1 prefix receipt mismatch"))
    if any(name in authority["local_imports"] for name in sys.modules): raise RuntimeError("R-257 local import preceded guard")
    bootstrap = _record(authority["files"]["bootstrap"], Path(ROOT_TEXT)); main = sys.modules["__main__"]; _require(list(sys.orig_argv) == [sys.executable, "-S", "-P", "-B", "-X", f"pycache_prefix={prefix}", str(bootstrap), *sys.argv[1:]] and _same(bootstrap, __file__) and main.__spec__ is None and getattr(main, "__cached__", None) is None and type(getattr(main, "__loader__", None)) is importlib.machinery.SourceFileLoader, RuntimeError("R-257 bootstrap command or identity drift")); return identity
def _loaded_file(name: str, module, local: dict, by_name: dict, authorized: set, prefix: Path, allowed: tuple, paths: dict):
    spec, raw = getattr(module,"__spec__",None), getattr(module,"__file__",None); _require(raw is not None or name not in by_name,RuntimeError(f"R-257 loaded local identity is incomplete: {name}"))
    if raw is None or name == "__main__": return None
    source, loader, origin = _known(paths,raw), getattr(spec,"loader",None), getattr(spec,"origin",None)
    if origin in {"built-in","frozen"}:
        if loader not in {importlib.machinery.BuiltinImporter,importlib.machinery.FrozenImporter}: raise RuntimeError(f"R-257 frozen loader drift: {name}")
        return None
    if source in local:
        if (name,str(source)) not in authorized or type(loader) is not importlib.machinery.SourceFileLoader or getattr(module,"__loader__",None) is not loader or _known(paths,loader.path) != source or _known(paths,spec.origin) != source or not _under(_known(paths,spec.cached),(prefix,),True): raise RuntimeError(f"R-257 local loader drift: {name}")
    elif name in by_name or not _under(source,allowed,True) or type(loader) not in {importlib.machinery.SourceFileLoader,importlib.machinery.ExtensionFileLoader} or _known(paths,loader.path) != source or _known(paths,spec.origin) != source or type(loader) is importlib.machinery.SourceFileLoader and not _under(_known(paths,spec.cached),(prefix,),True): raise RuntimeError(f"R-257 loaded file escaped authority: {name}")
    return {"module":name,"path":str(source),"sha256":_sha(source)}
def _required(authority: dict, guard: _Guard, role: str, by_name: dict) -> None:
    root = Path(ROOT_TEXT); authorized = set(by_name.items()); used = {(item["module"],item["path"]) for item in guard.ledger if "path" in item and ((candidate := Path(item["path"])) == root or root in candidate.parents)}; _require(used <= authorized and not any(name not in sys.modules for name,_path in used) and set(authority["source_execution"]["required_local_imports"][role]) <= set(sys.modules), RuntimeError("R-257 local import ledger is incomplete"))
def _namespaces(guard: _Guard, namespaces: list) -> None:
    expected = [*guard.namespace_baseline,*[item for item in guard.ledger if item.get("namespace")]]; key = lambda item:(item["module"],item["raw_location"],item["resolved_location"]); _require(sorted(expected,key=key) == sorted(namespaces,key=key) and all(len({item[field] for item in namespaces}) == len(namespaces) for field in ("module","raw_location","resolved_location")), RuntimeError("R-262 namespace ledger drift"))
def _validate_loaded(authority: dict, guard: _Guard, prefix: Path, role: str) -> dict:
    root, runtime = Path(ROOT_TEXT), Path(sys.executable).resolve().parent; local = {(root/key).resolve(strict=True):value.lower() for key,value in authority["local_modules"].items()}; test = authority["files"]["test_module"]; local[_record(test,root)] = test["sha256"].lower(); site = Path(authority["site_packages"]).resolve(strict=True); allowed = (runtime,site); loaded, namespaces = [], []; paths = _path_map(tuple(sys.modules.values()))
    for source, expected in local.items(): _require(_sha(source) == expected, RuntimeError(f"R-257 local source drift: {source}"))
    by_name = {name:str(_record(record,root)) for name,record in authority["local_imports"].items()}; authorized = set(by_name.items())
    for name,module in tuple(sys.modules.items()):
        spec = getattr(module,"__spec__",None)
        if type(getattr(spec,"loader",None)) is importlib.machinery.NamespaceLoader or getattr(spec,"origin",object()) is None and getattr(spec,"submodule_search_locations",None) is not None: record = _loaded_namespace(name,module,site); loaded.append(record); namespaces.append(record)
        elif (record := _loaded_file(name,module,local,by_name,authorized,prefix,allowed,paths)) is not None: loaded.append(record)
    _required(authority,guard,role,by_name); _namespaces(guard,namespaces)
    identity = (int(os.environ[VOLUME]),int(os.environ[FILE_ID]),os.environ[FINAL_PATH]); _record(authority["files"]["bootstrap"],root); guard.stable(); _assert_prefix(prefix,identity); return {"imports":guard.ledger,"loaded":loaded,"namespace_baseline":guard.namespace_baseline,"prefix":{"file_id":identity[1],"final_path":identity[2],"path":str(prefix),"volume":identity[0]}}
def _child_state(prefix: Path, authority_path: Path, authority_sha: str, role: str, target: list[str], binding: tuple):
    bound = _bound(authority_path,authority_sha,binding); bootstrap = _record(bound["files"]["bootstrap"],Path(ROOT_TEXT))
    prefix.mkdir(); handle, identity = _identity(prefix); environment = {key: value for key, value in os.environ.items() if not key.upper().startswith("PYTHON") and key != MARKER}
    environment.update({"MKL_NUM_THREADS":"1", "NUMEXPR_NUM_THREADS":"1", "OMP_NUM_THREADS":"1", "OPENBLAS_NUM_THREADS":"1", "PYTHONDONTWRITEBYTECODE":"1", "PYTHONHASHSEED":"0", "PYTHONPYCACHEPREFIX":str(prefix), VOLUME:str(identity[0]), FILE_ID:str(identity[1]), FINAL_PATH:identity[2], MARKER:"1"})
    command = [sys.executable, "-S", "-P", "-B", "-X", f"pycache_prefix={prefix}", str(bootstrap), "--stage1", "--stage0-prefix", str(prefix), "--authority", str(authority_path.resolve()), "--expected-authority-sha256", authority_sha, "--role", role, "--target", *target]
    _bound(authority_path,authority_sha,binding); return command, environment, handle, identity
def finish_child(prefix: Path, handle: int, identity: tuple[int, int, str]) -> None:
    try: _assert_prefix(prefix, identity)
    finally: _close(handle)
    prefix.rmdir()
def worker_child(authority_path: Path, authority_sha: str, target: list[str]):
    nonce = hashlib.sha256(os.urandom(32)).hexdigest()[:24]; prefix = Path(PREFIX_ROOT_TEXT, f"worker-{os.getpid()}-{nonce}-s1"); _require(not prefix.exists(), FileExistsError("R-257 worker prefix collision"))
    if ACTIVE_AUTHORITY is None: raise RuntimeError("R-263 worker authority is unavailable")
    return prefix, _child_state(prefix,authority_path,authority_sha,"controller",target,ACTIVE_AUTHORITY)
def _stage1(arguments, authority: dict, prefix: Path) -> int:
    _stage1_check(authority, prefix)
    if arguments.role == "controller": sys.argv = [str(_record(authority["files"]["gate"], Path(ROOT_TEXT))), *arguments.target]
    guard = _install(authority,arguments.authority,arguments.expected_authority_sha256); _progress("stage1_full_closure")
    module = importlib.import_module("test_maf_source_filter_oracle" if arguments.role == "focused" else "r232_s15_source_filter_gate")
    if arguments.role == "focused":
        stream = _Bounded(); _progress("tests_start"); result = unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(module)); output = stream.getvalue(); _progress("tests_end",completed=result.testsRun); code = 0 if result.wasSuccessful() else 1
    else: module.main(); code = 0
    _require(_canonical(_document(arguments.authority,arguments.expected_authority_sha256)) == _canonical(authority), RuntimeError("R-263 Stage-1 authority content drift")); receipt = _validate_loaded(authority, guard, prefix, arguments.role); receipt.update({"authority_sha256": arguments.expected_authority_sha256.lower(), "role": arguments.role, "schema":"resonith-r263-stage1-receipt-1", "status":"PASS" if code == 0 else "FAIL"})
    _progress("stage1_endpoint"); print("R257_RECEIPT=" + json.dumps(receipt, sort_keys=True, separators=(",", ":"))); return code
def _relay_frames(source, errors: list) -> None:
    sequence = 0
    try:
        while header := source.read(4):
            if len(header) != 4: raise RuntimeError("R-263 truncated progress header")
            size = int.from_bytes(header,"little"); payload = b""
            while len(payload) < size and (chunk := source.read(size-len(payload))): payload += chunk
            if size < 2 or size > 4096 or len(payload) != size: raise RuntimeError("R-263 invalid progress frame")
            record = json.loads(payload); sequence += 1; _require(record.get("schema") == "resonith-r263-progress-1" and record.get("producer") == "stage1" and record.get("sequence") == sequence, RuntimeError("R-263 progress sequence drift")); _outer_progress(record)
    except BaseException as error: errors.append(error)
def _stage0(arguments, authority: dict, prefix: Path) -> int:
    if not (sys.flags.isolated and sys.flags.no_site and sys.flags.safe_path and sys.dont_write_bytecode and sys.flags.optimize == 0) or list(sys.orig_argv) != [sys.executable, "-I", "-S", "-B", "-X", f"pycache_prefix={prefix}", str(_record(authority["files"]["bootstrap"], Path(ROOT_TEXT))), *sys.argv[1:]]: raise RuntimeError("R-257 Stage-0 command or flags mismatch")
    if prefix.parent.resolve(strict=True) != (root := Path(PREFIX_ROOT_TEXT).resolve(strict=True)) or getattr(root.lstat(), "st_file_attributes", 0) & REPARSE: raise RuntimeError("R-257 prefix-root drift")
    runtime_cache = Path(sys.executable).resolve().parent / "Lib"; default_cache = _tree(runtime_cache, True)
    if not STARTUP_CACHES or any(not _under(Path(path), (prefix,)) for path in STARTUP_CACHES): raise RuntimeError("R-257 Stage-0 startup cache escaped its prefix")
    _progress("stage0_preflight"); handle0, identity0 = _identity(prefix); prefix1 = prefix.with_name(prefix.name.removesuffix("-s0") + "-s1")
    if prefix1.exists(): _close(handle0); raise RuntimeError("R-257 Stage-1 prefix was not fresh")
    try: command, environment, handle1, identity1 = _child_state(prefix1,arguments.authority,arguments.expected_authority_sha256,arguments.role,arguments.target,_binding(arguments.authority,arguments.expected_authority_sha256,authority))
    except BaseException: _close(handle0); raise
    try:
        child = subprocess.Popen(command,cwd=ROOT_TEXT,env=environment,shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE); output, errors = [], []; readers = (threading.Thread(target=lambda:output.append(child.stdout.read(4 << 20))),threading.Thread(target=_relay_frames,args=(child.stderr,errors)))
        for reader in readers: reader.start()
        child.wait(); [reader.join() for reader in readers]
        if errors or len(output) != 1 or len(output[0]) >= 4 << 20: raise errors[0] if errors else RuntimeError("R-263 Stage-1 stdout exceeded its bound")
        stdout = b"".join(output); sys.stdout.buffer.write(stdout); receipts = [json.loads(line.removeprefix(b"R257_RECEIPT=").decode()) for line in stdout.splitlines() if line.startswith(b"R257_RECEIPT=")]
        expected = {"file_id": identity1[1], "final_path": identity1[2], "path": str(prefix1), "volume": identity1[0]}
        if child.returncode != 0 or len(receipts) != 1 or receipts[0].get("schema") != "resonith-r263-stage1-receipt-1" or receipts[0].get("status") != "PASS" or receipts[0].get("prefix") != expected or receipts[0].get("authority_sha256") != arguments.expected_authority_sha256.lower() or receipts[0].get("role") != arguments.role or identity0 == identity1: raise RuntimeError("R-257 child failed or receipt was missing, reused, or mismatched")
        _assert_prefix(prefix, identity0); _authority(arguments.authority, arguments.expected_authority_sha256); _require(_tree(runtime_cache, True) == default_cache, RuntimeError("R-257 default runtime cache changed"))
        _progress("stage0_endpoint"); print("R257_STAGE0_RECEIPT=" + json.dumps({"authority_sha256":arguments.expected_authority_sha256.lower(), "child_command":command, "child_exit_code":child.returncode, "default_cache_sha256":default_cache, "role":arguments.role, "schema":"resonith-r263-stage0-receipt-1", "stage0":{"file_id":identity0[1], "final_path":identity0[2], "path":str(prefix), "volume":identity0[0]}, "stage1":expected, "startup_cache_paths":STARTUP_CACHES, "status":"PASS"}, sort_keys=True, separators=(",", ":"))); return child.returncode
    finally:
        try: finish_child(prefix1, handle1, identity1)
        finally: _close(handle0); _assert_prefix(prefix,identity0); prefix.rmdir()
def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--stage1", action="store_true"); parser.add_argument("--stage0-prefix", type=Path, required=True); parser.add_argument("--authority", type=Path, required=True); parser.add_argument("--expected-authority-sha256", required=True); parser.add_argument("--role", choices=("focused", "controller"), required=True); parser.add_argument("--target", nargs=argparse.REMAINDER, default=[]); arguments = parser.parse_args()
    if any(sys.argv.count(name) != 1 for name in ("--stage0-prefix", "--authority", "--expected-authority-sha256", "--role", "--target")) or sys.argv.count("--stage1") != int(IS_STAGE1) or arguments.stage1 != IS_STAGE1 or not _same(arguments.stage0_prefix, PREFIX_TEXT): raise RuntimeError("R-257 argument or prologue mismatch")
    authority = _authority(arguments.authority, arguments.expected_authority_sha256); return (_stage1 if arguments.stage1 else _stage0)(arguments, authority, arguments.stage0_prefix.resolve(strict=True))
if __name__ == "__main__": raise SystemExit(main())
