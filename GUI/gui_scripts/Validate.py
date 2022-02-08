
def Validate(datac):
    #Initializing variables:
    chnlsarray=[]
    hvslotarray=[]

    #Loading recorded data from data structure:
    for detector, attrs in datac['Detectors_config'].items():
        chnlsarray.append(attrs['AssignedChnls'])
        hvslotarray.append(attrs['HVSlot'])

    #Initializing validation variable:
    ok=True

    #Checking for errors in the mapping:
    for hvlen1 in range(len(hvslotarray)):
        for hvlen2 in range(len(hvslotarray)):
            if hvlen1!=hvlen2:
                if hvslotarray[hvlen1]==hvslotarray[hvlen2]:
                    for ch1 in chnlsarray[hvlen1]:
                        for ch2 in chnlsarray[hvlen2]:
                            if ch1==ch2:
                                ok=False

    return ok
    