import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'login.dart';
import 'home.dart';
import 'mentor_dashboard.dart';
import 'strivers_dashboard.dart';

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<User?>(
      stream: FirebaseAuth.instance.authStateChanges(),
      builder: (context, snapshot) {
        // Show loading while checking authentication state
        if (snapshot.connectionState == ConnectionState.waiting) {
          return const Scaffold(
            body: Center(
              child: CircularProgressIndicator(),
            ),
          );
        }

        // If user is not authenticated, show login screen
        if (!snapshot.hasData || snapshot.data == null) {
          return const LoginScreen();
        }

        // User is authenticated, now check their role
        final user = snapshot.data!;

        return StreamBuilder<DocumentSnapshot>(
          // Use StreamBuilder instead of FutureBuilder for real-time updates
          stream: FirebaseFirestore.instance
              .collection('users')
              .doc(user.uid)
              .snapshots(),
          builder: (context, userSnapshot) {
            // Show loading while fetching user data
            if (userSnapshot.connectionState == ConnectionState.waiting) {
              return const Scaffold(
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('Loading user profile...'),
                    ],
                  ),
                ),
              );
            }

            // Handle errors or missing user document
            if (userSnapshot.hasError) {
              print('Error fetching user data: ${userSnapshot.error}');
              return const Scaffold(
                body: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error, size: 64, color: Colors.red),
                      SizedBox(height: 16),
                      Text('Error loading user data'),
                      SizedBox(height: 8),
                      Text('Please try again later'),
                    ],
                  ),
                ),
              );
            }

            // If user document doesn't exist, create it or show default home
            if (!userSnapshot.hasData || !userSnapshot.data!.exists) {
              print('User document does not exist for UID: ${user.uid}');
              // Optionally create the user document here
              _createUserDocument(user);
              return const HomeScreen(); // Default to home screen
            }

            // Extract user data and role
            final userData = userSnapshot.data!.data() as Map<String, dynamic>?;
            if (userData == null) {
              print('User data is null for UID: ${user.uid}');
              return const HomeScreen();
            }

            final userRole = userData['role'] as String?;
            print('User UID: ${user.uid}, Role: $userRole'); // Debug print

            // Route based on role
            switch (userRole?.toLowerCase()) {
              case 'mentor':
                print('Routing to MentorDashboard');
                return const MentorDashboard();
              case 'strivers':
                print('Routing to StriversDashboard');
                return const StriversDashboard();
              case 'user':
              default:
                print('Routing to HomeScreen (role: $userRole)');
                return const HomeScreen();
            }
          },
        );
      },
    );
  }

  // Helper method to create user document if it doesn't exist
  Future<void> _createUserDocument(User user) async {
    try {
      await FirebaseFirestore.instance
          .collection('users')
          .doc(user.uid)
          .set({
        'email': user.email,
        'role': 'user', // Default role
        'displayName': user.displayName ?? '',
        'photoURL': user.photoURL ?? '',
        'createdAt': FieldValue.serverTimestamp(),
        'lastLogin': FieldValue.serverTimestamp(),
      }, SetOptions(merge: true)); // Use merge to avoid overwriting existing data

      print('Created user document for UID: ${user.uid}');
    } catch (e) {
      print('Error creating user document: $e');
    }
  }
}