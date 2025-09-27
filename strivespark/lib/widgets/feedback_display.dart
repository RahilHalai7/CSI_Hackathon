import 'package:flutter/material.dart';

class FeedbackDisplay extends StatelessWidget {
  final String strengths;
  final String weaknesses;
  final String feasibility;
  final String mentorFeedback;

  const FeedbackDisplay({
    super.key,
    required this.strengths,
    required this.weaknesses,
    required this.feasibility,
    required this.mentorFeedback,
  });

  Widget _buildSection(String title, String content) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          Text(content),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.all(16),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildSection("Strengths", strengths),
            _buildSection("Weaknesses", weaknesses),
            _buildSection("Feasibility", feasibility),
            _buildSection("Mentor Feedback", mentorFeedback),
          ],
        ),
      ),
    );
  }
}