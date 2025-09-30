import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';

class ApiService {
  final String baseUrl;

  const ApiService({this.baseUrl = 'http://127.0.0.1:8000'});

  Uri _uri(String path, [Map<String, dynamic>? query]) {
    return Uri.parse('$baseUrl$path').replace(queryParameters: query);
  }

  Future<Map<String, dynamic>> submitBusinessIdea({
    required String uid,
    required String title,
    required String description,
    String? filePath,
    String? fileUrl,
    String language = 'en',
  }) async {
    final body = {
      'uid': uid,
      'title': title,
      'description': description,
      'language': language,
      if (filePath != null) 'path': filePath,
      if (fileUrl != null) 'file_url': fileUrl,
    };
    final resp = await http
        .post(
          _uri('/ideas'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(minutes: 2));
    if (resp.statusCode != 200) {
      throw Exception('Submit idea failed: ${resp.body}');
    }
    return jsonDecode(resp.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getIdeasByUser(String uid) async {
    final resp = await http
        .get(_uri('/ideas', {'uid': uid}))
        .timeout(const Duration(minutes: 1));
    if (resp.statusCode != 200) {
      throw Exception('List ideas failed: ${resp.body}');
    }
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list.map((e) => e as Map<String, dynamic>).toList();
  }

  Future<void> addMentorFeedback(String ideaId, String feedback) async {
    final resp = await http
        .post(
          _uri('/ideas/$ideaId/feedback'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'feedback': feedback}),
        )
        .timeout(const Duration(minutes: 1));
    if (resp.statusCode != 200) {
      throw Exception('Add feedback failed: ${resp.body}');
    }
  }

  Future<Map<String, int>> getStats() async {
    final resp = await http
        .get(_uri('/stats'))
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode != 200) {
      throw Exception('Get stats failed: ${resp.body}');
    }
    final data = jsonDecode(resp.body) as Map<String, dynamic>;
    return data.map((key, value) => MapEntry(key, (value as num).toInt()));
  }

  Future<List<Map<String, dynamic>>> getRecentActivities({
    int limit = 5,
  }) async {
    final resp = await http
        .get(_uri('/activities', {'limit': '$limit'}))
        .timeout(const Duration(seconds: 30));
    if (resp.statusCode != 200) {
      throw Exception('Get activities failed: ${resp.body}');
    }
    final list = jsonDecode(resp.body) as List<dynamic>;
    return list.map((e) => e as Map<String, dynamic>).toList();
  }
}