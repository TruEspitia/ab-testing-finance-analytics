import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_squared_error, r2_score

#  Use XGBoost if available
try:
    from xgboost import XGBRegressor
    has_xgb = True
except ImportError:
    has_xgb = False

# Load cleaned + engineered dataset
df = pd.read_csv("Engineered_Survey_Results.csv")
df = df.dropna(subset=["zas_score"])
df = df.drop(columns=["Unnamed: 0", "respondent_id"], errors='ignore')

# Define features and target
X = df.drop(columns=["zas_score"])
y = df["zas_score"]

# Identify feature types
num_cols = X.select_dtypes(include=["float64", "int64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object"]).columns.tolist()

# Preprocessing for numerical and categorical columns
numeric_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler())
])

categorical_transformer = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))  # Updated for sklearn >= 1.2
])

# Combine preprocessors
preprocessor = ColumnTransformer([
    ("num", numeric_transformer, num_cols),
    ("cat", categorical_transformer, cat_cols)
])

# Define models
models = {
    "LinearRegression": LinearRegression(),
    "RandomForest": RandomForestRegressor(n_estimators=100, random_state=42),
    "GradientBoosting": GradientBoostingRegressor(n_estimators=100, random_state=42)
}

if has_xgb:
    models["XGBoost"] = XGBRegressor(n_estimators=100, random_state=42)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Set MLflow experiment
mlflow.set_experiment("Zone Affluence Score Model")

# Train and log each model
for name, model in models.items():
    with mlflow.start_run(run_name=f"{name}_run"):
        pipeline = Pipeline([
            ("preprocessor", preprocessor),
            ("regressor", model)
        ])

        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)

        r2 = r2_score(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))  

        mlflow.log_param("model", name)
        mlflow.log_metric("r2_score", r2)
        mlflow.log_metric("rmse", rmse)

        mlflow.sklearn.log_model(
            pipeline,
            name.lower(),
            registered_model_name=name
        )

        print(f"Model: {name} | R2: {r2:.4f} | RMSE: {rmse:.4f}")
