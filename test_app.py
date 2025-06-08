import io
import json
import pytest
from wsgiref.util import setup_testing_defaults
from app import application

def request(path='/', method='GET', body=None):
    env = {}
    setup_testing_defaults(env)
    env['PATH_INFO'] = path
    env['REQUEST_METHOD'] = method
    if body is not None:
        b = body.encode('utf-8')
        env['CONTENT_LENGTH'] = str(len(b))
        env['wsgi.input'] = io.BytesIO(b)
    status = headers = None
    def start_response(s, h):
        nonlocal status, headers
        status, headers = s, dict(h)
    out = b''.join(application(env, start_response))
    return status, headers, out

def test_get_root_is_gmt():
    status, hdr, out = request('/')
    assert status.startswith('200')
    assert b'Current time in GMT:' in out

def test_get_named_tz():
    status, hdr, out = request('/Europe/Moscow')
    assert status.startswith('200')
    assert b'Current time in Europe/Moscow:' in out

def test_convert_endpoint():
    payload = {
        "date": {"date":"12.20.2021 22:21:05", "tz":"UTC"},
        "target_tz": "Europe/Moscow"
    }
    status, hdr, out = request('/api/v1/convert','POST', json.dumps(payload))
    assert status.startswith('200')
    data = json.loads(out.decode())
    # примерный формат "2021-12-21 01:21:05 CET+0100"
    assert 'converted' in data

def test_datediff_endpoint():
    payload = {
        "first_date":"2024-06-12 22:21:05", "first_tz":"UTC",
        "second_date":"2024-06-12 23:21:05", "second_tz":"UTC"
    }
    status, hdr, out = request('/api/v1/datediff','POST', json.dumps(payload))
    assert status.startswith('200')
    data = json.loads(out.decode())
    assert data['diff_seconds'] == 3600

def test_404():
    status, hdr, out = request('/no/such')
    assert status.startswith('404')
