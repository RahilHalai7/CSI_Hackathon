import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class MentorDashboard extends StatefulWidget {
  const MentorDashboard({super.key});

  @override
  State<MentorDashboard> createState() => _MentorDashboardState();
}

class _MentorDashboardState extends State<MentorDashboard> {
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const DashboardTab(),
    const StudentsTab(),
    const MentorshipTab(),
    const ResourcesTab(),
    const SettingsTab(),
  ];

  Future<void> _signOut() async {
    try {
      await FirebaseAuth.instance.signOut();
      if (mounted) {
        Navigator.pushNamedAndRemoveUntil(context, '/login', (route) => false);
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Error signing out. Please try again.'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      body: Row(
        children: [
          // Sidebar
          Container(
            width: 280,
            color: Colors.white,
            child: Column(
              children: [
                // Header
                Container(
                  padding: const EdgeInsets.all(24),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'StriveSpark',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Colors.grey[800],
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Mentor',
                        style: TextStyle(
                          fontSize: 14,
                          color: Colors.grey[600],
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 1),

                // Navigation Items
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      _buildNavItem(0, Icons.dashboard, 'Dashboard'),
                      _buildNavItem(1, Icons.people, 'Students'),
                      _buildNavItem(2, Icons.psychology, 'Mentorship'),
                      _buildNavItem(3, Icons.folder, 'Resources'),
                    ],
                  ),
                ),

                // Bottom section
                Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    children: [
                      _buildNavItem(4, Icons.settings, 'Settings'),
                      const SizedBox(height: 16),
                      ListTile(
                        leading: const Icon(Icons.logout, color: Colors.red),
                        title: const Text('Sign Out', style: TextStyle(color: Colors.red)),
                        onTap: _signOut,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),

          // Main Content
          Expanded(
            child: _pages[_selectedIndex],
          ),
        ],
      ),
    );
  }

  Widget _buildNavItem(int index, IconData icon, String title) {
    final isSelected = _selectedIndex == index;
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      child: ListTile(
        leading: Icon(
          icon,
          color: isSelected ? const Color(0xFF3B82F6) : Colors.grey[600],
        ),
        title: Text(
          title,
          style: TextStyle(
            color: isSelected ? const Color(0xFF3B82F6) : Colors.grey[800],
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
          ),
        ),
        selected: isSelected,
        selectedTileColor: const Color(0xFF3B82F6).withOpacity(0.1),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        onTap: () {
          setState(() {
            _selectedIndex = index;
          });
        },
      ),
    );
  }
}

