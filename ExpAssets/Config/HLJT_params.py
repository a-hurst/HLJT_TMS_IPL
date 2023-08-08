### Klibs Parameter overrides ###

#########################################
# Runtime Settings
#########################################
collect_demographics = True
manual_demographics_collection = False
manual_trial_generation = False
run_practice_blocks = True
multi_user = False
view_distance = 57 # in centimeters, 57cm = 1 deg of visual angle per cm of screen

#########################################
# TMS Configuration
#########################################
tms_serial_port = '/dev/ttyUSB0' # Usually 'COM1' on Windows
labjack_port = 'FIO' # Either FIO, EIO, or CIO
trigger_codes = {
    'trial_start': 2,
    'fire_tms': 17, # EMG marker 1 + fire TMS on pin 5
}

#########################################
# Environment Aesthetic Defaults
#########################################
default_fill_color = (0, 0, 0, 255)
default_color = (255, 255, 255, 255)
default_font_size = 0.6
default_font_unit = 'deg'
default_font_name = 'Hind-Medium'

#########################################
# EyeLink Settings
#########################################
manual_eyelink_setup = False
manual_eyelink_recording = False

saccadic_velocity_threshold = 20
saccadic_acceleration_threshold = 5000
saccadic_motion_threshold = 0.15

#########################################
# Experiment Structure
#########################################
trials_per_block = 72
blocks_per_experiment = 3
session_count = 2
table_defaults = {}
conditions = ["A", "B"]
default_condition = "A"

#########################################
# Development Mode Settings
#########################################
dm_auto_threshold = True
dm_trial_show_mouse = False
dm_ignore_local_overrides = False
dm_show_gaze_dot = True

#########################################
# Data Export Settings
#########################################
primary_table = "trials"
unique_identifier = "study_id"
exclude_data_cols = ["created"]
append_info_cols = ["random_seed"]
datafile_ext = ".txt"

#########################################
# PROJECT-SPECIFIC VARS
#########################################
break_interval = 36  # trials
fixation_duration = 3.5 # seconds
hand_size_deg = 8.0 # height of hand stimuli (in degrees)
tms_pulse_delays = [250, 500, 750] # milliseconds
greyscale_hands = True
