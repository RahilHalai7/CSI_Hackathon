import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class MentorApprovalScreen extends StatelessWidget {
  const MentorApprovalScreen({super.key});

  Future<void> approveMentor(String uid) async {
    await FirebaseFirestore.instance.collection('users').doc(uid).update({'approved': true});
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentor Approval')),
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance
            .collection('users')
            .where('role', isEqualTo: 'mentor')
            .where('approved', isEqualTo: false)
            .snapshots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final mentors = snapshot.data!.docs;
          return ListView.builder(
            itemCount: mentors.length,
            itemBuilder: (context, index) {
              final data = mentors[index].data() as Map<String, dynamic>;
              final uid = mentors[index].id;
              return ListTile(
                title: Text(data['email']),
                trailing: ElevatedButton(
                  onPressed: () => approveMentor(uid),
                  child: const Text('Approve'),
                ),
              );
            },
          );
        },
      ),
    );
  }
}