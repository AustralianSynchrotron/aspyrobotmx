TOP=../..

include $(TOP)/configure/CONFIG
#----------------------------------------
#  ADD MACRO DEFINITIONS AFTER THIS LINE
#=============================

#=============================
# Build the IOC application

PROD_IOC = RobotTestIOC
# RobotTestIOC.dbd will be created and installed
DBD += RobotTestIOC.dbd

# RobotTestIOC.dbd will be made up from these files:
RobotTestIOC_DBD += base.dbd

# Include dbd files from all support applications:
#RobotTestIOC_DBD += xxx.dbd

# Add all the support libraries needed by this IOC
#RobotTestIOC_LIBS += xxx

# RobotTestIOC_registerRecordDeviceDriver.cpp derives from RobotTestIOC.dbd
RobotTestIOC_SRCS += RobotTestIOC_registerRecordDeviceDriver.cpp

# Build the main IOC entry point on workstation OSs.
RobotTestIOC_SRCS_DEFAULT += RobotTestIOCMain.cpp
RobotTestIOC_SRCS_vxWorks += -nil-

# Add support from base/src/vxWorks if needed
#RobotTestIOC_OBJS_vxWorks += $(EPICS_BASE_BIN)/vxComLibrary

# Finally link to the EPICS Base libraries
RobotTestIOC_LIBS += $(EPICS_BASE_IOC_LIBS)

#===========================

include $(TOP)/configure/RULES
#----------------------------------------
#  ADD RULES AFTER THIS LINE

