# -*- coding: utf-8 -*-

__author__ = "Austin Hurst"

import os
import random

import klibs
from klibs import P
from klibs.KLGraphics import fill, flip, blit, NumpySurface
from klibs.KLGraphics import KLDraw as kld
from klibs.KLEventQueue import pump, flush
from klibs.KLUserInterface import any_key, key_pressed, ui_request
from klibs.KLUtilities import deg_to_px
from klibs.KLCommunication import message
from klibs.KLTime import CountDown

from PIL import Image

from responselistener import KeyPressListener


WHITE = (255, 255, 255)



class HLJT(klibs.Experiment):

	def setup(self):

		# Stimulus sizes
		fix_size = deg_to_px(0.5)
		fix_thickness = deg_to_px(0.1)
		img_height = int(P.screen_y * 0.6)

		self.fixation = kld.FixationCross(fix_size, fix_thickness, fill=WHITE)

		tmp = "{0}_{1}_{2}"
		hands = ['L', 'R']
		sexes = ['F', 'M']
		angles = [60, 90, 120, 240, 270, 300]

		self.images = {}
		for hand in hands:
			for sex in sexes:
				for angle in angles:
					# Load in image file and get its aspect ratio
					basename = tmp.format(sex, hand, angle)
					img = Image.open(os.path.join(P.image_dir, basename + ".png"))
					aspect = img.size[0] / float(img.size[1])
					# Resize the image while preserving aspect ratio
					new_size = (int(round(img_height * aspect)), img_height)
					img = img.resize(new_size, resample=Image.LANCZOS)
					# Save resized image to dict
					self.images[basename] = img

		# Initialize the response collector
		self.key_listener = KeyPressListener({
			'p': "R", # Right hand
			'q': "L", # Left hand
		})

		# Initialize runtime variables
		self.trials_since_break = 0

		# Insert familiarization block
		self.first_block = False
		if P.run_practice_blocks:
			self.insert_practice_block(1, trial_counts=12)

		# Experiment start message
		msg = message("Press any key to begin.", blit_txt=False)
		fill()
		blit(msg, 5, P.screen_c)
		flip()
		flush()
		any_key()

		self.instructions()


	def instructions(self):

		header_loc = (P.screen_c[0], int(P.screen_y * 0.2))
		text_loc = (P.screen_c[0], int(P.screen_y * 0.3))
		msg1 = message("Welcome to the Hand Laterality Judgement Task!", blit_txt=False)
		msg2 = message(
			("During this task, you will be shown a series of hands at different\n"
			 "angles and rotations. Your job will be to report whether each hand\n"
			 "is a right hand or a left hand."),
			blit_txt=False, align='center'
		)
		msg3 = message(
			("If you think the hand is a left hand, press the [q] key.\n"
			 "If you think it is a right hand, press the [p] key."),
			blit_txt=False, align='center'
		)
		next_msg = message("Press space to continue", blit_txt=False)

		hand_offsets = [-2, -1, 0, 1, 2]
		hands_width = int(P.screen_x * 0.6)
		hand_width = int(hands_width / (len(hand_offsets) + 1))
		hand_offset = hand_width + int(hand_width / 4)

		demo_hands = []
		for i in range(len(hand_offsets)):
			rotation = random.choice(self.trial_factory.exp_factors['rotation'])
			hand_name = random.choice(list(self.images.keys()))
			img = self.images[hand_name].rotate(rotation)
			demo_hands.append(NumpySurface(img, width=hand_width))
		demo_hand_l = NumpySurface(self.images["F_L_90"], width=hand_width)
		demo_hand_r = NumpySurface(self.images["F_R_90"], width=hand_width)

		flush()
		min_wait = CountDown(1.5)
		done = False
		while not done:
			q = pump(True)
			ui_request(queue=q)
			fill()
			blit(msg1, 5, header_loc)
			blit(msg2, 8, text_loc)
			for i in range(len(hand_offsets)):
				x_loc = int(P.screen_c[0] + (hand_offsets[i] * hand_offset))
				y_loc = int(P.screen_y * 0.6)
				blit(demo_hands[i], 5, (x_loc, y_loc))
			if not min_wait.counting():
				blit(next_msg, 5, (P.screen_c[0], int(P.screen_y * 0.85)))
				if key_pressed("space", queue=q):
					done = True
			flip()

		min_wait = CountDown(1.5)
		done = False
		while not done:
			q = pump(True)
			ui_request(queue=q)
			fill()
			blit(msg3, 8, text_loc)
			blit(demo_hand_l, 5, (int(P.screen_x * 0.4), int(P.screen_y * 0.6)))
			blit(demo_hand_r, 5, (int(P.screen_x * 0.6), int(P.screen_y * 0.6)))
			if not min_wait.counting():
				blit(next_msg, 5, (P.screen_c[0], int(P.screen_y * 0.85)))
				if key_pressed("space", queue=q):
					done = True
			flip()


	def block(self):
		if self.first_block:
			self.trials_since_break = 0
			msg1 = message("Practice complete!", blit_txt=False)
			msg2 = message("Press any key to begin the experiment.", blit_txt=False)
			wait_msg(msg1, msg2)
			self.first_block = False

		elif P.practicing:
			msg1 = message(
				("You will now complete a few practice trials to familiarize\n"
				 "you with the task."),
				blit_txt=False, align='center'
			)
			msg2 = message("Press any key to begin.", blit_txt=False)
			wait_msg(msg1, msg2)
			self.first_block = True


	def trial_prep(self):
		# Check if it's time for a break
		if self.trials_since_break >= P.break_interval:
			self.task_break()
			self.trials_since_break = 0

		# Prepare (and rotate) the hand image for the trial
		img_name = "{0}_{1}_{2}".format(self.sex, self.hand, self.angle)
		img = self.images[img_name].rotate(self.rotation)
		self.hand_image = NumpySurface(img)


	def trial(self):

		# Draw fixation and wait fixation period
		fill()
		blit(self.fixation, 5, P.screen_c)
		flip()
		fixation_period = CountDown(1.0)
		while fixation_period.counting():
			ui_request()

		# Show the hand stimulus on the screen
		fill()
		blit(self.hand_image, 5, P.screen_c)
		flip()

		# Initialize and enter the response collection loop
		response = self.key_listener.collect()

		return {
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"hand": self.hand,
			"sex": self.sex,
			"angle": self.angle,
			"rotation": self.rotation,
			"judgement": response.value,
			"rt": response.rt,
			"accuracy": response.value == self.hand,
		}


	def task_break(self):
		msg1 = message("Take a break!", blit_txt=False)
		msg2 = message("Press space to continue.", blit_txt=False)
		flush()
		break_minimum = CountDown(1.5)
		done = False
		while not done:
			fill()
			blit(msg1, 5, P.screen_c)
			if not break_minimum.counting():
				blit(msg2, 5, (int(P.screen_x / 2), int(P.screen_y * 0.6)))
			flip()
			if key_pressed('space'):
				done = True


	def trial_clean_up(self):
		self.trials_since_break += 1


	def clean_up(self):
		pass


def wait_msg(msg1, msg2, delay=1.0):
    # Show first part of message and wait for the delay
    message_interval = CountDown(delay)
    while message_interval.counting():
        ui_request() # Allow quitting during loop
        fill()
        blit(msg1, 8, (P.screen_c[0], P.screen_y*0.4))
        flip()
    flush()
    
    # Show the second part of the message and wait for input
    fill()
    blit(msg1, 8, (P.screen_c[0], P.screen_y*0.4))
    blit(msg2, 5, [P.screen_c[0], P.screen_y*0.6])
    flip()
    any_key()
