from openai import OpenAI

# Вверху файла, после загрузки ENV:
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# …

# В функции handle_text:
if context.user_data.pop("checking", False):
    prompt = f"Реши эту математическую задачу и объясни шаги:\n{update.message.text}"
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4",
            messages=[{"role":"user", "content": prompt}],
            temperature=0.2
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"⚠️ Ошибка OpenAI: {e}"
    await update.message.reply_text(answer)

# В функции handle_photo:
if context.user_data.pop("checking", False):
    # … подготовка base64 в переменную b64 …
    try:
        resp = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"user","content":"Реши математическую задачу на этом изображении."},
                {"role":"user","content":[
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{b64}"}}
                ]}
            ]
        )
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = f"⚠️ Ошибка при обработке фото: {e}"
    await update.message.reply_text(answer)
