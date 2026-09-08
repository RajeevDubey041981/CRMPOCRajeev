import json
import urllib.request
import urllib.error

BASE = 'http://localhost:8000'


def request(path, method='GET', data=None, token=None):
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    if data is not None:
        headers['Content-Type'] = 'application/json'
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            body = r.read().decode('utf-8', 'ignore')
            return r.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')
    except Exception as e:
        return None, str(e)


def main():
    # vendor login
    login_data = json.dumps({'email': 'vendor@indcool.com', 'password': 'vendor123'}).encode()
    status, body = request('/api/auth/login', method='POST', data=login_data)
    token = None
    if status == 200:
        token = json.loads(body).get('access_token')

    with urllib.request.urlopen(BASE + '/openapi.json') as r:
        spec = json.load(r)

    sample_payloads = {
        'POST': json.dumps({'email': 'vendor@indcool.com', 'password': 'vendor123'}).encode(),
        'PUT': json.dumps({'status': 'Delivered'}).encode(),
        'PATCH': json.dumps({'status': 'Delivered'}).encode(),
    }

    for path, methods in spec.get('paths', {}).items():
        for method, op in methods.items():
            m = method.lower()
            if m not in {'get', 'post', 'put', 'patch', 'delete'}:
                continue
            use_path = path
            if '{order_id}' in use_path:
                use_path = use_path.replace('{order_id}', '999999')
            if '{claim_id}' in use_path:
                use_path = use_path.replace('{claim_id}', '999999')
            if '{complaint_id}' in use_path:
                use_path = use_path.replace('{complaint_id}', '999999')
            if '{id}' in use_path:
                use_path = use_path.replace('{id}', '999999')
            if '/api/auth/login' in use_path and m == 'post':
                body = sample_payloads.get('POST')
            elif m in {'post', 'put', 'patch'}:
                body = sample_payloads.get(method.upper(), b'{}')
            else:
                body = None
            status, resp = request(use_path, method=m.upper(), data=body, token=token)
            print(f'{method.upper()} {use_path} -> {status}')


if __name__ == '__main__':
    main()
