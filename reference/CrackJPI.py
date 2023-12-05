# SOURCE: https://github.com/2sec/python-edm
from datetime import datetime
from datetime import timedelta
from DataBase import DataBase
import pandas as pd
import shutil
import struct
import sys
import os

"""
JPI Decoder:

- Reads and parses all flights from all JPI files in a source directory
- Writes each flight as a seperate CSV to a destination directory
- Columns are cleaned and new features are created to the data
- Clean data is writted flight by flight as CSV to a new directory 

"""


def isF(flags): return (flags >> 28) & 1


def cleanCSV():

    NEWLINE = "\n"

    print(NEWLINE + "Starting File Cleaning" + NEWLINE)

    flightcounter = 1
    for filename in os.listdir("data/raw_csv"):

        print("Processing File: " + filename)

        if filename.endswith(".csv"):
            # get the flight number
            splitfile = filename.split("-")
            flightnum = splitfile[1]
            # read in file
            df = pd.read_csv("data/raw_csv/" + filename)
            # create new features
            df['EGT_MEAN'] = df.iloc[:, 1:6].mean(axis=1)
            df['CHT_MEAN'] = df.iloc[:, 7:11].mean(axis=1)
            timedelta = []
            time = 0
            for i in range(df.shape[0]):
                timedelta.append(time)
                time += 6
            df['SECONDS'] = timedelta
            df['ID'] = flightnum.removesuffix(".csv")
            # remove empty empty columns
            df.drop(columns=['HP', 'MAP', 'GSPD',
                             'OILT', 'MARK', 'OILP',
                             'USD', 'CRB', 'CLD',
                             'VOLT',], inplace=True, axis=1)

            # write each flight file back to a new file in a new directory

            currfname = "data/clean_csv/" + flightnum
            flightcounter += 1
            df.to_csv(currfname, index=False)

    print("\nDone: " + str(flightcounter) + " flights cleaned and exported.")


def createCSV():

    inputDir = "data/jpi_bucket"
    outDir = "data/raw_csv"

    if not inputDir.endswith('/'):
        inputDir += '/'
    files = os.listdir(inputDir)
    files = [f for f in files if f.endswith('.JPI')]

    for f in files:
        print(inputDir + f)
        data = EDMData(inputDir + f, outDir)
        data.read()
        data.parseHeader()

        print(data.header)
        for key, value in data.config.items():
            print(key, value)

        print('')

        data.parseFlights()


class EDMFlight(object):

    def __init__(self, fnum, date, flags, isF, interval_secs):
        self.fnum = fnum
        self.date = date
        self.flags = flags
        self.isF = isF
        self.interval_secs = interval_secs


