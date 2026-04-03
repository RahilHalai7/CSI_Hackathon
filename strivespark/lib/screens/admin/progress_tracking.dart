import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../../widgets/feedback_display.dart';

class ProgressTrackingScreen extends StatefulWidget {
  const ProgressTrackingScreen({super.key});

  @override
  State<ProgressTrackingScreen> createState() => _ProgressTrackingScreenState();
}

class _ProgressTrackingScreenState extends State<ProgressTrackingScreen> {
  List<Map<String, dynamic>> businessIdeas = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadBusinessIdeas();
  }

  Future<void> _loadBusinessIdeas() async {
    try {
      final response = await http.get(
        Uri.parse('http://127.0.0.1:8000/ideas'),
        headers: {'Content-Type': 'application/json'},
      );
      
      if (response.statusCode == 200) {
        final List<dynamic> data = jsonDecode(response.body);
        setState(() {
          businessIdeas = data.cast<Map<String, dynamic>>();
          isLoading = false;
        });
      } else {
        setState(() {
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Business Progress')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : businessIdeas.isEmpty
              ? const Center(child: Text('No business ideas found'))
              : ListView.builder(
                  itemCount: businessIdeas.length,
                  itemBuilder: (context, index) {
                    final idea = businessIdeas[index];
                    return ExpansionTile(
                      title: Text(idea['title'] ?? 'Untitled'),
                      subtitle: Text(idea['status'] ?? 'pending'),
                      children: [
                        FeedbackDisplay(
                          strengths: idea['feedback']?['strengths'] ?? '',
                          weaknesses: idea['feedback']?['weaknesses'] ?? '',
                          feasibility: idea['feedback']?['feasibility'] ?? '',
                          mentorFeedback: idea['mentor_feedback'] ?? '',
                        ),
                      ],
                    );
                  },
                ),
    );
  }
}