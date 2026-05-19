"""
Integration test for the Cloud Clipboard API.

Flow:
  1. Register a new user via POST /auth/register
  2. Login via POST /auth/login using the same credentials
  3. Save a clipboard item via POST /clipboard/personal  (Bearer token, no user_id in body)
  4. Retrieve clipboard items via GET /clipboard/personal  (Bearer token, no user_id query param)
  5. Verify that unauthenticated requests are rejected
  6. Assert responses are correct and no user_id is exposed
"""
import urllib.request
import urllib.error
import json
import uuid


BASE_URL = "http://127.0.0.1:8001/api/v1"


def make_request(url, method="POST", data=None, token=None):
    """Helper to make an HTTP request and return (status_code, body_dict)."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req_data = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            error_body = json.loads(e.read().decode("utf-8"))
        except Exception:
            error_body = e.read().decode("utf-8")
        return e.code, error_body


def test_flow():
    # ------------------------------------------------------------------ #
    # 1. Register a new user
    # ------------------------------------------------------------------ #
    print("--- 1. Registering user via POST /auth/register ---")
    unique_id = str(uuid.uuid4())[:8]
    register_data = {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password": "password123",
        "confirm_password": "password123",
        "first_name": "Test",
        "last_name": "User",
    }
    status, response = make_request(f"{BASE_URL}/auth/register", data=register_data)
    print(f"  Status : {status}")
    print(f"  Response: {json.dumps(response, indent=4)}")

    if status != 200:
        print("✗ Registration failed. Aborting test.")
        return

    # Extract JWT access token — user_id is NOT used anywhere below
    access_token = response.get("token")
    if not access_token:
        print("✗ No token in registration response. Aborting test.")
        return
    print(f"  ✓ Got register token: {access_token[:30]}...")

    # ------------------------------------------------------------------ #
    # 2. Login with the same credentials
    # ------------------------------------------------------------------ #
    print()
    print("--- 2. Logging in via POST /auth/login ---")
    login_data = {
        "email": register_data["email"],
        "password": register_data["password"],
    }
    status, response = make_request(f"{BASE_URL}/auth/login", data=login_data)
    print(f"  Status : {status}")
    print(f"  Response: {json.dumps(response, indent=4)}")

    if status == 200:
        access_token = response.get("token")  # Use the login token from here on
        print(f"  ✓ Login successful. Token: {access_token[:30]}...")
    else:
        print(f"  ✗ Login returned {status} — continuing with register token.")
    

    # ------------------------------------------------------------------ #
    # 3. Save a clipboard item (JWT-protected, no user_id in body)
    # ------------------------------------------------------------------ #
    print()
    print("--- 3. Saving clipboard item via POST /clipboard/personal ---")
    clipboard_data = {
        "content": "This is a secure test clipboard item!",
        "content_type": "text",
        # Note: no user_id field — identity comes from the JWT token
    }
    status, response = make_request(
        f"{BASE_URL}/clipboard/personal",
        method="POST",
        data=clipboard_data,
        token=access_token,
    )
    print(f"  Status : {status}")
    print(f"  Response: {json.dumps(response, indent=4)}")

    if status != 200:
        print("✗ Clipboard save failed.")
    else:
        assert "user_id" not in response, "FAIL: user_id should NOT appear in save response"
        assert "content" in response,     "FAIL: content missing from save response"
        print("  ✓ Clipboard item saved. No user_id in response.")

    # ------------------------------------------------------------------ #
    # 4. Get clipboard items (JWT-protected, no user_id query param)
    # ------------------------------------------------------------------ #
    print()
    print("--- 4. Fetching clipboard items via GET /clipboard/personal ---")
    status, response = make_request(
        f"{BASE_URL}/clipboard/personal",
        method="GET",
        token=access_token,
    )
    print(f"  Status : {status}")
    print(f"  Response: {json.dumps(response, indent=4)}")

    if status != 200:
        print("✗ Clipboard get failed.")
    else:
        for item in response:
            assert "user_id" not in item, "FAIL: user_id should NOT appear in get response items"
        print(f"  ✓ Retrieved {len(response)} clipboard item(s). No user_id in any response item.")

    # ------------------------------------------------------------------ #
    # 5. Verify that unauthenticated requests are rejected
    # ------------------------------------------------------------------ #
    print()
    print("--- 5. Testing unauthenticated request to /clipboard/personal ---")
    status, response = make_request(
        f"{BASE_URL}/clipboard/personal",
        method="POST",
        data=clipboard_data,
        token=None,  # No token
    )
    print(f"  Status : {status}")
    print(f"  Response: {json.dumps(response, indent=4)}")

    if status == 403:
        print("  ✓ Unauthenticated request correctly rejected with 403.")
    elif status == 401:
        print("  ✓ Unauthenticated request correctly rejected with 401.")
    else:
        print(f"  ✗ Expected 401/403 but got {status}.")

    print()
    print("=== Test flow complete ===")


if __name__ == "__main__":
    test_flow()
