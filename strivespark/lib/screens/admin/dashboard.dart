import 'package:flutter/material.dart';
import 'mentor_approval.dart';
import 'assignment.dart';
import 'progress_tracking.dart';

class AdminDashboard extends StatelessWidget {
  const AdminDashboard({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Admin Dashboard')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          ElevatedButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const MentorApprovalScreen())),
            child: const Text('Approve Mentors'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const AssignmentScreen())),
            child: const Text('Assign Mentors to Entrepreneurs'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const ProgressTrackingScreen())),
            child: const Text('Track Business Progress'),
          ),
        ],
      ),
    );
  }
}