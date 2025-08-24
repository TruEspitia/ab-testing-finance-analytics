import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Load data
df = pd.read_csv("Engineered_Survey_Results.csv")

# Drop missing target
df = df.dropna(subset=["zas_score"])

# Split features and target
X = df.drop("zas_score", axis=1)
y = df["zas_score"]

# Separate numerical and categorical features
num_cols = X.select_dtypes(include=["int64", "float64"]).columns
cat_cols = X.select_dtypes(include=["object", "category", "bool"]).columns

# Preprocessing pipeline
numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="mean")),
    ("scaler", StandardScaler())
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))  # sparse_output for sklearn 1.6+
])

preprocessor = ColumnTransformer([
    ("num", numeric_pipeline, num_cols),
    ("cat", categorical_pipeline, cat_cols)
])

# Final pipeline
model = Pipeline([
    ("preprocessor", preprocessor),
    ("regressor", LinearRegression())
])

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train and log
with mlflow.start_run() as run:
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # Metrics
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    mlflow.log_metric("r2_score", r2)
    mlflow.log_metric("rmse", rmse)

    # Tags
    mlflow.set_tag("author", "Aeshy")
    mlflow.set_tag("model_type", "LinearRegression")
    mlflow.set_tag("project", "Zone Affluence Score")
    mlflow.set_tag("version", "v1")

    # Log & register
    mlflow.sklearn.log_model(
        sk_model=model,
        artifact_path="model",
        registered_model_name="zas_model"
    )

    print(f"Run complete. R² = {r2:.4f}, RMSE = {rmse:.4f}")
