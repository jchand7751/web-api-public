#from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
import requests
import datetime
import paho.mqtt.client as mqtt
import shutil
from secrets import secrets

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.subscribe(channelSubs)

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def on_publish(client,userdata,result):             #create function for callback
    print("data published \n")
    pass

#current access token
tokenURL="https://www.strava.com/api/v3/oauth/token"

jsonPostData = {'client_id': secrets["clientid"], 'client_secret': secrets["clientsecret"], 'grant_type': 'refresh_token', 'refresh_token': secrets["refreshtoken"]}
x = requests.post(tokenURL, data = jsonPostData)
token = x.json().get("access_token")
refreshToken = x.json().get("refresh_token")
print("Current Token:")
print(token)
print("Current Refresh Token:")
print(refreshToken)

### MQTT Setup ###

mqttServer = secrets["broker"]
mqttPort = secrets["mqport"]
channelSubs="#"

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.on_publish = on_publish
client.username_pw_set(secrets["user"], password=secrets["pass"])
client.connect(mqttServer,mqttPort, 60)

#Get epoch time for a week ago
now = round(time.time())
aweek = 60 * 60 * 24 * 7
weekAgo = now - aweek

#Do the swagger stuff
configuration = swagger_client.Configuration()
configuration.access_token = token
api_instance = swagger_client.ActivitiesApi(swagger_client.ApiClient(configuration))

after = weekAgo # int | An epoch timestamp to use for filtering activities that have taken place after a certain time. (optional)

#Call the API for the logged in athelete's activities
api_response = api_instance.get_logged_in_athlete_activities(after=after)

#Create our list
list = {}

#Take the API response and just get the stuff we want
count = 0
for i in api_response:
    activitynum = "activity" + count.__str__()
    print(i.type)
    activity = {"Date": i.start_date_local , "Type": i.type , "Name": i.name , "Average Speed": i.average_speed , "Average Watts": i.average_watts , "Weighted Average Watts": i.weighted_average_watts , "Distance": i.distance , "Elevation Gain": i.total_elevation_gain , "Moving Time": i.moving_time }
    list[activitynum] = activity
    count += 1
else:
    pass

### Maths ###
#All the data cleanup happens here

#Get the count of activities
activityCount = len(list)

#Get the count of rides
qcount = 0
for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            qcount += 1
rideCount = qcount

#Get the count of runs
qcount = 0
for data in list:
        print(data)
        if list[data].get("Type") == "Run":
            qcount += 1
runCount = qcount

#Get the total of ride miles
rideMiles = 0 
for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            rideMiles += list[data].get("Distance")
rideMiles = round((rideMiles * 0.00062), 1 )

#Get the total of run miles
runMiles = 0 
for data in list:
        print(data)
        if list[data].get("Type") == "Run":
            runMiles += list[data].get("Distance")
runMiles = round((runMiles * 0.00062), 1 )

#Average Ride speed
def Average(lst): 
    return sum(lst) / len(lst)
rideSpeed = []
for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            rideSpeed.append((list[data].get("Average Speed") * 2.2369))
rideSpeed = round((Average(rideSpeed)), 1 )

#Average Run pace
def Average(lst): 
    return sum(lst) / len(lst)
runSpeed = []
for data in list:
        print(data)
        if list[data].get("Type") == "Run":
            runSpeed.append((list[data].get("Average Speed") * 2.2369))
runSpeed = round((Average(runSpeed)), 1 )
tempNum = round((60/runSpeed), 2 )
numRight = tempNum.__str__().rsplit(".")[1]
numLeft = tempNum.__str__().rsplit(".")[0]
numRight = round(float("." + numRight) * 60)
runSpeed = numLeft + ":" + numRight.__str__().zfill(2)

#Average Ride watts
def Average(lst): 
    return sum(lst) / len(lst)
rideWatts = []
for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            rideWatts.append((list[data].get("Average Watts")))
rideWatts = round((Average(rideWatts)), 1 )

#Total distance
totalMiles = 0 
for data in list:
        print(data)
        totalMiles += list[data].get("Distance")
totalMiles = round((totalMiles * 0.00062), 1 )

#Total time
totalTime = 0 
for data in list:
        print(data)
        totalTime += list[data].get("Moving Time")
totalTime = round(((totalTime / 60) / 60) , 2 )
numRight = totalTime.__str__().rsplit(".")[1]
numLeft = totalTime.__str__().rsplit(".")[0]
numRight = round(float("." + numRight) * 60)
totalTime = numLeft + ":" + numRight.__str__().zfill(2)

#Active days
activeDays = []
for data in list:
    activeDays.append((list[data].get("Date")).strftime("%a"))

#Total time based on activity

#Create the list to send to devices/MQTT
summaryList = {"Total Activities": activityCount , "Total Miles": totalMiles , "Total Time": totalTime , "Average Ride Speed": rideSpeed , "Average Watts": rideWatts , "Total Rides": rideCount , "Total Ride Miles": rideMiles , "Average Run Pace": runSpeed , "Total Runs": runCount , "Total Run Miles": runMiles }

#For devices without network, write directly to it
with open('E:\stats.json', 'w') as filehandle:
    for listitem in summaryList:
        value = summaryList[listitem]
        line = '%s:%s\n' %(listitem, value)
        filehandle.write(line)
filehandle.close()

#Publish to MQTT, retain the message so each run will pull the current stats
returncode = client.publish(secrets["mqtopic"],summaryList.__str__(), retain=True)

#Disconnect from MQTT

#Update token
filehandle = open(secrets["secretspath"], 'r')
#output file to write the result to
fout = open("c:\\temp\\secrets.py", "wt")
for line in filehandle:
    fout.write(line.replace(secrets["accesstoken"], token))

filehandle.close()
fout.close()

#Get the new temp file and the existing secrets file
src_file = "C:\\temp\\secrets.py" 
dest_file = secrets["secretspath"] 

# move method to move the file
shutil.move(src_file,dest_file)