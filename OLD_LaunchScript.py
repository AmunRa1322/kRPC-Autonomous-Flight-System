import krpc
import math
import time

# connection to server
conn = krpc.connect(
    name='LaunchSequence',
    address='127.0.0.1',
    rpc_port=1000, stream_port=1004)

# definitions
vessel1 = conn.space_center.active_vessel
stage_resources = []
flight_info = vessel1.flight()
turn_start_alt = 250
turn_end_alt = 45000
target_alt = 100000
print(vessel1.name)

ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, flight_info, 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel1.orbit, 'apoapsis_altitude')
print(vessel1.control.current_stage)
start_stage = vessel1.control.current_stage
stage_1_fuel = vessel1.resources_in_decouple_stage(stage=start_stage-2, cumulative=False)
print(start_stage-2)
print('LFO = ', stage_1_fuel.amount('LiquidFuel'))
print('SFO = ', stage_1_fuel.amount('SolidFuel'))

srb_fuel = conn.add_stream(stage_1_fuel.amount, 'SolidFuel')
print(srb_fuel())

vessel1.control.sas = False
vessel1.control.rcs = False
vessel1.control.throttle = 1.0

vessel_state = vessel1.situation
print(type(vessel_state))
print(vessel_state)
if "VesselSituation.pre_launch" not in str(vessel_state):
    print('Vessel not in pre-launch, aborting')
    exit()
# Countdown...
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')

# Activate the first stage
vessel1.control.activate_next_stage()
vessel1.auto_pilot.engage()
vessel1.auto_pilot.target_pitch_and_heading(90, 90)

# Main ascent loop
srbs_separated = False
turn_angle = 0
while True:
    # Gravity turn
    if altitude() > turn_start_alt and altitude() < turn_end_alt:
        frac = ((altitude() - turn_start_alt) /
                (turn_end_alt - turn_start_alt))
        new_turn_angle = frac * 90
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            vessel1.auto_pilot.target_pitch_and_heading(90 - turn_angle, 90)
    # Separate SRBs when empty
    if not srbs_separated:
        if srb_fuel() < 0.1:
            vessel1.control.activate_next_stage()
            srbs_separated = True
            print('SRBs separated')
    if apoapsis() > target_alt*0.9:
        print('Approaching target apoapsis')
        break

# Disable engines when target apoapsis is reached
vessel1.control.throttle = 0.25
while apoapsis() < target_alt:
    pass
print('Target apoapsis reached')
vessel1.control.throttle = 0.0

# Wait until out of atmosphere
print('Coasting out of atmosphere')
while altitude() < 70500:
    pass
vessel1.control.activate_next_stage()
# Plan circularization burn (using vis-viva equation)
print('Planning circularization burn')
mu = vessel1.orbit.body.gravitational_parameter
r = vessel1.orbit.apoapsis
a1 = vessel1.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu*((2./r)-(1./a1)))
v2 = math.sqrt(mu*((2./r)-(1./a2)))
delta_v = v2 - v1
node = vessel1.control.add_node(
    ut() + vessel1.orbit.time_to_apoapsis, prograde=delta_v)

# Calculate burn time (using rocket equation)
F = vessel1.available_thrust
Isp = vessel1.specific_impulse * 9.82
m0 = vessel1.mass
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# Orientate ship
print('Orientating ship for circularization burn')
vessel1.auto_pilot.reference_frame = node.reference_frame
vessel1.auto_pilot.target_direction = (0, 1, 0)
vessel1.auto_pilot.wait()

# Wait until burn
print('Waiting until circularization burn')
burn_ut = ut() + vessel1.orbit.time_to_apoapsis - (burn_time/2.)
lead_time = 5
conn.space_center.warp_to(burn_ut - lead_time)

# Execute burn
print('Ready to execute burn')

time_to_apoapsis = conn.add_stream(getattr, vessel1.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2.) > 0:
    pass
print('Executing burn')
vessel1.control.throttle = 1.0
time.sleep(burn_time - 0.1)
print('Fine tuning')
vessel1.control.throttle = 0.05
remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
while remaining_burn()[1] > 0.1:
    pass
vessel1.control.throttle = 0.0
node.remove()
print('Launch complete')
