from klibs.KLIndependentVariable import IndependentVariableSet


# Initialize object containing project's factor set

HLJT_ind_vars = IndependentVariableSet()


# Define project variables and variable types

HLJT_ind_vars.add_variable('hand', str, ['L', 'R'])
HLJT_ind_vars.add_variable('sex', str, ['F', 'M'])
HLJT_ind_vars.add_variable('angle', int, [60, 90, 120, 240, 270, 300])
HLJT_ind_vars.add_variable('rotation', int, [0, 60, 300])
