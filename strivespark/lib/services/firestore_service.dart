import 'package:cloud_firestore/cloud_firestore.dart';

class FirestoreService {
  final _db = FirebaseFirestore.instance;

  Future<void> submitBusinessIdea({
    required String uid,
    required String title,
    required String description,
    required String fileUrl,
    required String language,
  }) async {
    await _db.collection('business_ideas').add({
      'entrepreneur_id': uid,
      'title': title,
      'description': description,
      'file_url': fileUrl,
      'language': language,
      'status': 'Submitted',
      'created_at': Timestamp.now(),
    });
  }

  Future<List<Map<String, dynamic>>> getIdeasByUser(String uid) async {
    final snapshot = await _db.collection('business_ideas').where('entrepreneur_id', isEqualTo: uid).get();
    return snapshot.docs.map((doc) => doc.data()).toList();
  }

  Future<void> addMentorFeedback(String ideaId, String feedback) async {
    await _db.collection('business_ideas').doc(ideaId).update({
      'mentor_feedback': feedback,
      'status': 'Reviewed',
    });
  }

  Future<void> createMentorGroup(String mentorId, List<String> entrepreneurIds) async {
    await _db.collection('mentor_groups').add({
      'mentor_id': mentorId,
      'entrepreneur_ids': entrepreneurIds,
      'created_at': Timestamp.now(),
    });
  }
}