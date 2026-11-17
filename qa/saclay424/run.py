"""Transfer the acknowledged publisher journal and retain one hosted research outcome."""

import base64
import copy
import json
import os
from pathlib import Path
import stat
import subprocess

import continuation as publisher
from hosted_identity import verify_run


LOCAL = Path(__file__).resolve().parent
TREE = LOCAL.parents[1]
CERT = LOCAL / 'reviewer.pem'
PINNED = {
    '.github/workflows/qa-saclay424-phd-track.yml',
    'qa/saclay424/continuation.py',
    'qa/saclay424/hosted_identity.py',
    'qa/saclay424/predecessor.json',
    'qa/saclay424/reviewer.pem',
    'qa/saclay424/run.py',
}


def require(condition, message):
    if not condition:
        raise publisher.Stop(message)


def git(*args):
    return subprocess.check_output(
        ['git', '-C', str(TREE), *args], stderr=subprocess.DEVNULL, timeout=10)


def reviewed(scope, identity):
    require(scope['enabled'] is True and publisher.decision(scope['decision'])
            and scope['decision'] != scope['old_decision'],
            'Exact bounded continuation is OFF')
    require(scope['urls'] == list(publisher.URLS) and set(scope['pins']) == PINNED,
            'Unexpected continuation footprint')
    sha = identity['head_sha']
    require(git('rev-parse', 'HEAD').decode().strip() == sha, 'Checkout differs')
    for name in sorted(PINNED | {'qa/saclay424/scope.json'}):
        raw = (TREE / name).read_bytes()
        require(git('show', sha + ':' + name) == raw, 'Commit blob differs')
        if name in PINNED:
            require(publisher.digest(raw) == scope['pins'][name], 'Frozen blob differs')


def seed_state(scope):
    previous = json.loads((LOCAL / 'predecessor.json').read_bytes())
    old = previous['original_state']
    strict = previous['transfer_state']
    candidate = copy.deepcopy(old)
    starts = set(old['starts'])
    for pair in previous['timing_pairs']:
        require(pair['reservation_wall'] in starts and
                pair['reservation_wall'] <= pair['prior_observed_pre_opener']
                <= pair['completion_wall'] <= old['completed'],
                'Original predecessor timing is invalid')
        starts.add(pair['prior_observed_pre_opener'])
    candidate['starts'] = sorted(starts)
    candidate['retained_eidos_rep'] = old['policy']
    require(previous['kind'] == 'settled-original-eidos-transfer'
            and previous['new_publisher_requests'] == 0
            and previous['prior_acknowledgements'] == 6
            and previous['actual_original_physical_count'] == 2
            and [pair['scope'] for pair in previous['timing_pairs']]
            == [publisher.EIDOS_ROBOTS, publisher.EIDOS_ENTRY]
            and publisher.digest(publisher.canonical(old))
            == previous['original_observed_local_state_sha256']
            == scope['original_state_sha256']
            and previous['root_proof_sha256'] == scope['predecessor_proof_sha256']
            and publisher.digest(publisher.canonical(strict))
            == previous['transfer_state_sha256'] == scope['seed_sha256']
            and strict == candidate and len(starts) == 4
            and old['target'] == publisher.EIDOS_ENTRY
            and old['policy'] == publisher.EIDOS_REP
            and old['outcome'] == 'response_assessed'
            and not any(old[key] for key in ('blocked', 'in_flight', 'physical_pending')),
            'Original owned state or transfer differs')
    return publisher.validate(strict)


