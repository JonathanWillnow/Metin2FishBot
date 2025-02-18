import numpy as np
import pydirectinput
import cv2 as cv
import math
from time import time
from windowcapture import WindowCapture
from hsvfilter import HsvFilter
from fishfilter import Filter
import constants
import time as time_count
import random

from nordvpn_switcher import initialize_VPN, rotate_VPN
instr = initialize_VPN(save = 1, area_input=['Germany'],skip_settings=1)

class FishingBot:

    #properties
    fish_pos_x = None
    fish_pos_y = None
    fish_last_time = None
    detect_text_enable = False
    botting = False

    FISH_RANGE = 74
    FISH_VELO_PREDICT = 30

    # BAIT_POSITION = (473, 750)
    # FISH_POSITION = (440, 750)

    FILTER_CONFIG = [49, 0, 58, 134, 189, 189, 0, 0, 0, 0]

    FISH_WINDOW_CLOSE = (430, 115)

    # set position of the fish windows
    # this value can be diferent by the sizes of the game window

    FISH_WINDOW_SIZE = (280, 226)
    FISH_WINDOW_POSITION = (95, 80)

    wincap = None

    fishfilter = Filter() if detect_text_enable else None

    # Load the needle image

    needle_img = cv.imread('images/fiss.jpg', cv.IMREAD_UNCHANGED)
    needle_img_clock = cv.imread('images/clock.jpg', cv.IMREAD_UNCHANGED)

    # Some time cooldowns

    detect_text = True

    # Limit time

    initial_time = None

    end_time_enable = False

    end_time = 0

    # for fps

    loop_time = time()

    # The mouse click cooldown

    timer_mouse = time()

    # The timer beteween the states

    timer_action = time()

    bait_time = 2
    throw_time = 0
    game_time = 2

    # This is the filter parameters, this help to find the right image
    hsv_filter = HsvFilter(*FILTER_CONFIG)

    state = 0

    def detect(self, haystack_img):

        # match the needle_image with the hasytack image
        result = cv.matchTemplate(haystack_img, self.needle_img, cv.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)

        # needle_image's dimensions
        needle_w = self.needle_img.shape[1]
        needle_h = self.needle_img.shape[0]

        # get the position of the match image
        top_left = max_loc
        bottom_right = (top_left[0] + needle_w, top_left[1] + needle_h)

        # Draw the circle of the fish limits
        cv.circle(haystack_img,
                (int(haystack_img.shape[1] / 2), int(haystack_img.shape[0] / 2)),
                self.FISH_RANGE, color=(0, 0, 255), thickness=1)

        # Only the max level of match is greater than 0.5
        if max_val > 0.5:
            pos_x = (top_left[0] + bottom_right[0])/2
            pos_y = (top_left[1] + bottom_right[1])/2

            if self.fish_last_time:
                dist = math.sqrt((pos_x - self.fish_pos_x)**2 + (self.fish_pos_y - pos_y)**2)
                cv.rectangle(haystack_img, top_left, bottom_right,
                            color=(0, 255, 0), thickness=2, lineType=cv.LINE_4)

                # Calculate the fish velocity
                velo = dist/(time() - self.fish_last_time)

                if velo == 0.0:
                    return (pos_x, pos_y, True)
                elif velo >= 150:

                    # With this velocity the fish position will be predict

                    pro = self.FISH_VELO_PREDICT / dist
                    destiny_x = int(pos_x + (pos_x - self.fish_pos_x) * pro)
                    destiny_y = int(pos_y + (pos_y - self.fish_pos_y) * pro)

                    # Draw the predict line

                    cv.line(haystack_img, (int(pos_x), int(pos_y)),
                            (destiny_x, destiny_y), (0, 255, 0),  thickness=3)

                    return (destiny_x, destiny_y, False)

            # get the fish position and the time

            self.fish_pos_x = pos_x
            self.fish_pos_y = pos_y
            self.fish_last_time = time()

        return None

    def detect_minigame(self, haystack_img):
        result = cv.matchTemplate(haystack_img, self.needle_img_clock, cv.TM_CCOEFF_NORMED)

        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(result)
        print(max_val)
        if max_val > 0.7:
            return True

        return False

    def detect_daily_reward(self, image):

        for i in range(0, 5):
            for j in range(0, 5):
                if image[10 + i,10 +  j, 0] + image[10 + i,10 +  j, 1] + image[10 + i,10 +  j, 2] > 0:
                    return False

        return True

    def set_to_begin(self, values):

        if values['-ENDTIMEP-']:
            self.end_time_enable = True
            try:
                self.end_time  = int(values['-ENDTIME-'])*60
            except:
                self.end_time = 0

        self.bait_time = values['-BAITTIME-']
        self.throw_time = values['-THROWTIME-']
        self.game_time = values['-STARTGAME-']

        self.wincap = WindowCapture(constants.GAME_NAME)
        self.state = 0
        self.initial_time = time()
        self.timer_action = time()

        mouse_x = int(self.FISH_WINDOW_POSITION[0] + self.wincap.offset_x + 200)
        mouse_y = int(self.FISH_WINDOW_POSITION[1] + self.wincap.offset_y + 200)

        pydirectinput.click(x=mouse_x, y=mouse_y, button='right')

    def runHack(self):
        screenshot = self.wincap.get_screenshot()

        # crop and aply hsv filter
        crop_img = screenshot[self.FISH_WINDOW_POSITION[1]:self.FISH_WINDOW_POSITION[1]+self.FISH_WINDOW_SIZE[1],
                            self.FISH_WINDOW_POSITION[0]:self.FISH_WINDOW_POSITION[0]+self.FISH_WINDOW_SIZE[0]]
        
        detect_end_img = screenshot
        crop_img = self.hsv_filter.apply_hsv_filter(crop_img)

        cv.putText(crop_img, 'FPS: ' + str(1/(time() - self.loop_time))[:2],
                (10, 200), cv.FONT_HERSHEY_SIMPLEX,  0.5, (0, 255, 0), 2)
        cv.putText(crop_img, 'State: ' + str(self.state) + ' ' + str(time() - self.timer_action)[:5],
                (10, 160), cv.FONT_HERSHEY_SIMPLEX,  0.5, (0, 255, 0), 2)
        self.loop_time = time()

        daily = self.detect_daily_reward(screenshot)

        if daily:
            mouse_x = int(self.wincap.offset_x + 350)
            mouse_y = int(self.wincap.offset_y + 280)
            pydirectinput.click(x=mouse_x, y=mouse_y)

        # Verify total time

        if self.end_time_enable and time() - self.initial_time > self.end_time:
            self.botting = False

        # State to click put the bait in the rod

        if self.state == 0:

            if time() - self.timer_action > self.bait_time:
                self.detect_text = True
                pydirectinput.keyDown('2')
                pydirectinput.keyUp('2')
                self.state = 1
                self.timer_action = time()

        # State to throw the bait

        if self.state == 1:
            if time() - self.timer_action > 0:
                time_count.sleep(random.uniform(0.15,0.3))
                pydirectinput.keyDown('1')
                pydirectinput.keyUp('1')
                self.state = 2
                self.timer_action = time()
            if time() - self.timer_action > 38+random.randint(1,8):
                time_count.sleep(random.uniform(0,2.5))
                self.timer_action = time()
                self.state = 0

        # Delay to start the clicks

        if self.state == 2:
            if time() - self.timer_action > self.game_time:
                time_count.sleep(random.uniform(0,0.5))
                self.state = 3
                self.timer_action = time()

        # Countdown to finish the state
        if self.state == 2:
            if time() - self.timer_action > 38+random.randint(1,8):
                time_count.sleep(random.uniform(0,2.5))
                self.timer_action = time()
                self.state = 0

        detected_end = self.detect_minigame(detect_end_img)
        if detected_end:
            fail = random.randint(3,10)
            if fail == 7:
                time_count.sleep(random.uniform(0.25,0.28))
            if fail == 5:
                time_count.sleep(random.uniform(0.15,0.35))
            time_count.sleep(random.uniform(0.1,0.23))
            pydirectinput.keyDown('1')
            pydirectinput.keyUp('1')
            time_count.sleep(random.uniform(0.2,1.7))
            if fail == 8:
                print("fail 8")
                time_count.sleep(random.uniform(4,9.7))
            if fail == 9:
                print("fail 9")
                time_count.sleep(random.uniform(5,17))
            if fail == 6:
                print("fail 6")
                time_count.sleep(random.uniform(2.0,3.7))
            self.state = 0
            self.timer_action = time()


        '''
        cv.imshow('Minha Janela', crop_img)

        if cv.waitKey(1) == ord('q'):
            cv.destroyAllWindows()
            return True
        '''

        return crop_img
