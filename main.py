#!/usr/bin/python
import os
import os.path
import sys
import time
import pygame
import threading
import socket
import json
import logging
import traceback
from config import *
from GIFImage import *
from utils import *
from novalct import *
import RPi.GPIO as GPIO

# -------------------------------------------------------------
# ------------------- Global variables definition -------------
# -------------------------------------------------------------
inilib = IniLib()
screen = None
msocket = None
novalct = None

g_exit_signal = False               # Request to exit application
g_app_mode = "Normal"               # Select application mode
g_display = False
g_display_index = 0

g_normal_gif1 = None                # Mode: Normal
g_normal_img2 = None
g_normal_pos1 = (0, 0)
g_normal_pos2 = (0, 0)
g_normal_timeon = 0.5               # In seconds
g_normal_timeoff = 0.5

g_ipanel_type = None                # Clock, Text, Image, Info0,1,2,3
g_ipanel_img1 = None                # Mode: IPanel
g_ipanel_img2 = None
g_ipanel_timeon = 0.5               # In seconds
g_ipanel_timeoff = 0.5

g_ipanel_seconds = 0                # For clock type only
g_ipanel_5min_gif = None
g_ipanel_3min_gif = None
g_ipanel_1min_gif = None
g_ipanel_30sec_gif = None

g_ads_img = None                    # Advertise image
g_lap_counter = 0                   # Lap counter

