import 'dart:io';
import 'dart:typed_data';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

class StorageService {
  // For web compatibility - upload using bytes
  Future<String> uploadFileBytes(
    Uint8List fileBytes,
    String storagePath,
    String fileName,
  ) async {
    try {
      debugPrint('StorageService(Local): Starting uploadFileBytes');
      debugPrint('StorageService(Local): File name: $fileName');
      debugPrint('StorageService(Local): File size: ${fileBytes.length} bytes');

      final uploadUrl = Uri.parse('http://127.0.0.1:8000/upload');
      final isPdf = fileName.toLowerCase().endsWith('.pdf');

      final req = http.MultipartRequest('POST', uploadUrl);
      req.files.add(
        http.MultipartFile.fromBytes('file', fileBytes, filename: fileName),
      );
      req.fields['process_pdf'] = isPdf ? 'true' : 'false';

      final streamed = await req.send().timeout(const Duration(minutes: 2));
      final resp = await http.Response.fromStream(streamed);
      debugPrint('StorageService(Local): Upload response: ${resp.statusCode}');
      debugPrint('StorageService(Local): Upload body: ${resp.body}');

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final storedPath = data['stored_path'] as String?;
        if (storedPath == null || storedPath.isEmpty) {
          throw Exception('Upload succeeded but stored_path missing');
        }
        debugPrint('StorageService(Local): Stored at: $storedPath');
        return storedPath;
      } else {
        throw Exception('Upload failed: ${resp.body}');
      }
    } catch (e) {
      debugPrint('StorageService(Local) ERROR: $e');
      throw Exception('Failed to upload file locally: $e');
    }
  }

  // Keep the original method for mobile/desktop compatibility
  Future<String> uploadFile(File file, String storagePath) async {
    try {
      debugPrint('StorageService(Local): Starting uploadFile');
      debugPrint('StorageService(Local): File path: ${file.path}');

      final uploadUrl = Uri.parse('http://127.0.0.1:8000/upload');
      final isPdf = file.path.toLowerCase().endsWith('.pdf');

      final req = http.MultipartRequest('POST', uploadUrl);
      req.files.add(await http.MultipartFile.fromPath('file', file.path));
      req.fields['process_pdf'] = isPdf ? 'true' : 'false';

      final streamed = await req.send().timeout(const Duration(minutes: 2));
      final resp = await http.Response.fromStream(streamed);
      debugPrint('StorageService(Local): Upload response: ${resp.statusCode}');
      debugPrint('StorageService(Local): Upload body: ${resp.body}');

      if (resp.statusCode == 200) {
        final data = jsonDecode(resp.body) as Map<String, dynamic>;
        final storedPath = data['stored_path'] as String?;
        if (storedPath == null || storedPath.isEmpty) {
          throw Exception('Upload succeeded but stored_path missing');
        }
        debugPrint('StorageService(Local): Stored at: $storedPath');
        return storedPath;
      } else {
        throw Exception('Upload failed: ${resp.body}');
      }
    } catch (e) {
      debugPrint('StorageService(Local) ERROR: $e');
      throw Exception('Failed to upload file locally: $e');
    }
  }

  // Universal method that works on both web and mobile
  Future<String> uploadUniversal({
    required String storagePath,
    required String fileName,
    Uint8List? fileBytes,
    File? file,
  }) async {
    try {
      // Use bytes if available (web), otherwise use file (mobile/desktop)
      if (fileBytes != null) {
        return await uploadFileBytes(fileBytes, storagePath, fileName);
      } else if (file != null) {
        return await uploadFile(file, storagePath);
      } else {
        throw Exception('Neither file bytes nor file provided');
      }
    } catch (e) {
      debugPrint('StorageService(Local) Universal ERROR: $e');
      throw Exception('Failed to upload locally: $e');
    }
  }
}