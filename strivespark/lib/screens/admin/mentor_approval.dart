import 'package:flutter/material.dart';
import 'dart:convert';
import 'package:http/http.dart' as http;

class MentorApprovalScreen extends StatefulWidget {
  const MentorApprovalScreen({super.key});

  @override
  State<MentorApprovalScreen> createState() => _MentorApprovalScreenState();
}

class _MentorApprovalScreenState extends State<MentorApprovalScreen> {
  List<Map<String, dynamic>> pendingMentors = [];
  bool isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadPendingMentors();
  }

  Future<void> _loadPendingMentors() async {
    try {
      final response = await http.get(
        Uri.parse('http://127.0.0.1:5000/api/admin/pending-mentors'),
        headers: {'Authorization': 'Bearer 1'}, // Mock token for admin
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        setState(() {
          pendingMentors = List<Map<String, dynamic>>.from(data['mentors']);
          isLoading = false;
        });
      } else {
        setState(() {
          isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        isLoading = false;
      });
    }
  }

  Future<void> approveMentor(int mentorId) async {
    try {
      final response = await http.post(
        Uri.parse('http://127.0.0.1:5000/api/admin/approve-mentor/$mentorId'),
        headers: {'Authorization': 'Bearer 1'}, // Mock token for admin
      );
      
      if (response.statusCode == 200) {
        _loadPendingMentors(); // Refresh the list
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mentor approved successfully')),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Failed to approve mentor')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Mentor Approval')),
      body: isLoading
          ? const Center(child: CircularProgressIndicator())
          : pendingMentors.isEmpty
              ? const Center(child: Text('No pending mentor approvals'))
              : ListView.builder(
                  itemCount: pendingMentors.length,
                  itemBuilder: (context, index) {
                    final mentor = pendingMentors[index];
                    return ListTile(
                      title: Text(mentor['email'] ?? 'Unknown'),
                      subtitle: Text('Role: ${mentor['role'] ?? 'mentor'}'),
                      trailing: ElevatedButton(
                        onPressed: () => approveMentor(mentor['id']),
                        child: const Text('Approve'),
                      ),
                    );
                  },
                ),
    );
  }
}