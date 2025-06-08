import json
from datetime import datetime
from wsgiref.simple_server import make_server
from zoneinfo import ZoneInfo
from dateutil import parser, tz

def application(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', '')
    if method == 'GET':
        return handle_get(path, start_response)
    elif method == 'POST':
        if path == '/api/v1/convert':
            return handle_convert(environ, start_response)
        elif path == '/api/v1/datediff':
            return handle_datediff(environ, start_response)
    start_response('404 Not Found', [('Content-Type', 'text/plain; charset=utf-8')])
    return [b'Not Found']

def handle_get(path, start_response):
    # GET /<tz> — текущий час в зоне или GMT
    tz_name = path.lstrip('/') or 'GMT'
    try:
        tzinfo = ZoneInfo(tz_name)
    except Exception:
        tzinfo = tz.gettz(tz_name)
    if tzinfo is None:
        start_response('404 Not Found', [('Content-Type', 'text/plain; charset=utf-8')])
        return [f'Unknown timezone: {tz_name}'.encode('utf-8')]

    now = datetime.now(tzinfo)
    t = now.strftime('%Y-%m-%d %H:%M:%S %Z%z')
    html = f'''<html>
  <head><meta charset="utf-8"/></head>
  <body><h1>Current time in {tz_name}: {t}</h1></body>
</html>'''
    start_response('200 OK', [('Content-Type', 'text/html; charset=utf-8')])
    return [html.encode('utf-8')]

def read_json(environ):
    try:
        n = int(environ.get('CONTENT_LENGTH', 0))
    except:
        n = 0
    body = environ['wsgi.input'].read(n) if n>0 else b''
    return json.loads(body.decode('utf-8'))

def handle_convert(environ, start_response):
    # POST /api/v1/convert
    # { "date": {"date":"12.20.2021 22:21:05","tz":"EST"}, "target_tz":"Europe/Moscow" }
    try:
        data = read_json(environ)
        ds = data['date']
        src_dt = parser.parse(ds['date'])
        src_tz = ZoneInfo(ds['tz']) if ds['tz'] else tz.UTC
        src_dt = src_dt.replace(tzinfo=src_tz)
        tgt = data['target_tz']
        tgt_tz = ZoneInfo(tgt) if tgt else tz.UTC
        out = src_dt.astimezone(tgt_tz)
        res = out.strftime('%Y-%m-%d %H:%M:%S %Z%z')
        start_response('200 OK', [('Content-Type','application/json; charset=utf-8')])
        return [json.dumps({'converted':res}).encode()]
    except Exception as e:
        start_response('400 Bad Request', [('Content-Type','text/plain; charset=utf-8')])
        return [str(e).encode()]

def handle_datediff(environ, start_response):
    # POST /api/v1/datediff
    # {"first_date":"...","first_tz":"EST","second_date":"...","second_tz":"Europe/Moscow"}
    try:
        d = read_json(environ)
        dt1 = parser.parse(d['first_date'])
        tz1 = ZoneInfo(d['first_tz']) if d['first_tz'] else tz.UTC
        dt1 = dt1.replace(tzinfo=tz1)
        dt2 = parser.parse(d['second_date'])
        tz2 = ZoneInfo(d['second_tz']) if d['second_tz'] else tz.UTC
        dt2 = dt2.replace(tzinfo=tz2)
        diff = abs(int((dt1 - dt2).total_seconds()))
        start_response('200 OK', [('Content-Type','application/json; charset=utf-8')])
        return [json.dumps({'diff_seconds':diff}).encode()]
    except Exception as e:
        start_response('400 Bad Request', [('Content-Type','text/plain; charset=utf-8')])
        return [str(e).encode()]

if __name__ == '__main__':
    # простой запуск для тестирования
    with make_server('', 8000, application) as srv:
        print('Listening on http://localhost:8000 …')
        srv.serve_forever()