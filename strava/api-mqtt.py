#from __future__ import print_statement
import time
import swagger_client
from swagger_client.rest import ApiException
from pprint import pprint
import requests
import datetime
from datetime import datetime, timedelta
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
#token = "847214ca03485a9d6891c7f9848cf084895b66a8"
print("Current Token:")
print(token)
print("Current Refresh Token:")
#print(refreshToken)

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

#Get the count of swims
qcount = 0
for data in list:
        print(data)
        if list[data].get("Type") == "Swim":
            qcount += 1
swimCount = qcount

if swimCount > 0:
    #Swim yards
    swimYards = 0 
    for data in list:
            print(data)
            if list[data].get("Type") == "Swim":
                swimYards += list[data].get("Distance")
    swimYards = round((swimYards * 1.09361), 1 )

    #Swim pace
    def Average(lst): 
        return sum(lst) / len(lst)
    swimPace = []
    for data in list:
            print(data)
            if list[data].get("Type") == "Swim":
                swimPace.append((list[data].get("Average Speed") * 1.0936))
    swimPace = round((Average(swimPace)), 2 )
    tempNum = round((100/swimPace), 2 )
    tempNum = round((tempNum/60), 2 )
    numRight = tempNum.__str__().rsplit(".")[1]
    numLeft = tempNum.__str__().rsplit(".")[0]
    numRight = round(float("." + numRight) * 60)
    swimPace = numLeft + ":" + (int(numRight)).__str__().zfill(2)
    swimPace = str(swimPace) + "/100yd"

    #Swim time
    totalTime = 0 
    for data in list:
            print(data)
            if list[data].get("Type") == "Swim":
                totalTime += list[data].get("Moving Time")
    totalTime = round(((float(totalTime) / 60) / 60) , 2 )
    numRight = totalTime.__str__().rsplit(".")[1]
    numLeft = totalTime.__str__().rsplit(".")[0]
    numRight = round(float("." + numRight) * 60)
    totalSwimTime = numLeft + ":" + (int(numRight)).__str__().zfill(2)
else:
    swimYards = 0
    swimPace = 0
    totalSwimTime = 0

if rideCount > 0:
    #Get the total of ride miles
    rideMiles = 0 
    for data in list:
            print(data)
            if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
                rideMiles += list[data].get("Distance")
    rideMiles = round((rideMiles * 0.00062), 1 )

    #Average Ride speed
    def Average(lst): 
        return sum(lst) / len(lst)
    rideSpeed = []
    for data in list:
            print(data)
            if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
                rideSpeed.append((list[data].get("Average Speed") * 2.2369))
    rideSpeed = round((Average(rideSpeed)), 1 )

    #Ride time
    totalTime = 0 
    for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            totalTime += list[data].get("Moving Time")
    totalTime = round(((float(totalTime) / 60) / 60) , 2 )
    numRight = totalTime.__str__().rsplit(".")[1]
    numLeft = totalTime.__str__().rsplit(".")[0]
    numRight = round(float("." + numRight) * 60)
    totalRideTime = numLeft + ":" + (int(numRight)).__str__().zfill(2)

    #Average Ride watts
    def Average(lst): 
        return sum(lst) / len(lst)
    rideWatts = []
    for data in list:
        print(data)
        if list[data].get("Type") == "VirtualRide" or list[data].get("Type") == "Ride":
            rideWatts.append((list[data].get("Average Watts")))
    rideWatts = round((Average(rideWatts)), 1 )
else:
    rideMiles = 0
    rideSpeed = 0
    totalRideTime = 0

if runCount > 0:
    #Get the total of run miles
    runMiles = 0 
    for data in list:
            print(data)
            if list[data].get("Type") == "Run":
                runMiles += list[data].get("Distance")
    runMiles = round((runMiles * 0.00062), 1 )

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
    runSpeed = numLeft + ":" + (int(numRight)).__str__().zfill(2)

    #Run time
    totalTime = 0 
    for data in list:
            print(data)
            if list[data].get("Type") == "Run":
                totalTime += list[data].get("Moving Time")
    totalTime = round(((float(totalTime) / 60) / 60) , 2 )
    numRight = totalTime.__str__().rsplit(".")[1]
    numLeft = totalTime.__str__().rsplit(".")[0]
    numRight = round(float("." + numRight) * 60)
    totalRunTime = numLeft + ":" + (int(numRight)).__str__().zfill(2)
else:
    runSpeed = 0
    totalRunTime = 0
    runMiles = 0
    
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
totalTime = round(((float(totalTime) / 60) / 60) , 2 )
numRight = totalTime.__str__().rsplit(".")[1]
numLeft = totalTime.__str__().rsplit(".")[0]
numRight = round(float("." + numRight) * 60)
totalTime = numLeft + ":" + (int(numRight)).__str__().zfill(2)

#Active days
activeDays = []
for data in list:
    activeDays.append((list[data].get("Date")).strftime("%a"))

#Total time based on activity

#Fitness and Form
startdate = datetime.today() - timedelta(days=7)
startdateyear = int(startdate.year)
startdatemonth = int(startdate.month).__str__().zfill(2)
startdateday = int(startdate.day).__str__().zfill(2)

currentday = datetime.today()
currentdayyear = currentday.year
currentdaymonth = int(currentday.month).__str__().zfill(2)
currentdayday = int(currentday.day).__str__().zfill(2)

#URL = "https://www.wattsboard.com/users/84827/performance.json?start_date=2021-03-03 00:00:00 UTC\u0026end_date=2021-03-10 23:59:59 UTC"
URL = "https://www.wattsboard.com/users/84827/performance.json?start_date=%s-%s-%s 00:00:00 UTC\u0026end_date=%s-%s-%s 23:59:59 UTC" %(startdateyear, startdatemonth, startdateday, currentdayyear, currentdaymonth, currentdayday)
response = requests.get(URL)
fitness = response.json()[1]['data'][-1][1]
form = response.json()[2]['data'][-1][1]


#Create the list to send to devices/MQTT
summaryList = {"Total Activities": activityCount , "Total Miles": totalMiles , "Total Time": totalTime , "Total Swims": swimCount , "Total Swim Time": totalSwimTime , "Total Swim Yards": swimYards , "Average Swim Pace": swimPace , "Average Ride Speed": rideSpeed , "Average Watts": rideWatts , "Total Rides": rideCount , "Total Ride Miles": rideMiles , "Total Ride Time": totalRideTime , "Average Run Pace": runSpeed , "Total Run Time": totalRunTime , "Total Runs": runCount , "Total Run Miles": runMiles , "Fitness": fitness , "Form": form }

#For devices without network, write directly to it
#with open('E:\stats.json', 'w') as filehandle:
#    for listitem in summaryList:
#        value = summaryList[listitem]
#        line = '%s:%s\n' %(listitem, value)
#        filehandle.write(line)
#filehandle.close()

#Publish to MQTT, retain the message so each run will pull the current stats
returncode = client.publish(secrets["mqtopic"],summaryList.__str__(), retain=True)

#Disconnect from MQTT

#Update token
filehandle = open(secrets["secretspath"], 'r')
#output file to write the result to
#fout = open("c:\\temp\\secrets.py", "wt")
fout = open("/tmp/secrets.py", "wt")
for line in filehandle:
    fout.write(line.replace(secrets["accesstoken"], token))

filehandle.close()
fout.close()

#Get the new temp file and the existing secrets file
#src_file = "C:\\temp\\secrets.py"
src_file = "/tmp/secrets.py"

dest_file = secrets["secretspath"] 

# move method to move the file
shutil.move(src_file,dest_file)
