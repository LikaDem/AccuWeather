from flask import Flask, Response, request, jsonify, render_template
import requests #Библиотека для выполнения HTTP-запросов
import json

app = Flask(__name__) #Экземпляр приложения Flask

API_KEY = 'f2xzWIvhaSahTB3vENImWBeqJCTff1Qh'
BASE_URL = "http://dataservice.accuweather.com" #Базовый URL для запросов к AccuWeather

#Получение данных о погоде
def get_weather(city_name):
    try:
        location_url = f"{BASE_URL}/locations/v1/cities/search"
        response = requests.get(location_url, params={"apikey": API_KEY, "q": city_name})
        response.raise_for_status()
        location_data = response.json()
        
        if not location_data:
            raise Exception("Город не найден")
        
        location_key = location_data[0]["Key"]
        forecast_url = f"{BASE_URL}/forecasts/v1/hourly/1hour/{location_key}"
        response = requests.get(forecast_url, params={"apikey": API_KEY, "metric": True})
        response.raise_for_status()
        
        forecast_data = response.json()[0]
        return {
            "temperature": forecast_data["Temperature"]["Value"],
            "wind_speed": forecast_data.get("Wind", {}).get("Speed", {}).get("Value", "Нет данных"),
            "precipitation": forecast_data.get("PrecipitationProbability", "Нет данных")
        }
    except Exception as e:
        return {"error": str(e)}

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

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        start_city = request.form.get("start_city")
        end_city = request.form.get("end_city")
        
        if not start_city or not end_city:
            return render_template("index.html", error="Введите оба города.")
        
        # Получаем данные о погоде для обоих городов
        start_weather = get_weather(start_city)
        end_weather = get_weather(end_city)
        
        if "error" in start_weather or "error" in end_weather:
            return render_template("index.html", error="Не удалось получить данные о погоде.")
        
        # Оценка погодных условий
        start_bad_weather = check_bad_weather(
            start_weather["temperature"], 
            start_weather["wind_speed"], 
            start_weather["precipitation"]
        )
        end_bad_weather = check_bad_weather(
            end_weather["temperature"], 
            end_weather["wind_speed"], 
            end_weather["precipitation"]
        )
        
        result = {
            "start_city": {
                "name": start_city,
                "weather": start_weather,
                "bad_weather": "Плохая" if start_bad_weather else "Хорошая"
            },
            "end_city": {
                "name": end_city,
                "weather": end_weather,
                "bad_weather": "Плохая" if end_bad_weather else "Хорошая"
            }
        }
        return render_template("result.html", result=result)
    
    return render_template("index.html")

@app.errorhandler(404)
def page_not_found(error):
    return "Страница не найдена, проверьте маршрут и файл HTML.", 404

@app.errorhandler(500)
def internal_server_error(error):
    return "Внутренняя ошибка сервера: {error}", 500

if __name__ == '__main__':
    app.run(debug=True)
