#!/usr/bin/env python3

from posixpath import abspath, dirname, join
from flask import Flask, render_template,request,g,redirect,session,url_for,make_response,request,jsonify
import json
import os
from influxdb import InfluxDBClient
from datetime import datetime
import sys
sys.path.insert(0, abspath(join(dirname(__file__), '..')))
import MACE_main.MACE as mace
import gui_scripts.Validate as val
import threading
import redis
import Confjson.load_config as cnfg
import time


def GUI():
    with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json",'r') as dbjson:
        data_dbjson=json.load(dbjson)

    redis_host='localhost'
    host=data_dbjson["Credentials"]["ip"]
    port=data_dbjson["Credentials"]["redis_port"]
    redis_db=data_dbjson["Credentials"]["redis_db_no"]
    influx_db=data_dbjson["Credentials"]["influx_db_name"]
    influx_port=data_dbjson["Credentials"]["influx_port"]
    influx_msr=data_dbjson["Credentials"]["influx_measurement_name"]

    redb=redis.Redis(redis_host,port,redis_db)

    cnfg.ldcnfg()
   
    
    #Defining InfluxDB client from server and working database:
    client=InfluxDBClient(host=host,port=influx_port,database=influx_db)

    #Creating Flask back-end for GUI:
    app=Flask(__name__)

    #Creating login page back-end:
    class User:
        def __init__(self,id,username,password):
            self.id=id
            self.username=username
            self.password=password

    users=[]
    users.append(User(id=1,username=data_dbjson["Credentials"]["gui_user"],password=data_dbjson["Credentials"]["gui_password"]))

    app.secret_key=data_dbjson["Credentials"]["gui_password"]


    #Defining request for login:
    @app.before_request
    def before_request():
        g.user=None
        if 'user_id' in session:
            user=[x for x in users if x.id==session['user_id']][0]
            g.user=user

    @app.route('/',methods=['GET','POST'])
    def login():
        if request.method=='POST':
            session.pop('user_id',None)
            username=request.form['username']
            password=request.form['password']

            user=[x for x in users if x.username==username][0]
            if user and user.password==password:
                session['user_id']=user.id
                return redirect(url_for('index'))

            return redirect(url_for('index'))

        return render_template('login.html')

    #Creating Flask GUI back-end main page:
    @app.route('/ELIADE-MACE',methods=['GET','POST'])
    def index():

        #Validation variable that shows if channels are overlapping
        validationvariable=2
        
        #If a button has been pressed:
        if request.method=="POST":

            #Bringing post information to a suitable form:
            reg=request.form
            
            regdict=reg.to_dict()
            regkeys=[]
            for i in regdict.keys():
                regkeys.append(i)
            for i in regkeys:
                print(regkeys[0])
            
            #Checking post information to see what button has been pressed:
            #1. Reset button:
            if 'reset' in regkeys[0]:
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata1:
                    jsonobj1=json.load(jsondata1)
                #Opening json working file:
                detaldata=json.loads(redb.get('Detectors_Alarms').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #detaldata=json.loads(reddata2)


                #Setting corresponding alarm levels and trigger counters to 0:
                detaldata['Detector '+str(regdict['reset'][5])]['AlarmLevel']=0
                jsonobj1['Detectors_Alarms']['Detector '+str(regdict['reset'][5])]['AlarmLevel']=0
                for trigger in range(len(detaldata['triggerlist'][int(reg['reset'][5])-1])):
                    detaldata['triggerlist'][int(regdict['reset'][5])-1][trigger]=0
                    jsonobj1['Variables']['triggerlist'][int(regdict['reset'][5])-1][trigger]=0
                
                detaldata['alarmlvllist'][int(regdict['reset'][5])-1]=0
                jsonobj1['Variables']['alarmlvllist'][int(regdict['reset'][5])-1]=0
                
                #Dumping changes into json working file:
                redb.watch("Detectors_Alarms")
                redjson=json.dumps(detaldata,ensure_ascii=False).encode('utf-8')
                redb.set('Detectors_Alarms',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata1:
                    json.dump(jsonobj1,jsondata1,indent=1)

            #2. Set Map button:       
            elif 'CHNLS' in regkeys[0]:
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata2:
                    jsonobj2=json.load(jsondata2)
                #Records detector:
                detchosen=regkeys[0]

                #Loads settings json file to record into main configuration:
                detcnfgdata=json.loads(redb.get('Detectors_config').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #detcnfgdata=json.loads(reddata2)
                
                #If erase option has been entered:
                if regdict[str(detchosen)]=='null':
                    detcnfgdata['Detector '+str(detchosen[-1])]['AssignedChnls']=[]
                    detcnfgdata['Detector '+str(detchosen[-1])]['HVSlot']=0
                    jsonobj2['Detectors_config']['Detector '+str(detchosen[-1])]['AssignedChnls']=[]
                    jsonobj2['Detectors_config']['Detector '+str(detchosen[-1])]['HVSlot']=0
                else:
                    #Else input is converted into suitable form and recorded in the data structure:
                    #Recording slot,channels
                    chnlarray=request.form[str(detchosen)].split(",")
                    for z in range(len(chnlarray)):
                        chnlarray[z]=int(chnlarray[z])
                    
                    #Iterating through detectors and changing only on chosen detector:
                    for detector,attrs in detcnfgdata.items():
                        if detchosen[-1] in detector[-1]:
                            attrs['HVSlot']=chnlarray[0]
                            attrs['AssignedChnls']=chnlarray[1:]

                    for detector,attrs in jsonobj2["Detectors_config"].items():
                        if detchosen[-1] in detector[-1]:
                            attrs['HVSlot']=chnlarray[0]
                            attrs['AssignedChnls']=chnlarray[1:]

                #Dumping data structure into main configuration json file:     
                redb.watch("Detectors_config")   
                redjson=json.dumps(detcnfgdata,ensure_ascii=False).encode('utf-8')
                redb.set('Detectors_config',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata2:
                    json.dump(jsonobj2,jsondata2,indent=1)

            #3. Activate button (MonVar):
            elif 'actmon' in regkeys[0]:
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata3:
                    jsonobj3=json.load(jsondata3)
                #Recording detector:
                detchosen=regkeys[0]

                #Opening main json settings file:
                detcnfgdata=json.loads(redb.get('Detectors_config').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #detcnfgdata=json.loads(reddata2)

                #Executing changes:
                detcnfgdata['Detector '+str(detchosen[-1])]['MonVar']=1
                jsonobj3["Detectors_config"]['Detector '+str(detchosen[-1])]['MonVar']=1

                #Dumping changes into json configuration file:
                redb.watch("Detectors_config")
                redjson=json.dumps(detcnfgdata,ensure_ascii=False).encode('utf-8')
                redb.set('Detectors_config',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata3:
                    json.dump(jsonobj3,jsondata3,indent=1)
            
            #4. Disable button (MonVar):
            elif 'dismon' in regkeys[0]:
                #Recording detector:
                detchosen=regkeys[0]
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata4:
                    jsonobj4=json.load(jsondata4)
                #Opening json configuration file:
                detcnfgdata=json.loads(redb.get('Detectors_config').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #detcnfgdata=json.loads(reddata2)

                #Executing changes:
                detcnfgdata['Detector '+str(detchosen[-1])]['MonVar']=0
                jsonobj4["Detectors_config"]['Detector '+str(detchosen[-1])]['MonVar']=0

                #Dumping changes into json configuration file:
                redb.watch("Detectors_config")
                redjson=json.dumps(detcnfgdata,ensure_ascii=False).encode('utf-8')
                redb.set('Detectors_config',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata4:
                    json.dump(jsonobj4,jsondata4,indent=1)
            
            #5. Set Parameters button (For condition alarming intervals):
            elif 'limits' in regkeys[0]:

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata5:
                    jsonobj5=json.load(jsondata5)

                #Recording detector:
                detchosen=regkeys[0]
                
                #Opening json configuration file:
                detcnfgdata=json.loads(redb.get('Detectors_config').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #detcnfgdata=json.loads(reddata2)

                #Converting to desired format:
                regdict['limitsC1'+str(detchosen[-1])]=regdict['limitsC1'+str(detchosen[-1])].split(",")
                regdict['limitsC2'+str(detchosen[-1])]=regdict['limitsC2'+str(detchosen[-1])].split(",")
                regdict['limitsC3'+str(detchosen[-1])]=regdict['limitsC3'+str(detchosen[-1])].split(",")
                regdict['limitsC4'+str(detchosen[-1])]=regdict['limitsC4'+str(detchosen[-1])].split(",")
                

                #Changing variables in data structure:
                detcnfgdata['Detector '+str(detchosen[-1])]['Condition 1']=regdict['limitsC1'+str(detchosen[-1])]
                detcnfgdata['Detector '+str(detchosen[-1])]['Condition 2']=regdict['limitsC2'+str(detchosen[-1])]
                detcnfgdata['Detector '+str(detchosen[-1])]['Condition 3']=regdict['limitsC3'+str(detchosen[-1])]
                detcnfgdata['Detector '+str(detchosen[-1])]['Condition 4']=regdict['limitsC4'+str(detchosen[-1])]

                jsonobj5['Detectors_config']['Detector '+str(detchosen[-1])]['Condition 1']=regdict['limitsC1'+str(detchosen[-1])]
                jsonobj5['Detectors_config']['Detector '+str(detchosen[-1])]['Condition 2']=regdict['limitsC2'+str(detchosen[-1])]
                jsonobj5['Detectors_config']['Detector '+str(detchosen[-1])]['Condition 3']=regdict['limitsC3'+str(detchosen[-1])]
                jsonobj5['Detectors_config']['Detector '+str(detchosen[-1])]['Condition 4']=regdict['limitsC4'+str(detchosen[-1])]

                #Dumping changes into configuration file:
                redb.watch("Detectors_config")
                redjson=json.dumps(detcnfgdata,ensure_ascii=False).encode('utf-8')
                redb.set('Detectors_config',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata5:
                    json.dump(jsonobj5,jsondata5,indent=1)

            #6. Start button:
            elif 'Start' in regkeys[0]:
                cnfg.ldcnfg()
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata6:
                    jsonobj6=json.load(jsondata6)

                datavar=json.loads(redb.get('Variables').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #datavar=json.loads(reddata2)
                
                #Defining MACE.py thread to run in parallel with GUI.py
                x=threading.Thread(target=mace.MACE,name='MACE-MAIN')
                
                #Setting activation variables:
                
                datavar['stopvar']=0

                
                jsonobj6['Variables']['stopvar']=0

                #Dumping changes into working json file:
                redb.watch("Variables")
                redjson=json.dumps(datavar,ensure_ascii=False).encode('utf-8')
                redb.set('Variables',redjson)

                #Starting MACE.py thread in parallel with GUI.py:
                x.start()

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata6:
                    json.dump(jsonobj6,jsondata6,indent=1)
                
            #7. Stop button:
            elif 'Stop' in regkeys[0]:

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata7:
                    jsonobj7=json.load(jsondata7)

                #Loading working json file:
                datavar=json.loads(redb.get('Variables').decode('utf-8'))
                #reddata2=json.loads(reddata1)
                #datavar=json.loads(reddata2)

                #Setting stop variables:
                datavar['stopvar']=1
                

                jsonobj7['Variables']['stopvar']=1
                

                #Dumping changes into working json file:
                redb.watch("Variables")
                redjson=json.dumps(datavar,ensure_ascii=False).encode('utf-8')
                redb.set('Variables',redjson)

                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","w") as jsondata7:
                    json.dump(jsonobj7,jsondata7,indent=1)
                
                
                time.sleep(1)
                cnfg.ldcnfg()
                
                
            
            #8. Validate mapping button:
            elif 'Validate' in regkeys[0]:

                #Loading settings json file:
                with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as jsondata8:
                    jsonobj8=json.load(jsondata8)

                #Recording output from gui_scripts/Validate.py script that has been imported:
                condition=val.Validate(jsonobj8)

                #If the condition is true, then validation is succesful, if not, it failed. Data is recorded in a variable for jinja2 to compile in html. 
                if condition:
                    validationvariable=1
                else:
                    validationvariable=0

            #9. Clear database button:
            elif 'InfDel' in regkeys[0]:
                #An InfluxDB query command is issued which deletes the recorded alarm table:
                client.query('drop measurement AlarmTable')        
                
        #The following part of the code will concern itself with just taking values from the working file for html to parse using jinja2.
        #Initializing variables that are going to be used.
        splist=[]
        alarmlist=[]
        hvslotarray=[]
        chnlsarray=[]
        monvararray=[]
        detlistno=0

        #Recording working and settings json files into data structures:
        #Load redis into json
        detcnfgdata=json.loads(redb.get('Detectors_config').decode("utf-8"))
        
        
        detaljson=json.loads(redb.get('Detectors_Alarms').decode("utf-8"))
        

        detmonjson=json.loads(redb.get('Monitoring_Data').decode("utf-8"))
      

        varjson=json.loads(redb.get('Variables').decode("utf-8"))

        #Recording Temperatures for jinja2:
        dataval=detmonjson["CurrentTemp"]

        #Recording other variables:
        for detector, attrs in detaljson.items():
            if detector[0:3]=="Det":
                #Alarm levels for jinja2:
                alarmlist.append(attrs['AlarmLevel'])

        for detector,attrs in detcnfgdata.items():
            #Number of detectors for jinja2:
            detlistno+=1

            #Array of activation variables for jinja2:
            monvararray.append(attrs['MonVar'])

            #Array of hv slot hv channels for jinja2:
            hvslotarray.append(attrs['HVSlot'])
            chnlsarray.append(attrs['AssignedChnls'])

            #Matrix of alarming condition limits for jinja2:
            splistaux=[]

            splistaux.append(attrs['Condition 1'])
            splistaux.append(attrs['Condition 2'])
            splistaux.append(attrs['Condition 3'])
            splistaux.append(attrs['Condition 4'])
            
            #Converting values to float:
            for splen in range(len(splistaux)):
                splistaux[splen][0]=float(splistaux[splen][0])
                splistaux[splen][1]=float(splistaux[splen][1])

            splist.append(splistaux)
        
        #Code activation variable for jinja2:
        if varjson['stopvar']:
            activevar=0
        else:
            activevar=1

        #Querying InfluxDB table for alarm table:
        headings=[]
        data=[]
        result=client.query('SELECT * FROM AlarmTable')

        if result:
            headings=result.raw['series'][0]['columns']

            for entry in reversed(result.raw['series'][0]['values']): 
                #Bringing time format to understandable shape:   
                entry[0]=entry[0].replace("T"," / ")
                entry[0]=entry[0].replace("Z","")

                #Recording entries into data structure:
                data.append(entry)      

        #Part of login code:
        if not g.user:
            return redirect(url_for('login'))
        
        #Returns html page with its corresponding variables for jinja2:
        return render_template('index.html',detlistno=detlistno,validationvariable=validationvariable,activevar=activevar,data=data,headings=headings,dataval=dataval,splist=splist,alarmlist=alarmlist,hvslotarray=hvslotarray,chnlsarray=chnlsarray,monvararray=monvararray)
    
    with open("/home/eliade/Desktop/MACE-System/RMACE/Confjson/db_config_settings.json","r") as db_conf:
        json_end=json.load(db_conf)

    #Run server that can be accessed through browser at respective IP and PORT:
    app.run(host=os.getenv('IP',json_end["Credentials"]["ip"]),port=int(os.getenv('PORT',json_end["Credentials"]["flask_server_port"])),debug=True)

if __name__=='__main__':
     #Loading settings into working file:
    
    GUI()