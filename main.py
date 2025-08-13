import calendar
import json
import os
import pandas as pd
import requests
from flask import Flask, render_template, redirect, url_for
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from flask_wtf import FlaskForm
from flask_bootstrap import Bootstrap5
from datetime import datetime, date, timedelta

pd.set_option('display.max_columns', None)
pd.set_option("display.precision", 10)

app = Flask(__name__)
bootstrap = Bootstrap5(app)
app.config['SECRET_KEY'] = 'secret'
month_names = [[month, True] for month in list(calendar.month_abbr)[1:]]
orig_nb = 2 #to put to 0
origin_loc = ['Paris', 'Sydney']  # Used to store the cities to search and display on the HTML code
API_destinations = []  # Used to store API response from KIWI

#TO DELETE ----------------Used to put only dec and jan as month
for x in range(len(month_names)):
    month_names[x][1] = False
month_names[0][1] = True
month_names[11][1] = True
# Used to put default data in the website
#Test_city = 'paris'

#TO DELETE ------------------

# KIWI API
KIWI_KEY = os.environ.get('API_KEY')
KIWI_BASE_URL = 'https://api.tequila.kiwi.com/v2'
KIWI_HEAD = {
    'apikey': KIWI_KEY,
}

# AVIATION STACK API
IATA_KEY = os.environ.get('IATA_KEY')
IATA_BASE_URL = 'https://api.aviationstack.com/v1/'
offset = 0
city_found = False
reach_offset_limit = False
errors = ''  # Used to retrieve error

class DestForm(FlaskForm):
    Destination = StringField('destination', validators=[DataRequired()])
    Add = SubmitField()


@app.route("/", methods=['GET', 'POST'])
def home():
    myForm = DestForm()
    global errors  # Put to False
    if myForm.validate_on_submit():
        entry = myForm.Destination.data.capitalize()
        # TODO check if the city is already here
        if not get_IATA(entry):
            errors = 'city_error'
        else:
            # Limit the number of destination to two for now
            if len(origin_loc) == 2:
                errors = 'max_orig'
                return redirect("/")
            else:
                origin_loc.append(entry)
                print(f'New list of destination {origin_loc}')
                return redirect(url_for('change_orig', value=True))

    # TO DELETE ------------------
    # with open('API_response_multiple.json') as json_data:
    #     data = json.load(json_data)
    # API_destinations = sorting_result(filt_dests(data))
    #------------------------------------------
    return render_template('index.html', cal=month_names, dest=orig_nb, destinations=origin_loc, form=myForm,
                           current_year=datetime.now().year, errors=errors,
                           API_destinations=API_destinations[0:5])


@app.route("/update_period/<month_id>")
def update_period(month_id):
    # Recreate the list via list-comprehension
    global month_names
    month_names = [(m, not v) if m == month_id else (m, v)
                   for m, v in month_names]
    return redirect("/")


@app.route("/change_orig/<value>")
def change_orig(value):
    global orig_nb, errors
    if value == 'True':
        orig_nb += 1
    elif orig_nb > 0:
        orig_nb -= 1
    print(f'Based on :{value} - Nb dest changed:{orig_nb}')
    errors = ''
    return redirect("/")


@app.route("/remove/<dest>")
def remove_orig(dest):
    global origin_loc, errors
    origin_loc.remove(dest)
    print(f'New list of destination {origin_loc}')
    errors = ''
    return redirect(url_for('change_orig', value=False))


@app.route("/search/")
def search_flight():
    # Where the results are going to be stored
    global API_destinations
    API_destinations = []

    # Link the name put in HTML code by the user to IATA for the API request
    IATA_CODE = get_IATA(origin_loc[0])

    # Retrieve the period or research based on HTML interface
    dates = get_period()

    # KIWI API REQUESTS
    flight_info = {
        'fly_from': IATA_CODE,
        'date_from': dates[0],
        'date_to': dates[1],
    }
    # TO uncomment when online request
    # response = requests.get(f'{KIWI_BASE_URL}/search', params=flight_info, headers=KIWI_HEAD)
    # print(response.status_code)

    # Using offline request :
    with open('API_response_multiple.json') as json_data:
        data = json.load(json_data)

    #Use a function to keep only wanted information
    API_destinations = filt_dests(data)
    print(API_destinations[0])

    return redirect("/")


