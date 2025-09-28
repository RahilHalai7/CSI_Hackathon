import 'dart:io';
import 'dart:typed_data';
import 'package:firebase_storage/firebase_storage.dart';
import 'package:flutter/foundation.dart';

class StorageService {
  final FirebaseStorage _storage = FirebaseStorage.instance;

  // For web compatibility - upload using bytes
  Future<String> uploadFileBytes(
      Uint8List fileBytes,
      String storagePath,
      String fileName,
      ) async {
    try {
      debugPrint('StorageService: Starting uploadFileBytes');
      debugPrint('StorageService: Storage path: $storagePath');
      debugPrint('StorageService: File name: $fileName');
      debugPrint('StorageService: File size: ${fileBytes.length} bytes');

      // Create a reference to the Firebase Storage path
      final ref = _storage.ref().child(storagePath);
      debugPrint('StorageService: Reference created');

      // Upload the file bytes
      final uploadTask = ref.putData(
        fileBytes,
        SettableMetadata(
          customMetadata: {
            'uploaded_by': 'flutter_app',
            'file_name': fileName,
            'upload_timestamp': DateTime.now().toIso8601String(),
          },
        ),
      );
      debugPrint('StorageService: Upload task created');

      // Monitor upload progress
      uploadTask.snapshotEvents.listen((TaskSnapshot snapshot) {
        final progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        debugPrint('StorageService: Upload progress: ${progress.toStringAsFixed(2)}%');
      });

      // Wait for the upload to complete
      debugPrint('StorageService: Waiting for upload to complete...');
      final snapshot = await uploadTask.whenComplete(() {
        debugPrint('StorageService: Upload completed');
      });

      debugPrint('StorageService: Getting download URL...');
      // Get the download URL
      final downloadUrl = await snapshot.ref.getDownloadURL();

      debugPrint('StorageService: Upload successful! URL: $downloadUrl');
      return downloadUrl;
    } catch (e) {
      debugPrint('StorageService ERROR: $e');
      debugPrint('StorageService ERROR Type: ${e.runtimeType}');
      throw Exception('Failed to upload file: $e');
    }
  }

  // Keep the original method for mobile/desktop compatibility
  Future<String> uploadFile(File file, String storagePath) async {
    try {
      debugPrint('StorageService: Starting uploadFile');
      debugPrint('StorageService: File path: ${file.path}');
      debugPrint('StorageService: Storage path: $storagePath');

      // Create a reference to the Firebase Storage path
      final ref = _storage.ref().child(storagePath);
      debugPrint('StorageService: Reference created');

      // Upload the file
      final uploadTask = ref.putFile(
        file,
        SettableMetadata(
          customMetadata: {
            'uploaded_by': 'flutter_app',
            'file_name': file.path.split('/').last,
            'upload_timestamp': DateTime.now().toIso8601String(),
          },
        ),
      );
      debugPrint('StorageService: Upload task created');

      // Monitor upload progress
      uploadTask.snapshotEvents.listen((TaskSnapshot snapshot) {
        final progress = (snapshot.bytesTransferred / snapshot.totalBytes) * 100;
        debugPrint('StorageService: Upload progress: ${progress.toStringAsFixed(2)}%');
      });

      // Wait for the upload to complete
      debugPrint('StorageService: Waiting for upload to complete...');
      final snapshot = await uploadTask.whenComplete(() {
        debugPrint('StorageService: Upload completed');
      });

      debugPrint('StorageService: Getting download URL...');
      // Get the download URL
      final downloadUrl = await snapshot.ref.getDownloadURL();

      debugPrint('StorageService: Upload successful! URL: $downloadUrl');
      return downloadUrl;
    } catch (e) {
      debugPrint('StorageService ERROR: $e');
      debugPrint('StorageService ERROR Type: ${e.runtimeType}');
      throw Exception('Failed to upload file: $e');
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
      debugPrint('StorageService Universal ERROR: $e');
      throw Exception('Failed to upload: $e');
    }
  }

  // Delete file from storage
  Future<void> deleteFile(String storagePath) async {
    try {
      final ref = _storage.ref().child(storagePath);
      await ref.delete();
      debugPrint('StorageService: File deleted successfully: $storagePath');
    } catch (e) {
      debugPrint('StorageService Delete ERROR: $e');
      throw Exception('Failed to delete file: $e');
    }
  }

  // Get file metadata
  Future<FullMetadata> getFileMetadata(String storagePath) async {
    try {
      final ref = _storage.ref().child(storagePath);
      final metadata = await ref.getMetadata();
      return metadata;
    } catch (e) {
      debugPrint('StorageService Metadata ERROR: $e');
      throw Exception('Failed to get file metadata: $e');
    }
  }
}