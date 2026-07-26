"""
Crop Price Forecasting API — Rwanda
------------------------------------
Serves predictions from the best (deployable) model trained in
summative/linear_regression/multivariate.ipynb (Decision Tree Regressor,
chosen over Random Forest for deployability - see notebook Section 6/7),
and exposes a retraining endpoint for when new price data becomes available.

Run locally:
    uvicorn prediction:app --reload

Docs (Swagger UI):
    http://127.0.0.1:8000/docs
"""

import json
import os
from enum import Enum
from typing import List

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------
# Load model artifacts (produced by the Task 1 notebook)
# ---------------------------------------------------------------------
model = joblib.load(os.path.join(BASE_DIR, "best_model.pkl"))
scaler = joblib.load(os.path.join(BASE_DIR, "scaler.pkl"))
feature_cols: List[str] = joblib.load(os.path.join(BASE_DIR, "feature_cols.pkl"))

with open(os.path.join(BASE_DIR, "meta.json")) as f:
    META = json.load(f)

NUMERIC_COLS = META["numeric_cols"]           # ['latitude', 'longitude', 'year', 'month']
CATEGORICAL_COLS = META["categorical_cols"]   # ['admin1', 'commodity', 'unit', 'pricetype']

LAT_MIN, LAT_MAX = -2.9, -1.0     # Rwanda's approximate latitude bounds (with small margin)
LON_MIN, LON_MAX = 28.8, 30.9     # Rwanda's approximate longitude bounds (with small margin)
YEAR_MIN, YEAR_MAX = 2000, 2035   # historical start to a reasonable forecast horizon

# ---------------------------------------------------------------------
# Dynamic Enums built from the exact categories seen during training,
# so Swagger UI renders them as dropdowns and invalid categories are
# rejected with a 422 before ever reaching the model.
# ---------------------------------------------------------------------
def _make_enum(name: str, values: List[str]) -> Enum:
    return Enum(name, {v.replace(" ", "_").replace("(", "").replace(")", "")
                        .replace(",", "").replace("/", "_"): v for v in values})

Admin1Enum = _make_enum("Admin1Enum", META["admin1_values"])
CommodityEnum = _make_enum("CommodityEnum", META["commodities"])
UnitEnum = _make_enum("UnitEnum", META["unit_values"])
PriceTypeEnum = _make_enum("PriceTypeEnum", META["pricetype_values"])


class PredictionInput(BaseModel):
    admin1: Admin1Enum = Field(..., description="Rwandan province")
    commodity: CommodityEnum = Field(..., description="Food commodity")
    unit: UnitEnum = Field(..., description="Unit of sale")
    pricetype: PriceTypeEnum = Field(..., description="Retail or Wholesale")
    latitude: float = Field(..., ge=LAT_MIN, le=LAT_MAX,
                             description=f"Market latitude ({LAT_MIN} to {LAT_MAX})")
    longitude: float = Field(..., ge=LON_MIN, le=LON_MAX,
                              description=f"Market longitude ({LON_MIN} to {LON_MAX})")
    year: int = Field(..., ge=YEAR_MIN, le=YEAR_MAX,
                       description=f"Year ({YEAR_MIN}-{YEAR_MAX})")
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")

    class Config:
        json_schema_extra = {
            "example": {
                "admin1": "Kigali City",
                "commodity": "Maize",
                "unit": "KG",
                "pricetype": "Retail",
                "latitude": -1.95,
                "longitude": 30.06,
                "year": 2026,
                "month": 7,
            }
        }


class PredictionOutput(BaseModel):
    predicted_price_rwf: float
    input_echo: PredictionInput


class RetrainResponse(BaseModel):
    message: str
    rows_used: int
    r2_score: float
    rmse_rwf: float


# ---------------------------------------------------------------------
# App + CORS
# ---------------------------------------------------------------------
app = FastAPI(
    title="Rwanda Crop Price Forecasting API",
    description=(
        "Predicts crop/food prices (RWF) across Rwanda from a Decision Tree "
        "Regressor trained on WFP historical price data. Built to support "
        "the mission of using technology to support sustainable growth in "
        "agriculture."
    ),
    version="1.0.0",
)

# CORS configuration and reasoning:
# - This API has no authentication and returns no user-specific or sensitive
#   data (only a commodity price prediction), so exposure risk is inherently
#   low. Even so, we deliberately avoid a blanket wildcard ("*") for origins
#   and headers and instead enumerate specific values:
# - allow_origins: the known, legitimate callers of this API. The Flutter
#   mobile app itself sends NO browser "Origin" header at all (CORS is a
#   browser-only mechanism and does not apply to native HTTP clients), so it
#   is unaffected by this list either way. What DOES need explicit origins
#   are (a) the Swagger UI /docs page testing tool if opened from a
#   different host, and (b) local development tools during testing. We
#   therefore explicitly whitelist localhost dev origins and this API's own
#   deployed origin, rather than "*".
# - allow_credentials=False: no cookies or auth headers are used by this
#   API, so credentialed cross-origin requests are unnecessary and are
#   explicitly disabled.
# - allow_methods=["GET", "POST"]: the only two HTTP verbs this API actually
#   implements (health check + predict/retrain); PUT/DELETE/PATCH are not
#   exposed and are therefore not allowed.
# - allow_headers=["Content-Type"]: the only header genuinely required by
#   clients calling this API (JSON request bodies); no wildcard.
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "https://linear-regression-crop-price.onrender.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------
# Shared preprocessing (mirrors the Task 1 notebook exactly)
# ---------------------------------------------------------------------
def _build_feature_row(admin1, commodity, unit, pricetype, latitude, longitude, year, month) -> pd.DataFrame:
    row = pd.DataFrame([{
        "admin1": admin1, "commodity": commodity, "unit": unit, "pricetype": pricetype,
        "latitude": latitude, "longitude": longitude, "year": year, "month": month,
    }])
    row_encoded = pd.get_dummies(row, columns=CATEGORICAL_COLS)
    row_encoded = row_encoded.reindex(columns=feature_cols, fill_value=0)
    row_encoded[NUMERIC_COLS] = scaler.transform(row_encoded[NUMERIC_COLS])
    return row_encoded


