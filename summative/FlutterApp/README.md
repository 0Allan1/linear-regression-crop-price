# Rwanda Crop Price Predictor — Flutter App

A single-page Flutter app that calls the `/predict` endpoint of the FastAPI
service in `../API/` and shows the predicted crop price, or a clear error
message if inputs are invalid or missing.

## Before running

Open `lib/main.dart` and update this line with your deployed Render URL
(no trailing slash):

```dart
static const String baseUrl = 'https://YOUR-RENDER-APP-NAME.onrender.com';
```

## Run instructions

1. Install the [Flutter SDK](https://docs.flutter.dev/get-started/install) if you haven't already.
2. From this folder:
   ```bash
   flutter pub get
   flutter run
   ```
   Select a connected device or emulator when prompted.
3. To build a release APK (Android):
   ```bash
   flutter build apk --release
   ```
   The output APK will be at `build/app/outputs/flutter-apk/app-release.apk`.

## What the app does

- 8 text fields, one per model input: Province, Commodity, Unit, Price Type,
  Latitude, Longitude, Year, Month.
- A **Predict** button that calls `POST {baseUrl}/predict`.
- A result area that shows either:
  - the predicted price in RWF, or
  - a clear error message (missing fields, invalid types, out-of-range
    values, or a network/connection problem).

## Note

This code was written and syntax-checked (balanced braces/parens) but
**could not be compiled or run** in the environment it was generated in
(no Flutter SDK available there). Please run `flutter analyze` and
`flutter run` yourself before recording your demo video, and let me know
if you hit any errors — I can fix them from the error message.
