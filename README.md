# Rwanda Crop Price Forecasting — Summative Project

## Mission

To build impactful technology solutions that improve lives by combining
software development, innovation, and problem-solving to support
sustainable growth in agriculture and other critical sectors. Volatile,
hard-to-predict crop prices make it difficult for farmers, traders, and
buyers in Rwanda to plan planting, selling, and purchasing decisions —
this project addresses that with a real, deployed price-forecasting tool.

## Dataset

**[WFP Food Prices for Rwanda](https://data.humdata.org/dataset/wfp-food-prices-for-rwanda)**,
published by the UN World Food Programme via the Humanitarian Data
Exchange (HDX). It contains ~156,000 monthly retail/wholesale price
records for 65 food commodities across 109 markets and all 5 provinces
of Rwanda, from January 2000 to mid-2026.

## Project Structure

```
linear_regression_model/
├── summative/
│   ├── linear_regression/
│   │   ├── multivariate.ipynb       # EDA, feature engineering, model training/comparison
│   │   └── wfp_food_prices_rwa.csv  # dataset
│   ├── API/
│   │   ├── prediction.py            # FastAPI service (/predict, /retrain)
│   │   ├── requirements.txt
│   │   ├── best_model.pkl, scaler.pkl, feature_cols.pkl, meta.json
│   │   └── README.md                # API run/deploy instructions
│   ├── FlutterApp/
│   │   ├── lib/main.dart            # single-page prediction app
│   │   ├── pubspec.yaml
│   │   └── README.md                # app run instructions
│   ├── pyproject.toml
│   └── uv.lock
└── README.md                        # this file
```

## Live API

- **Public API base URL:** `https://linear-regression-crop-price.onrender.com`
- **Swagger UI docs:** `https://linear-regression-crop-price.onrender.com/docs`
- **GitHub repo:** `https://github.com/0Allan1/linear-regression-crop-price`

## Video Demo

- **YouTube link:** `<TODO: paste your ≤7-minute demo video link here>`

## Running the Notebook

Open `summative/linear_regression/multivariate.ipynb` in Jupyter or
Google Colab. If using Colab, upload `wfp_food_prices_rwa.csv` to the
Colab session's file storage first (same folder as the notebook expects
it), then Runtime → Run all.

## Running the API Locally (optional — the API is already deployed live, see above)

```bash
cd summative/API
pip install -r requirements.txt
uvicorn prediction:app --reload
```
This starts a server on your own machine only. While `uvicorn` is running,
`http://127.0.0.1:8000/docs` will work in **your** browser. It is NOT a
public link — it only works while you're actively running the command above
on your own computer. For the public, always-available Swagger UI, use the
Live API link above instead. See `summative/API/README.md` for Render
deployment steps.

## Running the Mobile App

```bash
cd summative/FlutterApp
flutter pub get
flutter run
```
Update `baseUrl` in `lib/main.dart` with your deployed API URL first.
See `summative/FlutterApp/README.md` for details.
