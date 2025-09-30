import 'api_service.dart';

class FirestoreService {
  final _api = const ApiService();

  Future<void> submitBusinessIdea({
    required String uid,
    required String title,
    required String description,
    required String fileUrl,
    required String language,
  }) async {
    await _api.submitBusinessIdea(
      uid: uid,
      title: title,
      description: description,
      fileUrl: fileUrl,
      language: language,
    );
  }

  Future<List<Map<String, dynamic>>> getIdeasByUser(String uid) async {
    return await _api.getIdeasByUser(uid);
  }

  Future<void> addMentorFeedback(String ideaId, String feedback) async {
    await _api.addMentorFeedback(ideaId, feedback);
  }

  Future<void> createMentorGroup(
    String mentorId,
    List<String> entrepreneurIds,
  ) async {
    // Not implemented in local API yet. Intentionally left as a no-op.
  }
}