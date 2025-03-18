import os
import logging
import convertapi

# إعداد مفتاح ConvertAPI
convertapi.api_secret = 'secret_q4ijKpkWw17sLQx8'

logger = logging.getLogger(__name__)

def convert_to_pdf(input_path):
    """تحويل ملفات DOCX أو PPTX إلى PDF"""
    output_path = input_path.rsplit('.', 1)[0] + '_converted.pdf'
    try:
        result = convertapi.convert('pdf', {'File': input_path})
        result.save_files(output_path)
        return output_path
    except Exception as e:
        logger.error(f"فشل تحويل الملف إلى PDF: {e}")
        return None

def convert_pdf_to(input_path, target_format):
    """تحويل ملفات PDF إلى DOCX أو PPTX"""
    output_path = input_path.rsplit('.', 1)[0] + f'_converted.{target_format}'
    try:
        result = convertapi.convert(target_format, {'File': input_path})
        result.save_files(output_path)
        return output_path
    except Exception as e:
        logger.error(f"فشل تحويل PDF إلى {target_format}: {e}")
        return None
