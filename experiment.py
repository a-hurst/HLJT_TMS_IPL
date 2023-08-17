# -*- coding: utf-8 -*-

__author__ = "Austin Hurst"

import os
import time
import random

import klibs
from klibs import P
from klibs.KLGraphics import fill, flip, blit, NumpySurface
from klibs.KLGraphics import KLDraw as kld
from klibs.KLEventQueue import pump, flush
from klibs.KLUserInterface import any_key, key_pressed, ui_request
from klibs.KLUtilities import deg_to_px
from klibs.KLCommunication import message
from klibs.KLTime import CountDown, precise_time

from PIL import Image, ImageOps, ImageEnhance

from responselistener import KeyPressListener
from communication import get_trigger_port, get_tms_controller


WHITE = (255, 255, 255)



class HLJT(klibs.Experiment):

	def setup(self):

		# Initialize communication with with the TMS and trigger port
		self.trigger = get_trigger_port()
		self.trigger.add_codes(P.trigger_codes)
		self.magstim = get_tms_controller()

		# Stimulus sizes
		fix_size = deg_to_px(0.5)
		fix_thickness = deg_to_px(0.1)
		img_height = deg_to_px(P.hand_size_deg)

		self.fixation = kld.FixationCross(fix_size, fix_thickness, fill=WHITE)

		tmp = "{0}_{1}_{2}"
		hands = ['L', 'R']
		sexes = ['F', 'M']
		angles = [60, 90, 120, 240, 270, 300]

		self.images = {}
		for hand in hands:
			for sex in sexes:
				for angle in angles:
					# Load in image file and crop out the transparent regions
					basename = tmp.format(sex, hand, angle)
					img = Image.open(os.path.join(P.image_dir, basename + ".png"))
					img = img.crop(img.getbbox())
					# If requested, convert hand images to greyscale
					if P.greyscale_hands:
						img = ImageOps.grayscale(img)
						enhancer = ImageEnhance.Brightness(img)
						img = enhancer.enhance(0.8)
					# Resize the image while preserving its aspect ratio
					img = img_scale(img, height=img_height)
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

		# Determine session type (sham or stim) based on condition
		session_seq = ["stim", "sham"] if P.condition == "A" else ["sham", "stim"]
		self.session_type = session_seq[P.session_number - 1]

		# Set power level to a percentage of the participant's RMT
		self.rmt = self.get_rmt_power()
		self.stim_power = int(round(self.rmt * 1.2))
		if self.session_type == "sham":
			self.stim_power = 15
		self.magstim.set_power(self.stim_power)

		# Gather possible TMS onset delays
		self.task_blocks = P.tms_pulse_delays.copy()
		random.shuffle(self.task_blocks)
		self.tms_pulse_onset = -1  # Default value, gets set later in block()

		# Run through task instructions
		if not P.resumed_session:
			self.instructions()
		random.seed(P.random_seed) # Ensures instructions don't affect random seed


	def get_rmt_power(self):
		rmt = self.magstim.get_power()
		txt = "Is {0}% the correct RMT for the participant? (Yes / No)"
		msg1 = message(txt.format(rmt), blit_txt = False)
		msg2 = message(
			"Please set the TMS power level to the correct RMT using the arrow keys,\n"
			"then press the [return] key to continue.",
			blit_txt = False, align = 'center'
		)

		rmt_confirmed = False
		flush()
		while not rmt_confirmed:
			# Draw RMT prompt to the screen
			fill()
			blit(msg1, 5, P.screen_c)
			flip()
			# Check for responses in input queue
			q = pump(True)
			if key_pressed('y', queue=q):
				rmt_confirmed = True
			elif key_pressed('n', queue=q):
				break

		# If TMS power level is incorrect, give chance to adjust w/ arrow keys
		rmt_temp = rmt
		while not rmt_confirmed:
			pwr_msg = message("Power level: {0}%".format(rmt_temp), blit_txt=False)
			fill()
			blit(msg2, 2, P.screen_c)
			blit(pwr_msg, 5, (P.screen_c[0], int(P.screen_y * 0.55)))
			flip()
			q = pump(True)
			if key_pressed('up', queue=q) and rmt_temp <= 100:
				rmt_temp += 1
			elif key_pressed('down', queue=q) and rmt_temp >= 0:
				rmt_temp -= 1
			elif key_pressed('return', queue=q):
				self.magstim.set_power(rmt_temp)
				time.sleep(0.1)  # Give the TMS a break between commands
				rmt = self.magstim.get_power()
				rmt_confirmed = True

		return rmt


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
		hand_rotations = random_choices(self.trial_factory.exp_factors['rotation'], 5)

		demo_hands = []
		for i in range(len(hand_offsets)):
			rotation = hand_rotations[i]
			hand_name = random.choice(list(self.images.keys()))
			img = img_scale(self.images[hand_name], height=hand_width)
			img = img.rotate(rotation, expand=True)
			demo_hands.append(NumpySurface(img))
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
				y_loc = int(P.screen_y * 0.65)
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
		# If not the practice block, grab the randomized TMS pulse onset for the block
		if not P.practicing:
			self.tms_pulse_onset = self.task_blocks.pop()

		# Maximum allowable gap between pulses is 8 trials, otherwise we risk the
		# TMS disarming from inactivity. The following code ensures that the maximum
		# possible interval between pulses is 8 trials.
		self.pulse_sequence = []
		if P.practicing:
			self.pulse_sequence = [False] * P.trials_per_block
		else:
			stim_sub_block = [True] * 4 + [False] * 4
			while len(self.pulse_sequence) < P.trials_per_block:
				random.shuffle(stim_sub_block)
				self.pulse_sequence += stim_sub_block

		if P.resumed_session:
			self.trials_since_break = P.trial_number % P.break_interval
			msg1 = message("Session reloaded successfully!", blit_txt=False)
			msg2 = message("Press any key to begin the experiment.", blit_txt=False)
			wait_msg(msg1, msg2)
			P.resumed_session = False

		elif self.first_block:
			self.trials_since_break = 0
			msg1 = message("Practice complete!", blit_txt=False)
			msg2 = message("Press any key to begin the experiment.", blit_txt=False)
			wait_msg(msg1, msg2)
			self.first_block = False

		elif P.practicing:
			msg1 = message(
				("You will now complete a few practice trials to familiarize\n"
				 "yourself with the task."),
				blit_txt=False, align='center'
			)
			msg2 = message("Press any key to begin.", blit_txt=False)
			wait_msg(msg1, msg2)
			self.first_block = True


	def trial_prep(self):
		# Check if it's time for a break
		if self.trials_since_break >= P.break_interval:
			self.magstim.disarm()
			self.task_break()
			self.trials_since_break = 0

		# Prepare (and rotate) the hand image for the trial
		img_name = "{0}_{1}_{2}".format(self.sex, self.hand, self.angle)
		img = self.images[img_name].rotate(self.rotation, expand=True)
		self.hand_image = NumpySurface(img)

		# Determine whether the current trial is a TMS pulse trial
		self.tms_trial = self.pulse_sequence.pop()

		# Ensure stimulator is armed before starting trial
		if not P.practicing and not self.magstim.armed:
			self.magstim.arm()


	def trial(self):

		# Draw fixation and wait fixation period
		fill()
		blit(self.fixation, 5, P.screen_c)
		flip()
		self.trigger.send('trial_start')
		fixation_period = CountDown(P.fixation_duration)
		while fixation_period.counting():
			ui_request()

		# Show the hand stimulus on the screen
		fill()
		blit(self.hand_image, 5, P.screen_c)
		flip()

		# Initialize timers and variables for the response collection loop
		self.key_listener.init()
		hand_shown = precise_time()
		pulse_delay = self.tms_pulse_onset / 1000
		allow_status_check = self.tms_trial == True
		allow_fire = self.tms_trial == True
		tms_fired = False

		# Enter the response collection loop
		response = None
		while not response:
			# Check for keypress responses
			q = pump(True)
			ui_request(queue=q)
			response = self.key_listener.listen(q)
			# 100 ms before pulse, make sure TMS is ready/able to fire
			elapsed = precise_time() - hand_shown
			if allow_status_check and elapsed > (pulse_delay - 0.1):
				if not self.magstim.ready:
					allow_fire = False
				allow_status_check = False
			# After pulse delay has elapsed, fire TMS
			elif allow_fire and elapsed > pulse_delay:
				self.trigger.send('fire_tms')
				tms_fired = True
				allow_fire = False
				if P.development_mode:
					# In dev mode, flash the screen when TMS is supposed to fire
					fill(WHITE)
					flip()
					fill(WHITE)
					flip()
					fill()
					blit(self.hand_image, 5, P.screen_c)
					flip()

		self.key_listener.cleanup()

		return {
			"session_num": P.session_number,
			"block_num": P.block_number,
			"trial_num": P.trial_number,
			"hand": self.hand,
			"sex": self.sex,
			"angle": self.angle,
			"rotation": self.rotation,
			"tms_onset": self.tms_pulse_onset,
			"sham": self.session_type == "sham",
			"judgement": response.value,
			"rt": response.rt,
			"accuracy": response.value == self.hand,
			"tms_trial": self.tms_trial,
			"tms_fired": tms_fired,
			"rmt": self.rmt,
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
		msg1 = message("You're all done, thanks for participating!", blit_txt=False)
		msg2 = message("Press any key to exit.", blit_txt=False)
		wait_msg(msg1, msg2, delay=1.5)



def random_choices(x, n=1):
	# Make random choices from a list, ensuring all elements from x are chosen
	# at least once if n >= len(x)
	out = x.copy()
	random.shuffle(out)
	while len(out) < n:
		more = x.copy()
		random.shuffle(more)
		out += more
	return out[:n]


def img_scale(img, width=None, height=None):
	# Resize an image while perserving its aspect ratio
	aspect = img.size[0] / float(img.size[1])
	if height:
		if width:
			new_size = (height, width)
		else:
			new_size = (int(round(height * aspect)), height)
	else:
		if width:
			new_size = (width, int(round(width / aspect)))
		else:
			return img.copy()
	return img.resize(new_size, resample=Image.LANCZOS)


def wait_msg(msg1, msg2, delay=1.5):
	# Try sizing/positioning relative to first message
	y1_loc = P.screen_y * 0.45 + (msg1.height / 2)
	y2_loc = y1_loc + msg2.height

	# Show first part of message and wait for the delay
	message_interval = CountDown(delay)
	while message_interval.counting():
		ui_request() # Allow quitting during loop
		fill()
		blit(msg1, 2, (P.screen_c[0], y1_loc))
		flip()
	flush()
	
	# Show the second part of the message and wait for input
	fill()
	blit(msg1, 2, (P.screen_c[0], y1_loc))
	blit(msg2, 8, [P.screen_c[0], y2_loc])
	flip()
	any_key()
