import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

void main() {
  runApp(const CropPriceApp());
}

class CropPriceApp extends StatelessWidget {
  const CropPriceApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Rwanda Crop Price Predictor',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(
          seedColor: const Color(0xFF2E7D32), // agricultural green
          brightness: Brightness.light,
        ),
        scaffoldBackgroundColor: const Color(0xFFF4F6F1),
        inputDecorationTheme: InputDecorationTheme(
          filled: true,
          fillColor: Colors.white,
          border: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: BorderSide(color: Colors.grey.shade300),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFF2E7D32), width: 2),
          ),
          contentPadding:
              const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        ),
      ),
      home: const PredictionPage(),
    );
  }
}

class PredictionPage extends StatefulWidget {
  const PredictionPage({super.key});

  @override
  State<PredictionPage> createState() => _PredictionPageState();
}

class _PredictionPageState extends State<PredictionPage> {
  // --------------------------------------------------------------
  // IMPORTANT: update this to your deployed Render URL, e.g.
  // 'https://rwanda-crop-price-api.onrender.com'
  // Keep it with NO trailing slash.
  // --------------------------------------------------------------
  static const String baseUrl = 'https://YOUR-RENDER-APP-NAME.onrender.com';

  final _admin1Controller = TextEditingController(text: 'Kigali City');
  final _commodityController = TextEditingController(text: 'Maize');
  final _unitController = TextEditingController(text: 'KG');
  final _pricetypeController = TextEditingController(text: 'Retail');
  final _latitudeController = TextEditingController(text: '-1.95');
  final _longitudeController = TextEditingController(text: '30.06');
  final _yearController = TextEditingController(text: '2026');
  final _monthController = TextEditingController(text: '7');

  bool _isLoading = false;
  String? _resultText;
  String? _errorText;

  @override
  void dispose() {
    _admin1Controller.dispose();
    _commodityController.dispose();
    _unitController.dispose();
    _pricetypeController.dispose();
    _latitudeController.dispose();
    _longitudeController.dispose();
    _yearController.dispose();
    _monthController.dispose();
    super.dispose();
  }

