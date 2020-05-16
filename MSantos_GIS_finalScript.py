import datetime as dt, arcpy, random as rm
arcpy.env.overwriteOutput=True
path="E:/G_GISFileDatabase/MoveBank/points_pjLambert.shp"
desc=arcpy.Describe(path)
flds=[f.name for f in arcpy.ListFields(desc.catalogPath)]
fldsPt=flds+["SHAPE@"]
unit=desc.SpatialReference.linearUnitName
if unit=="":
    unit=desc.SpatialReference.angularUnitName
n=500
whereclause="ind_ident = 'TERF04'"
tMax=1
tUnit="days"
dUnit2Seconds={"minutes":60,"hours":60*60,"seconds":1,"days":60*60*24}
tMax2Sec=tMax*dUnit2Seconds[tUnit]
critTime="17:30:00"##Ideal time to sample for criterionCHP
critTimeD=dt.datetime.strptime(critTime, "%H:%M:%S")
tIdeal=critTimeD.time()
report=["Orig. file= "+str(path),"Units= "+str(unit),"Where Clause= "+whereclause,"Max time between pts for VPSP= "+str(tMax)+" "+tUnit, "Ideal time for Criterion sampling = "+str(critTime)]
##report object results in a .txt file with information on resulting files
total=0##find out how many sample points we have
with arcpy.da.SearchCursor(desc.catalogPath,flds,whereclause) as sc0:
    for row in sc0:
        total+=1
del sc0
report.append("Total # of sample data= "+str(total))##adds total to report
l_total=[i for i in range(total)]##creates a mutable listof "total"
l_random=[]
for i in range(n):##identify which points to add to randomCHP to result in n number of samples
    l_random.append(rm.choice(l_total))
    l_total.remove(l_random[-1])
    l_random.sort()

dCriterion={}
dSubsets={"chpRandom":[],"chpCriterion":dCriterion,"vpsp":[]}
ct=0
vMax=0
last=[]
with arcpy.da.SearchCursor(desc.catalogPath,fldsPt,whereclause) as sc:
    for i in sc:
        pt=i[-1].firstPoint
        for x in [1]:
            if l_random:
                if ct==l_random[0]:
                    dSubsets["chpRandom"].append([pt,i[0]])
                    l_random.pop(0)
                else: continue
            else: continue
        d=dt.datetime.strptime(i[2],"%Y-%m-%d %H:%M:%S")##converts timestamps to readable format
        diff=0
        for x in [1]:
            if i[3] =="Pacific Daylight Time":
                d=d+dt.timedelta(0,3600)##adds 1hr to timestamp for daylight savings time if appropriate
        d2=dt.datetime(d.year,d.month,d.day,tIdeal.hour,tIdeal.minute,tIdeal.second)
        tDiff=d-d2
        diff=abs(tDiff.seconds)
        for x in [1]:##adds point to "Criterion" subset
            KEY=(d.year,d.month,d.day)
            if (KEY) not in dCriterion.keys():
                dCriterion[KEY]=[pt,i[0],diff]
            elif (KEY) in dCriterion.keys():
                if dCriterion[(KEY)][2]<diff:
                    dCriterion[(KEY)]=[pt,i[0],diff]
        dur=dt.timedelta(0)
        dist=0
        vel=0
        for x in [1]:##adds points toVPSP subset
            if last:
                dur=d-last[0]
                arr=arcpy.Array(last[1])
                arr.append(pt)
                line=arcpy.Polyline(arr)
                dist=line.length
                for x in [1]:
                    if dur.seconds>0:
                        vel=line.length/dur.seconds ## source "unit" per second
                for x in [1]:
                    if vMax<vel:
                        vMax=vel
                if dur.seconds<tMax2Sec:
                    DATE="{0}/{1}/{2} {3}:{4}:00 {5}".format(d.month,d.day,d.year,d.strftime("%I").lstrip("0"),d.strftime("%M"),d.strftime("%p"))
                    dSubsets["vpsp"].append([pt,i[0],DATE,vel])##"DATE" object mimics Prisms tool format requirements
        ct+=1
        last=[d,pt]
del sc
report.append("Max velocity= "+str(vMax))##adds max velocity to report
time=str(dt.datetime.now().timetuple().tm_yday)+"t"+str(dt.datetime.now().timetuple().tm_hour*100+dt.datetime.now().timetuple().tm_min)
report.append("Analysis timesamp= "+time)##adds timestamp for anaysis to sync report with resulting outputs
for i in dSubsets.keys():##creates resulting featureclasses
    outName=str("Results_"+i+"_TSd"+time)
    for x in [1]:
        if str(desc.catalogPath.split(".")[-1]):
            outName=outName+"."+str(desc.catalogPath.split(".")[-1])
        else: continue
    outLong=desc.path+"/"+outName
    arcpy.CreateFeatureclass_management(desc.path,outName, "POINT","","","",desc.SpatialReference)
    if type(dSubsets[i])==list:
        col=len(dSubsets[i][0])
        fldsNew=["SHAPE@","Orig_FID"]
        for x in range(1,col-1):
            fldsNew.append("attData_"+str(x))
        for x in fldsNew[1:]:
            arcpy.AddField_management(outLong,x,"TEXT","#","#",50)
        with arcpy.da.InsertCursor(outLong,fldsNew) as ic:
            for row in dSubsets[i]:
                if i=="vpsp":
                    row[-1]=vMax
                    ic.insertRow(row)
                else:
                    ic.insertRow(row)
        del ic
    elif type(dSubsets[i])==dict:
        l_keys=dSubsets[i].keys()
        l_keys.sort()
        fldsNew=["SHAPE@","Orig_FID"]
        col=len(dSubsets[i][l_keys[0]])
        for x in range(1,col-1):
            fldsNew.append("attData_"+str(x))
        for x in fldsNew[1:]:
            arcpy.AddField_management(outLong,x,"TEXT","#","#",50)
        with arcpy.da.InsertCursor(outLong,fldsNew) as ic:
            for k in l_keys:
                ic.insertRow(dSubsets[i][k])
        del ic
txt= open(desc.path+"/"+"Rep_TS"+time+".txt","w")##writes output report file
for i in report:
    txt.write(i+"\n")
txt.close()