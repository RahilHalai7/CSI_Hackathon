import 'package:flutter/material.dart';
import 'package:strivespark/services/api_service.dart';
import '../../widgets/idea_card.dart';
import 'feedback_form.dart';

class IdeaReviewScreen extends StatelessWidget {
  const IdeaReviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Business Ideas')),
      body: FutureBuilder<List<Map<String, dynamic>>>(
        future: ApiService().getIdeas(),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }
          final ideas = snapshot.data ?? [];
          return ListView.builder(
            itemCount: ideas.length,
            itemBuilder: (context, index) {
              final data = ideas[index];
              return IdeaCard(
                title: data['title'] ?? 'Untitled',
                description: data['description'] ?? '',
                status: data['status'] ?? 'submitted',
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => FeedbackFormScreen(
                      ideaId: (data['id'] ?? '').toString(),
                      ideaData: data,
                    ),
                  ),
                ),
              );
            },
          );
        },
      ),
    );
  }
}