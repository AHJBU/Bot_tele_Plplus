def generate_image(update: Update, context: CallbackContext):
    user_data = context.user_data
    template_type = user_data.get('template_type')
    news_text = update.message.text

    if not template_type:
        update.message.reply_text('الرجاء اختيار نوع الخبر أولاً.')
        return

    template_info = config.get(template_type, {})
    try:
        font_path = template_info.get('font')
        font_size = template_info.get('font_size', 12)
        font_color = template_info.get('font_color', '#000000')
        template_path = template_info.get('template_path')
        line_spacing = template_info.get('line_spacing', 14)
        max_words = template_info.get('max_words_per_line', 5)
        alignment = template_info.get('alignment', {'horizontal': 'center', 'vertical': 'center'})

        # التحقق من وجود الملفات المطلوبة
        if not all([font_path, template_path]):
            missing = []
            if not font_path: missing.append("font_path")
            if not template_path: missing.append("template_path")
            raise FileNotFoundError(f"الملفات المطلوبة غير موجودة: {', '.join(missing)}")

        # معالجة الصورة
        with Image.open(template_path).convert("RGBA") as image:
            draw = ImageDraw.Draw(image)
            
            try:
                font = ImageFont.truetype(font_path, font_size)
            except IOError:
                raise ValueError(f"تعذر تحميل الخط من المسار: {font_path}")

            # تقسيم النص إلى أسطر
            words = news_text.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(current_line) >= max_words:
                    lines.append(" ".join(current_line))
                    current_line = []
            if current_line:
                lines.append(" ".join(current_line))
            
            # حساب المواضع
            img_width, img_height = image.size
            total_text_height = (font_size + line_spacing) * len(lines)
            
            # تحديد الموضع الرأسي
            y = (img_height - total_text_height) / 2
            if alignment.get('vertical') == 'center' and 'vertical_offset' in alignment:
                y -= alignment['vertical_offset']
            
            # رسم النص
            for line in lines:
                text_width = font.getlength(line)
                x = (img_width - text_width) / 2  # محاذاة أفقية للوسط
                draw.text((x, y), line, font=font, fill=font_color)
                y += font_size + line_spacing
            
            # حفظ وإرسال الصورة
            temp_path = "temp.png"
            image.save(temp_path)
            with open(temp_path, 'rb') as photo:
                update.message.reply_photo(photo=photo)
            
            # تنظيف الملف المؤقت
            if os.path.exists(temp_path):
                os.remove(temp_path)

    except FileNotFoundError as e:
        logging.error(f"خطأ في الملفات: {str(e)}")
        update.message.reply_text("حدث خطأ في تحميل الموارد المطلوبة")
    except ValueError as e:
        logging.error(f"خطأ في القيم: {str(e)}")
        update.message.reply_text("حدث خطأ في إعدادات التصميم")
    except Exception as e:
        logging.error(f"خطأ غير متوقع: {str(e)}", exc_info=True)
        update.message.reply_text("حدث خطأ غير متوقع أثناء معالجة الصورة")
    finally:
        user_data.clear()
