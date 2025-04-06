import os
import json
import logging
import textwrap
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters
)
from PIL import Image, ImageDraw, ImageFont

# إعدادات التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# لوحة المفاتيح
keyboard = [['خبر عاجل', 'خبر عادي'], ['متابعة إخبارية']]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# تحميل الإعدادات من config.json
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("مرحباً! اختر نوع الخبر:", reply_markup=reply_markup)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    try:
        if 'template_type' not in user_data:
            await update.message.reply_text('الرجاء اختيار نوع الخبر أولاً.')
            return

        template_type = user_data['template_type']
        template_info = config.get(template_type, {})

        required_fields = ['font', 'font_size', 'font_color', 'template_path']
        if not all(field in template_info for field in required_fields):
            missing = [field for field in required_fields if field not in template_info]
            await update.message.reply_text(f'إعدادات ناقصة: {", ".join(missing)}')
            return

        font = ImageFont.truetype(template_info['font'], template_info['font_size'])
        image = Image.open(template_info['template_path']).convert("RGBA")
        draw = ImageDraw.Draw(image)

        max_words = template_info.get('max_words_per_line', 5)
        words = update.message.text.split()
        lines = [' '.join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

        line_spacing = template_info.get('line_spacing', 10)
        total_text_height = len(lines) * (template_info['font_size'] + line_spacing)
        img_width, img_height = image.size

        alignment = template_info.get('alignment', {})
        vertical_align = alignment.get('vertical', 'center')
        vertical_offset = alignment.get('vertical_offset', 0)

        if vertical_align == 'center':
            y = (img_height - total_text_height) / 2 + vertical_offset
        else:
            y = vertical_offset

        for line in lines:
            text_width = draw.textlength(line, font=font)
            horizontal_align = alignment.get('horizontal', 'center')
            if horizontal_align == 'center':
                x = (img_width - text_width) / 2
            elif horizontal_align == 'left':
                x = 20
            elif horizontal_align == 'right':
                x = img_width - text_width - 20
            else:
                x = (img_width - text_width) / 2

            draw.text((x, y), line, font=font, fill=template_info['font_color'])
            y += template_info['font_size'] + line_spacing

        temp_file = "temp_news.png"
        image.save(temp_file)
        with open(temp_file, 'rb') as photo:
            await update.message.reply_photo(photo=photo)

    except Exception as e:
        logger.error(f"خطأ: {str(e)}", exc_info=True)
        await update.message.reply_text("حدث خطأ أثناء إنشاء الصورة.")
    finally:
        if os.path.exists("temp_news.png"):
            os.remove("temp_news.png")
        user_data.clear()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in config:
        context.user_data['template_type'] = text
        await update.message.reply_text("أرسل نص الخبر الآن:")
    else:
        await generate_image(update, context)

def main():
    try:
        TOKEN = os.getenv('TELEGRAM_TOKEN')
        if not TOKEN:
            raise ValueError("يرجى تعيين TELEGRAM_TOKEN في متغيرات البيئة")

        # قراءة اسم النطاق الذي توفره Render تلقائياً في متغير البيئة
        HOSTNAME = os.getenv('RENDER_EXTERNAL_HOSTNAME')
        if not HOSTNAME:
            raise ValueError("RENDER_EXTERNAL_HOSTNAME غير متوفر")

        # رقم المنفذ الذي تحدده Render تلقائياً
        PORT = int(os.environ.get('PORT', 8443))

        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Bot started with Webhook")

        # تشغيل Webhook
        app.run_webhook(
            listen="0.0.0.0",
            port=10000,  # استخدم المنفذ 10000
            webhook_url=f"https://{HOSTNAME}/{TOKEN}"
        )
    except Exception as e:
        logger.error(f"فشل تشغيل البوت: {e}", exc_info=True)

if __name__ == '__main__':
    main()
