import pickle
from datetime import datetime, time

def time_difference(time1, time2):
    common_date = datetime(2023, 1, 1)
    datetime1 = datetime.combine(common_date, time1)
    datetime2 = datetime.combine(common_date, time2)

    time_diff = datetime2 - datetime1

    return time_diff

def get_free_rooms():
    with open("lesson_times.pickle", "rb") as file:
        room_to_lesson_times = pickle.load(file)

    current_time = time(14, 15)

    free_rooms = []
    occupied_rooms = []

    for room_lesson_times in room_to_lesson_times:
        room = room_lesson_times[0]

        for i, lesson_time in enumerate(room_lesson_times[1]):
            if current_time <= lesson_time[0]:
                free_duration = time_difference(current_time, lesson_time[0])
                free_rooms.append((room, free_duration))
                break
            elif current_time >= lesson_time[1]:
                if i == len(room_lesson_times[1]) - 1:
                    free_duration = time_difference(current_time, time.max)
                    free_rooms.append((room, free_duration))
                    break
                continue
            elif current_time >= lesson_time[0]:
                if i < len(room_lesson_times[1]) - 1:
                    next_lesson_time = room_lesson_times[1][i + 1]
                    free_duration = time_difference(lesson_time[1], next_lesson_time[0])
                else:
                    free_duration = time_difference(current_time, time.max)

                if current_time <= lesson_time[1]:
                    occupied_duration = time_difference(current_time, lesson_time[1])
                    occupied_rooms.append((room, occupied_duration, free_duration))
                    break

    free_rooms.sort(key=lambda x: x[1], reverse=True)
    occupied_rooms.sort(key=lambda x: (x[1], -x[2]), reverse=False)

    free_rooms = [(room[0], str(room[1])) for room in free_rooms]
    occupied_rooms = [(room[0], str(room[1]), str(room[2])) for room in occupied_rooms]
    print(free_rooms)
    print(occupied_rooms)
