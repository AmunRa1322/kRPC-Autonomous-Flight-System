import krpc
import time
import fnmatch
import array

# connection to server
conn = krpc.connect(
    name='Staging Monitor',
    address='127.0.0.1',
    rpc_port=1000, stream_port=1004)

vessel1 = conn.space_center.active_vessel
print(vessel1.name)
resource_types = vessel1.resources.names
print(resource_types)
fuel_types = fnmatch.filter(resource_types, '*Fuel')
print(fuel_types)
print(vessel1.control.current_stage)

# Find stages with engines to activate
engine_act_stages = []
for Engine in vessel1.parts.engines:
    engine_act_stages.append(Engine.part.stage)
    print(engine_act_stages)

while vessel1.control.current_stage > 0:
    while vessel1.control.current_stage in engine_act_stages:
        print('start loop')
        fuel_amount = [0 for x in range(5)]
        print(fuel_amount)
        stage_fuel = 1
        while stage_fuel >= 0.1:
            for index, fuel in enumerate(fuel_types):
                fuel_amount[index] = vessel1.resources_in_decouple_stage(stage=vessel1.control.current_stage-1, cumulative=False).amount(fuel)
                print(fuel_amount[index])
            print(fuel_amount)
            stage_fuel = sum(fuel_amount)
            print(stage_fuel)
            time.sleep(0.1)
        print("Booster separation")
        vessel1.control.activate_next_stage()