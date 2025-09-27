import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';

class AuthService {
  final _auth = FirebaseAuth.instance;
  final _firestore = FirebaseFirestore.instance;

  Future<User?> signUp(String email, String password, String role) async {
    final userCredential = await _auth.createUserWithEmailAndPassword(email: email, password: password);
    await _firestore.collection('users').doc(userCredential.user!.uid).set({
      'email': email,
      'role': role,
      'approved': role == 'entrepreneur' ? true : false,
    });
    return userCredential.user;
  }

  Future<User?> login(String email, String password) async {
    final userCredential = await _auth.signInWithEmailAndPassword(email: email, password: password);
    return userCredential.user;
  }

  Future<String?> getUserRole(String uid) async {
    final doc = await _firestore.collection('users').doc(uid).get();
    return doc.data()?['role'];
  }

  Future<bool> isApproved(String uid) async {
    final doc = await _firestore.collection('users').doc(uid).get();
    return doc.data()?['approved'] ?? false;
  }

  void logout() => _auth.signOut();
}