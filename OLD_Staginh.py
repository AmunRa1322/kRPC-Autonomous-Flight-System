import krpc
import array
import time

# connection to server
conn = krpc.connect(
    name='LaunchSequence',
    address='127.0.0.1',
    rpc_port=1000, stream_port=1004)

vessel1 = conn.space_center.active_vessel
stage_resources = []
flight_info = vessel1.flight()

print(vessel1.control.current_stage)
start_stage = vessel1.control.current_stage
stage_1_fuel = vessel1.resources_in_stage(stage=start_stage, cumulative=False)
print(start_stage)
print('LFO = ', stage_1_fuel.amount('LiquidFuel'))
print('SFO = ', stage_1_fuel.amount('SolidFuel'))

srb_fuel = conn.add_stream(stage_1_fuel.amount, 'SolidFuel')
liq_fuel = conn.add_stream(stage_1_fuel.amount, 'LiquidFuel')
print(srb_fuel())


srbs_separated = False
parts = vessel1.parts.in_decouple_stage(vessel1.control.current_stage-2)
print(parts)
# Separate SRBs when empty

for part in parts:
    engine = part.engines
    print(engine)
    print(engine.active)
    print(engine.has_fuel)

    if engine and engine.active and engine.has_fuel:
        print(engine)
        print(engine.active)
        print(engine.has_fuel)
    print(engine)
print('end')
exit()

if not srbs_separated:
    if srb_fuel() < 0.1:
        vessel1.control.activate_next_stage()
        srbs_separated = True
        print('SRBs separated')