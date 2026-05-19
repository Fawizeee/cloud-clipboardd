import urllib.request
import urllib.error
import json
import uuid

def make_request(url, method='POST', data=None):
    headers = {'Content-Type': 'application/json'}
    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode('utf-8'))
        except:
            error_body = e.read().decode('utf-8')
        return e.code, error_body

def test_flow():
    base_url = 'http://127.0.0.1:8001/api/v1'
    
    # 1. Create User via /auth/register
    print("--- 1. Creating User via API ---")
    unique_id = str(uuid.uuid4())[:8]
    register_data = {
        'username': f'testuser_{unique_id}',
        'email': f'test_{unique_id}@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'first_name': 'Test',
        'last_name': 'User'
    }
    status, response = make_request(f"{base_url}/auth/register", data=register_data)
    print(f"Status: {status}")
    print(f"Response: {response}")
    
    if status != 200:
        print("Failed to create user. Exiting.")
        return
        
    user_id = response.get('id')
    print(f"Got User ID: {user_id}")
    
    # 2. Test Clipboard Save
    print("\n--- 2. Testing Clipboard Save ---")
    clipboard_data = {
        'content': 'This is a test clipboard item!',
        'user_id': user_id,
        'content_type': 'text'
    }
    status, response = make_request(f"{base_url}/clipboard/save", data=clipboard_data)
    print(f"Status: {status}")
    print(f"Response: {response}")

if __name__ == '__main__':
    test_flow()
