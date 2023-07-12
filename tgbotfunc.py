import requests
import json
import wave
from io import BytesIO


def handle_command(event):
    command = event.get('message', {}).get('text')
    if command == '/start' or command == '/help':
        response = "Я сообщу вам о погоде в том месте, которое сообщите мне.\nЯ могу ответить на:\n- Текстовое сообщение с названием населенного пункта.\n- Голосовое сообщение с названием населенного пункта.\n- Сообщение с точкой на карте."
    else:
        response = "Неверная команда."
    send_message(event['message']['chat']['id'], response)


def handle_text_message(event):
    location = event.get('message', {}).get('text')
    weather_info = get_weather_info(location)
    if weather_info:
        response = generate_text_response(weather_info)
    else:
        response = f"Я не нашел населенный пункт \"{location}\"."
    send_message(event['message']['chat']['id'], response)


def handle_voice_message(event):
    voice_message = event.get('message', {}).get('voice')
    if voice_message:
        duration = voice_message.get('duration', 0)
        if duration <= 30:
            file_id = voice_message.get('file_id')
            if file_id:
                location = get_voice_location(file_id)
                if location:
                    weather_info = get_weather_info(location)
                    if weather_info:
                        response = generate_voice_response(weather_info)
                    else:
                        response = f"Я не нашел населенный пункт \"{location}\"."
                else:
                    response = f"Я не могу понять голосовое сообщение длительностью более 30 секунд."
            else:
                response = "Не удалось получить идентификатор файла голосового сообщения."
        else:
            response = f"Я не могу понять голосовое сообщение длительностью более 30 секунд."
    else:
        response = "Голосовое сообщение не найдено."
    send_message(event.get('message', {}).get('chat', {}).get('id'), response)


def handle_location_message(event):
    latitude = event.get('message', {}).get('location', {}).get('latitude')
    longitude = event.get('message', {}).get('location', {}).get('longitude')
    location = get_location_from_coordinates(latitude, longitude)
    if location:
        weather_info = get_weather_info(location)
        if weather_info:
            response = generate_text_response(weather_info)
        else:
            response = "Я не знаю какая погода в этом месте."
    else:
        response = "Я не знаю какая погода в этом месте."
    send_message(event['message']['chat']['id'], response)


def handle_other_message(event):
    response = "Я не могу ответить на такой тип сообщения.\n\nНо могу ответить на:\n- Текстовое сообщение с названием населенного пункта.\n- Голосовое сообщение с названием населенного пункта.\n- Сообщение с точкой на карте."
    send_message(event['message']['chat']['id'], response)


def get_weather_info(location):
    # Используем OpenWeatherMap API для получения информации о погоде
    api_key = "Your API KEY OpenWeatherMap"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        weather_data = json.loads(response.text)
        return weather_data
    return None


def generate_text_response(weather_info):
    # Получаем необходимые данные из weather_info и формируем ответное текстовое сообщение
    description = weather_info['weather'][0]['description']
    temperature = round(weather_info['main']['temp'] - 273.15)
    feels_like = round(weather_info['main']['feels_like'] - 273.15)
    pressure = round(weather_info['main']['pressure'] * 0.75006375541921)
    humidity = weather_info['main']['humidity']
    visibility = weather_info.get('visibility', 0)
    wind_speed = weather_info['wind']['speed']
    wind_direction = get_wind_direction(weather_info['wind']['deg'])
    sunrise = convert_unix_timestamp(weather_info['sys']['sunrise'])
    sunset = convert_unix_timestamp(weather_info['sys']['sunset'])

    response = {
        "message": f"{description}.\nТемпература {temperature} ℃, ощущается как {feels_like} ℃.\nАтмосферное давление {pressure} мм рт. ст.\nВлажность {humidity} %.\nВидимость {visibility} метров.\nВетер {wind_speed} м/с {wind_direction}.\nВосход солнца {sunrise} МСК. Закат {sunset} МСК."
    }
    return json.dumps(response)