# This function is looping through the list of IATA code returned by the API and return the unique IATA
def get_IATA_online(Test_city):
    global reach_offset_limit, city_found, offset
    while not reach_offset_limit or not city_found:
        IATA_PARAMS = {
            'access_key': IATA_KEY,
            'offset': offset,  # To remove if using premium option search
            # 'search': Test_city
        }
        IATA_RESPONSE = requests.get(f'{IATA_BASE_URL}cities', params=IATA_PARAMS)
        print(f'for offset:{offset} - Code:{IATA_RESPONSE.status_code}')
        try:
            IATA_CITIES = IATA_RESPONSE.json()['data']
        except KeyError:
            return ''
        offset_limit = int(IATA_RESPONSE.json()['pagination']['total'] / 100)  # Used to know the max nb of loop request
        for entry in IATA_CITIES:
            if entry['city_name'] == Test_city:  # City found
                print(entry['iata_code'])
                city_found = True
                return entry['iata_code']

        if not city_found:
            # Try for the next 100 cities
            offset += 100
            if offset > offset_limit:
                reach_offset_limit = True

    return ''

# Check if the IATA code is in the historic file, otherwise check online through API
def get_IATA(city):
    IATA_CODE = ''
    IATA_MEMORY = pd.read_csv('IATA_memory.csv')
    try:
        IATA_CODE = IATA_MEMORY[IATA_MEMORY
            ['City'] == city.capitalize()]['Code'].item()
    except ValueError:
        print('IATA local 404.')
        # TODO Before checking online, verify that the city name exist
        # Looking online
        IATA_CODE = get_IATA_online(city)
        if IATA_CODE != '':
            new_row = pd.DataFrame({'City': [city], 'Code': [IATA_CODE]})
            IATA_MEMORY = pd.concat([IATA_MEMORY, new_row], ignore_index=True)
            IATA_MEMORY.to_csv('IATA_memory.csv')
        else:
            print('IATA 404')
            return False
    return IATA_CODE


# Function to make it compatible and easy to fetch for WEB display
def get_period():
    current_year = date.today().year
    current_month = date.today().month
    date_from = ''
    date_to = ''
    for x in range(current_month - 1, len(month_names)):  # Starting from the current month
        if date_from == '':
            if month_names[x][1]:
                date_from = f'01/{dformat(x + 1)}/{current_year}'
        else:
            if not month_names[x][1]:
                date_to = f'{calendar.monthrange(current_year, x + 1)[1]}/{dformat(x + 1)}/{current_year}'

    if date_to == '':
        for x in range(current_month - 1):
            if not month_names[x][1]:
                date_to = f'{calendar.monthrange(current_year + 1, x)[1]}/{dformat(x)}/{current_year + 1}'
                break
        if date_to == '':
            date_to = f'{calendar.monthrange(current_year + 1, current_month)[1]}/{dformat(current_month)}/{current_year + 1}'

    print(f'date_from:{date_from}, date_to:{date_to}')
    return date_from, date_to


def dformat(x):
    if x < 10:
        x2 = f'0{x}'
    else:
        x2 = x
    return x2


