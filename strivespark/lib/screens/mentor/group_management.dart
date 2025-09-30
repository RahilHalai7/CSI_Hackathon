import 'package:flutter/material.dart';

class GroupManagementScreen extends StatelessWidget {
  const GroupManagementScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentor Group Management')),
      body: const Center(
        child: Padding(
          padding: EdgeInsets.all(16.0),
          child: Text(
            'Mentor group management is not available yet with the local API. '
            'We are migrating away from Firestore. This screen will return once '
            'groups are supported via FastAPI.',
            textAlign: TextAlign.center,
          ),
        ),
      ),
    );
  }
}