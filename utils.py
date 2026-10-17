#!/usr/bin/python
import os
import sys
import os.path
import time
import threading
import base64
import pygame
from PIL import Image
from GIFImage import *

class IniLib(object):
    """ Python parser library for INI string. 

        Encode/decode a sequence of keys and values. 

        Encode: key1=value1;key2=value2;
        Decode: bmFtZQ==|dHVhbg==;YWdl|MTc=;
    """
    
    DATE    = '16/09/2017'
    AUTHOR  = 'Tran Tuan'

    def __init__(self):
        super(IniLib, self).__init__()
        
    def info(self):
        return (self.DATE, self.AUTHOR)

    def compose(self, *args):
        """ Encode a sequence of keys and values. 

            Example: key1=value1;key2=value2;

            @params tuple args Length of tuple must be an even number.
            @return 
                None    Error
                tupple  Success
        """
        if len(args) < 2 or (len(args)%2) != 0:
            return None

        retval = ""

        for i in range(0, len(args), 2):
            key = base64.urlsafe_b64encode(str(args[i]))
            val = base64.urlsafe_b64encode(str(args[i+1]))

            retval += key + "|" + val + ";"

        return retval

    def parse(self, arg):
        """ Decode a sequence of keys and values. 

            Example: bmFtZQ==|dHVhbg==;YWdl|MTc=;

            @params str arg A base64 encoded string.
            @return 
                None    Error
                tupple  Success
        """
        if not isinstance(arg, str):
            return None
        
        args = arg.split(";")

        retval = ()

        for i in range(0, len(args)):
            if len(args[i]) < 3:
                continue

            tmp = args[i].split("|")

            key = base64.urlsafe_b64decode(tmp[0])
            val = base64.urlsafe_b64decode(tmp[1])

            retval += (key, val)

        return retval

class CountDownTimer(object):
    """ Count down timer
        with periodic (sec) and tick handler.
    """
    DATE    = '17/09/2017'
    AUTHOR  = 'Tran Tuan'
    
    def __init__(self):
        super(CountDownTimer, self).__init__()
        
        self.ticker = None
        self.count  = 0
        self.period = 1
        self.listener = None
    
    def info(self):
        return (self.DATE, self.AUTHOR)

    def on_tick(self):
        self.listener(self.count)

        if self.count == 0 and self.ticker != None:
            self.ticker.cancel()
            self.ticker = None
            return
        
        self.count -= 1

        self.ticker.cancel()
        self.ticker = threading.Timer(self.period, self.on_tick)
        self.ticker.start()

    def start(self, period, count, listener):
        self.count = count
        self.period = period
        self.listener = listener

        if self.ticker != None:
            self.ticker.cancel()
        
        self.ticker = threading.Timer(period, self.on_tick)
        self.ticker.start()

    def stop(self):
        self.count = 0
        self.listener = None

        if self.ticker != None:
            self.ticker.cancel()
            self.ticker = None

class MiscUtils(object):
    """ 
        File, path utilities
    """
    def __init__(self):
        super(MiscUtils, self).__init__()
        
    def get_app_path(self):
        """
            Get path to current script/application
        """
        return os.path.dirname(os.path.abspath(__file__))

    def path_combine(self, path1, path2):
        """
            Combine 2 paths together
        """
        if path1 == None:
            return path2
        if path2 == None:
            return path1

        # Vary between linux: /, windows: \
        pathsep = os.path.sep
        
        if path1.endswith(pathsep):
            path1 = path1[:len(path1) - 1]
        
        if path2.startswith(pathsep):
            path2 = path2[1:]
        
        return path1 + pathsep + path2

    def path_combine3(self, path1, path2, path3):
        """
            Combine 3 paths together
        """
        path = self.path_combine(path1, path2)
        return self.path_combine(path, path3)

    def path_combine4(self, path1, path2, path3, path4):
        """
            Combine 4 paths together
        """
        p1 = self.path_combine(path1, path2)
        p2 = self.path_combine(p1, path3)
        return self.path_combine(p2, path4)

    def restart_app(self, delay_sec):
        """
            Restart this application with same arguments.
            Delay few seconds before actually restart
        """
        if delay_sec <= 0:
            delay_sec = 1.0
        
        time.sleep(delay_sec)
        os.execl(sys.executable, os.path.abspath(__file__), *sys.argv)
    
    def infopanel_flagname_to_text(self, flag_name):
        """
            Convert info panel flag name to text
        """
        if flag_name == None:
            return ""
        if flag_name == "finish01.gif":
            return "Change Position"
        if flag_name == "finish02.gif":
            return "Time Penalty"
        if flag_name == "finish03.gif":
            return "LLP X2"
        if flag_name == "finish04.gif":
            return "Ride Through"
        if flag_name == "finish05.gif":
            return "Long Lap"
        if flag_name == "finish06.gif":
            return "Warning"
        if flag_name == "finish07.gif":
            return "Equipment"
        if flag_name == "finish08.gif":
            return "Start Delayed"
        if flag_name == "finish09.gif":
            return "Wet Race"
        if flag_name == "finish10.gif":
            return "Rain On Grid"
        if flag_name == "finish11.gif":
            return "Dry Race"
        if flag_name == "finish12.gif":
            return "Ride Though"
        return ""
    
