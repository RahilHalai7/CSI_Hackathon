import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import '../../widgets/feedback_display.dart';

class ProgressTrackingScreen extends StatelessWidget {
  const ProgressTrackingScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Business Progress')),
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance.collection('business_ideas').snapshots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final ideas = snapshot.data!.docs;
          return ListView.builder(
            itemCount: ideas.length,
            itemBuilder: (context, index) {
              final data = ideas[index].data() as Map<String, dynamic>;
              return ExpansionTile(
                title: Text(data['title']),
                subtitle: Text(data['status']),
                children: [
                  FeedbackDisplay(
                    strengths: data['feedback']?['strengths'] ?? '',
                    weaknesses: data['feedback']?['weaknesses'] ?? '',
                    feasibility: data['feedback']?['feasibility'] ?? '',
                    mentorFeedback: data['mentor_feedback'] ?? '',
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }
}