# -------------------------------------------------------------
# ------------------- LCD screen update (other thread) --------
# -------------------------------------------------------------
def screen_update():
    global screen
    global inilib, novalct, g_exit_signal, g_app_mode, g_display, g_display_index
    global g_normal_gif1, g_normal_img2, g_normal_pos1, g_normal_pos2, g_normal_timeon, g_normal_timeoff
    global g_ipanel_type, g_ipanel_img1, g_ipanel_img2, g_ipanel_timeon, g_ipanel_timeoff, g_ipanel_seconds

    try:
        while True:
            if g_display == False:
                screen.fill(0)
                pygame.display.update()
                time.sleep(0.05)
                continue

            if g_app_mode == "Normal":
                if isinstance(g_normal_gif1, GIFImage):
                    if g_normal_img2 == None:
                        g_normal_gif1.render(screen, g_normal_pos1)
                        pygame.display.flip()
                    else:
                        # Display gif and image in sequence
                        seconds = g_display_index*0.05

                        if seconds <= g_normal_timeon:
                            screen.fill(0)
                            g_normal_gif1.render(screen, g_normal_pos1)
                            g_normal_gif1.pause()
                            pygame.display.flip()
                        elif seconds <= (g_normal_timeon + g_normal_timeoff):
                            screen.fill(0)
                            screen.blit(g_normal_img2, g_normal_pos2)
                            pygame.display.update()
                        else:
                            g_display_index = 0

                        # Increase display index
                        g_display_index += 1
                
            elif g_app_mode == "Ads":
                if g_ads_img != None:
                    screen.fill(0)
                    screen.blit(g_ads_img, (0, 0))
                    pygame.display.update()

            elif g_app_mode == "FLine":
                if isinstance(g_normal_gif1, GIFImage):
                    g_normal_gif1.render(screen, g_normal_pos1)
                    pygame.display.flip()
                elif g_normal_gif1 != None:
                    screen.blit(g_normal_gif1, g_normal_pos1)
                    pygame.display.update()
                
                if g_normal_img2 != None:
                    screen.blit(g_normal_img2, g_normal_pos2)
                    pygame.display.update()
                
            elif g_app_mode == "IPanel":
                if g_ipanel_type == "Clock":
                    if (g_ipanel_seconds >= 290) and (g_ipanel_seconds <= 300):
                        g_ipanel_5min_gif.render(screen, (0,0))       # (x,y)
                        pygame.display.flip()
                    elif (g_ipanel_seconds >= 170) and (g_ipanel_seconds <= 180):
                        g_ipanel_3min_gif.render(screen, (0,0))       # (x,y)
                        pygame.display.flip()
                    elif (g_ipanel_seconds >= 50) and (g_ipanel_seconds <= 60):
                        g_ipanel_1min_gif.render(screen, (0,0))       # (x,y)
                        pygame.display.flip()
                    elif (g_ipanel_seconds >= 20) and (g_ipanel_seconds <= 30):
                        g_ipanel_30sec_gif.render(screen, (0,0))       # (x,y)
                        pygame.display.flip()
                    else:
                        clear_list = [289, 169, 49, 19]
                        if g_ipanel_seconds in clear_list:
                            screen.fill(0)
                            pygame.display.update()

                        if g_ipanel_img1 != None:
                            screen.blit(g_ipanel_img1, (45,45))      # (x,y)
                            pygame.display.update()
                    
                elif g_ipanel_type == "Text":
                    if g_ipanel_img1 != None:
                        # Display text and background in sequence
                        seconds = g_display_index*0.05

                        if seconds <= g_ipanel_timeon:
                            screen.blit(g_ipanel_img1, (0,0))
                            pygame.display.update()
                        elif seconds <= (g_ipanel_timeon + g_ipanel_timeoff):
                            screen.fill(0)
                            pygame.display.update()
                        else:
                            g_display_index = 0

                        # Increase display index
                        g_display_index += 1

                elif g_ipanel_type == "Image":
                    if g_ipanel_img1 != None:
                        if isinstance(g_ipanel_img1, GIFImage):
                            g_ipanel_img1.render(screen, (0,0))
                            pygame.display.flip()
                        else:
                            screen.blit(g_ipanel_img1, (0,0))
                            pygame.display.update() 
                    
                elif g_ipanel_type in ["Info0", "Info1", "Info2", "Info3"]:
                    # Display background and foreground in sequence
                    seconds = g_display_index*0.05

                    if seconds <= g_ipanel_timeon:
                        screen.blit(g_ipanel_img1, (0,0))
                        pygame.display.update()
                    elif seconds <= (g_ipanel_timeon + g_ipanel_timeoff):
                        screen.blit(g_ipanel_img2, (0,0))
                        pygame.display.update()
                    else:
                        g_display_index = 0

                    # Increase display index
                    g_display_index += 1

            elif g_app_mode == "LCounter":
                if g_normal_img2 == None:
                    screen.fill(0)
                else:
                    screen.fill(0)
                    screen.blit(g_normal_img2, g_normal_pos2)
                
                pygame.display.update()

            # Exit thread on demand
            if g_exit_signal == True:
                break
            
            # Delay between frames
            time.sleep(0.05)
    except Exception as ex:
        logging.error("Error while display screen: %s", ex)

