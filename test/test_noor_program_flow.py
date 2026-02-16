from fastapi.testclient import TestClient

from app.main import app


def test_noor_registration_page_is_public_and_shows_form():
    with TestClient(app) as client:
        response = client.get('/ui/dashboard/noor')

    assert response.status_code == 200
    assert 'ثبت درخواست کلاس قرآن' in response.text
    assert 'name="first_name"' in response.text
    assert 'name="last_name"' in response.text


def test_noor_registration_submit_works_without_authentication():
    with TestClient(app) as client:
        response = client.post(
            '/ui/dashboard/noor',
            data={
                'first_name': 'محمد',
                'last_name': 'رضایی',
                'level': 3,
            },
        )

    assert response.status_code == 200
    assert 'درخواست کلاس قرآن با موفقیت ثبت شد.' in response.text