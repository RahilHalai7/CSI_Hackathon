import 'package:flutter/material.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class AssignmentScreen extends StatefulWidget {
  const AssignmentScreen({super.key});

  @override
  State<AssignmentScreen> createState() => _AssignmentScreenState();
}

class _AssignmentScreenState extends State<AssignmentScreen> {
  String? selectedMentor;
  List<String> selectedEntrepreneurs = [];

  Future<void> assignGroup() async {
    if (selectedMentor != null && selectedEntrepreneurs.isNotEmpty) {
      await FirebaseFirestore.instance.collection('mentor_groups').add({
        'mentor_id': selectedMentor,
        'entrepreneur_ids': selectedEntrepreneurs,
        'created_at': Timestamp.now(),
      });
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Group assigned')));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Assign Mentors')),
      body: Column(
        children: [
          const SizedBox(height: 16),
          const Text('Select Mentor'),
          StreamBuilder<QuerySnapshot>(
            stream: FirebaseFirestore.instance.collection('users').where('role', isEqualTo: 'mentor').where('approved', isEqualTo: true).snapshots(),
            builder: (context, snapshot) {
              if (!snapshot.hasData) return const CircularProgressIndicator();
              final mentors = snapshot.data!.docs;
              return DropdownButton<String>(
                value: selectedMentor,
                hint: const Text('Choose Mentor'),
                items: mentors.map((doc) {
                  final data = doc.data() as Map<String, dynamic>;
                  return DropdownMenuItem(value: doc.id, child: Text(data['email']));
                }).toList(),
                onChanged: (value) => setState(() => selectedMentor = value),
              );
            },
          ),
          const Divider(),
          const Text('Select Entrepreneurs'),
          Expanded(
            child: StreamBuilder<QuerySnapshot>(
              stream: FirebaseFirestore.instance.collection('users').where('role', isEqualTo: 'entrepreneur').snapshots(),
              builder: (context, snapshot) {
                if (!snapshot.hasData) return const CircularProgressIndicator();
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
          ),
          ElevatedButton(onPressed: assignGroup, child: const Text('Assign Group')),
        ],
      ),
    );
  }
}