  Future<void> _predict() async {
    // Basic presence check before calling the API - the API itself is the
    // source of truth for type/range validation and returns a clear error
    // message we surface below.
    final fields = <String, TextEditingController>{
      'Province': _admin1Controller,
      'Commodity': _commodityController,
      'Unit': _unitController,
      'Price Type': _pricetypeController,
      'Latitude': _latitudeController,
      'Longitude': _longitudeController,
      'Year': _yearController,
      'Month': _monthController,
    };
    final missing = fields.entries
        .where((e) => e.value.text.trim().isEmpty)
        .map((e) => e.key)
        .toList();

    if (missing.isNotEmpty) {
      setState(() {
        _resultText = null;
        _errorText = 'Missing value(s) for: ${missing.join(', ')}';
      });
      return;
    }

    final latitude = double.tryParse(_latitudeController.text.trim());
    final longitude = double.tryParse(_longitudeController.text.trim());
    final year = int.tryParse(_yearController.text.trim());
    final month = int.tryParse(_monthController.text.trim());

    if (latitude == null || longitude == null || year == null || month == null) {
      setState(() {
        _resultText = null;
        _errorText =
            'Latitude/Longitude must be numbers, and Year/Month must be whole numbers.';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _resultText = null;
      _errorText = null;
    });

    try {
      final uri = Uri.parse('$baseUrl/predict');
      final response = await http
          .post(
            uri,
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode({
              'admin1': _admin1Controller.text.trim(),
              'commodity': _commodityController.text.trim(),
              'unit': _unitController.text.trim(),
              'pricetype': _pricetypeController.text.trim(),
              'latitude': latitude,
              'longitude': longitude,
              'year': year,
              'month': month,
            }),
          )
          .timeout(const Duration(seconds: 20));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final price = data['predicted_price_rwf'];
        setState(() {
          _resultText = '$price RWF';
          _errorText = null;
        });
      } else {
        setState(() {
          _resultText = null;
          _errorText = _parseApiError(response.body);
        });
      }
    } catch (e) {
      setState(() {
        _resultText = null;
        _errorText =
            'Could not reach the prediction service. Check your internet connection and try again.';
      });
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  /// FastAPI validation errors arrive as {"detail": [{"msg": "...", "loc": [...]}]}.
  /// Extract a readable message, or fall back to raw body on parse failure.
  String _parseApiError(String body) {
    try {
      final data = jsonDecode(body);
      final detail = data['detail'];
      if (detail is List && detail.isNotEmpty) {
        final messages = detail.map((d) {
          final loc = (d['loc'] as List?)?.last ?? '';
          final msg = d['msg'] ?? 'Invalid value';
          return '$loc: $msg';
        }).join('\n');
        return messages;
      } else if (detail is String) {
        return detail;
      }
      return 'Prediction failed. Please check your inputs.';
    } catch (_) {
      return 'Prediction failed. Please check your inputs.';
    }
  }

  Widget _buildTextField({
    required String label,
    required TextEditingController controller,
    TextInputType keyboardType = TextInputType.text,
  }) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: TextField(
        controller: controller,
        keyboardType: keyboardType,
        decoration: InputDecoration(labelText: label),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Rwanda Crop Price Predictor'),
        centerTitle: true,
        backgroundColor: const Color(0xFF2E7D32),
        foregroundColor: Colors.white,
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(20),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                'Enter the details below to predict a crop or food price '
                'in Rwandan Francs (RWF).',
                style: TextStyle(fontSize: 14, color: Colors.black54),
              ),
              const SizedBox(height: 20),

              Container(
                padding: const EdgeInsets.all(18),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.05),
                      blurRadius: 8,
                      offset: const Offset(0, 3),
                    ),
                  ],
                ),
                child: Column(
                  children: [
                    _buildTextField(
                      label: 'Province (e.g. Kigali City)',
                      controller: _admin1Controller,
                    ),
                    _buildTextField(
                      label: 'Commodity (e.g. Maize)',
                      controller: _commodityController,
                    ),
                    _buildTextField(
                      label: 'Unit (KG, L, Sack, Unit)',
                      controller: _unitController,
                    ),
                    _buildTextField(
                      label: 'Price Type (Retail or Wholesale)',
                      controller: _pricetypeController,
                    ),
                    Row(
                      children: [
                        Expanded(
                          child: _buildTextField(
                            label: 'Latitude',
                            controller: _latitudeController,
                            keyboardType:
                                const TextInputType.numberWithOptions(
                                    decimal: true, signed: true),
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildTextField(
                            label: 'Longitude',
                            controller: _longitudeController,
                            keyboardType:
                                const TextInputType.numberWithOptions(
                                    decimal: true, signed: true),
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        Expanded(
                          child: _buildTextField(
                            label: 'Year',
                            controller: _yearController,
                            keyboardType: TextInputType.number,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: _buildTextField(
                            label: 'Month (1-12)',
                            controller: _monthController,
                            keyboardType: TextInputType.number,
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 20),

              SizedBox(
                height: 50,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _predict,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(0xFF2E7D32),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                    ),
                  ),
                  child: _isLoading
                      ? const SizedBox(
                          height: 22,
                          width: 22,
                          child: CircularProgressIndicator(
                            color: Colors.white,
                            strokeWidth: 2.5,
                          ),
                        )
                      : const Text('Predict', style: TextStyle(fontSize: 16)),
                ),
              ),

              const SizedBox(height: 24),

              // Display area: shows the predicted value or an error message.
              if (_resultText != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: const Color(0xFFE8F5E9),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFF2E7D32)),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Predicted Price',
                        style: TextStyle(
                          fontSize: 13,
                          color: Colors.black54,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _resultText!,
                        style: const TextStyle(
                          fontSize: 26,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1B5E20),
                        ),
                      ),
                    ],
                  ),
                ),

              if (_errorText != null)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFDECEA),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFC62828)),
                  ),
                  child: Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Icon(Icons.error_outline, color: Color(0xFFC62828)),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          _errorText!,
                          style: const TextStyle(color: Color(0xFFC62828)),
                        ),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}
