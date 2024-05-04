import time


def calculate_first_byte(start_time):
    # Record the time when the first byte is received
    first_byte_time = time.time()

    # Calculate the time to first byte
    ttfb = int((first_byte_time - start_time) * 1000)
    print(f"TTS Time to First Byte (TTFB): {ttfb}ms\n")
    return ttfb


def get_player_commands():
    return ["ffplay", "-autoexit", "-", "-nodisp"]