def socket_received_handler(message):
    """
        Socket message received handler
    """
    global inilib, novalct, g_exit_signal, g_app_mode, g_display, g_display_index
    global g_normal_gif1, g_normal_img2, g_normal_pos1, g_normal_pos2, g_normal_timeon, g_normal_timeoff
    global g_ipanel_type, g_ipanel_img1, g_ipanel_img2, g_ipanel_timeon, g_ipanel_timeoff, g_ipanel_seconds
    global g_ipanel_5min_gif, g_ipanel_3min_gif, g_ipanel_1min_gif, g_ipanel_30sec_gif
    global g_ads_img, g_lap_counter

    # Extract data
    jdata = json.loads(message)
    command = jdata["command"]
    
    if command == COMMAND_EXIT:
        g_exit_signal = True
        return None
    
    elif command == COMMAND_REBOOT:
        logging.warning("Reboot panel by remote command...")
        os.system("reboot -f")
        exit()
        return None

    elif command == COMMAND_SHUTDOWN:
        logging.warning("Shutting down panel by remote command...")
        os.system("shutdown -h now")
        exit()
        return None

    elif command == COMMAND_SET_FSMODE:
        mode = jdata["fsMode"]
        if mode != None:
            if mode == "RW" or mode == "FS_RW":
                logging.warning("Set file system mode to: read/write")
                os.system("mount -o remount,rw /")
            elif mode == "RO" or mode == "FS_RO":
                logging.warning("Set file system mode to: read only")
                os.system("mount -o remount,ro /")
        return None

    elif command == COMMAND_SET_MODE:
        mode = jdata["appMode"]
        if mode == None or mode == g_app_mode:
            return None
        
        logging.info("Change app mode to: %s", mode)

        # Turn off display to prevent flick, if any
        g_display = False
        g_app_mode = mode
        return None

    elif command == COMMAND_SET_ADS_IMG:
        file_name = jdata["fileName"]
        path = jdata["path"]

        if g_app_mode != "Ads":
            return None

        # Turn off display to prevent flick, if any
        g_display = False

        g_ads_img = image_utils.load_image(file_name, path, dpi="")
        
        # Turn on display
        g_display = True
        return None

    elif command == COMMAND_SET_FLAG:
        """ Set flag and/or alterative text """

        flag_code = jdata["code"]
        file_name = jdata["fileName"]
        path = jdata["path"]
        pos_x = jdata["posX"]
        pos_y = jdata["posY"]
        flag_size = jdata["flagSize"]
        alt_text = jdata["altText"]

        if flag_size != None:
            flag_size = flag_size.lower()

        # Turn off display to prevent flicker, if any
        if g_app_mode == "Normal":
            g_display = False

        g_normal_gif1 = image_utils.load_gif_image(file_name=file_name, path=path,dpi=flag_size)
        g_normal_pos1 = (pos_x, pos_y)
        g_display_index = 0

        if alt_text != None:
            text = alt_text["text"]
            time_on_ms = alt_text["timeOnMS"]
            time_off_ms = alt_text["timeOffMS"]

            panel_width = PANEL_WIDTH
            panel_height = PANEL_HEIGHT

            # Don't let number to overlay flag border
            if flag_code == FLAG_BLUE_NUM:
                panel_width -= 8

            # Text must be center the screen
            dpi_array = ["sdpi", "mdpi", "hdpi", "xhdpi"]

            g_normal_img2 = image_utils.create_image_from_lines(text, panel_width, dpi_array)

            (w, h) = g_normal_img2.get_size()
            pos_x2 = (PANEL_WIDTH - w)/2
            pos_y2 = (PANEL_HEIGHT - h)/2

            # Add offset to move text to bottom
            pos_y2 += 4

            g_normal_pos2 = (pos_x2, pos_y2)
            g_normal_timeon = time_on_ms/1000.0
            g_normal_timeoff = time_off_ms/1000.0

            # Combine flag and number into one image
            # Then, blink as a single gif image
            if flag_code == FLAG_BLUE_NUM:
                img3 = image_utils.load_image(file_name=file_name, path=path,dpi=flag_size)
                g_normal_img2 = image_utils.combine_surfaces(img3, g_normal_img2, g_normal_pos2)
                g_normal_pos2 = (0, 0)
        else:
            g_normal_img2 = None
            g_normal_pos2 = (0, 0)
            g_normal_timeon = 0.5
            g_normal_timeoff = 0.5

        # Turn on display
        if g_app_mode == "Normal":
            g_display = True
        
        return None

    elif command == COMMAND_IPANEL_SET:
        """ Set info panel in sport motor """

        ipanel_type = jdata["type"]
        title = jdata["title"]
        file_name = jdata["fileName"]
        path = jdata["path"]
        counters = jdata["counters"]
        text = jdata["text"]

        # Turn off display to prevent flicker, if any
        if g_app_mode == "IPanel" and ipanel_type != "Clock":
            g_display = False

        # Set info panel type
        g_ipanel_type = ipanel_type

        if ipanel_type == "Clock":
            g_ipanel_seconds = counters[0]
            g_ipanel_img1 = image_utils.create_clock_image(time_sec=g_ipanel_seconds)

            if g_ipanel_5min_gif == None:
                g_ipanel_5min_gif = image_utils.load_gif_image(file_name="ipanel17.gif", path=path, dpi="xxxhdpi")
            
            if g_ipanel_3min_gif == None:
                g_ipanel_3min_gif = image_utils.load_gif_image(file_name="ipanel18.gif", path=path, dpi="xxxhdpi")
            
            if g_ipanel_1min_gif == None:
                g_ipanel_1min_gif = image_utils.load_gif_image(file_name="ipanel19.gif", path=path, dpi="xxxhdpi")
            
            if g_ipanel_30sec_gif == None:
                g_ipanel_30sec_gif = image_utils.load_gif_image(file_name="ipanel20.gif", path=path, dpi="xxxhdpi")

        elif ipanel_type == "Text":
            # Split text message by newline
            text = text.replace("\r", "")
            lines = text.split("\n")

            # Remove empty line
            lines = [s for s in lines if s != ""] 

            # Find row with highest length
            max_line = max(lines, key=len)
            max_len = len(max_line)

            # Check the best dpi that fit text message
            dpi_array = ["mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi", "x4hdpi", "x5hdpi", "x6hdpi"]
            dpi_fit = dpi_array[0]

            for dpi in dpi_array:
                img0 = image_utils.create_image_from_text("O", dpi)
                (w0, h0) = img0.get_size()

                if (w0 * max_len) >= (IPANEL_WIDTH - 5):
                    break
                else:
                    dpi_fit = dpi

            # Create image for each line
            # then append to parent image
            img1 = image_utils.create_empty_surface(0, 0)
            for line in lines:
                img2 = image_utils.create_image_from_text(text=line, dpi=dpi_fit)
                (w, h) = img1.get_size()
                img1 = image_utils.combine_surfaces(img1, img2, (4, h))

            g_ipanel_img1 = img1
            
            # Reset display values
            g_display_index = 0
            g_ipanel_timeon = 0.5
            g_ipanel_timeoff = 0.5

        elif ipanel_type == "Image":
            g_ipanel_img1 = image_utils.load_gif_image(file_name=file_name, path=path, dpi="xxxhdpi")
            
        elif ipanel_type == "Info0":
            # Load background image
            bg_img = image_utils.load_image(file_name=file_name, path=path, dpi="xxxhdpi")
            g_ipanel_img1 = bg_img
            bg_img2 = bg_img

            (w0, h0) = (IPANEL_WIDTH, IPANEL_HEIGHT)

            # Load title image (top, center)
            title = title.replace("\r", "")
            title_array = title.split("\n")
            
            if len(title_array) > 2:
                raise ValueError("Info panel does not support title contains more than 2 lines")
            
            elif len(title_array) == 2:
                title2 = title_array[0]
                title3 = title_array[1]

                # Combine title (line 1) to background image
                img2 = image_utils.create_image_from_text(text=title2, dpi="xhdpi")
                (w2, h2) = img2.get_size()

                x2 = (w0 - w2) / 2
                y2 = ((h0 / 4) - h2) / 2

                bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

                # Combine title (line 2) to background image
                img3 = image_utils.create_image_from_text(text=title3, dpi="xhdpi")
                (w3, h3) = img3.get_size()

                x3 = (w0 - w3) / 2
                y3 = (((h0 / 4) - h3) / 2) + (h0 / 4)

                bg_img2 = image_utils.combine_surfaces(bg_img2, img3, (x3, y3))

            else:
                # Combine title to background image
                img2 = image_utils.create_image_from_text(text=title, dpi="xxhdpi")
                (w2, h2) = img2.get_size()
                
                x2 = (w0 - w2) / 2
                y2 = ((h0 / 4) - h2) / 2

                bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load rider number (bottom, left)
            text_rider = str(counters[0])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="x6hdpi")
            (w2, h2) = img2.get_size()
            
            x2 = ((w0 / 2) - w2) / 2
            y2 = (h0 / 2) + ((h0 / 2) - h2) / 2

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load penalty text (bottom, right)
            img2 = image_utils.create_image_from_text(text=text, dpi="x6hdpi")
            
            (w2, h2) = img2.get_size()
            x2 = (w0 / 2) + ((w0 / 2) - w2) / 2
            y2 = (h0 / 2) + ((h0 / 2) - h2) / 2

            g_ipanel_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))
            
            # Reset display values
            g_display_index = 0
            g_ipanel_timeon = 0.5
            g_ipanel_timeoff = 0.5
            
        elif ipanel_type == "Info1":
            # Load background image
            bg_img = image_utils.load_image(file_name=file_name, path=path, dpi="xxxhdpi")
            g_ipanel_img1 = bg_img
            bg_img2 = bg_img

            (w0, h0) = (IPANEL_WIDTH, IPANEL_HEIGHT)

            # Load title image (top, center)
            img2 = image_utils.create_image_from_text(text=title, dpi="xhdpi")
            (w2, h2) = img2.get_size()
            
            x2 = (w0 - w2) / 2
            y2 = ((h0 / 3) - h2) / 2

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load rider number (bottom, center)
            text_rider = str(counters[0])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="x6hdpi")
            (w2, h2) = img2.get_size()

            x2 = (w0 - w2) / 2
            y2 = (h0 / 3) + ((h0 / 3 * 2) - h2) / 2

            g_ipanel_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Reset display values
            g_display_index = 0
            g_ipanel_timeon = 0.5
            g_ipanel_timeoff = 0.5
            
        elif ipanel_type == "Info2":
            # Load background image
            bg_img = image_utils.load_image(file_name=file_name, path=path, dpi="xxxhdpi")
            g_ipanel_img1 = bg_img
            bg_img2 = bg_img

            (w0, h0) = (IPANEL_WIDTH, IPANEL_HEIGHT)

            # Letter and number has a big space in bottom
            # so, add offset to move line down few pixels
            Y_OFFSET = 5

            # Load title image (top, center)
            img2 = image_utils.create_image_from_text(text=title, dpi="xhdpi")
            (w2, h2) = img2.get_size()
            
            x2 = (w0 - w2) / 2
            y2 = ((h0 / 3) - h2) / 2

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load rider number (middle, center)
            text_rider = str(counters[0])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
            (w2, h2) = img2.get_size()

            x2 = (w0 - w2) / 2
            y2 = (h0 / 3) + ((h0 / 3) - h2) / 2 + Y_OFFSET

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))
            
            # Load rider number (bottom, center)
            text_rider = str(counters[1])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
            (w2, h2) = img2.get_size()

            x2 = (w0 - w2) / 2
            y2 = (h0 / 3 * 2) + ((h0 / 3) - h2) / 2 + Y_OFFSET

            g_ipanel_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Reset display values
            g_display_index = 0
            g_ipanel_timeon = 0.5
            g_ipanel_timeoff = 0.5
            
        elif ipanel_type == "Info3":
            # Load background image
            bg_img = image_utils.load_image(file_name=file_name, path=path, dpi="xxxhdpi")
            g_ipanel_img1 = bg_img
            bg_img2 = bg_img

            (w0, h0) = (IPANEL_WIDTH, IPANEL_HEIGHT)

            # Letter and number has a big space in bottom
            # so, add offset to move line down few pixels
            Y_OFFSET = 5

            # Load title image (top, center)
            img2 = image_utils.create_image_from_text(text=title, dpi="xhdpi")
            (w2, h2) = img2.get_size()

            x2 = (w0 - w2) / 2
            y2 = ((h0 / 3) - h2) / 2

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load rider number (left, middle)
            text_rider = str(counters[0])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
            (w2, h2) = img2.get_size()

            x2 = ((w0 / 2) - w2) / 2
            y2 = (h0 / 3) + ((h0 / 3) - h2) / 2 + Y_OFFSET

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))
            
            # Load rider number (right, middle)
            text_rider = str(counters[1])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
            (w2, h2) = img2.get_size()

            x2 = (w0 / 2) + ((w0 / 2) - w2) / 2
            y2 = (h0 / 3) + ((h0 / 3) - h2) / 2 + Y_OFFSET

            bg_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))

            # Load rider number (left, bottom)
            text_rider = str(counters[2])
            img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
            (w2, h2) = img2.get_size()

            x2 = ((w0 / 2) - w2) / 2
            y2 = (h0 / 3 * 2) + ((h0 / 3) - h2) / 2 + Y_OFFSET

            g_ipanel_img2 = image_utils.combine_surfaces(bg_img2, img2, (x2, y2))
            
            # Load rider number (right, bottom)
            if (len(counters)) >= 4:
                text_rider = str(counters[3])
                img2 = image_utils.create_image_from_text(text=text_rider, dpi="xxxhdpi")
                (w2, h2) = img2.get_size()

                x2 = (w0 / 2) + ((w0 / 2) - w2) / 2
                y2 = (h0 / 3 * 2) + ((h0 / 3) - h2) / 2 + Y_OFFSET

                g_ipanel_img2 = image_utils.combine_surfaces(g_ipanel_img2, img2, (x2, y2))

            # Reset display values
            g_display_index = 0
            g_ipanel_timeon = 0.5
            g_ipanel_timeoff = 0.5
            
        # Turn on display
        if g_app_mode == "IPanel":
            g_display = True

        return None

    elif command == COMMAND_IPANEL_CLR:
        if g_app_mode != "IPanel":
            return None

        # Turn off display
        g_display = False
        return None

    elif command == COMMAND_FLINE_SET:
        """ Set finish line in sport car """

        file_name = jdata["fileName"]
        path = jdata["path"]
        text = jdata["text"]

        # Turn off display to prevent flicker, if any
        if g_app_mode == "FLine":
            g_display = False

        # Create left gif image
        g_normal_gif1 = image_utils.load_gif_image(file_name=file_name, path=path, dpi="xxxhdpi")
        g_normal_pos1 = (0, 0)

        # Create right text image
        # Do not create if text is empty or "0"
        if text != "" and text != "0":
            g_normal_img2 = image_utils.create_image_from_text(text=text, dpi="x9hdpi")
        else:
            g_normal_img2 = None

        # Right text must be center in case 1,2,3 characters
        if g_normal_img2 != None:
            (w1, h1) = g_normal_gif1.get_size()
            (w2, h2) = g_normal_img2.get_size()

            pos_x = w1 + (IPANEL_WIDTH - w1 - w2)/2
            pos_y = (h1 - h2)/2
            g_normal_pos2 = (pos_x, pos_y)
        else:
            g_normal_pos2 = (0, 0)

        # Turn on display
        if g_app_mode == "FLine":
            g_display = True

        return None
    
    elif command == COMMAND_FLINE_CLR:
        if g_app_mode != "FLine":
            return None

        # Turn off display
        g_display = False
        return None

    elif command == COMMAND_LCOUNTER_SET:
        """ Set Lap Counter panel """

        mode = jdata["mode"]
        seconds = jdata["seconds"]
        counter = jdata["counter"]
        text = jdata["text"]
        panel_width = jdata["panelWidth"]
        panel_height = jdata["panelHeight"]

        # Set panel default size
        if panel_width == None or panel_width <= 0:
            panel_width = LCOUNTER_WIDTH
        
        if panel_height == None or panel_height <= 0:
            panel_height = LCOUNTER_HEIGHT

        text_lines = ""
        if mode == "Clock":
            if seconds < 0:
                seconds = 0
            
            hour = seconds/3600
            minute = (seconds%3600)/60
            second = seconds%60
            text_lines = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
            dpi_array = ["x6hdpi", "x9hdpi", "x10hdpi", "x11hdpi"]
        elif mode == "Counter":
            g_lap_counter = counter
            text_lines = "LAP " + str(counter)
            dpi_array = ["x6hdpi", "x9hdpi", "x10hdpi", "x11hdpi"]
        elif mode == "Text":
            text_lines = text
            dpi_array = ["hdpi", "xhdpi", "xxhdpi", "xxxhdpi", "x4hdpi", "x5hdpi", "x6hdpi"]
        else:
            raise ValueError("Not support Lap Counter mode: " + str(mode))
        
        # Generate image from text
        img = image_utils.create_image_from_lines(text_lines, panel_width, dpi_array)

        # Text must be center the screen
        (w, h) = img.get_size()
        pos_x = (panel_width - w)/2
        pos_y = (panel_height - h)/2

        g_normal_pos2 = (pos_x, pos_y)
        g_normal_img2 = img
        g_display = True
        return None
        
    elif command == COMMAND_LCOUNTER_CLR:
        g_normal_img2 = None
        g_normal_pos2 = (0, 0)

        # Turn off display
        g_display = False
        return None

    elif command == COMMAND_LCOUNTER_GET:
        jresponse = json.loads("{}")
        jresponse["counter"] = g_lap_counter
        return json.dumps(jresponse)
            
    elif command == COMMAND_SENSOR_GET:
        """ Get data from sensors """

        sensor_type = jdata["sensorType"]
        jresponse = json.loads("{}")
        jresponse["message"] = ""

        try:
            novalct.reopen()
            if sensor_type == "temp":
                value = novalct.read_temperature_receiving_card()
                jresponse["temperature"] = value
            elif sensor_type == "voltage":
                value = novalct.read_receiving_card_voltage()
                jresponse["voltage"] = value
            elif sensor_type == "brightness":
                value = novalct.read_brightness()
                jresponse["brightness"] = value
            elif sensor_type == "video":
                value = novalct.read_sending_card_video_signal()
                jresponse["video"] = value
        except Exception:
            _, ex_value, _ = sys.exc_info()
            novalct.uart = None
            jresponse["message"] = repr(ex_value)
            
        return json.dumps(jresponse)

    elif command == COMMAND_SENSOR_SET:
        """ Set brightness to Novastar led receiving card """

        jresponse = json.loads("{}")
        jresponse["message"] = ""

        try:
            if "brightness" in jdata:
                value = jdata["brightness"]
                if value > 255:
                    value = 255
                elif value < 0:
                    value = 0

                novalct.reopen()
                novalct.write_brightness(value)
        except Exception:
            _, ex_value, _ = sys.exc_info()
            novalct.uart = None
            jresponse["message"] = repr(ex_value)

        return json.dumps(jresponse)
        
    return None