def generate_voice_response(weather_info):
    # Получаем необходимые данные из weather_info и формируем ответное голосовое сообщение
    location = weather_info['name']
    description = weather_info['weather'][0]['description']
    temperature = round(weather_info['main']['temp'] - 273.15)
    feels_like = round(weather_info['main']['feels_like'] - 273.15)
    pressure = round(weather_info['main']['pressure'] * 0.75006375541921)
    humidity = weather_info['main']['humidity']

    response = {
        "message": f"Населенный пункт {location}.\n{description}.\nТемпература {temperature}.\nОщущается как {feels_like}.\nДавление {pressure}.\nВлажность {humidity}."
    }
    return json.dumps(response)


def send_message(chat_id, text):
    # Используем Telegram Bot API для отправки сообщения с заданным текстом на указанный chat_id
    bot_token = "Your Token TG BOT"
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, json=data)
    if response.status_code == 200:
        print("Message sent successfully")
    else:
        print(f"Failed to send message. Status code: {response.status_code}")


def get_voice_location(file_id):
    # Используем Yandex SpeechKit API для распознавания голоса
    bot_token = "Your Token TG BOT"
    oauth_token = "Your Token Yandex Cloud Functions"
    url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
    headers = {
        "Authorization": f"Api-Key {oauth_token}",
        "Content-Type": "audio/ogg"
    }
    params = {
        "lang": "ru-RU"
    }
    file_url = f"https://api.telegram.org/file/bot{bot_token}/getFile?file_id={file_id}"
    file_response = requests.get(file_url)
    if file_response.status_code == 200:
        file_path = file_response.json()['result']['file_path']
        file_content_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
        file_content_response = requests.get(file_content_url)
        if file_content_response.status_code == 200:
            audio_data = BytesIO(file_content_response.content)
            audio = wave.open(audio_data, 'rb')

            # Convert the audio to 16kHz 16-bit mono PCM
            pcm_data = convert_audio_to_pcm(audio)

            response = requests.post(url, headers=headers, params=params, data=pcm_data)
            if response.status_code == 200:
                recognized_text = response.json()['result']
                return recognized_text
    return None


def convert_audio_to_pcm(audio):
    # Convert audio to 16kHz 16-bit mono PCM
    pcm_data = BytesIO()
    pcm = wave.open(pcm_data, 'wb')
    pcm.setnchannels(1)
    pcm.setsampwidth(2)
    pcm.setframerate(16000)
    pcm.writeframes(audio.readframes(audio.getnframes()))
    pcm.close()
    pcm_data.seek(0)
    return pcm_data


def get_location_from_coordinates(latitude, longitude):
    api_key = 'Your API key for Yandex Geocoder'
    url = f'https://geocode-maps.yandex.ru/1.x/?apikey={api_key}&format=json&geocode={longitude},{latitude}'

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        locality = data['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['name']
        return locality

    return None


def get_wind_direction(degrees):
    # Определяем направление ветра по градусам
    if degrees >= 337.5 or degrees < 22.5:
        return "С"
    elif degrees >= 22.5 and degrees < 67.5:
        return "СВ"
    elif degrees >= 67.5 and degrees < 112.5:
        return "В"
    elif degrees >= 112.5 and degrees < 157.5:
        return "ЮВ"
    elif degrees >= 157.5 and degrees < 202.5:
        return "Ю"
    elif degrees >= 202.5 and degrees < 247.5:
        return "ЮЗ"
    elif degrees >= 247.5 and degrees < 292.5:
        return "З"
    else:
        return "СЗ"


def convert_unix_timestamp(timestamp):
    import datetime
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%H:%M")


def handler(event, context):
    if 'message' in event:
        message_type = event['message'].get('message_type')
        if message_type == 'command':
            response = handle_command(event)
        elif message_type == 'text':
            response = handle_text_message(event)
        elif message_type == 'voice':
            response = handle_voice_message(event)
        elif message_type == 'location':
            response = handle_location_message(event)
        else:
            response = handle_other_message(event)

        send_message(event['message']['chat']['id'], response)

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'method': 'sendMessage',
            'chat_id': event['message']['chat']['id'],
            'text': response
        }),
        'isBase64Encoded': False
    }




