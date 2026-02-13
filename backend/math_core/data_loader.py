import pandas as pd
import numpy as np
import io

class DataLoader:
    @staticmethod
    def load_file(filepath):
        """
        Loads a file and returns x, y data.
        Assumes first column is x, second is y.
        Returns: { 'filename': name, 'data': [{'x': val, 'y': val}, ...] }
        """
        try:
            if filepath.endswith('.csv') or filepath.endswith('.txt'):
                df = pd.read_csv(filepath)
            elif filepath.endswith('.xlsx') or filepath.endswith('.xls'):
                df = pd.read_excel(filepath)
            else:
                return {"error": "Unsupported file format"}

            # Basic cleaning: drop NaNs
            df = df.dropna()
            
            # Select ALL numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            
            if len(numeric_cols) < 2:
                return {"error": "File must have at least two numeric columns"}
            
            # Convert to list of records {col1: val, col2: val}
            # Convert numpy types to native Python types for JSON serialization
            data_list = []
            for record in df.to_dict(orient='records'):
                converted_record = {}
                for key, val in record.items():
                    if isinstance(val, (np.integer, np.floating)):
                        converted_record[key] = float(val)
                    else:
                        converted_record[key] = val
                data_list.append(converted_record)
                
            return {
                "filename": filepath,
                "columns": numeric_cols,
                "data": data_list
            }

        except Exception as e:
            return {"error": str(e)}
