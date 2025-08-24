import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

# Load the cleaned dataset
df = pd.read_csv("cleaned_survey_results.csv")

from sklearn.preprocessing import LabelEncoder

# Encode target column
label_encoder = LabelEncoder()
df[target_col] = label_encoder.fit_transform(df[target_col])

# Set the target column
target_col = "consume_frequency(weekly)"

# Check if target column exists
if target_col not in df.columns:
    print("Available columns:", df.columns.tolist())
    raise ValueError(f"Target column '{target_col}' not found in dataset!")

# Drop non-numeric or identifier columns that shouldn't be used as features
columns_to_drop = ['respondent_id']
if target_col in df.columns:
    columns_to_drop.append(target_col)

# Prepare features and target
X = df.drop(columns=columns_to_drop)
y = df[target_col]

# Encode categorical features
X = pd.get_dummies(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# Train a Random Forest model
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("MSE:", mean_squared_error(y_test, y_pred))
print("R²:", r2_score(y_test, y_pred))

# Save model
joblib.dump(model, "rf_model.pkl")
print("✅ Model trained and saved as 'rf_model.pkl'")
