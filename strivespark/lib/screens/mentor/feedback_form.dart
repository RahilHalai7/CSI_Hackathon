import 'package:flutter/material.dart';
import '../../widgets/feedback_display.dart';
import '../../services/firestore_service.dart';

class FeedbackFormScreen extends StatefulWidget {
  final String ideaId;
  final Map<String, dynamic> ideaData;

  const FeedbackFormScreen({super.key, required this.ideaId, required this.ideaData});

  @override
  State<FeedbackFormScreen> createState() => _FeedbackFormScreenState();
}

class _FeedbackFormScreenState extends State<FeedbackFormScreen> {
  final _controller = TextEditingController();
  bool isSubmitting = false;

  Future<void> _submitFeedback() async {
    setState(() => isSubmitting = true);
    await FirestoreService().addMentorFeedback(widget.ideaId, _controller.text);
    setState(() => isSubmitting = false);
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Feedback submitted')));
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final feedback = widget.ideaData['feedback'] ?? {};
    return Scaffold(
      appBar: AppBar(title: const Text('Review Idea')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          FeedbackDisplay(
            strengths: feedback['strengths'] ?? '',
            weaknesses: feedback['weaknesses'] ?? '',
            feasibility: feedback['feasibility'] ?? '',
            mentorFeedback: widget.ideaData['mentor_feedback'] ?? '',
          ),
          const SizedBox(height: 20),
          TextField(
            controller: _controller,
            maxLines: 5,
            decoration: const InputDecoration(
              labelText: 'Your Feedback',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 12),
          ElevatedButton(
            onPressed: isSubmitting ? null : _submitFeedback,
            child: isSubmitting ? const CircularProgressIndicator() : const Text('Submit Feedback'),
          ),
        ],
      ),
    );
  }
}