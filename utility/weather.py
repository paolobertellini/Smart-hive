import pyowm


def weather(location):
    owm = pyowm.OWM('c984a283dfd9a79d06e234a7c62f2e2a')
    mgr = owm.weather_manager()
    observation = mgr.weather_at_place(location + ', IT')
    w = observation.weather
    temp = w.temperature('celsius')
    status = w.detailed_status
    return ({'temperature': temp, 'status': status})
# c984a283dfd9a79d06e234a7c62f2e2a
# 3164794
