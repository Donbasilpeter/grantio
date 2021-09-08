from flask import Flask, request, jsonify
import pymongo
import json
import requests
from bson.objectid import ObjectId

# importing the config file data
with open("config.json", "r") as jsonfile:
    config = json.load(jsonfile)

#  setting conncection, Database and table
connection_url = config['connection_url']
client = pymongo.MongoClient(connection_url)
Database = client.get_database(config['database'])
Table = Database[config['table']]

# setting app name
app = Flask(__name__)




# Post api to query forcast using location.saves the data into database
@app.route("/api/location", methods=['POST'])
def location_add():
    try:
        #get data from request which is in json format
        input_data = request.get_json()
        location = input_data['location']
        max_temp = input_data['max']
        min_temp = input_data['min']

        # get forcast from api using location
        api_key = config['api-key']
        days = config['forecast-days']
        api_url = config['weather-api'].format(api_key, location, days)
        response = requests.get(api_url).json()
        dct = {}
        cnt = 1

        #create dict of all future predicts and select data that is only needed
        for i in response['forecast']['forecastday']:
            dct['day' + str(cnt)] = {"date": i['date'], "temp": i['day']['avgtemp_c']}
            cnt += 1
       #strucrure the data to be saved
        data = {
            'max_temp' : max_temp,
            'min_temp' : min_temp,
            'location': location,
            'longitude': response['location']['lon'],
            'latitude': response['location']['lat'],
            'forecast': dct
        }

        #insert into database
        reply = Table.insert_one(data)
        out = {'Status': 'Successfully Inserted',
                  'Document_ID': str(reply.inserted_id)}
        return jsonify(out)
    except :
        return jsonify({'message' : 'error in adding data by location'})

# Post api to query forcast using cordinate, saves the data into database
@app.route("/api/cordinate", methods=['POST'])
def codinatea_add():
    try:
        #get inputs in json format
        input_data = request.get_json()
        cordinates =input_data['latitude'] + "," + input_data['longitude']
        max_temp = input_data['max']
        min_temp = input_data['min']

        # send api using
        api_key = config['api-key']
        days = config['forecast-days']
        api_url = config['weather-api'].format(api_key, cordinates, days)
        response = requests.get(api_url).json()
        dct = {}
        cnt = 1

        #get the needed data and format into a json structure
        for i in response['forecast']['forecastday']:
            dct['day' + str(cnt)] = {"date": i['date'], "temp": i['day']['avgtemp_c']}
            cnt += 1

        #format all data into a specifc format
        data = {
            'max_temp' : max_temp,
            'min_temp' : min_temp,
            'location': response['location']['name'],
            'longitude': input_data['longitude'],
            'latitude': input_data['latitude'],
            'forecast': dct
        }

        #save the data into the database
        reply = Table.insert_one(data)
        out = {'Status': 'Successfully Inserted',
                  'Document_ID': str(reply.inserted_id)}
        return jsonify(out)
    except :
        return jsonify({'message': 'error in adding data by cordinates'})



#reset all the data in the database
@app.route("/api/reset", methods=['GET'])
def remove_all():
    try:
        reply = Table.remove()
        out = {'Status': 'Successfully reset database',
               }
        return jsonify(out)
    except:
        return jsonify({'message': 'error in reseting database'})


#get specific data from the database using the object id and return it as a json response
@app.route("/api/data", methods=['POST'])
def data_by_id():
    try:
        _id = request.get_json()['Document_ID']
        out = [i for i in Table.find({"_id": ObjectId(_id)},{'_id': False})]
        return jsonify(out[0])
    except:
        return jsonify({'message': 'error in adding data accessing'})


#remove a specific data from database using object id
@app.route("/api/delete", methods=['POST'])
def remove_one():
    try:

        _id = request.get_json()['Document_ID']
        out =  Table.delete_one({"_id": ObjectId(_id)})
        out = {'Status': 'Successfully removed the data by given id',
               }
        return jsonify(out)
    except:
        return jsonify({'message': 'error in deleting data by id'})

#update the cordinates of a particular place.all colloction record with given location will be updated with given cordinates
@app.route("/api/update", methods=['POST'])
def update_cordinates():
    try:
        data = request.get_json()
        myquery = {"location": data['location']}
        newvalues = {"$set": {"longitude": data['longitude'], "latitude" : data['latitude'] }}
        x = Table.update_many(myquery, newvalues)
        out = {'Status': 'Successfully updated the coordinates',
               }
        return jsonify(out)
    except:
        return jsonify({'message': 'error in updating cordinates'})


if __name__ == '__main__':
    app.run(debug=True)
