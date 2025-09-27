import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';

class FileUploadWidget extends StatefulWidget {
  final Function(PlatformFile) onFileSelected;

  const FileUploadWidget({super.key, required this.onFileSelected});

  @override
  State<FileUploadWidget> createState() => _FileUploadWidgetState();
}

class _FileUploadWidgetState extends State<FileUploadWidget> {
  String? fileName;

  Future<void> _pickFile() async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'mp3', 'wav'],
    );
    if (result != null && result.files.isNotEmpty) {
      setState(() {
        fileName = result.files.first.name;
      });
      widget.onFileSelected(result.files.first);
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
            child: Text("Selected: $fileName"),
          ),
      ],
    );
  }
}