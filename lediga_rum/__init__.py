import time
from lesson_times import save_lesson_times

start_time = time.time()
save_lesson_times()
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Function took {elapsed_time} seconds to execute.")
