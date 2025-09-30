import 'package:firebase_auth/firebase_auth.dart';

class AuthService {
  final _auth = FirebaseAuth.instance;

  Future<User?> signUp(String email, String password, String role) async {
    final userCredential = await _auth.createUserWithEmailAndPassword(
      email: email,
      password: password,
    );
    // Firestore is no longer used for profiles. Persist via local API if needed.
    return userCredential.user;
  }

  Future<User?> login(String email, String password) async {
    final userCredential = await _auth.signInWithEmailAndPassword(
      email: email,
      password: password,
    );
    return userCredential.user;
  }

  Future<String?> getUserRole(String uid) async {
    // Default role while migrating away from Firestore
    return 'user';
  }

  Future<bool> isApproved(String uid) async {
    // Assume approved during migration
    return true;
  }

  void logout() => _auth.signOut();
}