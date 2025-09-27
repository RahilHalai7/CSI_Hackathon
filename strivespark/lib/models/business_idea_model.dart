class BusinessIdea {
  final String id;
  final String entrepreneurId;
  final String title;
  final String description;
  final String fileUrl;
  final String language;
  final String status;
  final String strengths;
  final String weaknesses;
  final String feasibility;
  final String mentorFeedback;

  BusinessIdea({
    required this.id,
    required this.entrepreneurId,
    required this.title,
    required this.description,
    required this.fileUrl,
    required this.language,
    required this.status,
    required this.strengths,
    required this.weaknesses,
    required this.feasibility,
    required this.mentorFeedback,
  });

  factory BusinessIdea.fromMap(String id, Map<String, dynamic> data) {
    return BusinessIdea(
      id: id,
      entrepreneurId: data['entrepreneur_id'] ?? '',
      title: data['title'] ?? '',
      description: data['description'] ?? '',
      fileUrl: data['file_url'] ?? '',
      language: data['language'] ?? 'en',
      status: data['status'] ?? 'Submitted',
      strengths: data['feedback']?['strengths'] ?? '',
      weaknesses: data['feedback']?['weaknesses'] ?? '',
      feasibility: data['feedback']?['feasibility'] ?? '',
      mentorFeedback: data['mentor_feedback'] ?? '',
    );
  }

  Map<String, dynamic> toMap() {
    return {
      'entrepreneur_id': entrepreneurId,
      'title': title,
      'description': description,
      'file_url': fileUrl,
      'language': language,
      'status': status,
      'feedback': {
        'strengths': strengths,
        'weaknesses': weaknesses,
        'feasibility': feasibility,
      },
      'mentor_feedback': mentorFeedback,
    };
  }
}