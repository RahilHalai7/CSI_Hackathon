import 'package:http/http.dart' as http;
import 'dart:convert';

class LLMFeedbackService {
  final String apiUrl = 'https://your-llm-endpoint.com/generate';

  Future<Map<String, String>> generateFeedback(String ideaText) async {
    final response = await http.post(
      Uri.parse(apiUrl),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'prompt': ideaText}),
    );

    final data = jsonDecode(response.body);
    return {
      'strengths': data['strengths'],
      'weaknesses': data['weaknesses'],
      'feasibility': data['feasibility'],
    };
  }
}