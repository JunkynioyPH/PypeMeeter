import subprocess, time
# import numpy as np

# Define your custom source and target nodes
target_input_device = "alsa_input.pci-0000_2f_00.4.analog-stereo" 
target_output_device = "Soundboard_Device" # Replace with your target sink name

# 1. Setup the Capture Process (Input)
input_command = [
    "ffmpeg",
    "-threads", "1",                  # Rule 2: Limit to a single thread
    "-thread_queue_size", "16",      # Rule 1: Shrink input buffer queue size
    "-f", "pulse",
    "-stream_name", f"IN_PypeMeeter-{target_input_device}",
    "-i", target_input_device,
    "-fflags", "nobuffer",
    "-f", "s16le", "-ac", "2", "-ar", "48000",
    "pipe:1"  # Write to stdout
]

# 2. Setup the Playback Process (Output)
output_command = [
    "ffmpeg",
    "-threads", "1",               # Force single-threading
    "-fflags", "nobuffer",         # Disable input buffering
    "-thread_queue_size", "16",    # Strictly limit the input pipe RAM buffer
    "-f", "s16le", 
    "-ac", "2", 
    "-ar", "48000",
    "-i", "pipe:0",                 # Read raw PCM from stdin
    "-f", "pulse",                  # Output muxer format
    "-buffer_duration", "2",        # 2ms hardware buffer duration (low latency/RAM)
    "-device", target_output_device, # The actual output device/sink destination
    f"OUT_PypeMeeter-{target_output_device}"
]
# Spin them both up
# try to use "with:" statement
input_proc = subprocess.Popen(input_command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
output_proc = subprocess.Popen(output_command, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
print("Audio pipeline linked. Processing data...")
time.sleep(0.5) # Allow initialization
# def getRMS(data):
#         rmsData = np.frombuffer(data, dtype=np.int16)
#         # np.sqrt(np.mean(rmsData**2))
#         positive_ify = 0 if np.mean(rmsData) < 0 else 1
#         rms = np.mean(rmsData)*positive_ify
#         #{'|'*int(rms if rms is not np.nan else 0)}
#         os.system('clear')
#         print(f"[Output Node] RMS: {str(int(rms)).ljust(5,'_')} {'|'*int(rms/25)}")
try:
    chunk_size = 16 * 2 * 2
    while True:
        # Read the raw chunks from the input device...
        data = input_proc.stdout.read(chunk_size)
        if not data:
            print('Data is NOT')
            break
        # Optional: You can manipulate, analyze, or process the 'data' bytearray here!
        # threading.Thread(target=getRMS, args=(data,)).start()
        
        # ...and pass it cleanly out to the output device
        output_proc.stdin.write(data)
        
except KeyboardInterrupt:
    print("\nTearing down pipeline.")
finally:
    input_proc.terminate()
    output_proc.stdin.close()
    output_proc.terminate()