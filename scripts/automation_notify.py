#!/usr/bin/env python3
"""Private Slack Receipts outcome outbox; no Slack credentials stored in source."""
from __future__ import annotations
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import subprocess
import time

QUIET = {'unchanged', 'coalesced', 'active'}


def message(outcome):
    state = outcome.get('state', 'failed')
    version = outcome.get('target', {}).get('version', '')
    title = f'Chromium StealthCDP {version}'.strip()
    labels = {'complete': 'upgrade succeeded', 'failed': 'upgrade failed',
              'rolled_back': 'upgrade failed; previous activation restored',
              'deferred': 'upgrade deferred: insufficient workstation resources',
              'awaiting_checks': 'upgrade waiting for GitHub checks',
              'stopped': 'upgrade stopped; operator review required',
              'test': 'notification setup test'}
    text = f'{title}: {labels.get(state, state)}.'
    if outcome.get('stage'):
        text += f' Stage: {outcome["stage"]}.'
    publication = outcome.get('publication', {})
    if publication.get('url', '').startswith('https://github.com/CochranResearchGroup/chromium-stealthcdp/releases/'):
        text += '\n' + publication['url']
    if state == 'complete':
        text += '\nNew launches use the verified build. Existing sessions continue normally.'
    elif state != 'test':
        text += '\nDetails are in the local updater receipts and GitHub failure issue, when available.'
    else:
        text += '\nFuture upgrade successes and failures will be sent here. Unchanged daily checks stay quiet.'
    return text