class ImageUtils(object):
    """ 
        Image utilities
    """
    def __init__(self):
        super(ImageUtils, self).__init__()
        
    def combine_images(self, img_files):
        """ Combine many images together in horizontal. 

            @param  img_files tuple  List of image file path.
            @return 
                None on failed.
                Surface on success.
        """
        if not isinstance(img_files, tuple):
            return None

        if len(img_files) == 0:
            return None
        
        # WARN: This operation can slow down processing speed.
        # Check if files exists.
        # for i in range(0, len(img_files)):
        #     path = img_files[i]
            
        #     if os.path.isfile(path) == False:
        #         return None

        # Open images using a for loop
        images = []
        for file in img_files:
            img = Image.open(file)
            images.append(img)

        # Extract widths and heights using a for loop
        widths = []
        heights = []
        for img in images:
            size = img.size
            widths.append(size[0])
            heights.append(size[1])

        # Convert lists to tuples
        w = tuple(widths)
        h = tuple(heights)

        w_total = sum(w)
        h_max   = max(h)
        img_new  = Image.new('RGB', (w_total, h_max))
        x_offset = 0

        for img in images:
            img_new.paste(img, (x_offset,0))
            x_offset += img.size[0]
            mode = img_new.mode
            size = img_new.size
            data = img_new.tobytes()

        return pygame.image.fromstring(data, size, mode)

    def load_image(self, file_name, path, dpi):
        """
            Load image from given file path and dpi
            @return 
                None on failed.
                Surface on success.
        """
        app_path = misc_utils.get_app_path()
        path_no_dpi = misc_utils.path_combine3(app_path, path, file_name)

        if dpi == None or dpi == "":
            image_path = path_no_dpi
        else:
            image_path = misc_utils.path_combine3(app_path, path + "-" + dpi, file_name)
        
        if not os.path.exists(image_path):
            image_path = path_no_dpi
        
        if not os.path.exists(image_path):
            print("Image file not found: %s" % image_path)
            return None
        
        return pygame.image.load(image_path)
        
    def load_gif_image(self, file_name, path, dpi):
        """
            Load gif image from given file path and dpi
            @return 
                None on failed.
                GIFImage on success.
        """
        app_path = misc_utils.get_app_path()
        path_no_dpi = misc_utils.path_combine3(app_path, path, file_name)

        if dpi == None or dpi == "":
            image_path = path_no_dpi
        else:
            image_path = misc_utils.path_combine3(app_path, path + "-" + dpi, file_name)
        
        if not os.path.exists(image_path):
            image_path = path_no_dpi
        
        if not os.path.exists(image_path):
            print("Gif file not found: %s" % image_path)
            return None
        
        return GIFImage(str(image_path))
    
    def create_image_from_text(self, text, dpi):
        """
            Create surface from given text and dpi
            @return 
                None on failed.
                Surface on success.
        """
        if text == None or text == "":
            return None

        path1 = misc_utils.get_app_path()
        path2 = misc_utils.path_combine3(path1, "images/flags", "letters-" + dpi)
        files = ()
        for ch in text:
            if ord(ch) == ord('.'):
                files += (misc_utils.path_combine(path2, 'dot.gif'),)
            elif ord(ch) == ord(':'):
                files += (misc_utils.path_combine(path2, 'colon.gif'),)
            elif ord(ch) == ord(' '):
                files += (misc_utils.path_combine(path2, 'space.gif'),)
            elif ord(ch) == ord('*'):
                files += (misc_utils.path_combine(path2, 'asterisk.gif'),)
            elif ord(ch) == ord('\\'):
                files += (misc_utils.path_combine(path2, 'bslash.gif'),)
            elif ord(ch) == ord('/'):
                files += (misc_utils.path_combine(path2, 'slash.gif'),)
            elif ord(ch) == ord('>'):
                files += (misc_utils.path_combine(path2, 'greater.gif'),)
            elif ord(ch) == ord('<'):
                files += (misc_utils.path_combine(path2, 'less.gif'),)
            elif ord(ch) == ord('|'):
                files += (misc_utils.path_combine(path2, 'pipe.gif'),)
            elif ord(ch) == ord('?'):
                files += (misc_utils.path_combine(path2, 'question.gif'),)
            elif ord(ch) == ord('"'):
                files += (misc_utils.path_combine(path2, 'quote.gif'),)
            elif ord(ch) >= ord('a') and ord(ch) <= ord('z'):
                files += (misc_utils.path_combine(path2, '_' + ch + '.gif'),)
            else:
                files += (misc_utils.path_combine(path2, ch + '.gif'),)

        return self.combine_images(files)

    def split_text_to_lines(self, text, max_char_per_line):
        """
            Split a long line of text to multiple shorter lines.
            Use special characters like: space, dot, comma, semicolon to split the line
            
            @return 
                Tuple contains lines of text
        """
        if text == None or text == "":
            return ()
        
        if len(text) <= max_char_per_line:
            return (text,)
        
        lines = ()
        while len(text) > max_char_per_line:
            i = max_char_per_line - 1
            line = None
            while i >= 0:
                ch = text[i]
                if ch == ' ' or ch == '.' or ch == ',' or ch == ';':
                    line = text[:i+1]
                    text = text[i+1:]
                    break
                i = i-1
            
            if line == None:
                line = text[:max_char_per_line]
                text = text[max_char_per_line:]

            if line == "":
                text = text[1:]
            else:
                lines += (line, )
        
        lines += (text, )
        return lines
        
    def create_clock_image(self, time_sec):
        """
            Create clock surface from given total seconds. Clock format: MM:ss

            @param timeSec  Time in seconds
            @return 
                None on failed.
                Surface on success.
        """
        if time_sec < 0:
            time_sec = 0
        
        hour = time_sec/3600
        minute = (time_sec%3600)/60
        second = time_sec%60
        
        if hour > 0:
            clock_text = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
        else:
            clock_text = "{:02d}:{:02d}".format(minute, second)

        return self.create_image_from_text(clock_text, "x10hdpi")
    
    def create_lap_counter_clock_image(self, time_sec, panel_width):
        """
            Create lap counter clock surface from given total seconds. Clock format: HH:mm:ss

            @param timeSec  Time in seconds
            @return 
                None on failed.
                Surface on success.
        """
        if time_sec < 0:
            time_sec = 0
        
        hour = time_sec/3600
        minute = (time_sec%3600)/60
        second = time_sec%60
        clock_text = "{:02d}:{:02d}:{:02d}".format(hour, minute, second)
        return self.create_image_from_text(clock_text, "x11hdpi")

    def create_image_from_lines(self, text, panel_width, dpi_array):
        """
            Create image surface from given multi lines text.

            @param text         A text contains multi lines
            @param panel_width  The width of panel 
            @return 
                None on failed.
                Surface on success.
        """
        # Split text message by newline
        text = text.replace("\r", "")
        lines = text.split("\n")

        # Remove empty line
        lines = [s for s in lines if s != ""] 

        # Find row with highest length
        max_line = max(lines, key=len)
        max_len = len(max_line)

        # Check the best dpi that fit text message
        dpi_fit = dpi_array[0]

        for dpi in dpi_array:
            img0 = image_utils.create_image_from_text("8", dpi)
            (w0, h0) = img0.get_size()

            if (w0 * max_len) >= (panel_width - 5):
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

        return img1
    
    def combine_surfaces(self, surf1, surf2, position):
        """ Combine 2 surfaces into 1 single surface.

            @param surf1 Background image surface
            @param surf2 Overlay image surface
            @param position Tuple contains left, top position of surf2
            @return Surface contains image
        """
        if surf2 == None:
            return surf1
        if position == None:
            position = (0, 0)
        
        (w1, h1) = surf1.get_size()
        (w2, h2) = surf2.get_size()
        w2 += position[0]
        h2 += position[1]

        w = max(w1, w2)
        h = max(h1, h2)

        surf0 = pygame.Surface((w, h))
        surf0.blit(surf1, (0, 0))
        surf0.blit(surf2, position)
        return surf0
    
    def create_empty_surface(self, width, height):
        """ Create an empty surface with given size.

            @param width
            @param height
            @return Surface
        """
        size = (width, height)
        surf = pygame.Surface(size)
        return surf

# public instances
image_utils = ImageUtils()
misc_utils = MiscUtils()
