import os
import json
import logging
import textwrap
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
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
keyboard = [
    ['خبر عاجل', 'خبر عادي'],
    ['متابعة إخبارية']
]
reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('مرحباً! اختر نوع الخبر:', reply_markup=reply_markup)

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

        # إعدادات النص
        max_words = template_info.get('max_words_per_line', 5)
        text_color = template_info['font_color']
        line_spacing = template_info.get('line_spacing', 10)
        alignment = template_info.get('alignment', {})
        vertical_offset = alignment.get('vertical_offset', 0)

        # تقسيم النص إلى أسطر
        words = update.message.text.split()
        lines = [" ".join(words[i:i + max_words]) for i in range(0, len(words), max_words)]

        img_width, img_height = image.size
        total_text_height = len(lines) * (template_info['font_size'] + line_spacing)

        # المحاذاة الرأسية
        if alignment.get('vertical') == 'center':
            y = (img_height - total_text_height) / 2 + vertical_offset
        else:
            y = vertical_offset

        for line in lines:
            text_width = draw.textlength(line, font=font)
            # المحاذاة الأفقية
            if alignment.get('horizontal') == 'center':
                x = (img_width - text_width) / 2
            else:
                x = 0

            draw.text((x, y), line, font=font, fill=text_color)
            y += template_info['font_size'] + line_spacing

        temp_file = "temp_news.png"
        image.save(temp_file)
        with open(temp_file, 'rb') as photo:
            await update.message.reply_photo(photo=photo)

    except FileNotFoundError as e:
        logger.error(f"خطأ في الملف: {str(e)}")
        await update.message.reply_text("تعذر العثور على أحد الملفات المطلوبة")
    except Exception as e:
        logger.error(f"خطأ غير متوقع: {str(e)}", exc_info=True)
        await update.message.reply_text('حدث خطأ أثناء معالجة طلبك')
    finally:
        if 'temp_file' in locals() and os.path.exists(temp_file):
            os.remove(temp_file)
        user_data.clear()

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text in ['خبر عاجل', 'خبر عادي', 'متابعة إخبارية']:
        context.user_data['template_type'] = text
        await update.message.reply_text('أرسل نص الخبر الآن:')
    else:
        await generate_image(update, context)

async def main():
    try:
        TOKEN = os.getenv('TELEGRAM_TOKEN')

        if not TOKEN:
            raise ValueError("لم يتم تعيين TELEGRAM_TOKEN")

        app = ApplicationBuilder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        logger.info("Bot started successfully")
        await app.run_polling()

    except Exception as e:
        logger.error(f"فشل تشغيل البوت: {e}")

if __name__ == '__main__':
    with open('config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)

    import asyncio
    asyncio.run(main())
