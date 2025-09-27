import 'package:flutter/material.dart';

class IdeaCard extends StatelessWidget {
  final String title;
  final String description;
  final String status;
  final VoidCallback onTap;

  const IdeaCard({
    super.key,
    required this.title,
    required this.description,
    required this.status,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      child: ListTile(
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.bold)),
        subtitle: Text(description, maxLines: 2, overflow: TextOverflow.ellipsis),
        trailing: Chip(label: Text(status)),
        onTap: onTap,
      ),
    );
  }
}