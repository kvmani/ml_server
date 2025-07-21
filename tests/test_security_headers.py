def test_csp_header(client):
    resp = client.get("/")
    csp = resp.headers.get("Content-Security-Policy")
    assert csp is not None
    assert "script-src" in csp
    assert "nonce" in csp
