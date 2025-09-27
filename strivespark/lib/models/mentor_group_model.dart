class MentorGroup {
  final String id;
  final String mentorId;
  final List<String> entrepreneurIds;

  MentorGroup({
    required this.id,
    required this.mentorId,
    required this.entrepreneurIds,
  });

  factory MentorGroup.fromMap(String id, Map<String, dynamic> data) {
    return MentorGroup(
      id: id,
      mentorId: data['mentor_id'] ?? '',
      entrepreneurIds: List<String>.from(data['entrepreneur_ids'] ?? []),
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'mentor_id': mentorId,
      'entrepreneur_ids': entrepreneurIds,
    };
  }
}