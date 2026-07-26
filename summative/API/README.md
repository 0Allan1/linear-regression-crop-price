# Rwanda Crop Price Forecasting API

FastAPI service that predicts crop/food prices (RWF) in Rwanda, using the
Decision Tree model trained in `../linear_regression/multivariate.ipynb`.

## Already deployed (use this)

This API is live at **https://linear-regression-crop-price.onrender.com** —
Swagger UI: **https://linear-regression-crop-price.onrender.com/docs**

(Free-tier Render instances sleep after inactivity; the first request after
idling can take 30-60 seconds to wake up — this is normal.)

## Run locally (optional, for development only)

```bash
cd summative/API
pip install -r requirements.txt
uvicorn prediction:app --reload
```

While this command is actively running, `http://127.0.0.1:8000/docs` will
work in your own browser. It is NOT a public URL — if you're not currently
running this command yourself, that link will fail to connect. Use the
deployed URL above instead.
## Endpoints

- `GET /` — health check
- `POST /predict` — predict a price from province, commodity, unit, price type, market coordinates, year, and month
- `POST /retrain` — upload a new CSV (same schema as the training data) to retrain and hot-swap the model in place

## Files

- `prediction.py` — the FastAPI app
- `best_model.pkl`, `scaler.pkl`, `feature_cols.pkl` — trained model artifacts
- `meta.json` — valid categorical values used to build request validation
- `wfp_food_prices_rwa.csv` — base training data (used as the retraining baseline)
- `requirements.txt` — pinned dependencies for Render's build step
