# Rwanda Crop Price Forecasting API

FastAPI service that predicts crop/food prices (RWF) in Rwanda, using the
Decision Tree model trained in `../linear_regression/multivariate.ipynb`.

## Run locally

```bash
cd summative/API
pip install -r requirements.txt
uvicorn prediction:app --reload
```

Then open http://127.0.0.1:8000/docs for the Swagger UI.

## Deploy on Render

1. Push this repo to GitHub.
2. On Render: **New +** → **Web Service** → connect the repo.
3. **Root Directory:** `summative/API`
4. **Build Command:** `pip install -r requirements.txt`
5. **Start Command:** `uvicorn prediction:app --host 0.0.0.0 --port $PORT`
6. Deploy. Your Swagger UI will be publicly available at:
   `https://<your-service-name>.onrender.com/docs`

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
