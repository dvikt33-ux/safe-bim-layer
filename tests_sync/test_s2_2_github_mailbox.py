"""S2.2 GitHub Contents mailbox contracts. Offline only; no BIM runtime."""
import base64
import contextlib
import io
import json
import threading
import traceback
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.parse import unquote, urlparse

from sync_bridge.bridge import InjectedCrash, SafeBIMBridge
from sync_bridge.identity import canonical_hash, canonical_json
from sync_bridge.mailbox import (
    AckLost,
    GITHUB_BACKEND_STATUS,
    GitHubContentsBackend,
    GitHubMailbox,
    HttpResponse,
    OfflineError,
    canonical_remote_object,
)
from sync_bridge.polling import PollScheduler
from sync_bridge.protocol import ProtocolError, parse_envelope
from sync_bridge.security import PeerIdentity
from sync_bridge.store import BridgeStore
from tests_sync.closing import ClosingDirectory


OWNER = PeerIdentity('S-1-5-21-2200', 'session-s22')


class FakeContentsHttp:
    """Thread-safe GitHub Contents API model, not a production backend."""

    def __init__(self):
        self.objects = {}
        self.calls = []
        self.version = 0
        self.put_count = 0
        self.drop_ack_once = False
        self.offline = False
        self.force_status = None
        self.force_headers = {}
        self.force_json = {}
        self.missing_barrier = None
        self.lock = threading.RLock()

    @property
    def etag(self):
        return '"contents-%d"' % self.version

    def seed(self, path, value):
        with self.lock:
            self.objects[path] = json.loads(json.dumps(value))
            self.version += 1

    def request(self, method, url, headers, body=None):
        with self.lock:
            self.calls.append((method, url, dict(headers or {}), body))
            if self.offline:
                raise ConnectionError('offline')
            if self.force_status is not None:
                return HttpResponse(self.force_status, self.force_json, dict(self.force_headers))
        parsed = urlparse(url)
        marker = '/contents/'
        if marker not in parsed.path:
            return HttpResponse(200, {'private': True}, {})
        path = unquote(parsed.path.split(marker, 1)[1])
        if method == 'GET':
            with self.lock:
                if path in self.objects:
                    value = self.objects[path]
                    encoded = base64.b64encode(
                        json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   separators=(',', ':')).encode('utf-8')).decode('ascii')
                    return HttpResponse(200, {'encoding': 'base64', 'content': encoded}, {})
                entries = [key for key in self.objects if key.rsplit('/', 1)[0] == path]
                if entries:
                    current = self.etag
                    if headers.get('If-None-Match') == current:
                        return HttpResponse(304, {}, {'ETag': current})
                    listing = [{'type': 'file', 'name': key.rsplit('/', 1)[-1], 'path': key}
                               for key in sorted(entries)]
                    return HttpResponse(200, listing, {'ETag': current})
                barrier = self.missing_barrier
            if barrier is not None and path.endswith('.json'):
                barrier.wait(timeout=5)
            return HttpResponse(404, {'message': 'Not Found'}, {})
        if method == 'PUT':
            value = json.loads(base64.b64decode(body['content']).decode('utf-8'))
            with self.lock:
                if path in self.objects:
                    return HttpResponse(422, {'message': 'sha was not supplied'}, {})
                self.objects[path] = value
                self.version += 1
                self.put_count += 1
                if self.drop_ack_once:
                    self.drop_ack_once = False
                    raise AckLost('lost after create')
                return HttpResponse(201, {'content': {'path': path}}, {})
        return HttpResponse(405, {}, {})


def remote(message_id, payload, kind='job'):
    return canonical_remote_object({
        'protocolVersion': 1,
        'messageId': message_id,
        'kind': kind,
        'createdAt': '2026-09-28T12:00:00+00:00',
        'payload': payload,
    }, kind)


def mailbox(http, root='safe-bim-mailbox'):
    backend = GitHubContentsBackend(
        'private-owner', 'private-bridge', branch='bridge-mailbox', root=root,
        http=http, token_provider=lambda: 'sensitive-value')
    return GitHubMailbox(backend=backend)


def started(directory, http):
    store = BridgeStore(Path(directory) / 'bridge.sqlite3')
    service = SafeBIMBridge(store, mailbox(http), owner=OWNER)
    service.start()
    return service


