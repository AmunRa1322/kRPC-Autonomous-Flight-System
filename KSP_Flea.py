import krpc
import time

conn = krpc.connect(
    name='Flea',
    address='127.0.0.1',
    rpc_port=1000, stream_port=1004)


vessel = conn.space_center.active_vessel
loopAlt = []
flight_info = vessel.flight()
vessel.control.activate_next_stage()
while True:
    print("Loop start")
    loopAlt.clear()
    for _ in range(3):

        loopAlt.append(flight_info.mean_altitude)
        print(loopAlt)
        time.sleep(1)
    if loopAlt[2] < loopAlt[1] and loopAlt[1] < loopAlt[0]:
        vessel.control.activate_next_stage()
        print("losing alt")
        break

print("Loop End")
