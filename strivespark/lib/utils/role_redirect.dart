import 'package:flutter/material.dart';
import '../screens/admin/dashboard.dart';
import '../screens/mentor/dashboard.dart';
import '../screens/entreprenuer/dashboard.dart';

class RoleRedirect {
  static Widget getDashboard(String role) {
    switch (role) {
      case 'admin':
        return const AdminDashboard();
      case 'mentor':
        return const MentorDashboard();
      case 'entrepreneur':
        return const EntrepreneurDashboard();
      default:
        return const Center(child: Text('Unknown role'));
    }
  }
}