#!/usr/bin/python

# import library for working with midi files
import midi
import math
import sys
import argparse

def create_pattern_file(outfilename, pattern_name, category, length, new_notes):
    # open file for writing
    outfile = open(outfilename,"w")
    outfile.write("<drumkit_pattern>\n")
    outfile.write("    <pattern_for_drumkit>GMkit</pattern_for_drumkit>\n")
    outfile.write("    <pattern>\n")
    outfile.write("        <pattern_name>" + pattern_name + "</pattern_name>\n")
    outfile.write("        <category>"+category+"</category>\n")
    outfile.write("        <size>" + str(length) + "</size>\n")
    outfile.write("        <noteList>\n")
    for note in new_notes:
        outfile.write("            <note>\n")
        outfile.write("            <position>" + str(note[0]) + "</position>\n")
        outfile.write("            <leadlag>0</leadlag>\n")
        outfile.write("            <velocity>" + str((note[1][1]/127)) + "</velocity>\n")
        outfile.write("            <pan_L>0.5</pan_L>\n")
        outfile.write("            <pan_R>0.5</pan_R>\n")
        outfile.write("            <pitch>0</pitch>\n")
        outfile.write("            <key>C0</key>\n")
        outfile.write("            <length>-1</length>\n")
        outfile.write("            <instrument>" + str(note[1][0]-36) + "</instrument>\n")
        outfile.write("            </note>\n")
    outfile.write("        </noteList>\n")
    outfile.write("    </pattern>\n")
    outfile.write("</drumkit_pattern>\n")
    outfile.close

class MidiToPattern():

    def __init__(self, filename, outfilename='', category='Uncategorized', pattern_name=''):
        self.filename = filename
        self.outfilename = outfilename if outfilename else filename.rsplit('.', 1)[0]+'.h2pattern'  # if no out name, keep same name and replace extension
        self.category = category
        self.pattern_name = pattern_name if pattern_name else filename.rsplit('.', 1)[0]  # if no pattern name, get file name

        # list for new note items
        self.new_notes = []

        # beats per quarter in midi file
        self.resolution = 8

        # Constant : max number of "beat" in an hydrogen pattern
        self.pat_size = 768

        self.length = -1

    def extract_notes(self):
        # load file
        pattern = midi.read_midifile(self.filename)

        # magic number for resolution of hydrogen files
        res = 48

        # number of beats per quarter note in midi file
        self.resolution = pattern.resolution


        note = midi.NoteOnEvent()
        noteoff = midi.NoteOffEvent()
        timeSig = midi.TimeSignatureEvent()
        tempo = midi.SetTempoEvent()

        # number of beats per quarter in midi file / number of beats per quater in hydrogen
        ratio = self.resolution / res

        # get length from total number of ticks
        total_ticks = 0
        for track in pattern:
            this_track_ticks = 0
            for line in track:
                if type(line) == type(timeSig):
                    timeSig = line
                elif type(line) == type(tempo):
                    tempo = line
                elif type(line) == type(note):
                    this_track_ticks += line.tick
                    self.new_notes.append([round(this_track_ticks/ratio),line.data])
                elif type(line) == type(noteoff):
                    this_track_ticks += line.tick
            if this_track_ticks>total_ticks:
                total_ticks = this_track_ticks

        num_of_quarter_notes = math.ceil(total_ticks/self.resolution)
        self.length = num_of_quarter_notes*res

    def build_patterns_files(self):
        # While hydrogen patterns cannot be infinite in length,
        # determine maximums beats of a pattern and split it into several files if needed

        pat_list = []
        for n in range(math.ceil(self.length/self.pat_size)):
            pat_beg = self.pat_size*n
            pat_end = self.pat_size*(n+1)
            note_list = [note for note in self.new_notes if pat_beg <= note[0] < pat_end ]
            for note in note_list:
                note[0] -= pat_beg  # apply offset
            pat_list.append(note_list)

        for i, notes in enumerate(pat_list):
            out_name = "{splt[0]}_{index}.{splt[1]}".format(splt=self.outfilename.rsplit('.', 1), index=i+1)  # create files as <name>_#.h2pattern with # = index
            pattern_name_indexed = self.pattern_name + str(i+1)

            create_pattern_file(out_name, pattern_name_indexed, self.category, self.pat_size, notes)

    def do_convertion(self):
        self.extract_notes()
        self.build_patterns_files()


if __name__=="__main__":

    parser = argparse.ArgumentParser(description='Convert midi files to hydrogen patterns')
    parser.add_argument('filename', help='MIDI file to convert', type=str)
    parser.add_argument('outfilename', help='Output filename', nargs='?', default=argparse.SUPPRESS, type=str)
    parser.add_argument('category', help='pattern category', nargs='?', default="Uncategorized", type=str)
    parser.add_argument('pattern_name', help='Pattern name', nargs='?', default=argparse.SUPPRESS, type=str)

    args = parser.parse_args()

    # Fill arguments to constructor
    program = MidiToPattern(**(vars(args)))

    program.do_convertion()


