#!/usr/bin/env python3
from epics import PV
import redis
import json
import time
from datetime import datetime

#opening configuration file:
with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as db_json:
    json_object=json.load(db_json)

#Redis configuration variables
redis_host=json_object["Credentials"]["redis_ip"]
redis_port=json_object["Credentials"]["redis_port"]
redis_db=json_object["Credentials"]["redis_db_no"]

#Defining redis object
redb=redis.Redis(redis_host,redis_port,redis_db)

crio=json_object["cntrllrs"]["LN2"]["chosen_cRio"]


#Function used for testing
def TempMonitoring1(stop):
    inc=0
    for i in range(2):
        while(inc <97):
            now=datetime.now()
            timeset=now.strftime("%H:%M:%S")
            inc+=1
            time.sleep(2)
            #Epics importing data into local array:
            #DetTempValues=caget('172.18.4.108:EpicsLibrary:DetTempValues.VAL')
            
            with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/MACE_test.json","r") as testfile:
                json_obj=json.load(testfile)
            
            data=json.loads(redb.get('Monitoring_Data').decode('utf-8'))
           

            #Changing data structure variables with local array values:
            for val in range(len(data['CurrentTemp'])):
                data['CurrentTemp'][val]=json_obj['8det'][str(inc)][val]
                #str(DetTempValues[val])
            redb.watch("Monitoring_Data")
            redjson=json.dumps(data,ensure_ascii=False).encode('utf-8')
            redb.set('Monitoring_Data',redjson)
            print(str(timeset)+" "+str(json_obj['8det'][str(inc)])+"\n")
            
            if stop():
                
                print('Stopping Monitoring Unit')
                break
        while(inc >1):
            inc-=1
            time.sleep(2)
            #Epics importing data into local array:
            #DetTempValues=caget('172.18.4.108:EpicsLibrary:DetTempValues.VAL')
            
            with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/MACE_test.json","r") as testfile:
                json_obj=json.load(testfile)
            
            data=json.loads(redb.get('Monitoring_Data').decode('utf-8'))

            #Changing data structure variables with local array values:
            for val in range(len(data['CurrentTemp'])):
                data['CurrentTemp'][val]=json_obj['8det'][str(inc)][val]
                #str(DetTempValues[val])
            redb.watch("Monitoring_Data")
            redjson=json.dumps(data,ensure_ascii=False).encode('utf-8')
            redb.set('Monitoring_Data',redjson)
            print(str(timeset)+" "+str(json_obj['8det'][str(inc)])+"\n")
            
            if stop():
                
                print('Stopping Monitoring Unit')
                break
       
#Real data function
def TempMonitoring(stop):
    
    inMemDb=redb.exists('Detectors_Alarms')
    try:
        if(inMemDb):
            chnlsCreated=False 
            while(True):
                time.sleep(2)
                if not chnlsCreated:
                    global crio
                    channels=json.loads(redb.get("PV_channels").decode("utf-8"))
                    cntrllrs = json.loads(redb.get("cntrllrs").decode("utf-8"))
                    data_mon=json.loads(redb.get("Monitoring_Data").decode("utf-8"))
                    #pvs = [PV(cntrllrs["LN2"][str(crio)] + ':' + channels["Channels2Monitor"][key]) for key in channels["Channels2Monitor"]]
                    chnlsCreated=True

                    #Epics importing data into local array:
                     
                    DetTempValues=PV(cntrllrs['LN2'][str(crio)]+":"+channels["Channels2Monitor"]["TempChnl"])
                    CurrentSystemState=PV(cntrllrs['LN2'][str(crio)]+":"+channels["Channels2Monitor"]["SystemState"])
                    CurrentControlState=PV(cntrllrs['LN2'][str(crio)]+":"+channels["Channels2Monitor"]["ControlState"])
                    NextFill=PV(cntrllrs['LN2'][str(crio)]+":"+channels["Channels2Monitor"]["NextFill"])
                try:
                    #(DetTempValues, ValvTempValues, data_mon['CurrentSystemState'], data_mon['CurrentControlState'], data_mon['NextFill']) = [p.get() for p in pvs]
                    data_mon['CurrentSystemState']=CurrentSystemState.get()
                    data_mon['CurrentControlState']=CurrentControlState.get()
                    data_mon['NextFill']=NextFill.get()
                    
                    print(list(DetTempValues.get()))
                     #Changing data structure variables with local array values:
                    
                    for val in range(len(data_mon["CurrentTemp"])):
                        data_mon['CurrentTemp'][val]=str(list(DetTempValues.get())[val])

                    
                    redb.watch("Monitoring_Data")
                    redjson=json.dumps(data_mon,ensure_ascii=False).encode('utf-8')
                    redb.set('Monitoring_Data',redjson)   

                    #if data['Variables']['stopvar']==1:
                        #stop=1
                    if stop():
                        print('Stopping Monitoring Unit')
                        break
                except:
                    chnlsCreated=False
        
        else:
            print("No InMemDB.")
    except Exception as e:
        print("Failed to get data. Reason: "+str(e))

    print("Finishing TempMonitoring.")
    



        
    
    

        

        
