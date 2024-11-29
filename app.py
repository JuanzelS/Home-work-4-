import os
import requests
from pprint import PrettyPrinter
from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request


################################################################################
## SETUP
################################################################################

app = Flask(__name__)

# Load the API key from the '.env' file
load_dotenv()

pp = PrettyPrinter(indent=4)

API_KEY = os.getenv('API_KEY')
API_URL = 'http://api.openweathermap.org/data/2.5/weather'

if not API_KEY:
    raise ValueError("API_KEY is missing. Please check your '.env' file.")

################################################################################
## ROUTES
################################################################################

@app.route('/')
def home():
    """Displays the homepage with forms for current or historical data."""
    context = {
        'min_date': (datetime.now() - timedelta(days=5)),
        'max_date': datetime.now()
    }
    return render_template('home.html', **context)

def get_letter_for_units(units):
    """Returns a shorthand letter for the given units."""
    return 'F' if units == 'imperial' else 'C' if units == 'metric' else 'K'

@app.route('/results')
def results():
    """Displays results for current weather conditions."""
    city = request.args.get('city', '').strip()
    units = request.args.get('units', 'imperial')  # Default to imperial

    if not city:
        return render_template('home.html', error="City name is required.")

    params = {
        'q': city,
        'appid': API_KEY,
        'units': units
    }

    result_json = requests.get(API_URL, params=params).json()

    if result_json.get('cod') == 200:  # API call successful
        context = {
            'date': datetime.now(),
            'city': result_json['name'],
            'description': result_json['weather'][0]['description'].capitalize(),
            'temp': result_json['main']['temp'],
            'humidity': result_json['main']['humidity'],
            'wind_speed': result_json['wind']['speed'],
            'sunrise': datetime.fromtimestamp(result_json['sys']['sunrise']),
            'sunset': datetime.fromtimestamp(result_json['sys']['sunset']),
            'units_letter': get_letter_for_units(units)
        }
    else:
        context = {
            'error': f"City '{city}' not found. Please try again."
        }

    return render_template('results.html', **context)

@app.route('/comparison_results')
def comparison_results():
    """Displays the relative weather for 2 different cities."""
    city1 = request.args.get('city1', '').strip()
    city2 = request.args.get('city2', '').strip()
    units = request.args.get('units', 'imperial')  # Default to imperial

    if not city1 or not city2:
        return render_template('home.html', error="Both city names are required.")

    def get_city_weather(city):
        """Fetch weather data for a city."""
        params = {
            'q': city,
            'appid': API_KEY,
            'units': units
        }
        response = requests.get(API_URL, params=params).json()
        if response.get('cod') == 200:  # API call successful
            return {
                'name': response['name'],
                'temp': response['main']['temp'],
                'humidity': response['main']['humidity'],
                'wind_speed': response['wind']['speed'],
                'sunset': datetime.fromtimestamp(response['sys']['sunset']),
            }
        return None

    city1_info = get_city_weather(city1)
    city2_info = get_city_weather(city2)

    if not city1_info or not city2_info:
        error_message = f"Could not fetch data for one or both cities: {city1}, {city2}."
        return render_template('home.html', error=error_message)

    context = {
        'city1_info': city1_info,
        'city2_info': city2_info,
        'units_letter': get_letter_for_units(units)
    }

    return render_template('comparison_results.html', **context)

if __name__ == '__main__':
    app.config['ENV'] = 'development'
    app.run(debug=True)
   
