import 'package:file_picker/file_picker.dart';

class FileUtils {
  static Future<PlatformFile?> pickPdfOrAudio() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'mp3', 'wav'],
    );
    return result?.files.first;
  }

  static String getFileType(String fileName) {
    if (fileName.endsWith('.pdf')) return 'PDF';
    if (fileName.endsWith('.mp3') || fileName.endsWith('.wav')) return 'Audio';
    return 'Unknown';
  }
}