import os
import json
import logging
import textwrap
from telegram import Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    ReplyKeyboardMarkup
)
from PIL import Image, ImageDraw, ImageFont

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# لوحة المفاتيح
keyboard = [
    ['خبر عاجل', 'خبر عادي'],
    ['متابعة إخبارية']
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def start(update: Update, context: CallbackContext):
    """Handler لبدء التشغيل"""
    update.message.reply_text('مرحباً! اختر نوع الخبر:', reply_markup=reply_markup)

def generate_image(update: Update, context: CallbackContext):
    """Handler لإنشاء الصورة"""
    user_data = context.user_data
    
    try:
        # التحقق من وجود نوع الخبر المحدد
        if 'template_type' not in user_data:
            update.message.reply_text('الرجاء اختيار نوع الخبر أولاً.')
            return

        template_type = user_data['template_type']
        template_info = config.get(template_type, {})
        
        # التحقق من وجود جميع المتطلبات
        required_fields = ['font', 'font_size', 'font_color', 'template_path']
        if not all(field in template_info for field in required_fields):
            missing = [field for field in required_fields if field not in template_info]
            update.message.reply_text(f'إعدادات ناقصة: {", ".join(missing)}')
            return

        # تحميل الخط والتصميم
        font = ImageFont.truetype(template_info['font'], template_info['font_size'])
        image = Image.open(template_info['template_path']).convert("RGBA")
        draw = ImageDraw.Draw(image)
        
        # معالجة النص
        lines = textwrap.wrap(update.message.text, width=template_info.get('max_width', 30))
        
        # حساب المواضع
        img_width, img_height = image.size
        y = template_info.get('y_position', img_height // 2)
        
        # رسم النص
        for line in lines:
            text_width = draw.textlength(line, font=font)
            x = (img_width - text_width) / 2  # محاذاة للوسط
            draw.text((x, y), line, font=font, fill=template_info['font_color'])
            y += template_info['font_size'] + template_info.get('line_spacing', 10)
        
        # حفظ وإرسال الصورة
        temp_file = "temp_news.png"
        image.save(temp_file)
        with open(temp_file, 'rb') as photo:
            update.message.reply_photo(photo=photo)
        
    except FileNotFoundError as e:
        logger.error(f"خطأ في الملف: {str(e)}")
        update.message.reply_text("تعذر العثور على أحد الملفات المطلوبة")
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}", exc_info=True)
        update.message.reply_text('حدث خطأ أثناء معالجة طلبك')
    finally:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        user_data.clear()

def handle_message(update: Update, context: CallbackContext):
    """توجيه الرسائل"""
    text = update.message.text
    if text in ['خبر عاجل', 'خبر عادي', 'متابعة إخبارية']:
        context.user_data['template_type'] = text
        update.message.reply_text('أرسل نص الخبر الآن:')
    else:
        generate_image(update, context)

def main():
    """الدالة الرئيسية"""
    try:
        # استخراج التوكن من متغيرات البيئة
        TOKEN = os.getenv('TELEGRAM_TOKEN')
        
        if not TOKEN:
            raise ValueError("لم يتم تعيين TELEGRAM_TOKEN")
        
        # إنشاء Updater
        updater = Updater(TOKEN)
        dispatcher = updater.dispatcher
        
        # إضافة Handlers
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
        
        # بدء البوت
        updater.start_polling()
        logger.info("Bot started successfully")
        updater.idle()
        
    except Exception as e:
        logger.error(f"فشل تشغيل البوت: {e}")

if __name__ == '__main__':
    # تحميل الإعدادات
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    main()
