def read_sensors(cooler, psutil=False):
    sensors = {}
    if cooler.hasattr('read_temperature'):
        sensors[cooler.description] = cooler.read_temperature()
    if psutil:
        import psutil
        for m, li in psutil.sensors_temperatures().items():
            for label, current, _, _ in li:
                sensors['{}:{}'.format(m, label)] = current
    return sensors
