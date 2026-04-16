def test_home_returns_200(client):
    assert client.get('/').status_code == 200


def test_unlock_page_redirects_without_session(client):
    r = client.get('/unlock', follow_redirects=False)
    assert r.status_code in (301, 302)


def test_dashboard_redirects_when_not_signed_in(client):
    r = client.get('/dashboard', follow_redirects=False)
    assert r.status_code in (301, 302)


def test_settings_redirects_when_not_signed_in(client):
    r = client.get('/settings', follow_redirects=False)
    assert r.status_code in (301, 302)


def test_api_logout_returns_json(client):
    r = client.post('/api/logout', json={})
    assert r.status_code == 200
    assert r.get_json().get('status') == 'success'
