

#!/usr/bin/env python3

import json
import redis




def ldcnfg():
    try:
        with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as dbset:
            json_obj=json.load(dbset)

        host=json_obj["Credentials"]["redis_ip"]
        port=json_obj["Credentials"]["redis_port"]
        db=json_obj["Credentials"]["redis_db_no"]

        redb=redis.Redis(host,port,db)
            
        with redb.pipeline() as pipe:
            pipe.multi()
            detcnfg=json.dumps(json_obj["Detectors_config"],ensure_ascii=False).encode('utf-8')
            cred=json.dumps(json_obj["Credentials"],ensure_ascii=False).encode('utf-8')
            detal=json.dumps(json_obj["Detectors_Alarms"],ensure_ascii=False).encode('utf-8')
            var=json.dumps(json_obj["Variables"],ensure_ascii=False).encode('utf-8')
            datamon=json.dumps(json_obj["Monitoring_Data"],ensure_ascii=False).encode('utf-8')
            cntrl=json.dumps(json_obj["cntrllrs"],ensure_ascii=False).encode('utf-8')
            pvch=json.dumps(json_obj["PV_channels"],ensure_ascii=False).encode('utf-8')
            fillt=json.dumps(json_obj["Filling_Time"],ensure_ascii=False).encode('utf-8')

            pipe.set("Detectors_Config",detcnfg)
            
            pipe.set("Credentials",cred)
            
            pipe.set("Detectors_Alarms",detal)
            
            pipe.set("Variables",var)
            
            pipe.set("Monitoring_Data",datamon)
            
            pipe.set("cntrllrs",cntrl)
            
            pipe.set("PV_channels",pvch)
            
            pipe.set("Filling_Time",fillt)
            

            pipe.execute()
            


    except Exception as e:
        print("Error loading config file: "+str(e))

    