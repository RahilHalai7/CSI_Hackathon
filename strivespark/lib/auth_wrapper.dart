import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:strivespark/screens/admin/dashboard.dart';
import 'screens/common/login.dart';
import 'screens/entreprenuer/dashboard.dart';
import 'screens/mentor/dashboard.dart';
import 'screens/entreprenuer/dashboard.dart';

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

        // User is authenticated. Default to EntrepreneurDashboard.
        // Later, integrate role-based routing via local API or claims.
        return const EntrepreneurDashboard();
      },
    );
  }
}