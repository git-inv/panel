#!/usr/bin/python
import logging

#
# Socket definitions
#
COMMAND_EXIT         = "EXIT"           # Exit python application
COMMAND_REBOOT       = "REBOOT"         # Reboot panel
COMMAND_SHUTDOWN     = "SHUTDOWN"       # Shutdown panel

COMMAND_SET_FSMODE   = "SET-FSMODE"     # Set filesystem mode: RO, RW
COMMAND_SET_MODE     = "SET-MODE"       # Set application mode: Normal, Ads, Fline, IPanel, LCounter
COMMAND_SET_ADS_IMG  = "SET-ADS-IMG"    # Set advertise file name and path
COMMAND_SET_FLAG     = "SET-FLAG"       # Set flag and/or alt text

COMMAND_IPANEL_SET   = "SET-IPANEL"     # Set Info panel
COMMAND_IPANEL_CLR   = "CLR-IPANEL"     # Clear Info panel

COMMAND_FLINE_SET    = "SET-FLINE"      # Set Finish line
COMMAND_FLINE_CLR    = "CLR-FLINE"      # Clear Finish line

COMMAND_LCOUNTER_SET = "SET-LCOUNTER"   # Set Lap counter
COMMAND_LCOUNTER_GET = "GET-LCOUNTER"   # Get Lap counter
COMMAND_LCOUNTER_CLR = "CLR-LCOUNTER"   # Clear Lap counter

COMMAND_SENSOR_SET   = "SENSOR-SET"
COMMAND_SENSOR_GET   = "SENSOR-GET"

#
# Flag code definitions
#
FLAG_BLUE_NUM        = 16       # Blue with number

#
# Flag panel definitions
#
PANEL_WIDTH     = 60   # pixels
PANEL_HEIGHT    = 60

#
# Info & Finish Line panel definitions
#
IPANEL_WIDTH     = 512   # pixels
IPANEL_HEIGHT    = 256

#
# Lap Counter panel definitions
#
LCOUNTER_WIDTH  = 768   # pixels
LCOUNTER_HEIGHT = 256   # pixels

SOCKET_HOST    = "localhost"
SOCKET_PORT    = 6070
SOCKET_TIMEOUT_SEC = 4.0

MAX_CHAR_PER_LINE = 21

LIST_DPI = ("tdpi", "mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi", "x4hdpi", "x5hdpi", "x6hdpi", "x7hdpi", "x8hdpi", "x9hdpi", "x10hdpi", "x11hdpi")

#
# Logging definitions
#
LOG_FOLDER = "Logs"
LOG_FILE_NAME = LOG_FOLDER + "/lcdserver.log"
LOG_LEVEL = logging.DEBUG
LOG_MAX_SIZE_MB = 10

#
# Lap counter buttons (BOARD numbering)
#
PIN_LCOUNTER_UP     = 36
PIN_LCOUNTER_DOWN   = 38
