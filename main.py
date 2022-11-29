import binascii
import inspect
import math
import random
import time
import midi
import cv2
import numpy as np
from midi2audio import FluidSynth

eot = midi.EndOfTrackEvent(tick=1)


def sinusoidal_function(n):
    return (math.sin(n) + 1) / 2


def parse_img_data(data):
    img = cv2.imread(data)
    return img.reshape((len(img) * len(img[0]), 3))


def parse_txt_data(data):
    with open(data, 'r') as file:
        data = file.read()  # .replace('\n', '')
    data = binascii.hexlify(data.encode('utf-8'))
    return str(int(data.decode('utf-8'), 16))


def make_single_track(notes_limit, min_pitch, pitch_range, data=None):
    track = midi.Track()

    if data is not None:
        if inspect.isfunction(data):
            track = track_function(notes_limit, min_pitch, pitch_range, track, data)
        if type(data) is np.ndarray:
            track = track_img(notes_limit, min_pitch, pitch_range, track, data)
        if isinstance(data, str):
            track = track_text(notes_limit, min_pitch, pitch_range, track, data)
    else:
        track = track_random(notes_limit, min_pitch, pitch_range, track)

    track.append(eot)
    return track


def track_function(notes_limit, min_pitch, pitch_range, track, data):
    for i in range(notes_limit):
        pitch = int(min_pitch + data(math.pi * i / (float(min_pitch) / 5)) * pitch_range)
        volume = random.randint(55, 60 + int(min_pitch / 8))
        on_note = midi.NoteOnEvent(tick=0, channel=0, data=[pitch, volume])
        off_note = midi.NoteOffEvent(tick=140, channel=0, data=[pitch, volume])

        track.append(on_note)
        track.append(off_note)

    return track


def track_img(notes_limit, min_pitch, pitch_range, track, data):
    per_note = int(len(data) / notes_limit)

    for i in range(notes_limit):
        shift = i * per_note
        denominator = per_note * 255 * 3
        numerator = 0
        for j in range(per_note):
            numerator += int(data[j + shift][0]) + int(data[j + shift][1]) + int(data[j + shift][2])

        normalized_pitch = numerator / denominator

        pitch = int(min_pitch + normalized_pitch * pitch_range)
        # volume = random.randint(55, 60 + int(min_pitch / 8))
        volume = 70
        on_note = midi.NoteOnEvent(tick=0, channel=0, data=[pitch, volume])
        off_note = midi.NoteOffEvent(tick=140, channel=0, data=[pitch, volume])

        track.append(on_note)
        track.append(off_note)

    return track


def track_text(notes_limit, min_pitch, pitch_range, track, data):
    n = len(data)
    per_note = int(n / notes_limit)
    last_note = n - (per_note * (notes_limit - 1))

    for i in range(notes_limit - 1):
        shift = i * per_note
        denominator = 10 ** per_note
        numerator = int(data[shift:(shift + per_note)])
        normalized_pitch = int(data[shift:(shift + per_note)]) / 10 ** per_note

        pitch = int(min_pitch + normalized_pitch * pitch_range)
        volume = 70
        on_note = midi.NoteOnEvent(tick=0, channel=0, data=[pitch, volume])
        off_note = midi.NoteOffEvent(tick=140, channel=0, data=[pitch, volume])

        track.append(on_note)
        track.append(off_note)

    normalized_pitch = int(data[(n - last_note):n]) / 10 ** last_note
    pitch = int(min_pitch + normalized_pitch * pitch_range)
    volume = 70
    on_note = midi.NoteOnEvent(tick=0, channel=0, data=[pitch, volume])
    off_note = midi.NoteOffEvent(tick=140, channel=0, data=[pitch, volume])

    track.append(on_note)
    track.append(off_note)

    return track


def track_random(notes_limit, min_pitch, pitch_range, track):
    for i in range(notes_limit):
        pitch = random.randint(min_pitch, min_pitch + pitch_range)
        on_note = midi.NoteOnEvent(tick=0, channel=0, data=[pitch, 75])
        off_note = midi.NoteOffEvent(tick=140, channel=0, data=[pitch, 75])
        track.append(on_note)
        track.append(off_note)

    return track


def make_pattern(limit, number_of_tracks, min_pitch, pitch_range, data=None):
    pattern = midi.Pattern()
    n = number_of_tracks

    if n >= 1:
        track_range = pitch_range / n
        for i in range(n - 1):
            track = make_single_track(limit, min_pitch + i * track_range, track_range, data)
            pattern.append(track)
        track = make_single_track(limit, min_pitch + (n - 1) * track_range, pitch_range - (n - 1) * track_range, data)
        pattern.append(track)
    else:
        print("Error: number of tracks must be integer bigger than 0")
        return -1

    return pattern


if __name__ == '__main__':
    filename, max_notes, tracks, min_pitch, pitch_range = "sin.mid", 70, 1, 50, 30
    data = sinusoidal_function
    # data = parse_img_data('trees.jpg')
    # data = parse_txt_data('some_text.txt')

    # Write the MIDI
    pattern = make_pattern(max_notes, tracks, min_pitch, pitch_range, data)
    if pattern == -1:
        exit(-1)
    midi.write_midifile(filename, pattern)

    # Play the MIDI
    fs = FluidSynth
    fs('FluidR3_GM.sf2').play_midi(filename)

