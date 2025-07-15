import requests


def allowed_file(filename: str, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def check_service_health(health_url: str, timeout: int = 3) -> bool:
    try:
        response = requests.get(health_url, timeout=timeout)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False
