""" Unit tests for the API """

def test_filter_api(client):
    """ Dummy test to show API is working """
    body = {"gender": "Men"}
    response = client.post("/filter", json=body)
    assert response.status_code == 200
