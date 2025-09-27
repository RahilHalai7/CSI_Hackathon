import 'package:translator/translator.dart';

class TranslationService {
  final translator = GoogleTranslator();

  Future<String> translateText(String text, String targetLangCode) async {
    final translation = await translator.translate(text, to: targetLangCode);
    return translation.text;
  }
}