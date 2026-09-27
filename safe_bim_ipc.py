"""Validated localhost JSON controls. 'active' is a read alias, never a command target."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse, unquote
import hmac
import json
import secrets
from safe_bim_runtime import ExecutorError, TERMINAL, valid_job_id

MAX_BODY = 4096
ACTIONS = {'continue', 'pause', 'stop'}


def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON field')
            result[key] = value
        return result
    def bad_constant(_):
        raise ValueError('non-finite JSON number')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)


class PaletteHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True
    request_queue_size = 64

    def __init__(self, address, executor):
        if address[0] not in {'127.0.0.1', 'localhost'}:
            raise ValueError('Safe BIM IPC must bind to localhost')
        self.executor = executor
        self.capability = secrets.token_urlsafe(32)
        super().__init__(address, PaletteHandler)


class PaletteHandler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        return

    def _send(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.end_headers()
        try:
            self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError):
            pass  # response loss never starts another worker

    def _local_origin(self):
        try:
            hosts = self.headers.get_all('Host', [])
            if len(hosts) != 1:
                return False
            host = urlparse('http://' + hosts[0])
            if host.username or host.path or host.hostname not in {'127.0.0.1', 'localhost'} or host.port != self.server.server_address[1]:
                return False
            origins = self.headers.get_all('Origin', [])
            if not origins:
                return True  # native controller; mutation still requires capability
            if len(origins) != 1:
                return False
            origin = urlparse(origins[0])
            return (origin.scheme == 'http' and origin.hostname == host.hostname
                    and origin.port == host.port and not origin.path and not origin.username)
        except ValueError:
            return False

    def do_OPTIONS(self):
        return self._send(405, {'error': 'cross-origin controls are not supported'})

    def do_GET(self):
        if not self._local_origin():
            return self._send(403, {'error': 'origin/host rejected'})
        parsed = urlparse(self.path)
        if parsed.path == '/palette' and not parsed.query:
            data = (Path(__file__).parent / 'palette/RFIX/Safe_BIM_Palette.html').read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return
        if parsed.path != '/state':
            return self._send(404, {'error': 'not found'})
        query = parse_qs(parsed.query, keep_blank_values=True)
        if set(query) != {'job_id'} or len(query['job_id']) != 1 or not query['job_id'][0]:
            return self._send(400, {'error': 'one job_id required'})
        job_id = query['job_id'][0]
        try:
            state = self.server.executor.palette_state(job_id)
            return self._send(200, dict(state, capability=self.server.capability))
        except ExecutorError as exc:
            return self._send(404, {'error': str(exc), 'code': 'NO_ACTIVE_JOB' if job_id == 'active' else 'UNKNOWN_JOB'})
        except Exception:
            return self._send(503, {'error': 'state unavailable'})

    def do_POST(self):
        if not self._local_origin():
            return self._send(403, {'error': 'origin/host rejected'})
        tokens = self.headers.get_all('X-Safe-BIM-Token', [])
        if len(tokens) != 1 or not hmac.compare_digest(tokens[0].encode('utf-8'), self.server.capability.encode('ascii')):
            return self._send(403, {'error': 'local capability required'})
        parsed = urlparse(self.path)
        parts = parsed.path.split('/')
        if len(parts) != 4 or parts[:2] != ['', 'jobs'] or parsed.query or parsed.fragment:
            return self._send(404, {'error': 'not found'})
        job_id, action = unquote(parts[2]), parts[3]
        if action not in ACTIONS or not valid_job_id(job_id):
            return self._send(400, {'error': 'explicit job_id and known action required'})
        try:
            lengths = self.headers.get_all('Content-Length', [])
            if self.headers.get('Transfer-Encoding') or len(lengths) != 1 or not lengths[0].isdigit():
                raise ValueError('one bounded Content-Length required')
            size = int(lengths[0])
            if not 0 < size <= MAX_BODY:
                self.close_connection = True
                return self._send(413 if size > MAX_BODY else 400, {'error': 'nonempty bounded JSON body required'})
            if self.headers.get_content_type() != 'application/json':
                raise ValueError('application/json required')
            self.connection.settimeout(5)
            data = self.rfile.read(size)
            if len(data) != size:
                raise ValueError('incomplete body')
            payload = strict_json(data.decode('utf-8'))
            if not isinstance(payload, dict) or set(payload) != {'job_id', 'action', 'revision'}:
                raise ValueError('exact command object required: job_id, action, revision')
            if not valid_job_id(payload['job_id']) or payload['job_id'] != job_id or payload['action'] != action:
                raise ValueError('body/path command mismatch')
            revision = payload['revision']
            if isinstance(revision, bool) or not isinstance(revision, int) or revision < 0:
                raise ValueError('integer revision required')
        except (ValueError, UnicodeError, OSError) as exc:
            self.close_connection = True
            return self._send(400, {'error': str(exc)})
        try:
            job = self.server.executor.store.job(job_id)
        except ExecutorError:
            return self._send(404, {'error': 'unknown job'})
        except Exception:
            return self._send(503, {'error': 'checkpoint store unavailable'})
        if job['status'] in {s.value for s in TERMINAL} or (action == 'pause' and job['status'] not in {'RUNNING', 'PENDING'}):
            return self._send(409, {'error': 'action not permitted for current state'})
        if revision != job['revision']:
            return self._send(409, {'error': 'stale revision; refresh state'})
        try:
            method = self.server.executor.resume if action == 'continue' else getattr(self.server.executor, action)
            status = method(job_id, expected_revision=revision)
            return self._send(200, {'job_id': job_id, 'status': status.value})
        except Exception as exc:
            return self._send(409, {'error': f'{type(exc).__name__}: {exc}'})


def serve(executor, port=19731):
    server = PaletteHTTPServer(('127.0.0.1', port), executor)
    try:
        server.serve_forever()
    finally:
        server.server_close()
