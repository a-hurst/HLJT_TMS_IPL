# Hand Laterality Judgement Task

The Hand Laterality Judgement Task (HLJT) is a paradigm for measuring motor imagery performance, first described in [Cooper and Shepard (1975)](https://psycnet.apa.org/doi/10.1037/0096-1523.1.1.48) and extended in later work (e.g. [Ter Horst et al., 2010](https://doi.org/10.1007/s00221-010-2235-1)). This version is based on the implementation described in [Kraeutner et al. (2020)](https://doi.org/10.1016/j.psychsport.2020.101673).

![HLJT Animation](task.gif)

During the HLJT, images of left and right hands are presented on screen at different viewing angles and rotations, and participants are asked to judge whether each presented hand is a left hand or right hand using the keyboard.


## Requirements

This version of the HLJT is programmed in Python 3.9 using the [KLibs framework](https://github.com/a-hurst/klibs). It is written to be platform-independent and is tested and working on recent versions of macOS, Windows, and Linux.


## Getting Started

### Installation

First, you will need to install the KLibs framework by following the instructions [here](https://github.com/a-hurst/klibs).

Then, you can then download and install the experiment program with the following commands (replacing `~/Downloads` with the path to the folder where you would like to put the program folder):

```
cd ~/Downloads
git clone https://github.com/LBRF/HLJT.git
```

### Running the Experiment

This implementation of the HLJT is a KLibs experiment, meaning that it is run using the `klibs` command at the terminal (running the 'experiment.py' file using Python directly will not work).

To run the experiment, navigate to the HLJT folder in Terminal and run `klibs run [screensize]`,
replacing `[screensize]` with the diagonal size of your display in inches (e.g. `klibs run 24` for a 24-inch monitor). If you just want to test the program out for yourself and skip demographics collection, you can add the `-d` flag to the end of the command to launch the experiment in development mode.


### Exporting Data

To export data from the HLJT, simply run

```
klibs export
```

while in the HLJT directory. This will export the data for each participant into individual tab-separated text files in the project's `ExpAssets/Data` subfolder.
