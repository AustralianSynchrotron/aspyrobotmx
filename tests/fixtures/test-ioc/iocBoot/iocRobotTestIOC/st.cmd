#!../../bin/linux-x86/RobotTestIOC

## You may have to change RobotTestIOC to something else
## everywhere it appears in this file

< envPaths

cd ${TOP}

## Register all support components
dbLoadDatabase "dbd/RobotTestIOC.dbd"
RobotTestIOC_registerRecordDeviceDriver pdbbase

epicsEnvSet(ROBOT,"ROBOT_MX_TEST")

## Load record instances
dbLoadRecords("RobotTestIOCApp/Db/RobotEpsonIP.db","P=${ROBOT},R=,L0=0,L1=1, FLNK=${ROBOT}:GRIPOPEN_STATUS")
dbLoadRecords("RobotTestIOCApp/Db/RobotEpsonMX.db","P=${ROBOT},R=,L0=0,L1=1, SCAN=.5 second")

cd ${TOP}/iocBoot/${IOC}
iocInit

## Start any sequence programs
#seq sncxxx,"user=blctlHost"
