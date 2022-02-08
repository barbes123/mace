
from ppadb.client import Client as AdbClient
#sudo adb start-server
from influxdb import InfluxDBClient
from epics import caput,caget
import json
from datetime import datetime, timedelta, time
import smtplib
import time
import redis

#opening json config file
with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as json_config:
    json_data=json.load(json_config)

#Defining connection to redis
redis_host=json_data["Credentials"]["redis_ip"]
redis_port=json_data["Credentials"]["redis_port"]
redis_db=json_data["Credentials"]["redis_db_no"]

redb=redis.Redis(redis_host,redis_port,redis_db)

#Phone number list:
phonearray=json_data['Credentials']['phonearray']

#Email addreses list:
emailarray=json_data['Credentials']['emails']

#HV Source Serial Number Address for EPICS:
epicsaddress =json_data['cntrllrs']['CAEN_HV']['epicsnumber']

#Set your ip and port here for InfluxDB to pick up:
inf_db_ip=json_data['Credentials']['ip']
inf_db_port=json_data['Credentials']['influx_port']

#Influx Database name:
inf_db=json_data['Credentials']['influx_db_name']

#Influx Measurement name:
inf_msr=json_data['Credentials']['influx_measurement_name']


#Function that records entries into InfluxDB table (alarm type and id of the detector):
def influx(altype,iddet):
    #Defining InfluxDB client object
    client=InfluxDBClient(host=inf_db_ip,port=inf_db_port,database=inf_db)
     
    #Recording time of function execution for entry:
    timeset= datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
     
    #Creating json table entry object:
    json_body = [
        {
            "measurement": inf_msr,
            "time": timeset,
            "fields": {
                "type":altype,
                "detno":iddet,
            }
        }]

    #Writing entry into InfluxDB table:
    client.write_points(json_body)
    time.sleep(1)

#Shut down Voltage function:
def ShutDownVoltage(id):
    #Initializing lists that will work with the alarm functions:
    slotarr=[]
    sdcharr=[]
    #Load json main configuration file:
    datadetcnfg=json.loads(redb.get('Detectors_config').decode("utf-8"))

    #Loading lists with variables from the data structure:
    for detector,values in datadetcnfg.items():
        
        sdcharraux=[]
        a=[x-1 for x in datadetcnfg[detector]['AssignedChnls']]
        for unit in a:
            sdcharraux.append(str(unit).zfill(3))
        sdcharr.append(sdcharraux)
        slotarr.append(str(datadetcnfg[detector]['HVSlot']).zfill(2))

    if 0 and sdcharr and slotarr:
        index=int(id)-1
        for sdch in sdcharr[index]:
            try:
                caput(epicsaddress+':'+str(slotarr[index])+':'+str(sdch)+':Pw',0)
            except:
                pass
            
    print("Shd "+str(id))
    influx("ShutDownVoltage",str(id))
    
    

#Send Email function:
def SendEmail(id):
    if(0):
        EMAIL_ADDRESS=json_data["Credentials"]["email_sender"]
        EMAIL_PASSWORD=json_data["Credentials"]["password_sender"]

        with smtplib.SMTP('smtp.gmail.com',587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()

            smtp.login(EMAIL_ADDRESS,EMAIL_PASSWORD)

            subject='Alarm State 1 triggered on '+str(id)+'!'
            body='This is an automatic message part of the MACE program of ELI-NP. \nLevel 1 alarm has been triggered on Detector '+str(id)+'!'
            
            msg=f'Subject:{subject}\n\n{body}'

            for email in emailarray:
                smtp.sendmail(EMAIL_ADDRESS,email,msg)
                time.sleep(0.5)

    print("Email "+str(id))
    influx("SendEmail",str(id))
    
    
def AlarmCall(id):
    
    if(0):
        client=AdbClient(host="127.0.0.1", port=5037)
        
        devices=client.devices()
    
        if len(devices)==0:
            quit()

    
    if phonearray:
        for phone in phonearray:
            
            #os.system(f'adb shell am start -a android.intent.action.CALL -d tel:{phone}')
            pass
    
    print("Call "+str(id))
    influx("Call",str(id))
    
    

#Trigger Filling Function:
def TriggerFilling(id):

    #Recording current time
    timefill=datetime.now()
    
    #execute filling code
    #Load json main configuration file:
    datafill=json.loads(redb.get('Filling_Time').decode("utf-8"))

    with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata:
        jsondata_obj=json.load(jsondata)

    #Comparing with last fill:
    
    if timefill>=datetime.strptime(datafill['Detector '+str(id)],'%Y-%m-%d %H:%M:%S.%f')+timedelta(minutes=jsondata_obj["Detectors_Alarms"]['Alarm_Actions']["filling_pause (min)"]):
        
        jsondata_obj['Filling_Time']['Detector '+str(id)]=str(timefill)

        with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata:
           json.dump(jsondata_obj,jsondata,indent=1)

        datafill['Detector '+str(id)]=str(timefill)

        redb.watch("Filling_Time")
        redjson=json.dumps(datafill,ensure_ascii=False).encode('utf-8')
        redb.set('Filling_Time',redjson)
        
        #enter filling code here.

        print("Filling "+str(id))
        influx("Filling",str(id))
        
    else:
        pass
    
    
    




