import requests
import sys

BASE_URL = "http://localhost:8080/api/quick-stats"
DATASET_ID = "customer_segmentation_mixed.csv"

def test_endpoints():
    print("Testing refactored quick-stats endpoints...")
    
    # 1. Test Single Variable
    print("\n1. POST /api/quick-stats/single")
    try:
        r = requests.post(f"{BASE_URL}/single", json={"dataset_id": DATASET_ID, "variable": "Age"})
        if r.status_code == 200:
            data = r.json()
            print(f"   OK - type={data.get('type')}, n={data.get('n_observations')}")
        else:
            print(f"   FAIL - {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   ERROR - {e}")

    # 2. Test Dual Variable
    print("\n2. POST /api/quick-stats/dual")
    try:
        r = requests.post(f"{BASE_URL}/dual", json={
            "dataset_id": DATASET_ID, 
            "variable_x": "Age", 
            "variable_y": "Spending_Score",
            "correlation_type": "pearson"
        })
        if r.status_code == 200:
            data = r.json()
            print(f"   OK - corr={data.get('correlation',{}).get('coefficient')}")
        else:
            print(f"   FAIL - {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   ERROR - {e}")

    # 3. Test Time Series
    print("\n3. POST /api/quick-stats/time-series")
    try:
        r = requests.post(f"{BASE_URL}/time-series", json={
            "dataset_id": DATASET_ID, 
            "time_column": "Age", 
            "value_column": "Spending_Score",
            "periods_ahead": 5
        }, timeout=60)
        if r.status_code == 200:
            data = r.json()
            print(f"   OK - model={data.get('model_params',{}).get('order')}")
            print(f"   historical dates: {len(data.get('historical_data',{}).get('dates',[]))}")
        else:
            print(f"   FAIL - {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   ERROR - {e}")

    # 4. Test Export
    print("\n4. POST /api/quick-stats/export")
    try:
        r = requests.post(f"{BASE_URL}/export", json={
            "analysis_type": "single",
            "params": {"dataset_id": DATASET_ID, "variable": "Age"}
        })
        if r.status_code == 200:
            print(f"   OK - {len(r.content)} bytes received")
        else:
            print(f"   FAIL - {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"   ERROR - {e}")

    print("\nDone!")

if __name__ == "__main__":
    test_endpoints()
