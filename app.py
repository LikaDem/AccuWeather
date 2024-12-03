from flask import Flask, Response, request, jsonify
import requests #Библиотека для выполнения HTTP-запросов
import json

app = Flask(__name__) #Экземпляр приложения Flask

API_KEY = 'f2xzWIvhaSahTB3vENImWBeqJCTff1Qh'
BASE_URL = "http://dataservice.accuweather.com" #Базовый URL для запросов к AccuWeather

#Получение данных о погоде
def get_weather(lat, lon):
    #URL и параметры для определения ключа локации по координатам
    location_url = f'{BASE_URL}/locations/v1/cities/geoposition/search'
    params = { 'apikey': API_KEY, 'q': f'{lat},{lon}' }
    response = requests.get(location_url, params=params) #запрос
    if response.status_code != 200:
        raise Exception(f'Ошибка API: {response.status_code}, {response.text}')
    
    #извлечение ключа локации из полученного ответа
    location_data = response.json()
    location_key = location_data["Key"]

    #URL и параметры для получения прогноза погоды по ключу локации
    forecast_url = f'{BASE_URL}/forecasts/v1/hourly/1hour/{location_key}'
    params = { 'apikey': API_KEY, 'metric': True } #метрические единицы
    response = requests.get(forecast_url, params=params)
    if response.status_code != 200:
        raise Exception(f'Ошибка API: {response.status_code}, {response.text}')
    
    forecast_data = response.json()
    return forecast_data

#форматирование данных о погоде
def format_weather_data(data):
    return {
        'Температура (С)' : data[0]['Temperature']['Value'],
        'Влажность (%)' : data[0].get('RelativeHumidity', 'Нет данных'),
        "Скорость ветра (км/ч)": data[0].get("Wind", {}).get("Speed", {}).get("Value", "Нет данных"),
        "Вероятность дождя (%)": data[0].get("PrecipitationProbability", "Нет данных")
    }

def check_bad_weather(temp, wind_speed, precipitation_prob):
    if isinstance(temp, str) or isinstance(wind_speed, str) or isinstance(precipitation_prob, str):
        return True

    if temp < 0 or temp > 35:
        return True
    if wind_speed > 50:
        return True
    if precipitation_prob > 70:
        return True
    return False

@app.route('/weather', methods=['GET'])
def weather():
    #координаты из параметров запроса
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Параметры "lat" и "lon" обязательны'}), 400
    
    try:
        #данные о погоде
        weather_data = get_weather(lat, lon)
        formatted_data = format_weather_data(weather_data)

        bad_weather = check_bad_weather(
            temp=formatted_data['Температура (С)'],
            wind_speed=formatted_data.get("Скорость ветра (км/ч)", '0'),
            precipitation_prob=formatted_data.get("Вероятность дождя (%)", '0')
        )

        result = {
            'Погода': 'Плохая' if bad_weather else 'Хорошая',
            'Данные о погоде': formatted_data
        }

        return Response(
            response=json.dumps(result, ensure_ascii=False),  #ensure_ascii=False для отображения кириллицы
            status=200,
            mimetype='application/json' #тип содержимого
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