# Format the data retrieved from API into exploitable data
def filt_dests(data):
    all_results = []
    for result in data['data']:
        routes = []
        layover_time = ''
        arrival_time_local = ''  # Used to store the arrival_time from last route of multiple flight
        for flight in result['route']:

            # Extracting the date in the correct format
            depart_time_utc = get_day(flight['utc_departure'])[5]
            DTU = datetime.strptime(f"{depart_time_utc}:00", '%X')
            arrival_time_utc = get_day(flight['utc_arrival'])[5]
            ATU = datetime.strptime(f"{arrival_time_utc}:00", '%X')
            r_duration_temp = str(ATU - DTU)
            r_duration = f'{r_duration_temp[0:len(r_duration_temp) - 6]}h {r_duration_temp[len(r_duration_temp) - 5:len(r_duration_temp) - 3]}m'
            # print(f"{flight['flyFrom']} - {flight['flyTo']}")
            # print(r_duration)

            # Counting layover time
            if arrival_time_local == '':  # First flight
                arrival_time_local = get_day(flight['local_arrival'])[5]
                arrival_time_local = datetime.strptime(f"{arrival_time_local}:00", '%X')
            else:
                depart_time_local = get_day(flight['local_departure'])[5]
                depart_time_local = datetime.strptime(f"{depart_time_local}:00", '%X')
                layover_time = str(arrival_time_local - depart_time_local)
                layover_time = f'{layover_time[0:len(layover_time) - 6]}h {layover_time[len(layover_time) - 5:len(layover_time) - 3]}m'
                # print(layover_time)
                arrival_time_local = get_day(flight['local_arrival'])[5]
                arrival_time_local = datetime.strptime(f"{arrival_time_local}:00", '%X')

            route = {
                'from_airport': flight['flyFrom'],
                'from': flight['cityFrom'],
                'to_airport': flight['flyTo'],
                'to': flight['cityTo'],
                'r_duration': r_duration,
                'dep_date': get_day(flight['local_departure']),
                'ari_date': get_day(flight['local_arrival']),
                'layover': layover_time,
                'airline': flight['airline'],
            }
            routes.append(route)

        multiple_route = False
        if len(routes) > 1:
            multiple_route = True

        date_f = str(timedelta(seconds=result['duration']['total'])),
        if len(date_f[0]) > 10:  # Case where it's more than one day
            # Getting hour and minute from date_f that has a specific format if it is superior that one day
            date_split = date_f[0].split(',')
            time_string_h = date_split[1][1:len(date_split) - 8]
            time_string_m = date_split[1][len(date_split) - 7:len(date_split) - 5]
            duration_trip = f'{date_f[0][:1]}day {time_string_h}h {time_string_m}m'  # What will be display

        else:
            duration_trip = f'{date_f[0][0:2]}h {date_f[0][3:5]}m'

        one_dest = {
            'id': result['id'],
            'from': result['cityFrom'],
            'from_airport': result['flyFrom'],
            'to': result['cityTo'],
            'to_airport': result['flyTo'],
            'price': result['price'],
            'currency': list(result['conversion'].keys())[0],
            'local_departure': result['local_departure'],
            'dep_date': get_day(result['local_departure']),
            'ari_date': get_day(result['local_arrival']),
            'duration': duration_trip,
            'duration_numeric': int(result['duration']['total']),
            'airline': result['airlines'],
            'availability': result['availability']['seats'],
            'route': routes,
            'multiple_route': multiple_route
            # 'link': result['deep_link'],
        }
        all_results.append(one_dest)

    # Removing all the unique values
    all_results_unique = []
    for item in all_results:
        if item not in all_results_unique:
            all_results_unique.append(item)
    return all_results_unique


def sorting_result(all_results_unique, option=0):
    sorted_result = []
    # Most relevant sorting - 2 shortest, 2 cheapest, then in between
    # Weighted Scoring Model - default weight
    w_price = 1
    w_duration = 1
    if option == 0:
        # Assign Weights - Choose weights based on what most important
        pass

    # Normalize the Data - Bring all features (duration, price, layovers) to the same scale (e.g., [0, 1]):
    df_flight = pd.DataFrame(
        [(flight['id'], int(flight['price']), flight['duration_numeric']) for flight in all_results_unique],
        columns=['ID', 'price', 'duration'])
    df_flight['price_norm'] = 1 - (df_flight['price'] / df_flight['price'].max())
    df_flight['duration_norm'] = 1 - (df_flight['duration'] / df_flight['duration'].max())

    # Compute a Score for Each Flight
    df_flight['score'] = df_flight['price_norm'] * w_price + df_flight['duration_norm'] * w_duration
    # Sort flights by score
    df_flight = df_flight.sort_values('score', ascending=False)
    df_flight.to_csv('result_test.csv', index=False)  # Used to check results with Excel

    # Sort input with df
    order_map = {id_val: idx for idx, id_val in enumerate(df_flight["ID"])}
    sorted_result = sorted(all_results_unique, key=lambda x: order_map[x["id"]])

    return sorted_result


# Date Object format [0-Year, 1-Month, 2-Month-name, 3-Day, 4-Day-name, 5-time]
def get_day(input_date):
    datetime_object = datetime.strptime(
        f"{input_date[:4]}-{input_date[5:7]}-{input_date[8:10]}",
        "%Y-%m-%d").date()
    date_object = [input_date[:4], input_date[5:7], datetime_object.strftime("%b"), input_date[8:10], datetime_object.strftime("%a"),
                   input_date[11:16]]
    return date_object


if __name__ == '__main__':
    app.run()
