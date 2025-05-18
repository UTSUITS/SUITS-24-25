import gps

def get_gps_data():
    session = gps.gps(mode=gps.WATCH_ENABLE)
    try:
        while True:
            report = session.next()
            if getattr(report, 'class', None) == 'TPV':
                latitude = getattr(report, 'lat', None)
                longitude = getattr(report, 'lon', None)
                altitude = getattr(report, 'alt', None)
                print(f"Latitude: {latitude}, Longitude: {longitude}, Altitude: {altitude}")
    except StopIteration:
        print("No GPS data available.")
    except KeyError:
        pass
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    get_gps_data()
