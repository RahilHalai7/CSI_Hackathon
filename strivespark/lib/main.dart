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

// Route constants
class AppRoutes {
  // Auth routes
  static const home = '/';
  static const login = '/login';
  static const signup = '/signup';

  // Entrepreneur routes
  static const entrepreneurHome = '/entrepreneurHome';
  static const submitIdea = '/submitIdea';
  static const submissionHistory = '/submissionHistory';
  static const feedbackView = '/feedbackView';

  // Mentor routes
  static const mentorHome = '/mentorHome';
  static const reviewIdeas = '/reviewIdeas';
  static const mentorFeedback = '/mentorFeedback';
  static const groupManagement = '/groupManagement';

  // Admin routes
  static const adminHome = '/adminHome';
  static const approveMentors = '/approveMentors';
  static const assignMentors = '/assignMentors';
  static const trackProgress = '/trackProgress';
}

// Route arguments classes for type safety
class FeedbackViewArguments {
  final Map<String, dynamic> data;

  FeedbackViewArguments({required this.data});
}

class FeedbackFormArguments {
  final String ideaId;
  final Map<String, dynamic> ideaData;

  FeedbackFormArguments({required this.ideaId, required this.ideaData});
}

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
        appBarTheme: const AppBarTheme(
          centerTitle: true,
          elevation: 0,
        ),
      ),
      initialRoute: AppRoutes.home,
      onGenerateRoute: _generateRoute,
      onUnknownRoute: (settings) => MaterialPageRoute(
        builder: (context) => const NotFoundScreen(),
      ),
    );
  }

  static Route<dynamic> _generateRoute(RouteSettings settings) {
    switch (settings.name) {
    // Auth routes
      case AppRoutes.home:
        return MaterialPageRoute(builder: (_) => const AuthWrapper());

      case AppRoutes.login:
        return MaterialPageRoute(builder: (_) => const LoginScreen());

      case AppRoutes.signup:
        return MaterialPageRoute(builder: (_) => const SignupScreen());

    // Entrepreneur routes
      case AppRoutes.entrepreneurHome:
        return MaterialPageRoute(builder: (_) => const EntrepreneurDashboard());

      case AppRoutes.submitIdea:
        return MaterialPageRoute(builder: (_) => const IdeaFormScreen());

      case AppRoutes.submissionHistory:
        return MaterialPageRoute(builder: (_) => const SubmissionHistoryScreen());

      case AppRoutes.feedbackView:
        final args = settings.arguments as FeedbackViewArguments?;
        if (args == null) {
          return MaterialPageRoute(
            builder: (_) => const ErrorScreen(
              message: 'Missing required data for feedback view',
            ),
          );
        }
        return MaterialPageRoute(
          builder: (_) => FeedbackViewScreen(data: args.data),
        );

    // Mentor routes
      case AppRoutes.mentorHome:
        return MaterialPageRoute(builder: (_) => const MentorDashboard());

      case AppRoutes.reviewIdeas:
        return MaterialPageRoute(builder: (_) => const IdeaReviewScreen());

      case AppRoutes.mentorFeedback:
        final args = settings.arguments as FeedbackFormArguments?;
        if (args == null) {
          return MaterialPageRoute(
            builder: (_) => const ErrorScreen(
              message: 'Missing required data for feedback form',
            ),
          );
        }
        return MaterialPageRoute(
          builder: (_) => FeedbackFormScreen(
            ideaId: args.ideaId,
            ideaData: args.ideaData,
          ),
        );

      case AppRoutes.groupManagement:
        return MaterialPageRoute(builder: (_) => const GroupManagementScreen());

    // Admin routes
      case AppRoutes.adminHome:
        return MaterialPageRoute(builder: (_) => const AdminDashboard());

      case AppRoutes.approveMentors:
        return MaterialPageRoute(builder: (_) => const MentorApprovalScreen());

      case AppRoutes.assignMentors:
        return MaterialPageRoute(builder: (_) => const AssignmentScreen());

      case AppRoutes.trackProgress:
        return MaterialPageRoute(builder: (_) => const ProgressTrackingScreen());

      default:
        return MaterialPageRoute(builder: (_) => const NotFoundScreen());
    }
  }
}

// Navigation helper class
class NavigationHelper {
  // Entrepreneur navigation
  static void goToFeedbackView(BuildContext context, Map<String, dynamic> data) {
    Navigator.pushNamed(
      context,
      AppRoutes.feedbackView,
      arguments: FeedbackViewArguments(data: data),
    );
  }

  // Mentor navigation
  static void goToFeedbackForm(
      BuildContext context,
      String ideaId,
      Map<String, dynamic> ideaData,
      ) {
    Navigator.pushNamed(
      context,
      AppRoutes.mentorFeedback,
      arguments: FeedbackFormArguments(ideaId: ideaId, ideaData: ideaData),
    );
  }

  // Role-based dashboard navigation
  static void goToRoleDashboard(BuildContext context, String userRole) {
    String route;
    switch (userRole.toLowerCase()) {
      case 'entrepreneur':
        route = AppRoutes.entrepreneurHome;
        break;
      case 'mentor':
        route = AppRoutes.mentorHome;
        break;
      case 'admin':
        route = AppRoutes.adminHome;
        break;
      default:
        route = AppRoutes.login;
    }

    Navigator.pushNamedAndRemoveUntil(
      context,
      route,
          (route) => false,
    );
  }

  // Auth navigation
  static void logout(BuildContext context) {
    Navigator.pushNamedAndRemoveUntil(
      context,
      AppRoutes.login,
          (route) => false,
    );
  }
}

// Error screens
class NotFoundScreen extends StatelessWidget {
  const NotFoundScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Page Not Found'),
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Colors.grey,
            ),
            SizedBox(height: 16),
            Text(
              'Page Not Found',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 8),
            Text(
              'The page you are looking for does not exist.',
              style: TextStyle(color: Colors.grey),
            ),
          ],
        ),
      ),
    );
  }
}

class ErrorScreen extends StatelessWidget {
  final String message;

  const ErrorScreen({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Error'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.warning_amber_outlined,
              size: 64,
              color: Colors.orange,
            ),
            const SizedBox(height: 16),
            const Text(
              'Something went wrong',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 32),
              child: Text(
                message,
                style: const TextStyle(color: Colors.grey),
                textAlign: TextAlign.center,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('Go Back'),
            ),
          ],
        ),
      ),
    );
  }
}