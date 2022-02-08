#!/usr/bin/env python3

import json
import random

with open("/home/eliade/Desktop/RMACE/Confjson/MACE_test.json",'r') as testjson:
    json_obj=json.load(testjson)

for i in range(1,98):
    for elind in range(8):
        y=json_obj["8det"][str(i)][elind]
        if y !=0:
           
          x=round(random.uniform(-1.5,1.5),2)
          json_obj["8det"][str(i)][elind]=round(json_obj["8det"][str(i)][elind]+x,2)
          
with open("/home/eliade/Desktop/RMACE/Confjson/MACE_test.json",'w') as testjson:
    json.dump(json_obj,testjson,indent=6)
