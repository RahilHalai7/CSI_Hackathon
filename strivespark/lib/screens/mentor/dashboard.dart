import 'package:flutter/material.dart';
import 'idea_review.dart';
import 'group_management.dart';

class MentorDashboard extends StatelessWidget {
  const MentorDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentor Dashboard')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ElevatedButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const IdeaReviewScreen())),
            child: const Text('Review Business Ideas'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const GroupManagementScreen())),
            child: const Text('Manage Mentor Groups'),
          ),
        ],
      ),
    );
  }
}