# -------------------------------------------------------------
# ------------------- Lap Counter button handler --------------
# -------------------------------------------------------------
def button_up_handler(channel):
    """ Lap Counter button up handler """

    global g_lap_counter

    # wait for 50 milliseconds
    time.sleep(0.05)

    if GPIO.input(channel) == GPIO.LOW and g_app_mode == "LCounter":
        if not isinstance(g_lap_counter, int):
            g_lap_counter = 0
        
        if g_lap_counter < 999:
            g_lap_counter += 1

def button_down_handler(channel):
    """ Lap Counter button down handler """

    global g_lap_counter

    # wait for 50 milliseconds
    time.sleep(0.05)

    if GPIO.input(channel) == GPIO.LOW and g_app_mode == "LCounter":
        if not isinstance(g_lap_counter, int):
            g_lap_counter = 0
        
        if g_lap_counter > 0:
            g_lap_counter -= 1

def init_application():
    """ 
        Init application by setting up modules: logging, network, pygame, socket,...
    """
    global inilib, screen, msocket, novalct, g_app_mode

    g_app_mode = "Normal"

    # Make sure logs folder is exists
    if not os.path.exists(LOG_FOLDER):
        os.mkdir(LOG_FOLDER)

    # Init log module
    if os.path.isfile(LOG_FILE_NAME):
        file_stats = os.stat(LOG_FILE_NAME)
        file_size_mb = file_stats.st_size / (1024 * 1024)

        if file_size_mb >= LOG_MAX_SIZE_MB:
            logging.shutdown()
            os.remove(LOG_FILE_NAME)
    
    log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    # Add file log handler
    file_handler = logging.FileHandler(LOG_FILE_NAME)
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # Add console log handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    logging.info("LCD server starting up...")

    # Init LCD screen
    pygame.init()
    pygame.mouse.set_visible(False)
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    # Start new thread to display screen
    thread = threading.Thread(target= screen_update)
    thread.start()

    # Init socket server
    msocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    msocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    msocket.bind((SOCKET_HOST, SOCKET_PORT))
    msocket.listen(1)

    # Open serial port to Novastar led sending card
    novalct = NovaLCT(baud_rate= 115200, read_timeout_sec = 5)

    # Init lap counter up/down buttons
    GPIO.setmode(GPIO.BOARD)
    # GPIO.setwarnings(False)
    GPIO.setup(PIN_LCOUNTER_UP, GPIO.IN, pull_up_down= GPIO.PUD_UP)
    GPIO.setup(PIN_LCOUNTER_DOWN, GPIO.IN, pull_up_down= GPIO.PUD_UP)

    GPIO.add_event_detect(PIN_LCOUNTER_UP, GPIO.FALLING, callback=button_up_handler, bouncetime=150)
    GPIO.add_event_detect(PIN_LCOUNTER_DOWN, GPIO.FALLING, callback=button_down_handler, bouncetime=150)