# ---------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------
@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "message": "Rwanda Crop Price Forecasting API is running. See /docs for Swagger UI.",
        "model": META.get("best_model", "unknown"),
    }


@app.post("/predict", response_model=PredictionOutput, tags=["Prediction"])
def predict(payload: PredictionInput):
    """Predict a crop price (RWF) from province, commodity, unit, price type,
    market coordinates, and date."""
    try:
        row_encoded = _build_feature_row(
            payload.admin1.value, payload.commodity.value, payload.unit.value,
            payload.pricetype.value, payload.latitude, payload.longitude,
            payload.year, payload.month,
        )
        log_pred = model.predict(row_encoded.values)[0]
        price = float(np.expm1(log_pred))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return PredictionOutput(predicted_price_rwf=round(price, 2), input_echo=payload)


@app.post("/retrain", response_model=RetrainResponse, tags=["Retraining"])
def retrain(file: UploadFile = File(..., description=(
        "CSV with the same columns as the WFP Rwanda training data "
        "(date, admin1, admin2, market, market_id, latitude, longitude, "
        "category, commodity, commodity_id, unit, priceflag, pricetype, "
        "currency, price, usdprice). New rows are combined with the "
        "existing training data and the model is retrained from scratch."))):
    """Retrain the model when new price data is available (uploaded or streamed).
    Overwrites best_model.pkl and scaler.pkl in place so /predict immediately
    uses the updated model."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Please upload a .csv file.")

    try:
        new_df = pd.read_csv(file.file)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not parse CSV: {e}")

    required_cols = {"date", "admin1", "latitude", "longitude", "category", "commodity",
                      "unit", "priceflag", "pricetype", "currency", "price", "usdprice"}
    missing = required_cols - set(new_df.columns)
    if missing:
        raise HTTPException(status_code=422,
                             detail=f"Uploaded CSV is missing required columns: {sorted(missing)}")

    # Combine with the original training data
    base_df = pd.read_csv(os.path.join(BASE_DIR, "wfp_food_prices_rwa.csv"), skiprows=[1])
    combined = pd.concat([base_df, new_df], ignore_index=True).drop_duplicates()

    combined["date"] = pd.to_datetime(combined["date"])
    combined["year"] = combined["date"].dt.year
    combined["month"] = combined["date"].dt.month
    combined = combined[combined["priceflag"] == "actual"].copy()

    drop_cols = ["usdprice", "currency", "market_id", "commodity_id",
                 "admin2", "market", "category", "priceflag", "date"]
    combined = combined.drop(columns=[c for c in drop_cols if c in combined.columns])
    combined["log_price"] = np.log1p(combined["price"])

    encoded = pd.get_dummies(combined, columns=CATEGORICAL_COLS)
    new_feature_cols = [c for c in encoded.columns if c not in ("price", "log_price")]
    X = encoded[new_feature_cols].astype(float)
    y = encoded["log_price"].astype(float)
    y_price = encoded["price"].astype(float)

    X_train, X_test, y_train, y_test, yp_train, yp_test = train_test_split(
        X, y, y_price, test_size=0.2, random_state=42)

    from sklearn.preprocessing import StandardScaler
    new_scaler = StandardScaler()
    X_train_s = X_train.copy()
    X_test_s = X_test.copy()
    X_train_s[NUMERIC_COLS] = new_scaler.fit_transform(X_train[NUMERIC_COLS])
    X_test_s[NUMERIC_COLS] = new_scaler.transform(X_test[NUMERIC_COLS])

    new_model = DecisionTreeRegressor(max_depth=None, min_samples_leaf=3, random_state=42)
    new_model.fit(X_train_s.values, y_train.values)

    pred = new_model.predict(X_test_s.values)
    r2 = float(r2_score(y_test, pred))
    rmse_rwf = float(mean_squared_error(yp_test, np.expm1(pred)) ** 0.5)

    # Persist the retrained model in place
    global model, scaler, feature_cols
    joblib.dump(new_model, os.path.join(BASE_DIR, "best_model.pkl"))
    joblib.dump(new_scaler, os.path.join(BASE_DIR, "scaler.pkl"))
    joblib.dump(new_feature_cols, os.path.join(BASE_DIR, "feature_cols.pkl"))
    model, scaler, feature_cols = new_model, new_scaler, new_feature_cols

    return RetrainResponse(
        message="Model retrained and saved successfully.",
        rows_used=len(combined),
        r2_score=round(r2, 4),
        rmse_rwf=round(rmse_rwf, 2),
    )
