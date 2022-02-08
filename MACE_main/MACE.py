#!/usr/bin/env python3
from genericpath import exists
import json
from pickle import TRUE
import time
import sys
from os.path import dirname, join, abspath
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import Alarm.Alarm_H as handler
import Control.Alarm_Control as ctrl
import Monitor.Monitoring_Unit as mon
import epics
import redis
import threading
import Confjson.load_config as cnfg
        
def MACE():
    #Starting script:
    print("Initializing settings...\n")
    time.sleep(1)
       
    #opening configuration file:
    with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as db_json:
        json_object=json.load(db_json)
    time.sleep(1)

    #Initializing array with threads
    threads=[]

    #Redis configuration variables
    redis_host=json_object["Credentials"]["redis_ip"]
    redis_port=json_object["Credentials"]["redis_port"]
    redis_db=json_object["Credentials"]["redis_db_no"]

    #Defining redis object
    redb=redis.Redis(redis_host,redis_port,redis_db)
    
    
    try:
        
        stop=False

        epics.ca.use_initial_context()
        
        #Executing essential modules:
        x = epics.ca.CAThread(target=mon.TempMonitoring1,args=(lambda: stop,), name='Monitoring_Unit')
        x.daemon=True
        threads.append(x)

        y = threading.Thread(target=ctrl.Control,args=(lambda: stop,), name='Control')
        y.daemon=True
        threads.append(y)

        z = threading.Thread(target=handler.AlarmMonitoring,args=(lambda: stop,), name='AlarmMonitoring')
        z.daemon=True
        threads.append(z)

        #Starting threads
        for i in threads:
            i.start()
            print("Starting "+str(i.name)+".\n")

        while(True):
            mace_stop=json.loads(redb.get('Variables').decode('utf-8'))
            
            
            #reddata2=json.loads(reddata1)
            #data=json.loads(reddata2)

            time.sleep(1)
            if mace_stop['stopvar']==1:
               raise KeyboardInterrupt
               
    except:
        
        #Starting main thread finishing
        print('\nSending STOP signal')
        
        #Stopping threads
        stop=True
        time.sleep(0.5)
        
        with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json",'r') as dataend:
            data=json.load(dataend)

        #Making sure that code does not start automatically when GUI starts.
        data['Variables']['stopvar']=1
        

        with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json",'w') as dataend:
            json.dump(data,dataend,indent=1)

        #Waiting for dump to take place:
        time.sleep(1)
        print('Main finishing execution')

        #System exit:
        sys.exit()


    
    
