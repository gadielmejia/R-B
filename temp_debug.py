from app import create_app
from app.routes.auth_bp import login
from flask import json
app = create_app()
with app.test_request_context('/api/login', method='POST', data=json.dumps({'correo':'test@test.com','Contrasena':'x'}), content_type='application/json'):
    resp = login()
    if isinstance(resp, tuple):
        response, code = resp
    else:
        response, code = resp, resp.status_code
    print('status', code)
    data = response.get_data(as_text=True)
    print(data)

