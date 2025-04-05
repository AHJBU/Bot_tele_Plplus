def generate_image(update: Update, context: CallbackContext):
    # ... (الكود السابق حتى بداية try)
    
    try:
        font = ImageFont.truetype(font_path, font_size)
        image = Image.open(template_path).convert("RGBA")
        draw = ImageDraw.Draw(image)
        
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
        
        # حساب الأبعاد
        img_width, img_height = image.size
        total_text_height = (font_size + line_spacing) * len(lines)
        
        # تحديد الموضع الرأسي
        if template_info['alignment']['vertical'] == 'center':
            y = (img_height - total_text_height) / 2
            if 'vertical_offset' in template_info['alignment']:
                y -= template_info['alignment']['vertical_offset']
        
        # رسم كل سطر
        for line in lines:
            text_width = font.getlength(line)
            
            # تحديد الموضع الأفقي
            if template_info['alignment']['horizontal'] == 'center':
                x = (img_width - text_width) / 2
                
            draw.text((x, y), line, font=font, fill=font_color)
            y += font_size + line_spacing

        image.save("temp.png")
        update.message.reply_photo(photo=open("temp.png", "rb"))
        user_data.clear()
    # ... (بقية الكود)