import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';

class StriversDashboard extends StatefulWidget {
  const StriversDashboard({super.key});

  @override
  State<StriversDashboard> createState() => _StriversDashboardState();
}

class _StriversDashboardState extends State<StriversDashboard> {
  final user = FirebaseAuth.instance.currentUser;
  int _selectedIndex = 0;

  final List<Widget> _pages = [
    const StriversDashboardPage(),
    const StriversProfilePage(),
    const StriversGoalsPage(),
    const StriversProgressPage(),
  ];

  void _onItemTapped(int index) {
    setState(() {
      _selectedIndex = index;
    });
  }

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
      appBar: AppBar(
        title: const Text('StriveSpark - Strivers'),
        backgroundColor: const Color(0xFF10B981), // Emerald color for strivers
        foregroundColor: Colors.white,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            onPressed: _signOut,
            tooltip: 'Sign Out',
          ),
        ],
      ),
      body: _pages[_selectedIndex],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: _onItemTapped,
        type: BottomNavigationBarType.fixed,
        selectedItemColor: const Color(0xFF10B981),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.dashboard),
            label: 'Dashboard',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.person),
            label: 'Profile',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.flag),
            label: 'Goals',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.analytics),
            label: 'Progress',
          ),
        ],
      ),
    );
  }
}