class DashboardTab extends StatelessWidget {
  const DashboardTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Text(
            'Dashboard',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Review and manage student submissions',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),

          // Content
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                children: [
                  _buildSubmissionSection('New Submissions', _getNewSubmissions()),
                  const SizedBox(height: 32),
                  _buildSubmissionSection('In Progress', _getInProgressSubmissions()),
                  const SizedBox(height: 32),
                  _buildSubmissionSection('Completed', _getCompletedSubmissions()),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSubmissionSection(String title, List<Map<String, dynamic>> submissions) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.bold,
            color: Colors.black87,
          ),
        ),
        const SizedBox(height: 16),
        Container(
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: Colors.grey.shade200),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.grey.shade50,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(12),
                    topRight: Radius.circular(12),
                  ),
                ),
                child: const Row(
                  children: [
                    Expanded(flex: 2, child: Text('Student', style: TextStyle(fontWeight: FontWeight.w600))),
                    Expanded(flex: 3, child: Text('Idea', style: TextStyle(fontWeight: FontWeight.w600))),
                    Expanded(flex: 2, child: Text('Industry', style: TextStyle(fontWeight: FontWeight.w600))),
                    Expanded(flex: 1, child: Text('Priority', style: TextStyle(fontWeight: FontWeight.w600))),
                    Expanded(flex: 1, child: Text('Actions', style: TextStyle(fontWeight: FontWeight.w600))),
                  ],
                ),
              ),
              // Data rows
              ...submissions.map((submission) => _buildSubmissionRow(submission)),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildSubmissionRow(Map<String, dynamic> submission) {
    Color priorityColor = Colors.green;
    if (submission['priority'] == 'High') priorityColor = Colors.red;
    if (submission['priority'] == 'Medium') priorityColor = Colors.orange;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        border: Border(bottom: BorderSide(color: Colors.grey.shade200)),
      ),
      child: Row(
        children: [
          Expanded(
            flex: 2,
            child: Text(
              submission['student'],
              style: const TextStyle(fontWeight: FontWeight.w500),
            ),
          ),
          Expanded(
            flex: 3,
            child: Text(
              submission['idea'],
              style: TextStyle(color: Colors.grey[700]),
            ),
          ),
          Expanded(
            flex: 2,
            child: Text(
              submission['industry'],
              style: TextStyle(color: Colors.grey[700]),
            ),
          ),
          Expanded(
            flex: 1,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: priorityColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                submission['priority'],
                style: TextStyle(
                  color: priorityColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ),
          Expanded(
            flex: 1,
            child: submission['action'] != null
                ? ElevatedButton(
              onPressed: () {},
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF3B82F6),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
              ),
              child: Text(
                submission['action'],
                style: const TextStyle(fontSize: 12, color: Colors.white),
              ),
            )
                : TextButton(
              onPressed: () {},
              child: Text(
                submission['link'] ?? 'View',
                style: const TextStyle(fontSize: 12),
              ),
            ),
          ),
        ],
      ),
    );
  }

  List<Map<String, dynamic>> _getNewSubmissions() {
    return [
      {
        'student': 'Aarav Sharma',
        'idea': 'Eco-friendly packaging solutions for small businesses',
        'industry': 'Sustainability',
        'priority': 'High',
        'action': 'Review',
      },
      {
        'student': 'Priya Patel',
        'idea': 'AI-powered personalized learning platform',
        'industry': 'Education',
        'priority': 'Medium',
        'action': 'Review',
      },
      {
        'student': 'Vikram Singh',
        'idea': 'Mobile app for local farmers to sell produce directly',
        'industry': 'Agriculture',
        'priority': 'Low',
        'action': 'Review',
      },
    ];
  }

  List<Map<String, dynamic>> _getInProgressSubmissions() {
    return [
      {
        'student': 'Anika Verma',
        'idea': 'Subscription box for artisanal Indian crafts',
        'industry': 'E-commerce',
        'priority': 'High',
        'link': 'Provide Feedback',
      },
      {
        'student': 'Rohan Kapoor',
        'idea': 'Virtual reality tours of historical sites in India',
        'industry': 'Tourism',
        'priority': 'Medium',
        'link': 'Provide Feedback',
      },
    ];
  }

  List<Map<String, dynamic>> _getCompletedSubmissions() {
    return [
      {
        'student': 'Ishaan Malhotra',
        'idea': 'Online platform for freelance writers in regional languages',
        'industry': 'Content Creation',
        'priority': 'High',
        'link': 'View Feedback',
      },
    ];
  }
}

class StudentsTab extends StatelessWidget {
  const StudentsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Students',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Manage your mentees and their progress',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          const Center(
            child: Text(
              'Students management features coming soon!',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}

class MentorshipTab extends StatelessWidget {
  const MentorshipTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Mentorship',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Track mentorship sessions and outcomes',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          const Center(
            child: Text(
              'Mentorship tracking features coming soon!',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}

class ResourcesTab extends StatelessWidget {
  const ResourcesTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Resources',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Educational materials and guides',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          const Center(
            child: Text(
              'Resources library coming soon!',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}

class SettingsTab extends StatelessWidget {
  const SettingsTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Settings',
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.bold,
              color: Colors.grey[800],
            ),
          ),
          const SizedBox(height: 8),
          Text(
            'Configure your mentor dashboard',
            style: TextStyle(
              color: Colors.grey[600],
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 32),
          const Center(
            child: Text(
              'Settings panel coming soon!',
              style: TextStyle(fontSize: 16, color: Colors.grey),
            ),
          ),
        ],
      ),
    );
  }
}