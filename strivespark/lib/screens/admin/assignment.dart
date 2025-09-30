import 'package:flutter/material.dart';

class AssignmentScreen extends StatelessWidget {
  const AssignmentScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Assign Mentors')),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Mentor assignment is temporarily disabled while migrating from Firestore. '
            'This feature will return once the local FastAPI supports users and groups.',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}