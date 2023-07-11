#!/usr/bin/python 
from azure.storage.blob import BlobServiceClient
import json
import time
import base64
import asyncio
import nest_asyncio
nest_asyncio.apply()
import datetime #for checking today date with last updated data

#----SMS----
import os
account_sid = os.environ['TWILIO_ACCOUNT_SID'] = 'AC5be539af0d1732c7ced2aa718f217c8d'
auth_token = os.environ['TWILIO_AUTH_TOKEN'] = "2a660528a50340e1ae2de393536db5a4"
from twilio.rest import Client
client = Client(account_sid, auth_token)
#--------------------------------------------------------------BLOB ACCESSING
connect_str = "DefaultEndpointsProtocol=https;AccountName=binboys0storage;AccountKey=eO82ex6Fxz4vFtw6N6ySWz5CG6/92xVMH5K/3t/H70+NTUQeHzelsXrhiCGX4hMhnWndo7SKUyCD+AStUrk5Mg==;EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container = "binsdata"
containerClient = blob_service_client.get_container_client(container=container)
#------------------------------------
streetData = {
    "street1":{9398977650:['d1']},
    "street2":{9381767446:['d2']}
    }
#final dictionary for last value getting

outData = {}
#------------------------------------
print("\nListing blobs...")
blob_list = containerClient.list_blobs()
#------------------------------------
async def message_sender(phno,deviceId,fill_percent):
    print(deviceId,"-->",phno)
    message = client.messages \
        .create(
             body= "\n------------------\nDustbin Id: "+deviceId+"\nFill percent: "+str(fill_percent)+"\n------------------",
             from_ =  "+15854886273",
             to = "+91"+str(phno)
         )
    print("Message Id:",message.sid)
    return
#-----------------------------------
async def read(deviceId,fill_percent,date):
    for i,j in streetData.items():
        for k,l in j.items():
            if deviceId in l:
                phno = k
    #print(phno)
    outData[deviceId] = {date:fill_percent,"contact":phno}
    return

#-----------------------------------
lastUpdate = open("lastValues.txt","r")
print(lastUpdate.read())
print(type(lastUpdate.read()))
lastValues = json.loads()
lastUpdate.close()
#-----------------------------------
#lastValues = {'d18':0,'d31':0}
async def readBlobs():
    blob_list = containerClient.list_blobs()
    for blob in blob_list:
        #-----------------------
        arr = blob.name.split("/")
        date = arr[4] #date index in blob path name (seen from documentation)
        todayDate = datetime.datetime.now().day
        #---
        dustbin = arr[1]
        #---
        #[*******reading only today's and latest files**********]
        if int(date) == todayDate and int(arr[-3])>int(lastValues["d"+str(dustbin)]):
            #---
            lastValues["d"+str(dustbin)] = arr[-3]
            #---
            print(blob.name)
            #-----------------------
            data = str(containerClient.download_blob(blob.name).readall(),'utf-8')
            i = data.strip().split("\n")
            for j in i:
                j = json.loads(j)
                #print(j['deviceId']," = Fill percent: ",j['telemetry']['fill_percent'],"%")
                asyncio.run(read(j['deviceId'],j['telemetry']['fill_percent'],date))
while(True):
    #time.sleep() #seconds
    asyncio.run(readBlobs())
    #-----------------------------------
    lastUpdate = open("lastValues.txt","w")
    lastUpdate.write(str(lastValues))
    lastUpdate.close()
    #-----------------------------------
    print("Today Updated data: ",outData)
    #Now data Format = {'d1': {'09': 83, 'contact': 9398977650}, 'd2': {'09': 82, 'contact': 9381767446}}
    count =0
    for i,j in outData.items():
        contact = j['contact']
        for k,l in j.items():
            todayDate = datetime.datetime.now().day #for getting today date
            file = open("file_log.txt","a")
            file.writelines(str(count)+". "+str(datetime.datetime.now())+"\n")
            file.close()
            if int(k) == todayDate:
                if(l>80): #sends message if >80% dust
                    asyncio.run(message_sender(contact,i,l))
            break

