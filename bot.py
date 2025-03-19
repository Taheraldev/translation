import os
import logging
import requests
import base64
import json
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد سجل الأخطاء
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

ACCOUNT_ID = "63b1e7ba-ecdc-4978-a1a9-d27dd36d5b48"          # معرف الحساب (Account ID)
API_KEY = "2_FwEmd5QMpKxDbHnNnwydzEL3o"                # مفتاح API (ككلمة مرور)
PERMANENT_PROJECT_ID = "21355320-aee6-4b65-966f-a810e802b81a"  # معرف المشروع الدائم في Smartcat

# نطاق الخادم؛ اختر حسب موقع خادم Smartcat الخاص بك:
# للمخدم الأوروبي: https://smartcat.ai/
BASE_URL = "https://smartcat.ai/api/integration/v1/"

def get_auth_header():
    """
    تُرجع الهيدر الخاص بالمصادقة باستخدام Basic Authentication.
    """
    credentials = f"{ACCOUNT_ID}:{API_KEY}"
    encoded = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}

def upload_document(file_path):
    """
    يقوم برفع ملف إلى المشروع الدائم في Smartcat.
    يستخدم نقطة النهاية: POST project/document مع تمرير projectId عبر الرابط
    وإرسال بيانات documentModel كجزء من الـ multipart.
    """
    # تمرير معرف المشروع عبر الـ query string
    url = BASE_URL + "project/document?projectId=" + PERMANENT_PROJECT_ID

    # إعداد بيانات النموذج (documentModel)
    document_model = [
        {
            "externalId": os.path.basename(file_path),
            "metaInfo": "",
            "disassembleAlgorithmName": "",
            "presetDisassembleAlgorithm": "",
            "bilingualFileImportSetings": {
                "targetSubstitutionMode": "all",
                "lockMode": "none",
                "confirmMode": "none"
            },
            "targetLanguages": ["ar"],  # ترجمة إلى العربية؛ تأكد من توافقها مع إعدادات مشروعك
            "enablePlaceholders": True,
            "enableOcr": True
        }
    ]

    # إرسال البيانات كـ multipart بحيث يتم تحديد نوع المحتوى لـ documentModel
    files = {
        "file": open(file_path, "rb"),
        "documentModel": ("documentModel", json.dumps(document_model), "application/json")
    }
    headers = get_auth_header()
    try:
        response = requests.post(url, files=files, headers=headers)
        if response.status_code == 200:
            resp_json = response.json()
            # نفترض أن الرد يحتوي على معرف الوثيقة بالشكل التالي:
            # {"documentId": "f1e5e09a8ad7830434cc477d_25"}
            document_id = resp_json.get("documentId")
            if not document_id and isinstance(resp_json, list) and len(resp_json) > 0:
                document_id = resp_json[0].get("documentId")
            logger.info("تم رفع الملف بنجاح. document_id: %s", document_id)
            return document_id
        else:
            logger.error("فشل رفع الملف. الكود: %s، الرد: %s", response.status_code, response.text)
            return None
    except Exception as e:
        logger.error("استثناء أثناء رفع الملف: %s", str(e))
        return None

def export_document(document_id):
    """
    يقوم بتصدير الملف المترجم باستخدام Smartcat API.
    يستخدم نقطة النهاية: POST document/export مع معلمات الوثيقة.
    """
    url = BASE_URL + "document/export"
    params = {
        "documentIds": document_id,
        "mode": "current",
        "type": "target",      # "target" للحصول على الملف المترجم
        "stageNumber": "1"     # رقم المرحلة؛ تأكد من توافقه مع إعدادات مشروعك
    }
    headers = get_auth_header()
    try:
        response = requests.post(url, params=params, headers=headers)
        if response.status_code == 200:
            logger.info("تم تصدير الملف المترجم بنجاح.")
            return response.content
        else:
            logger.error("فشل تصدير الملف. الكود: %s، الرد: %s", response.status_code, response.text)
            return None
    except Exception as e:
        logger.error("استثناء أثناء تصدير الملف: %s", str(e))
        return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("مرحبًا! أرسل لي ملف PDF للترجمة من الإنجليزية إلى العربية.")

def handle_document(update: Update, context: CallbackContext):
    document = update.message.document
    if document.mime_type != "application/pdf":
        update.message.reply_text("يرجى إرسال ملف بصيغة PDF فقط.")
        return

    file_id = document.file_id
    new_file = context.bot.get_file(file_id)
    os.makedirs("downloads", exist_ok=True)
    file_path = os.path.join("downloads", document.file_name)
    new_file.download(file_path)
    update.message.reply_text("جاري رفع الملف إلى Smartcat...")

    document_id = upload_document(file_path)
    if not document_id:
        update.message.reply_text("فشل رفع الملف للترجمة. يرجى المحاولة مرة أخرى.")
        return

    update.message.reply_text("تم رفع الملف. جاري تصدير الملف المترجم...")
    translated_content = export_document(document_id)
    if translated_content:
        translated_file_path = file_path.replace('.pdf', '_translated.docx')
        with open(translated_file_path, "wb") as f:
            f.write(translated_content)
        update.message.reply_text("تمت الترجمة بنجاح! إليك الملف المترجم:")
        context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=open(translated_file_path, "rb")
        )
    else:
        update.message.reply_text("فشل تصدير الملف المترجم. يرجى المحاولة لاحقًا.")

def main():
    TELEGRAM_BOT_TOKEN = "5284087690:AAGRrcZBDcRW3k86XIyY6HVHs57oeiLZ3rc"  # استبدل بتوكن بوت تيليجرام الخاص بك
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.document.pdf, handle_document))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
