from datetime import datetime, timedelta
import requests

START = datetime(1900, 1, 1, 10, 0, 0)
END = datetime(1900, 1, 1, 19, 0, 0)

all_reserved = {}
testing_times = [("10:00:00", "11:45:00"), ("13:15:00", "14:30:00"), ("12:30:00", "14:00:00"), ("17:00:00", "17:15:00")]


def populate_free(curr_date):
    """
    Populates list of free times given list of reserved times
    :return: list of free times
    """

    free_arr = []

    if curr_date not in all_reserved:
        all_reserved[curr_date] = []

    reserved = all_reserved[curr_date]

    # Set entire day to one big free slot
    if len(reserved) == 0:
        free_arr.append((START, END))
    else:
        for i in range(len(reserved)):
            # If there is gap between first reserved slot and start of day
            if i == 0 and reserved[i][0] > START:
                free_arr.append((START, reserved[i][0]))
            else:
                # If next reserved slot starts after current slot ends (there is a gap)
                if reserved[i][0] > reserved[i - 1][1]:
                    free_arr.append((reserved[i - 1][1], reserved[i][0]))

        # If there is gap between last reserved slot and end of day
        if reserved[-1][1] < END:
            free_arr.append((reserved[-1][1], END))

    return free_arr


def check_time(time, curr_date):
    """
    Checks if time should be reserved or not
    :param curr_date:
    :param time: Time in format "HH:MM:SS"
    :return: Boolean true/false
    """
    start = datetime.strptime(time[0], "%H:%M:%S")
    end = datetime.strptime(time[1], "%H:%M:%S")

    free = populate_free(curr_date)

    for empty_times in free:
        if empty_times[1] - empty_times[0] >= timedelta(minutes=30) and empty_times[0] <= start < empty_times[1] and empty_times[0] < end <= empty_times[1]:
            return True

    return False


def insert_reserved_time(time, curr_date):
    start = datetime.strptime(time[0], "%H:%M:%S")
    end = datetime.strptime(time[1], "%H:%M:%S")

    free = populate_free(curr_date)

    if curr_date not in all_reserved:
        all_reserved[curr_date] = []

    reserved = all_reserved[curr_date]

    for empty_times in free:
        if empty_times[1] - empty_times[0] >= timedelta(minutes=30) and empty_times[0] <= start < empty_times[1]:
            if len(reserved) == 0:
                reserved.append((start, end))
            else:
                for i in range(len(reserved)):
                    if start < reserved[i][0]:
                        reserved.insert(i, (start, end))
                        break
                else:
                    reserved.append((start, end))


resp = requests.get("http://mangotests.asuscomm.com/getallbookings").json()
for booking in resp:
    date = datetime.strptime(booking["bookingDate"], "%Y-%m-%d")
    date_formatted = date.strftime("%d/%m/%Y")
    if date_formatted not in all_reserved:
        all_reserved[date_formatted] = []

    insert_reserved_time((booking["bookingStartTime"], booking["bookingEndTime"]), date_formatted)

print(all_reserved)