# -------------------------------------------------------------
# ----------------------- Main loop ---------------------------
# -------------------------------------------------------------
try:
    init_application()

    while True:
        conn, address = msocket.accept()
        buff = ""
        lastTime = time.time()
        logging.info("Socket connected to (%s, %s)" % (address))

        while True:
            try:
                data_bytes = conn.recv(2048)
                if len(data_bytes) == 0:
                    continue

                buff += data_bytes.decode("utf-8")
                timeout = time.time() - lastTime

                if (len(buff) == 0) and (timeout >= SOCKET_TIMEOUT_SEC):
                    conn.close()
                    logging.info("Socket connection to (%s) timed out!", (address))
                    break

                lastTime = time.time()

                while ("\n" in buff):
                    i    = buff.find("\n")
                    line = buff[0:i]
                    buff = buff[i+1:]

                    logging.debug("Socket received: %s", line)
                    response = socket_received_handler(line)

                    if response != None:
                        response = response + "\n"
                        logging.debug("Socket send: %s", response)
                        data_bytes = bytes(response, 'utf-8')
                        conn.sendall(data_bytes)

                # Process exit request
                if g_exit_signal:
                    logging.warning("LCD server is going to exit...")
                    g_exit_signal = False
                    conn.close()
                    pygame.quit()
                    exit(2)
            except Exception as ex2:
                logging.fatal("Process socket message error: %s", ex2)
                traceback.print_exc()

except Exception as ex:
    logging.fatal("Application fatal exception: %s", ex)
    logging.warning("Freeing resources: socket, pygame")

    if msocket != None:
        msocket.close()
    
    GPIO.cleanup()
    pygame.quit()

    logging.warning("Application is going to quit!")
    exit(1)