class Announcer:
    def __init__(self, config, sender=None):
        self.config = config
        self.root = Path(config['state_dir']) / 'slack-outbox'
        self.settings = config.get('slack', {})
        self.sender = sender or self.send

    def send(self, payload):
        home = Path.home()
        # Invoke the installed Slack Receipts service layer used by its MCP/API.
        # Its existing environment/config own credentials; none enter our config.
        interpreter = home / '.local/share/slack-receipts/venv/bin/python'
        envfile = home / '.config/slack-receipts/env.sh'
        service_config = home / '.config/slack-receipts/config.yaml'
        result = subprocess.run(['bash', '-c', 'set -euo pipefail; source "$1"; exec "$2" "$3" --transport-helper "$4"',
                                 'slack-receipts-transport', str(envfile), str(interpreter), str(Path(__file__).resolve()),
                                 str(service_config)], input=json.dumps(payload), text=True,
                                capture_output=True, timeout=20)
        if result.returncode:
            raise RuntimeError('Installed Slack Receipts transport failed; delivery remains unconfirmed')
        lines = [line.removeprefix('STEALTHCDP_SLACK_RESULT=') for line in result.stdout.splitlines()
                 if line.startswith('STEALTHCDP_SLACK_RESULT=')]
        if len(lines) != 1:
            raise RuntimeError('Slack Receipts returned no unique delivery receipt')
        action = json.loads(lines[0])
        if action.get('status') in ('failed', 'pending'):
            return action
        if action.get('status') != 'sent' or action.get('ok') is not True or not action.get('channel_id') or not action.get('ts'):
            raise RuntimeError(f'Slack Receipts action {action.get("id")} is {action.get("status")}; delivery unconfirmed')
        return action

    def enqueue(self, outcome):
        from automation import atomic_json, load
        if not self.settings.get('enabled') or outcome.get('state') in QUIET:
            return None
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        # Routing is part of identity; never move an already queued message to a new recipient.
        route = {k: self.settings[k] for k in ('workspace', 'recipient')}
        if self.settings.get('recipient_resolution_sha256'):
            route['recipient_resolution_sha256'] = self.settings['recipient_resolution_sha256']
        identity = {'route': route, 'id': outcome.get('id', 'controller-check'),
                    'state': outcome.get('state'), 'stage': outcome.get('stage', ''),
                    'attempt': outcome.get('notification_attempt', 1)}
        event = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
        path = self.root / f'{event}.json'
        with (self.root / 'outbox.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            if not path.exists():
                atomic_json(path, {'event': event, 'route': route, 'text': message(outcome),
                                   'idempotency_key': 'chromium-stealthcdp-' + event,
                                   'delivered': False, 'attempts': 0, 'created_at': time.time()})
        return str(path)

    def flush(self):
        from automation import atomic_json, load
        if not self.settings.get('enabled'):
            return []
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        results = []
        with (self.root / 'outbox.lock').open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            for path in sorted(self.root.glob('*.json')):
                receipt = load(path)
                if receipt.get('delivered') or receipt.get('requires_review'):
                    continue
                receipt['attempts'] += 1
                receipt['last_attempt_at'] = time.time()
                # Persist before any external effect. Uncertain outcomes reuse same key.
                atomic_json(path, receipt)
                transport_failed = False
                try:
                    receipt['delivery'] = self.sender(receipt)
                    action = receipt['delivery']
                    receipt['delivered'] = (action.get('status') == 'sent' and action.get('ok') is True
                                             and bool(action.get('channel_id')) and bool(action.get('ts')))
                    receipt['requires_review'] = action.get('status') == 'failed'
                    receipt.pop('error', None)
                    if not receipt['delivered']:
                        receipt['error'] = 'Provider acceptance unconfirmed; inspect existing Slack Receipts action'
                except Exception as exc:
                    transport_failed = True
                    receipt['error'] = str(exc)
                atomic_json(path, receipt)
                results.append({'event': receipt['event'], 'delivered': receipt['delivered']})
                if transport_failed:
                    break  # transport outage: one attempt; known provider actions cannot poison later events
        return results


def announce(config, outcome):
    """Slack outage never changes a browser release outcome."""
    try:
        notifier = Announcer(config)
        notifier.enqueue(outcome)
        return notifier.flush()
    except Exception as exc:
        from automation import atomic_json
        atomic_json(Path(config['state_dir']) / 'slack-error.json', {'error': str(exc), 'at': time.time()})
        return [{'delivered': False}]


def main():
    from automation import atomic_json, load
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('action', choices=['flush', 'test', 'service-result'])
    args = parser.parse_args()
    config = load(args.config)
    outcome = None
    if args.action == 'test':
        outcome = {'state': 'test', 'id': 'setup-v1'}
    elif args.action == 'service-result' and os.environ.get('SERVICE_RESULT', 'success') != 'success':
        root = Path(config['state_dir'])
        invocation = load(root / 'invocation.json', {})
        error = load(root / 'last-error.json', {})
        if not error.get('at') or error['at'] < invocation.get('started_at', 0):
            outcome = {'state': 'failed', 'id': 'service-' + os.environ.get('INVOCATION_ID', str(invocation.get('started_at', time.time()))),
                       'stage': 'service-' + os.environ.get('SERVICE_RESULT', 'unknown')}
    results = announce(config, outcome or {'state': 'unchanged'})
    print(json.dumps(results))
    return 0


def transport_helper(config_path):
    from slack_mirror.service.app import SlackMirrorAppService
    payload = json.load(sys.stdin)
    service = SlackMirrorAppService(config_path)
    conn = service.connect()
    try:
        readiness = service.resolve_recipient_readiness(conn, workspace=payload['route']['workspace'],
                                                       recipient_ref=payload['route']['recipient'], auth_mode='bot')
        if readiness.get('ready') is not True:
            raise RuntimeError('Slack recipient is not ready')
        resolution = payload['route'].get('recipient_resolution_sha256', readiness.get('resolution_sha256'))
        action = service.send_message(conn, workspace=payload['route']['workspace'],
                                      channel_ref=payload['route']['recipient'], text=payload['text'],
                                      options={'idempotency_key': payload['idempotency_key'], 'auth_mode': 'bot',
                                               'recipient_resolution_sha256': resolution})
        response = action.get('response') or {}
        receipt = {key: action.get(key) for key in ('id', 'status', 'channel_id', 'idempotent_replay', 'retryable')}
        receipt.update(ok=response.get('ok') is True, ts=response.get('ts'),
                       permalink=response.get('permalink'))
        print('STEALTHCDP_SLACK_RESULT=' + json.dumps(receipt))
    finally:
        conn.close()


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--transport-helper':
        transport_helper(sys.argv[2])
    else:
        sys.exit(main())
