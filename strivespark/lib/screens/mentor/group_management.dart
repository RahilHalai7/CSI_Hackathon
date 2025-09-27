import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';

class GroupManagementScreen extends StatefulWidget {
  const GroupManagementScreen({super.key});

  @override
  State<GroupManagementScreen> createState() => _GroupManagementScreenState();
}

class _GroupManagementScreenState extends State<GroupManagementScreen> {
  List<String> selectedEntrepreneurs = [];

  Future<void> createGroup() async {
    final mentorId = FirebaseAuth.instance.currentUser!.uid;
    await FirebaseFirestore.instance.collection('mentor_groups').add({
      'mentor_id': mentorId,
      'entrepreneur_ids': selectedEntrepreneurs,
      'created_at': Timestamp.now(),
    });
    ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Group created')));
    setState(() => selectedEntrepreneurs.clear());
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentor Group Management')),
      body: StreamBuilder<QuerySnapshot>(
        stream: FirebaseFirestore.instance.collection('users').where('role', isEqualTo: 'entrepreneur').snapshots(),
        builder: (context, snapshot) {
          if (!snapshot.hasData) return const Center(child: CircularProgressIndicator());
          final entrepreneurs = snapshot.data!.docs;
          return ListView(
            children: entrepreneurs.map((doc) {
              final data = doc.data() as Map<String, dynamic>;
              final uid = doc.id;
              return CheckboxListTile(
                title: Text(data['email']),
                value: selectedEntrepreneurs.contains(uid),
                onChanged: (checked) {
                  setState(() {
                    if (checked == true) {
                      selectedEntrepreneurs.add(uid);
                    } else {
                      selectedEntrepreneurs.remove(uid);
                    }
                  });
                },
              );
            }).toList(),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: createGroup,
        label: const Text('Create Group'),
        icon: const Icon(Icons.group_add),
      ),
    );
  }
}