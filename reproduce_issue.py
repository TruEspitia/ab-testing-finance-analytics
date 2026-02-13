
import requests
import pandas as pd
import io
import json

# Setup
BASE_URL = "http://localhost:8080/api"

def create_test_dataset():
    # Create a simple dataset with numeric variables
    data = {
        "var_a": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "var_b": [2, 4, 5, 4, 5, 7, 9, 10, 12, 14],
        "var_c": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1] # Constant
    }
    df = pd.DataFrame(data)
    
    # Save to CSV in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_content = csv_buffer.getvalue()
    
    # Upload
    files = {'file': ('test_data.csv', csv_content, 'text/csv')}
    response = requests.post(f"{BASE_URL}/upload", files=files)
    print("Upload response:", response.status_code)
    if response.status_code == 200:
        return response.json()['dataset']['id']
    return None

def test_full_analysis(dataset_id):
    if not dataset_id:
        print("Skipping analysis, no dataset")
        return

    payload = {
        "dataset_id": dataset_id,
        "variable_x": "var_a",
        "variable_y": "var_b",
        "correlation_type": "full"
    }
    
    print("\nTesting 'full' analysis...")
    try:
        response = requests.post(f"{BASE_URL}/quick-stats/dual", json=payload)
        print("Status Code:", response.status_code)
        if response.status_code != 200:
            print("Error Response:", response.text)
        else:
            print("Success! Response keys:", response.json().keys())
    except Exception as e:
        print("Request failed:", e)

if __name__ == "__main__":
    dataset_id = create_test_dataset()
    if dataset_id:
        test_full_analysis(dataset_id)
