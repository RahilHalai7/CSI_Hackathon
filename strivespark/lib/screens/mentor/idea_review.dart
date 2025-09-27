import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../widgets/idea_card.dart';
import 'feedback_form.dart';

class IdeaReviewScreen extends StatelessWidget {
  const IdeaReviewScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Business Ideas')),
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance.collection('business_ideas').snapshots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final ideas = snapshot.data!.docs;
          return ListView.builder(
            itemCount: ideas.length,
            itemBuilder: (context, index) {
              final data = ideas[index].data() as Map<String, dynamic>;
              return IdeaCard(
                title: data['title'],
                description: data['description'],
                status: data['status'],
                onTap: () => Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => FeedbackFormScreen(ideaId: ideas[index].id, ideaData: data),
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