import io
import os
import subprocess
import matplotlib.pyplot as plt
from tqdm import tqdm
def get_bitrate_every_second(process, raw_data_filename, file_duration):
   time_values, bitrates_per_second, current_bitrate_mbps = [], [], 0
   check_time, dts_packet_sizes = 1, {}
   progress_bar = tqdm(total=file_duration, unit='s', dynamic_ncols=True)
   previous_dts_time = 0
   for line in io.TextIOWrapper(process.stdout, encoding="UTF-8"):
       dts_time, packet_size = map(float, line.strip().split(","))
       packet_size = (packet_size * 8) / 1_000_000
       dts_packet_sizes[dts_time] = packet_size
       progress_bar.update(dts_time - previous_dts_time)
       previous_dts_time = dts_time
   progress_bar.close()
   ordered_dict = dict(sorted(dts_packet_sizes.items()))
   for dts_time, packet_size in ordered_dict.items():
       if dts_time >= check_time:
           time_values.append(dts_time)
           bitrates_per_second.append(current_bitrate_mbps)
           with open(raw_data_filename, 'a') as f:
               f.write(f"Timestamp: {dts_time} --> {round(current_bitrate_mbps, 3)} Kbps\n")
           current_bitrate_mbps = packet_size
           check_time += 1
       else:
           current_bitrate_mbps += packet_size
   return time_values, bitrates_per_second
filename = "Crop_fit.mp4"
stream_specifier = "V:0"
file_duration = float(subprocess.run(["ffprobe", "-v", "error", "-threads", str(os.cpu_count()),
                                     "-select_streams", stream_specifier,
                                     "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                                     filename], capture_output=True, text=True).stdout.strip())
number_of_frames = int(subprocess.run(["ffprobe", "-v", "error", "-threads", str(os.cpu_count()),
                                      "-select_streams", stream_specifier,
                                      "-show_entries", "stream=nb_frames", "-of", "default=noprint_wrappers=1:nokey=1",
                                      filename], capture_output=True, text=True).stdout.strip())
timestamp_bitrate_file = f"detailed_bitrates_{filename}.txt"
os.makedirs(f"[{filename}]", exist_ok=True)
open(timestamp_bitrate_file, 'w').close()
cmd = ["ffprobe", "-v", "error", "-threads", str(os.cpu_count()),
      "-select_streams", stream_specifier,
      "-show_entries", "packet=dts_time,size",
      "-of", "csv=print_section=0:nk=1",
      filename]
process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
time_values, bitrates_per_second = get_bitrate_every_second(process, timestamp_bitrate_file, file_duration)
bitrates_per_second = [bitrate * 1000 for bitrate in bitrates_per_second]
time_values = [time / 60 for time in time_values]
plt.figure(figsize=(15, 7))
plt.suptitle(f"{filename}\nMin: {min(bitrates_per_second)} | Max: {max(bitrates_per_second)} | Avg: {sum(bitrates_per_second) / len(bitrates_per_second)} Kbps")
plt.xlabel("Time (minutes)")
plt.ylabel("Bitrate (Kbps)")
plt.plot(time_values, bitrates_per_second, linewidth=0.7, color='orange')
plt.show()
