class UserModel {
  final String uid;
  final String email;
  final String role;
  final bool approved;

  UserModel({
    required this.uid,
    required this.email,
    required this.role,
    required this.approved,
  });

  factory UserModel.fromMap(String uid, Map<String, dynamic> data) {
    return UserModel(
      uid: uid,
      email: data['email'] ?? '',
      role: data['role'] ?? 'entrepreneur',
      approved: data['approved'] ?? false,
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'email': email,
      'role': role,
      'approved': approved,
    };
  }
}