class StriversDashboardPage extends StatelessWidget {
  const StriversDashboardPage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Welcome Card
          Card(
            elevation: 4,
            child: Container(
              width: double.infinity,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF10B981), // Emerald
                    const Color(0xFF10B981).withOpacity(0.7),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
              ),
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Welcome, Striver!',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    user?.displayName ?? 'Ambitious Striver',
                    style: Theme.of(context).textTheme.titleLarge?.copyWith(
                      color: Colors.white70,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      const Icon(Icons.rocket_launch, color: Colors.white, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        'Ready to achieve your dreams?',
                        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                          color: Colors.white70,
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          // Stats Cards
          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Active Goals',
                  '5',
                  Icons.flag,
                  const Color(0xFF3B82F6),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildStatCard(
                  'Completed',
                  '12',
                  Icons.check_circle,
                  const Color(0xFF10B981),
                ),
              ),
            ],
          ),

          const SizedBox(height: 16),

          Row(
            children: [
              Expanded(
                child: _buildStatCard(
                  'Success Rate',
                  '85%',
                  Icons.trending_up,
                  const Color(0xFF8B5CF6),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildStatCard(
                  'Streak Days',
                  '28',
                  Icons.local_fire_department,
                  const Color(0xFFF59E0B),
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          // Current Goals
          Text(
            'Current Goals',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),

          Card(
            child: ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: 3,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final goals = [
                  {'title': 'Complete Flutter Course', 'progress': 0.7, 'category': 'Learning'},
                  {'title': 'Read 2 Books This Month', 'progress': 0.5, 'category': 'Personal'},
                  {'title': 'Build Portfolio Website', 'progress': 0.3, 'category': 'Career'},
                ];

                final goal = goals[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: const Color(0xFF10B981).withOpacity(0.1),
                    child: const Icon(
                      Icons.flag,
                      color: Color(0xFF10B981),
                    ),
                  ),
                  title: Text(goal['title'] as String),
                  subtitle: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(goal['category'] as String),
                      const SizedBox(height: 4),
                      LinearProgressIndicator(
                        value: goal['progress'] as double,
                        backgroundColor: Colors.grey[300],
                        valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF10B981)),
                      ),
                    ],
                  ),
                  trailing: Text(
                    '${((goal['progress'] as double) * 100).toInt()}%',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                );
              },
            ),
          ),

          const SizedBox(height: 24),

          // Recent Achievements
          Text(
            'Recent Achievements',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),

          Card(
            child: ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: 3,
              separatorBuilder: (context, index) => const Divider(height: 1),
              itemBuilder: (context, index) {
                final achievements = [
                  {'title': 'Completed Daily Workout - Week 4', 'time': '2 days ago', 'icon': Icons.fitness_center},
                  {'title': 'Finished JavaScript Fundamentals', 'time': '1 week ago', 'icon': Icons.code},
                  {'title': 'Read "Atomic Habits"', 'time': '2 weeks ago', 'icon': Icons.menu_book},
                ];

                final achievement = achievements[index];
                return ListTile(
                  leading: CircleAvatar(
                    backgroundColor: const Color(0xFFF59E0B).withOpacity(0.1),
                    child: Icon(
                      achievement['icon'] as IconData,
                      color: const Color(0xFFF59E0B),
                    ),
                  ),
                  title: Text(achievement['title'] as String),
                  subtitle: Text(achievement['time'] as String),
                  trailing: const Icon(Icons.star, color: Color(0xFFF59E0B)),
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Container(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Icon(icon, color: color, size: 24),
                Text(
                  value,
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: color,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              title,
              style: const TextStyle(
                fontSize: 14,
                color: Colors.grey,
                fontWeight: FontWeight.w500,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class StriversProfilePage extends StatelessWidget {
  const StriversProfilePage({super.key});

  @override
  Widget build(BuildContext context) {
    final user = FirebaseAuth.instance.currentUser;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        children: [
          const SizedBox(height: 20),
          CircleAvatar(
            radius: 60,
            backgroundColor: const Color(0xFF10B981).withOpacity(0.1),
            child: user?.photoURL != null
                ? ClipRRect(
              borderRadius: BorderRadius.circular(60),
              child: Image.network(
                user!.photoURL!,
                width: 120,
                height: 120,
                fit: BoxFit.cover,
              ),
            )
                : const Icon(
              Icons.person,
              size: 60,
              color: Color(0xFF10B981),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            user?.displayName ?? 'Ambitious Striver',
            style: Theme.of(context).textTheme.headlineSmall?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            user?.email ?? 'striver@example.com',
            style: Theme.of(context).textTheme.bodyLarge?.copyWith(
              color: Colors.grey[600],
            ),
          ),
          const SizedBox(height: 32),
          Card(
            child: Column(
              children: [
                ListTile(
                  leading: const Icon(Icons.edit, color: Color(0xFF10B981)),
                  title: const Text('Edit Profile'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Edit profile coming soon!')),
                    );
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.psychology, color: Color(0xFF10B981)),
                  title: const Text('My Achievements'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Achievements coming soon!')),
                    );
                  },
                ),
                const Divider(height: 1),
                ListTile(
                  leading: const Icon(Icons.insights, color: Color(0xFF10B981)),
                  title: const Text('Performance Insights'),
                  trailing: const Icon(Icons.chevron_right),
                  onTap: () {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Insights coming soon!')),
                    );
                  },
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class StriversGoalsPage extends StatelessWidget {
  const StriversGoalsPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'My Goals',
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              FloatingActionButton(
                onPressed: () {
                  ScaffoldMessenger.of(context).showSnackBar(
                    const SnackBar(content: Text('Add goal coming soon!')),
                  );
                },
                backgroundColor: const Color(0xFF10B981),
                mini: true,
                child: const Icon(Icons.add, color: Colors.white),
              ),
            ],
          ),
          const SizedBox(height: 24),
          Expanded(
            child: ListView.builder(
              itemCount: 5,
              itemBuilder: (context, index) {
                final goals = [
                  {'title': 'Complete Flutter Course', 'progress': 0.7, 'category': 'Learning', 'deadline': 'Dec 31, 2024'},
                  {'title': 'Read 2 Books This Month', 'progress': 0.5, 'category': 'Personal', 'deadline': 'Nov 30, 2024'},
                  {'title': 'Build Portfolio Website', 'progress': 0.3, 'category': 'Career', 'deadline': 'Jan 15, 2025'},
                  {'title': 'Learn Spanish Basics', 'progress': 0.2, 'category': 'Language', 'deadline': 'Mar 1, 2025'},
                  {'title': 'Run 5K Marathon', 'progress': 0.8, 'category': 'Fitness', 'deadline': 'Dec 15, 2024'},
                ];

                final goal = goals[index];
                return Card(
                  margin: const EdgeInsets.only(bottom: 16),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            Expanded(
                              child: Text(
                                goal['title'] as String,
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Text(
                                goal['category'] as String,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFF10B981),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Due: ${goal['deadline']}',
                          style: TextStyle(
                            color: Colors.grey[600],
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(height: 12),
                        Row(
                          children: [
                            Expanded(
                              child: LinearProgressIndicator(
                                value: goal['progress'] as double,
                                backgroundColor: Colors.grey[300],
                                valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF10B981)),
                              ),
                            ),
                            const SizedBox(width: 12),
                            Text(
                              '${((goal['progress'] as double) * 100).toInt()}%',
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                color: Color(0xFF10B981),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}

class StriversProgressPage extends StatelessWidget {
  const StriversProgressPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Progress Analytics',
            style: Theme
                .of(context)
                .textTheme
                .headlineSmall
                ?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 24),

          // Weekly Progress Chart Placeholder
          Card(
            child: Container(
              height: 200,
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'Weekly Progress',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Expanded(
                    child: Container(
                      decoration: BoxDecoration(
                        color: Colors.grey[100],
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Center(
                        child: Text(
                          'Chart visualization coming soon',
                          style: TextStyle(color: Colors.grey),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),

          const SizedBox(height: 16),

          // Performance Metrics
          Row(
            children: [
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        const Icon(
                          Icons.trending_up,
                          size: 32,
                          color: Color(0xFF10B981),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Productivity',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          '92%',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF10B981),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      children: [
                        const Icon(
                          Icons.timer,
                          size: 32,
                          color: Color(0xFF3B82F6),
                        ),
                        const SizedBox(height: 8),
                        const Text(
                          'Focus Time',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey,
                          ),
                        ),
                        const SizedBox(height: 4),
                        const Text(
                          '6.2h',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF3B82F6),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ],
          ),

          const SizedBox(height: 24),

          const Text(
            'Recent Activity',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
          const SizedBox(height: 16),

          Expanded(
            child: Card(
              child: ListView.separated(
                padding: const EdgeInsets.all(16),
                itemCount: 4,
                separatorBuilder: (context, index) => const Divider(),
                itemBuilder: (context, index) {
                  final activities = [
                    {
                      'action': 'Completed goal milestone',
                      'time': '2 hours ago',
                      'icon': Icons.flag
                    },
                    {
                      'action': 'Added new learning goal',
                      'time': '1 day ago',
                      'icon': Icons.add_circle
                    },
                    {
                      'action': 'Updated progress tracking',
                      'time': '2 days ago',
                      'icon': Icons.update
                    },
                    {
                      'action': 'Achieved weekly target',
                      'time': '3 days ago',
                      'icon': Icons.celebration
                    },
                  ];

                  final activity = activities[index];
                  return ListTile(
                    leading: CircleAvatar(
                      backgroundColor: const Color(0xFF10B981).withOpacity(0.1),
                      child: Icon(
                        activity['icon'] as IconData,
                        color: const Color(0xFF10B981),
                        size: 20,
                      ),
                    ),
                    title: Text(activity['action'] as String),
                    subtitle: Text(activity['time'] as String),
                    contentPadding: EdgeInsets.zero,
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}