from flask import Flask, Response, request, jsonify
import requests #Библиотека для выполнения HTTP-запросов
import json

app = Flask(__name__) #Экземпляр приложения Flask

API_KEY = ' '
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
        return Response(
            response=json.dumps(formatted_data, ensure_ascii=False),  #ensure_ascii=False для отображения кириллицы
            status=200,
            mimetype='application/json' #тип содержимого
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
