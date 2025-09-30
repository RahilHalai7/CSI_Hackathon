import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/foundation.dart';

class FileUploadWidget extends StatefulWidget {
  final Function(PlatformFile) onFileSelected;

  const FileUploadWidget({super.key, required this.onFileSelected});

  @override
  State<FileUploadWidget> createState() => _FileUploadWidgetState();
}

class _FileUploadWidgetState extends State<FileUploadWidget> {
  String? fileName;
  bool isFileValid = true;

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: [
        'pdf',
        'ppt',
        'pptx',
        'doc',
        'docx',
        'jpg',
        'jpeg',
        'png',
        'mp3',
        'wav',
      ],
    );
    if (result != null && result.files.isNotEmpty) {
      final file = result.files.first;
      final isValid = await _checkFileValidity(file);

      setState(() {
        fileName = file.name;
        isFileValid = isValid;
      });

      if (isValid) {
        widget.onFileSelected(file);
      }
    }
  }

  Future<bool> _checkFileValidity(PlatformFile file) async {
    try {
      // On web, path is not available; validate using bytes and size
      if (kIsWeb) {
        final hasBytes = file.bytes != null && file.bytes!.isNotEmpty;
        return hasBytes && file.size > 0;
      }

      // On mobile/desktop, verify the file exists at the provided path
      if (file.path == null) {
        return false;
      }
      final fileObj = File(file.path!);
      final exists = await fileObj.exists();
      final size = await fileObj.length();
      return exists && size > 0;
    } catch (e) {
      print('Error checking file validity: $e');
      return false;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        ElevatedButton.icon(
          onPressed: _pickFile,
          icon: const Icon(Icons.upload_file),
          label: const Text("Upload PDF or Audio"),
        ),
        if (fileName != null)
          Padding(
            padding: const EdgeInsets.only(top: 8),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(
                  isFileValid ? Icons.check_circle : Icons.error_outline,
                  color: isFileValid ? Colors.green : Colors.orange,
                  size: 16,
                ),
                const SizedBox(width: 4),
                Text(
                  "Selected: $fileName",
                  style: TextStyle(color: isFileValid ? null : Colors.orange),
                ),
              ],
            ),
          ),
        if (fileName != null && !isFileValid)
          Padding(
            padding: const EdgeInsets.only(top: 4),
            child: Text(
              "File may be invalid or inaccessible. Please try again.",
              style: TextStyle(fontSize: 12, color: Colors.orange),
            ),
          ),
      ],
    );
  }
}