class EDMData(object):

    def __init__(self, fileName, outDir):
        self.fileName = fileName
        self.outDir = outDir

    def read(self):
        self.header = None
        self.offset = 0
        with open(self.fileName, "rb") as f:
            self.data = f.read()

    def parseHeader(self):
        data = self.data

        i = 0  # current position within the buffer being parsed
        header = {}
        flights = []
        atEnd = False

        while not atEnd:
            assert (data[i] == ord('$'))

            # extract field
            j = i
            while (data[i] != 0x0D):
                i += 1

            line = data[j:i].decode("ascii")

            i += 1
            assert (data[i] == 0x0A)
            i += 1

            # calculate checksumn
            calc = 0

            checksumIndex = 1
            while (line[checksumIndex] != '*'):
                calc ^= ord(line[checksumIndex])
                checksumIndex += 1

            checksum = int(line[checksumIndex + 1:], 16)
            assert (checksum == calc)

            # extract key and value
            line = line[1: checksumIndex]
            key, value = line.split(',', 1)
            value = value.strip(' ')

            atEnd = (key == 'L')

            # $D = flight info, they all have the same letter hence they are appended to a different list
            if key == 'D':
                flights.append(value)
            else:
                header[key] = value

        self.offset = i

        config = {}
        config['TAIL NO'] = header['U']

        # helper function used to convert list of integers
        def intLimits(key):
            limits = header[key]
            limits = limits.split(',')
            limits = [int(limit) for limit in limits]
            return limits

        limits = intLimits('A')
        config['VOLTS LIMIT HIGH'] = limits[0] / 10.0
        config['VOLTS LIMIT LOW'] = limits[1] / 10.0
        config['EGT SPAN DIF'] = limits[2]
        config['HIGH CHT TEMP'] = limits[3]
        config['SHOCK COOLING CLD'] = limits[4]
        # config['HIGH TIT TEMP'] = limits[5]

        config['OIL-T LIMIT HIGH'] = limits[6]
        config['OIL-T LIMIT LOW'] = limits[7]

        limits = intLimits('F')
        config['FUEL EMPTY'] = limits[0]
        config['MAIN TANK SIZE'] = limits[1]
        config['AUX TANK SIZE'] = limits[2]
        config['K-FACTOR 1'] = limits[3] / 100.0
        config['K-FACTOR 2'] = limits[4] / 100.0

        limits = intLimits('T')
        mo, d, y, h, mi = limits[0], limits[1], limits[2] + \
            2000, limits[3], limits[4]
        config['DOWNLOAD DATE TIME'] = datetime(y, mo, d, h, mi)
        config['LAST FLIGHT NO'] = limits[5]

        limits = intLimits('C')
        config['EDM TYPE'] = limits[0]
        flags = limits[1] | (limits[2] << 16)
        config['FLAGS'] = flags  # '{0:0b}'.format(flags)

        config['ENGINE TEMPS UNIT'] = 'F' if isF(flags) else 'C'

        n = len(limits)
        config['VERSION'] = limits[n - 1] / 10.0 + limits[n - 2]
        for i in range(3, n - 2):
            config['UNKNOWN C' + str(i)] = limits[i]

        config['CARB'] = int(header['P'])

        for i, flight in enumerate(flights):
            flight = flight.split(',')
            flight = [int(item) for item in flight]
            flight[1] *= 2  # flight data length in bytes
            flights[i] = flight

        self.header = header
        self.config = config
        self.flights = flights

    def parseFlights(self):

        data = self.data
        flights = self.flights

        struct_flightheader = struct.Struct('!14H')

        for i, flight in enumerate(flights):

            # read flightheader

            fnum = flight[0]
            flen = flight[1]
            header = struct_flightheader.unpack_from(data, self.offset)

            if header[0] != fnum:
                self.offset -= 1
                header = struct_flightheader.unpack_from(data, self.offset)

            flags = header[1] | (header[2] << 16)

            assert (header[0] == fnum)

            interval_secs = header[11]

            # read date and time
            def andShift(v, i): return v & (2**i - 1), v >> i

            date = header[12]
            d, date = andShift(date, 5)
            mo, date = andShift(date, 4)
            y = date + 2000

            time = header[13]
            s, time = andShift(time, 5)
            mi, time = andShift(time, 6)
            h = time
            date = datetime(y, mo, d, h, mi, s * 2)

            # read flight data

            flightdata = data[self.offset +
                              struct_flightheader.size:self.offset+flen]

            # debug - save flight data
            # with open(self.fileName + '-' + str(fnum), 'wb') as f: f.write(flightdata)

            convertEngineTemp = True

            # no idea where the unit is given in the header! I'll test when needed
            convertOilTemp = False

            if convertEngineTemp:
                convertEngineTemp = isF(flags)

            self.parseFlight(fnum, flightdata, date, interval_secs,
                             convertEngineTemp, convertOilTemp)

            flights[i] = EDMFlight(fnum, date, flags, 'C', interval_secs)

            self.offset += flen

    def parseFlight(self, fnum, data, date, interval_secs, convertEngineTemp, convertOilTemp):

        print('Decoding Flight', fnum, 'date', date)

        struct_flightdata = struct.Struct('!x2HB')

        td = timedelta(seconds=interval_secs)

        labels = \
            {
                'EGT1': (0, 48), 'EGT2': (1, 49), 'EGT3': (2, 50), 'EGT4': (3, 51), 'EGT5': (4, 52), 'EGT6': (5, 53),
                'CHT1': 8, 'CHT2': 9, 'CHT3': 10, 'CHT4': 11, 'CHT5': 12, 'CHT6': 13,
                'CRB': 18, 'CLD': 14, 'OILT': 15, 'MARK': 16, 'OILP': 17, 'VOLT': 20, 'OAT': 21,
                'USD': 22, 'FF': 23, 'HP': 30, 'MAP': 40, 'RPM': (41, 42), 'HOURS': (78, 79),
                'GSPD': 85
            }

        GSPD_index = labels['GSPD']

        # TODO: locate high byte for ground speed (GSPD) which must surely exists

        NUM_FIELDS = 128
        DEFAULT_VALUE = 0xF0
        default_values = [DEFAULT_VALUE] * NUM_FIELDS

        # special case for HP: default value is 0
        default_values[labels['HP']] = 0

        # default value for high bytes:
        for key, index in labels.items():
            if type(index) == tuple:
                default_values[index[1]] = 0

        previous_values = [None] * NUM_FIELDS
        GSPD_bug = True

        csv_header = 'date'
        csv_values = ''

        for key in labels:
            csv_header += ',' + key

        csv_header += '\n'

        count = 0
        offset = 0
        flen = len(data)
        while offset < flen - struct_flightdata.size:
            # read decode flags
            flightdata = struct_flightdata.unpack_from(data, offset)
            assert (flightdata[0] == flightdata[1])

            offset += struct_flightdata.size

            decodeflags = flightdata[0]
            repeatcount = flightdata[2]

            # TODO output the current data set repeatcount times
            assert (repeatcount == 0)
            for i in range(0, repeatcount):
                date += td

            # decode flags
            fieldflags = [0] * 16
            signflags = [0] * 16

            for i in range(0, 16):
                if decodeflags & (1 << i):
                    fieldflags[i] = data[offset]
                    offset += 1

            for i in range(0, 16):
                if decodeflags & (1 << i) and (i != 6 and i != 7):
                    signflags[i] = data[offset]
                    offset += 1

            # convert bits to lists for simplicity
            new_fieldflags = []
            new_signflags = []
            for f in fieldflags:
                for i in range(0, 8):
                    new_fieldflags.append(f & (1 << i))
            for f in signflags:
                for i in range(0, 8):
                    new_signflags.append(f & (1 << i))

            # sign value for high bytes is the one from the corresponding low bytes
            for key, index in labels.items():
                if type(index) == tuple:
                    new_signflags[index[1]] = new_signflags[index[0]]

            # read and calculate differences
            new_values = [None] * NUM_FIELDS

            for k in range(0, NUM_FIELDS):
                value = previous_values[k]

                if new_fieldflags[k]:
                    diff = data[offset]
                    offset += 1

                    negative = new_signflags[k]

                    if negative:
                        diff = -diff

                    if value is None and diff == 0:
                        pass
                    else:
                        if value is None:
                            value = default_values[k]

                        value += diff

                        previous_values[k] = value

                if value is None:
                    value = 0

                if k == GSPD_index:
                    if value == 150 and GSPD_bug:
                        value = 0
                    elif value:
                        GSPD_bug = False

                new_values[k] = value

            # save values
            values = {}
            values['date'] = date

            for key, index in labels.items():
                if type(index) == tuple:
                    value = new_values[index[0]] + (new_values[index[1]] << 8)
                else:
                    value = new_values[index]

                values[key] = value

            def f2c(t): return round((t - 32) * 5 / 9.0, 2)

            if convertEngineTemp:
                for key in ['EGT1', 'EGT2', 'EGT3', 'EGT4', 'EGT5', 'EGT6',
                            'CHT1', 'CHT2', 'CHT3', 'CHT4', 'CHT5', 'CHT6',
                            'CRB', 'CLD', 'OILT']:
                    values[key] = f2c(values[key])
            if convertOilTemp:
                values['OAT'] = f2c(values['OAT'])

            if values['GSPD'] < 0:  # this happens sometimes, dunno why
                values['GSPD'] = 0

            # convert to CSV
            row = ''
            for key, value in values.items():
                row += ',' + str(value)

            csv_values += row[1:] + '\n'

            count += 1
            date += td

        # save CSV
        with open(self.outDir + '/' + self.config['TAIL NO'] + '-' + str(fnum) + '.csv', 'wt') as f:
            f.write(csv_header)
            f.write(csv_values)

        return csv_header, csv_values


if __name__ == '__main__':

    engine_conn = 'postgresql://quinnodel:admin@localhost:5432/postgres'
    db = DataBase(engine_conn)

    # command line args

    # CrackJPI add <source directory of JPI files>
    # - iterate through and copy new files only

    createCSV()
    cleanCSV()
    db.updateDB()
