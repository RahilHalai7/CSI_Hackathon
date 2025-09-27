import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'firebase_options.dart';

// Common Screens
import 'auth_wrapper.dart';
import 'screens/common/login.dart';
import 'screens/common/signup.dart';

// Entrepreneur Screens
import 'screens/entreprenuer/dashboard.dart';
import 'screens/entreprenuer/feedback_view.dart';
import 'screens/entreprenuer/idea_form.dart';
import 'screens/entreprenuer/submission_history.dart';

// Mentor Screens
import 'screens/mentor/dashboard.dart';
import 'screens/mentor/idea_review.dart';
import 'screens/mentor/feedback_form.dart';
import 'screens/mentor/group_management.dart';

// Admin Screens
import 'screens/admin/dashboard.dart';
import 'screens/admin/mentor_approval.dart';
import 'screens/admin/assignment.dart';
import 'screens/admin/progress_tracking.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await Firebase.initializeApp(options: DefaultFirebaseOptions.currentPlatform);
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      debugShowCheckedModeBanner: false,
      title: 'StriveSpark',
      theme: ThemeData(
        primarySwatch: Colors.indigo,
        visualDensity: VisualDensity.adaptivePlatformDensity,
        useMaterial3: true,
      ),
      initialRoute: '/',
      routes: {
        // Auth
        '/': (context) => const AuthWrapper(),
        '/login': (context) => const LoginScreen(),
        '/signup': (context) => const SignupScreen(),

        // Entrepreneur
        '/entrepreneurHome': (context) => const EntrepreneurDashboard(),
        '/submitIdea': (context) => const IdeaFormScreen(),
        '/submissionHistory': (context) => const SubmissionHistoryScreen(),
        '/feedbackView': (context) => const FeedbackViewScreen(data: {}), // Pass data dynamically

        // Mentor
        '/mentorHome': (context) => const MentorDashboard(),
        '/reviewIdeas': (context) => const IdeaReviewScreen(),
        '/mentorFeedback': (context) => const FeedbackFormScreen(ideaId: '', ideaData: {}), // Pass dynamically
        '/groupManagement': (context) => const GroupManagementScreen(),

        // Admin
        '/adminHome': (context) => const AdminDashboard(),
        '/approveMentors': (context) => const MentorApprovalScreen(),
        '/assignMentors': (context) => const AssignmentScreen(),
        '/trackProgress': (context) => const ProgressTrackingScreen(),
      },
    );
  }
}