def adopt(seed):
    """Create a sole hosted owner from the exact authenticated prior bytes."""
    publisher.gate()
    parent = os.open(publisher.PARENT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    p = os.fstat(parent)
    handles = [(parent, publisher.identity(p))]
    primary = None
    try:
        publisher.parent_safe(p)
        leaf = publisher.paths().name
        os.mkdir(leaf, 0o700, dir_fd=parent)
        os.fsync(parent)
        directory = os.open(leaf, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        d = os.fstat(directory)
        handles.append((directory, publisher.identity(d)))
        require(d.st_uid == os.getuid() and stat.S_IMODE(d.st_mode) == 0o700,
                'Temporary owner metadata differs')
        locks = {}
        for name in ('collection.lock', 'state.lock'):
            _, locked = publisher.create_once(directory, name, {})
            locks[name] = list(locked)
        _, state_id = publisher.create_once(directory, 'state.json', seed)
        info = os.stat('state.json', dir_fd=directory, follow_symlinks=False)
        publisher.private_file(info)
        require(publisher.identity(info) == state_id, 'Transferred state owner differs')
        return {
            'parent_identity': list(publisher.identity(p)),
            'parent_metadata': [p.st_uid, p.st_gid, stat.S_IMODE(p.st_mode)],
            'directory_identity': list(publisher.identity(d)),
            'directory_metadata': [d.st_uid, d.st_gid, stat.S_IMODE(d.st_mode)],
            'state_identity': list(state_id),
            'state_metadata': [info.st_uid, info.st_gid, stat.S_IMODE(info.st_mode), info.st_nlink],
            'locks': locks,
        }
    except BaseException as error:
        primary = error
        raise
    finally:
        publisher.checked_close(handles, primary)


def retain(expected):
    """Read the same owner even after the publisher gate has latched closed."""
    with publisher.Journal(expected) as journal:
        state = journal.read()
        return {'state': state, 'raw': journal.ack, 'sha256': publisher.digest(journal.ack)}


def fully_qualified(seed, terminal):
    """Validate real reserve, wire, complete close, settlement and owned terminal."""
    requests, events = publisher.AUDIT['requests'], publisher.AUDIT['persistence']
    require(len(requests) == 2 and len(events) >= 6, 'Complete two-response trace required')
    before = seed
    for event in events:
        require(event['acknowledged'] is True and event['before'] == before
                and event['intended'] == event['after'] == event['RAM_state']
                and event['bytes'] == event['actual_journal_bytes']
                == publisher.canonical(event['after']),
                'Incomplete original journal acknowledgement')
        before = event['after']
    require(before == terminal['state'] and terminal['raw'] == publisher.canonical(before),
            'Final owner differs from final ACK')
    require(events[0]['after']['not_before'] >= events[0]['after']['observed_at'] + 60
            and all(events[0]['before'][key] == events[0]['after'][key]
                    for key in seed.keys() - {'observed_at', 'not_before'}),
            'Initial hosted quiet period differs')
    previous = None
    for request, url in zip(requests, publisher.URLS):
        require(request['url'] == url and request['closed'] is True
                and request['read_complete'] is True
                and request['segments'][-1:] == [b''] and 'error' not in request,
                'Response custody is incomplete')
        reserve = [v for v in events if v['after']['physical_id'] == request['request_id']
                   and v['before']['physical_id'] != request['request_id']]
        settle = [v for v in events if v['before']['physical_id'] == request['request_id']
                  and v['before']['physical_pending'] and not v['after']['physical_pending']]
        require(len(reserve) == len(settle) == 1, 'Unique physical owner required')
        start, end = reserve[0], settle[0]
        require(publisher.digest(start['bytes']) == request['reserve_sha256']
                and publisher.digest(end['bytes']) == request['settled_sha256']
                and start['before']['physical_pending'] is False
                and start['after']['physical_pending'] is True
                and start['after']['target'] == end['after']['target'] == url
                and start['after']['logical_id'] == end['after']['completed_logical_id']
                == request['logical_id']
                and end['after']['completed_physical_id'] == request['request_id']
                and start['after']['physical_started'] == request['reserve_wall']
                <= request['actual_open_wall'] <= request['wall_completion']
                <= end['after']['completed']
                and start['completed_monotonic'] <= request['actual_open_monotonic']
                <= request['completion'] <= end['monotonic']
                and request['actual_open_wall'] in end['after']['starts'],
                'Reserve, opener, close and settlement do not form one transaction')
        if previous is None:
            require(request['actual_open_wall'] >= events[0]['after']['not_before'],
                    'Actual opener violated the initial quiet period')
        else:
            previous_request, previous_settlement = previous
            require(request['actual_open_wall'] >= previous_settlement['after']['not_before']
                    and request['actual_open_monotonic'] - previous_request['completion']
                    >= previous_settlement['after']['interval'],
                    'Actual opener violated acknowledged pacing')
        previous = request, end
    robots, content = requests
    require((robots['status'] == 200 or 400 <= robots['status'] < 500
             and robots['status'] != 429) and content['status'] == 200
            and before['policy']['url'] == publisher.ROBOTS
            and before['policy']['body_sha256'] == publisher.digest(b''.join(robots['segments']))
            and before['policy']['new_allowed'] and before['policy']['legacy_allowed']
            and before['retained_eidos_rep'] == publisher.EIDOS_REP
            and not any(before[key] for key in ('in_flight', 'physical_pending', 'blocked')),
            'The completed capture did not qualify under exact current REP')


def json_binary(value):
    if isinstance(value, bytes):
        return {'binary_base64': base64.b64encode(value).decode('ascii')}
    raise TypeError('Unsupported evidence type')


def encrypt(raw):
    return subprocess.check_output(
        ['openssl', 'cms', '-encrypt', '-binary', '-outform', 'DER',
         '-aes-256-gcm', '-recip', str(CERT)],
        input=raw, stderr=subprocess.DEVNULL, timeout=40)


def write_once(target, raw):
    with target.open('xb') as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())


def main():
    output = Path(os.environ['RUNNER_TEMP']) / 'saclay424-phd-track'
    output.mkdir(mode=0o700)
    outcome = {'result': 'refused', 'records': None, 'native_test': False}
    envelope = {'outcome': outcome, 'audit': publisher.AUDIT}
    namespace = None
    may_encrypt = False
    try:
        scope = json.loads((LOCAL / 'scope.json').read_bytes())
        require(scope['enabled'] is True, 'Exact bounded continuation is OFF')
        identity = verify_run()
        reviewed(scope, identity)
        require(bool(encrypt(b'saclay424-reviewer-preflight')), 'Evidence encryption is unavailable')
        may_encrypt = True
        seed = seed_state(scope)
        context = {**identity, 'decision': scope['decision'], 'seed_sha256': scope['seed_sha256'],
                   'scope_sha256': publisher.digest((LOCAL / 'scope.json').read_bytes())}
        envelope.update(context=context, scope=scope, seed=seed)

        def admission():
            require(verify_run() == identity, 'Active hosted ownership differs')
            reviewed(scope, identity)

        publisher.bind(context, admission)
        admission()
        namespace = adopt(seed)
        envelope['owned_identity'] = namespace
        with publisher.Journal(namespace) as journal:
            require(journal.ack == publisher.canonical(seed), 'Exact adopted state differs')
            journal.capture_claim = publisher.create_once(journal.directory, publisher.CLAIM, context)
            envelope['owned_claim_identity'] = journal.capture_claim[1]
            quiet = journal.read()
            stamp = publisher.now()
            require(stamp >= quiet['observed_at'], 'Runner clock regressed')
            quiet.update(observed_at=stamp, not_before=max(quiet['not_before'], stamp + 60))
            journal.save(quiet)
            publisher.request(journal, publisher.ROBOTS)
            publisher.request(journal, publisher.ENTRY)
        terminal = retain(namespace)
        fully_qualified(seed, terminal)
        outcome['result'] = 'qualified_capture_pending_independent_review'
    except Exception as error:
        outcome['error'] = type(error).__name__
        if type(error) is publisher.Stop:
            outcome['reason'] = str(error)
    finally:
        if namespace is not None:
            try:
                envelope['terminal'] = retain(namespace)
            except Exception as error:
                outcome['result'] = 'refused'
                outcome['owned_terminal_error'] = type(error).__name__
        requests = publisher.AUDIT['requests']
        outcome.update({
            'reservation_count': sum(
                event['acknowledged'] is True
                and event['before']['physical_id'] != event['after']['physical_id']
                and event['after']['physical_pending'] is True
                for event in publisher.AUDIT['persistence']
            ),
            'physical_count': sum(x['actual_open_monotonic'] is not None for x in requests),
            'acknowledgements': sum(x['acknowledged'] is True for x in publisher.AUDIT['persistence']),
            'statuses': [x.get('status') for x in requests],
            'terminal_state_sha256': envelope.get('terminal', {}).get('sha256'),
        })
        if may_encrypt:
            try:
                raw = json.dumps(envelope, sort_keys=True, allow_nan=False,
                                 separators=(',', ':'), default=json_binary).encode()
                encrypted = encrypt(raw)
                write_once(output / 'capture.cms.der', encrypted)
                outcome.update(evidence_sha256=publisher.digest(raw),
                               encrypted_sha256=publisher.digest(encrypted))
            except Exception as error:
                outcome['result'] = 'refused'
                outcome['evidence_error'] = type(error).__name__
        write_once(output / 'manifest.json', publisher.canonical(outcome) + b'\n')
        print(json.dumps(outcome, sort_keys=True, allow_nan=False))
    return 0 if outcome['result'] == 'qualified_capture_pending_independent_review' else 1


if __name__ == '__main__':
    raise SystemExit(main())
