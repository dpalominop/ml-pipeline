""" Unit tests for the API """

def test_filter_api(client):
    """Unit test to check filter endpoint."""
    payload = {
        "gender": "Men", 
        "sub_category": "Shoes", 
        "start_year": 2012,
        "limit": 10,
    }
    response = client.post("/filter", json=payload)

    assert response.status_code == 201
    assert "task_id" in response.json()
    
def test_filter_aug_api(client):
    """Unit test to check filter endpoint with augmentation."""
    payload = {
        "gender": "Men", 
        "sub_category": "Shoes", 
        "start_year": 2012,
        "limit": 10,
        "augmentation_config": {'albumentation': {
            'input_image': {'width': 60, 'height': 80}, 
            'cropping': {'height': {'min': 30, 'max': 70}}, 
            'resize': {'width': 256, 'height': 256}}}
    }
    response = client.post("/filter", json=payload)

    assert response.status_code == 201
    assert "task_id" in response.json()

def test_predict_api(client):
    """Unit test to check predict endpoint."""
    payload = {"s3_target": "s3_target"}
    response = client.post("/predict", json=payload)

    assert response.status_code == 201
    assert "task_id" in response.json()

def test_get_task_result(client):
    """Unit test to check task endpoint."""
    task_id = "fake_task_id"
    response = client.get(f"/task/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"id": task_id, "status": "PENDING", "error": None, "result": None}