class ListedThenMissingHttp(FakeContentsHttp):
    def __init__(self, repo_response):
        super().__init__()
        self.repo_response = repo_response

    def request(self, method, url, headers, body=None):
        parsed = urlparse(url)
        if method == 'GET' and '/contents/' not in parsed.path:
            with self.lock:
                self.calls.append((method, url, dict(headers or {}), body))
            return self.repo_response
        if method == 'GET' and parsed.path.endswith('/VANISH.json'):
            with self.lock:
                self.calls.append((method, url, dict(headers or {}), body))
            return HttpResponse(404, {'message': 'Not Found'}, {})
        return super().request(method, url, headers, body)


class ImmutablePublishTests(unittest.TestCase):
    def test_message_id_is_exact_safe_ascii_path_component(self):
        invalid = ('', ' M', 'M ', 'M/M', 'M\\M', 'M%2FM', 'M M', 'M\tM',
                   'M\nM', '.', '..', 'Mé')
        for message_id in invalid:
            with self.subTest(message_id=repr(message_id)):
                http = FakeContentsHttp()
                with self.assertRaises(ProtocolError):
                    mailbox(http).publish_result({'messageId': message_id, 'result': {'ok': True}})
                self.assertEqual(http.put_count, 0)
                self.assertEqual(http.objects, {})
        http = FakeContentsHttp()
        mailbox(http).publish_result({'messageId': 'Ab._-9', 'result': {'ok': True}})
        self.assertIn('safe-bim-mailbox/results/Ab._-9.json', http.objects)
        with self.assertRaises(ProtocolError):
            mailbox(FakeContentsHttp()).publish_result(
                {'idempotencyKey': 'FALLBACK', 'result': {'ok': True}})

    def test_canonical_json_rejects_non_json_values_and_non_finite_numbers(self):
        class CustomValue:
            pass

        rejected = (CustomValue(), b'bytes', {1, 2}, float('nan'),
                    float('inf'), float('-inf'))
        for value in rejected:
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises((TypeError, ValueError)):
                    canonical_json({'value': value})
                with self.assertRaises((TypeError, ValueError)):
                    canonical_hash({'value': value})
        self.assertEqual(canonical_hash({'b': [2, 1], 'a': True}),
                         canonical_hash({'a': True, 'b': [2, 1]}))

    def test_publish_rejects_non_json_payload_before_remote_write(self):
        http = FakeContentsHttp()
        with self.assertRaises(ProtocolError):
            mailbox(http).publish_result({'messageId': 'STRICT', 'result': {'bad': b'bytes'}})
        self.assertEqual(http.put_count, 0)
        self.assertEqual(http.objects, {})

    def test_publish_new_immutable_object_is_created(self):
        http = FakeContentsHttp()
        result = mailbox(http).publish_result({'messageId': 'M1', 'result': {'ok': True}})
        self.assertEqual(result['status'], 'CREATED')
        stored = http.objects['safe-bim-mailbox/results/M1.json']
        self.assertEqual(stored['payloadHash'], canonical_hash(stored['payload']))
        self.assertEqual(set(('protocolVersion', 'messageId', 'kind', 'createdAt',
                              'payload', 'payloadHash')) - set(stored), set())

    def test_same_id_same_payload_is_already_published(self):
        http = FakeContentsHttp()
        first = mailbox(http).publish_result({'messageId': 'M2', 'result': {'n': 1}})
        second = mailbox(http).publish_result({'messageId': 'M2', 'result': {'n': 1}})
        self.assertEqual(first['status'], 'CREATED')
        self.assertEqual(second['status'], 'ALREADY_PUBLISHED')
        self.assertEqual(http.put_count, 1)

    def test_same_id_different_payload_is_conflict(self):
        http = FakeContentsHttp()
        one = mailbox(http)
        one.publish_result({'messageId': 'M3', 'result': {'n': 1}})
        before = json.loads(json.dumps(http.objects['safe-bim-mailbox/results/M3.json']))
        conflict = mailbox(http).publish_result({'messageId': 'M3', 'result': {'n': 2}})
        self.assertEqual(conflict['status'], 'MESSAGE_ID_CONFLICT')
        self.assertEqual(http.objects['safe-bim-mailbox/results/M3.json'], before)
        self.assertEqual(http.put_count, 1)

    def test_concurrent_same_payload_creates_one_remote_object(self):
        http = FakeContentsHttp()
        http.missing_barrier = threading.Barrier(2)
        results = []
        workers = [threading.Thread(
            target=lambda: results.append(mailbox(http).publish_result(
                {'messageId': 'MC', 'result': {'same': True}}))) for _ in range(2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(10)
        self.assertEqual(sorted(item['status'] for item in results),
                         ['ALREADY_PUBLISHED', 'CREATED'])
        self.assertEqual(http.put_count, 1)

    def test_concurrent_different_payload_has_one_winner_and_conflict(self):
        http = FakeContentsHttp()
        http.missing_barrier = threading.Barrier(2)
        results = []
        workers = [threading.Thread(
            target=lambda n=n: results.append(mailbox(http).publish_result(
                {'messageId': 'MD', 'result': {'n': n}}))) for n in (1, 2)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(10)
        self.assertEqual(sorted(item['status'] for item in results),
                         ['CREATED', 'MESSAGE_ID_CONFLICT'])
        self.assertEqual(http.put_count, 1)


class InboundAndETagTests(unittest.TestCase):
    def test_remote_message_id_must_exactly_match_path_derived_id(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/Exact.json', remote('exact', {'recipe': 'safe'}))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual(result['accepted'][0]['status'], 'MESSAGE_ID_CONFLICT')
            self.assertEqual(service.store.jobs(), [])
            service.stop()

    def test_protocol_version_requires_exact_int_type(self):
        base = {
            'protocolVersion': 1,
            'messageId': 'M',
            'requestId': 'R',
            'instanceId': 'I',
            'kind': 'PING',
            'payload': {},
        }
        for invalid in (True, False, 1.0, '1', None):
            with self.subTest(version=repr(invalid)):
                candidate = dict(base, protocolVersion=invalid)
                with self.assertRaises(ProtocolError):
                    parse_envelope(candidate)
                remote_value = remote('VERSION', {'recipe': 'safe'})
                remote_value['protocolVersion'] = invalid
                http = FakeContentsHttp()
                http.seed('safe-bim-mailbox/inbox/VERSION.json', remote_value)
                with ClosingDirectory() as directory:
                    service = started(directory, http)
                    result = service.tick()
                    self.assertEqual(result['accepted'][0]['status'], 'QUARANTINED')
                    self.assertEqual(service.store.jobs(), [])
                    service.stop()

    def test_listed_object_404_with_visible_repo_is_transient_and_does_not_advance_etag(self):
        http = ListedThenMissingHttp(HttpResponse(200, {'private': True}, {}))
        http.seed('safe-bim-mailbox/inbox/VANISH.json', remote('VANISH', {'recipe': 'safe'}))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual(result['status'], 'ERROR')
            self.assertEqual(result['code'], 'TRANSIENT_REMOTE_INCONSISTENCY')
            self.assertEqual(result['processed'], 0)
            self.assertEqual(service.store.jobs(), [])
            self.assertIsNone(service.store.message('VANISH'))
            self.assertEqual(service.store.messages_by_state('QUARANTINED'), [])
            self.assertIsNone(service.store.meta('remote_etag'))
            self.assertIsNone(service.mailbox.etag)
            service.stop()

    def test_listed_object_404_with_uncertain_access_does_not_advance_etag(self):
        probes = (
            (HttpResponse(401, {'message': 'Bad credentials'}, {}), 'NEEDS_AUTH', None),
            (HttpResponse(403, {'message': 'Forbidden'}, {}), 'ERROR', 'ACCESS_UNCERTAIN'),
            (HttpResponse(404, {'message': 'Not Found'}, {}), 'ERROR', 'ACCESS_UNCERTAIN'),
        )
        for probe, expected_status, expected_code in probes:
            with self.subTest(probe_status=probe.status):
                http = ListedThenMissingHttp(probe)
                http.seed('safe-bim-mailbox/inbox/VANISH.json',
                          remote('VANISH', {'recipe': 'safe'}))
                with ClosingDirectory() as directory:
                    service = started(directory, http)
                    result = service.tick()
                    self.assertEqual(result['status'], expected_status)
                    if expected_code is not None:
                        self.assertEqual(result['code'], expected_code)
                    self.assertEqual(result['processed'], 0)
                    self.assertEqual(service.store.jobs(), [])
                    self.assertIsNone(service.store.message('VANISH'))
                    self.assertEqual(service.store.messages_by_state('QUARANTINED'), [])
                    self.assertIsNone(service.store.meta('remote_etag'))
                    self.assertIsNone(service.mailbox.etag)
                    service.stop()

    def test_hash_mismatch_is_quarantined_and_creates_no_job(self):
        http = FakeContentsHttp()
        bad = remote('BAD', {'recipe': 'x'})
        bad['payload']['recipe'] = 'tampered'
        http.seed('safe-bim-mailbox/inbox/BAD.json', bad)
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual(result['accepted'][0]['status'], 'REMOTE_HASH_MISMATCH')
            self.assertEqual(service.store.jobs(), [])
            self.assertEqual(len(service.store.messages_by_state('QUARANTINED')), 1)
            service.stop()

    def test_malformed_is_quarantined_while_valid_object_is_processed(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/BROKEN.json', {'messageId': 'BROKEN'})
        http.seed('safe-bim-mailbox/inbox/GOOD.json', remote('GOOD', {'recipe': 'safe'}))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual([item['status'] for item in result['accepted']],
                             ['QUARANTINED', 'QUEUED'])
            self.assertEqual(len(service.store.jobs()), 1)
            service.stop()

    def test_etag_is_sent_in_if_none_match(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/E1.json', remote('E1', {'recipe': 'x'}))
        box = mailbox(http)
        first = box.poll_head()
        self.assertIsNone(box.etag)
        box.commit_etag(first.etag)
        box.poll_head()
        list_calls = [call for call in http.calls if '/contents/safe-bim-mailbox/inbox?' in call[1]]
        self.assertEqual(list_calls[-1][2]['If-None-Match'], first.etag)

    def test_matching_etag_returns_not_modified(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/E2.json', remote('E2', {'recipe': 'x'}))
        box = mailbox(http)
        first = box.poll_head()
        box.commit_etag(first.etag)
        second = box.poll_head()
        self.assertTrue(second.not_modified)
        self.assertFalse(second.changed)

    def test_crash_before_completed_tick_does_not_advance_etag(self):
        http = FakeContentsHttp()
        http.seed('safe-bim-mailbox/inbox/CRASH.json', remote('CRASH', {'recipe': 'x'}))
        with ClosingDirectory() as directory:
            service = started(directory, http)
            service.fault_after_persist = lambda: (_ for _ in ()).throw(InjectedCrash('crash'))
            with self.assertRaises(InjectedCrash):
                service.tick()
            self.assertIsNone(service.mailbox.etag)
            self.assertIsNone(service.store.meta('remote_etag'))
            service.crash()
            service.store.set_meta('lease_expires', '2000-01-01T00:00:00+00:00')
            service.store.close()

    def test_duplicate_inbound_after_restart_creates_one_job(self):
        http = FakeContentsHttp()
        obj = remote('REPLAY', {'recipe': 'x'})
        http.seed('safe-bim-mailbox/inbox/REPLAY.json', obj)
        with ClosingDirectory() as directory:
            service = started(directory, http)
            service.tick()
            service.stop()
            service.store.close()
            http.version += 1
            again = started(directory, http)
            result = again.tick()
            self.assertEqual(result['accepted'][0]['status'], 'DUPLICATE')
            self.assertEqual(len(again.store.jobs()), 1)
            again.stop()


class RecoveryAndStateTests(unittest.TestCase):
    def test_403_is_classified_without_masking_ambiguous_access(self):
        cases = (
            ({'message': 'API rate limit exceeded'}, {}, 'RATE_LIMITED', None),
            ({'message': 'SAML SSO authorization required'}, {}, 'NEEDS_AUTH', None),
            ({'message': 'Forbidden'}, {'X-GitHub-SSO': 'required'}, 'NEEDS_AUTH', None),
            ({'message': 'Resource not accessible by integration'}, {},
             'ERROR', 'PERMISSION_DENIED'),
            ({'message': 'Forbidden'}, {}, 'ERROR', 'ACCESS_UNCERTAIN'),
        )
        for body, headers, expected_status, expected_code in cases:
            with self.subTest(body=body, headers=headers):
                http = FakeContentsHttp()
                http.force_status = 403
                http.force_json = body
                http.force_headers = headers
                result = PollScheduler(mailbox(http)).poll_once()
                self.assertEqual(result['status'], expected_status)
                if expected_code is not None:
                    self.assertEqual(result['code'], expected_code)

    def test_ack_lost_then_restart_becomes_sent_without_second_object(self):
        http = FakeContentsHttp()
        http.drop_ack_once = True
        with ClosingDirectory() as directory:
            service = started(directory, http)
            service.queue_result('job-ack', {'status': 'ok'})
            first = service.flush_outbox()
            self.assertEqual(first[0]['status'], 'UNCERTAIN')
            service.stop()
            service.store.close()
            again = started(directory, http)
            second = again.flush_outbox()
            self.assertEqual(second[0]['status'], 'ALREADY_PUBLISHED')
            self.assertEqual(again.store.message('result-job-ack')['state'], 'SENT')
            self.assertEqual(http.put_count, 1)
            again.stop()

    def test_401_needs_auth_keeps_local_ready(self):
        http = FakeContentsHttp()
        http.force_status = 401
        with ClosingDirectory() as directory:
            service = started(directory, http)
            result = service.tick()
            self.assertEqual(result['status'], 'NEEDS_AUTH')
            self.assertTrue(service.running)
            self.assertEqual(service.connections.get('BRIDGE')['status'], 'CONNECTED')
            service.stop()

    def test_rate_limit_headers_drive_bounded_backoff(self):
        http = FakeContentsHttp()
        http.force_status = 429
        http.force_headers = {'Retry-After': '17', 'X-RateLimit-Remaining': '0'}
        result = PollScheduler(mailbox(http)).poll_once()
        self.assertEqual(result['status'], 'RATE_LIMITED')
        self.assertGreaterEqual(result['retryAfter'], 17)
        self.assertLessEqual(result['retryAfter'], 300)
        reset = FakeContentsHttp()
        reset.force_status = 403
        reset.force_headers = {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': '1042'}
        with patch('sync_bridge.mailbox.time.time', return_value=1000):
            from_reset = PollScheduler(mailbox(reset)).poll_once()
        self.assertEqual(from_reset['status'], 'RATE_LIMITED')
        self.assertEqual(from_reset['retryAfter'], 42)

    def test_internet_loss_keeps_outbox_pending(self):
        http = FakeContentsHttp()
        with ClosingDirectory() as directory:
            service = started(directory, http)
            service.queue_result('job-offline', {'status': 'ok'})
            http.offline = True
            result = service.flush_outbox()
            self.assertEqual(result[0]['status'], 'QUEUED')
            self.assertEqual(len(service.store.pending_outbox()), 1)
            self.assertEqual(http.put_count, 0)
            service.stop()

    def test_reconnect_publishes_outbox_exactly_once(self):
        http = FakeContentsHttp()
        with ClosingDirectory() as directory:
            service = started(directory, http)
            service.queue_result('job-reconnect', {'status': 'ok'})
            http.offline = True
            service.flush_outbox()
            http.offline = False
            sent = service.flush_outbox()
            service.flush_outbox()
            self.assertEqual(sent[0]['status'], 'CREATED')
            self.assertEqual(http.put_count, 1)
            self.assertEqual(service.store.pending_outbox(), [])
            service.stop()

    def test_authorization_is_redacted_from_errors_logs_diagnostics_and_sqlite(self):
        secret = 'sensitive-value'

        class ExplodingHttp:
            def request(self, method, url, headers, body=None):
                raise RuntimeError('request headers=' + repr(headers))

        backend = GitHubContentsBackend(
            'private-owner', 'private-bridge', http=ExplodingHttp(),
            token_provider=lambda: secret)
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            try:
                backend.list_objects('inbox')
            except OfflineError as exc:
                rendered = str(exc) + traceback.format_exc()
        self.assertNotIn(secret, rendered)
        self.assertNotIn(secret, stderr.getvalue())
        self.assertNotIn(secret, repr(backend.health()))
        with ClosingDirectory() as directory:
            store = BridgeStore(Path(directory) / 'bridge.sqlite3')
            service = SafeBIMBridge(store, GitHubMailbox(backend=backend), owner=OWNER)
            service.start()
            service._log('security-test', {'Authorization': 'Bearer ' + secret, 'safe': 'ok'})
            service.queue_result('job-redact', {'status': 'ok'})
            self.assertNotIn(secret, repr(service.logs))
            self.assertNotIn(secret, repr(service.health()))
            self.assertNotIn(secret, repr(service.store.pending_outbox()))
            service.stop()

    def test_backend_status_is_implemented_not_live_verified(self):
        self.assertEqual(GITHUB_BACKEND_STATUS, 'IMPLEMENTED_NOT_LIVE_VERIFIED')


if __name__ == '__main__':
    unittest.main()
