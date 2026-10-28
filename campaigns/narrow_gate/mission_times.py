"""Single source of truth for Operation Narrow Gate timing. Everything else derives from here."""
import datetime

START = datetime.datetime(2026, 10, 26, 7, 30, 0)   # mission start, local (Caucasus = Z+4)
TOT_OFFSET = 30 * 60                                 # TOT = start + 30:00
WINDOW = 60                                          # impact scored ON TIME within +/- this
SUP_BEFORE = 150                                     # FORD's jamming (its pass through 40 km of the SA-6) starts this long before TOT
SUP_AFTER = 120                                      # and ends this long after TOT
IN_LEAD = 50                                         # earliest IN = TOT - WINDOW - IN_LEAD
ZULU_OFFSET = 4 * 3600
RECOVERY_MIN = 50                                    # MOTHER waypoint = carrier position this long after start

START_S = START.hour * 3600 + START.minute * 60
TOT_S = START_S + TOT_OFFSET


def hms(s):
    s = int(round(s)) % 86400
    return f"{s // 3600:02d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def hm(s):
    return hms(s)[:5]


T_START = hms(START_S)
T_START_HM = hm(START_S)
T_TOT = hms(TOT_S)
T_TOT_HM = hm(TOT_S)
T_TOT_Z = hms(TOT_S - ZULU_OFFSET)
T_WIN_ON, T_WIN_OFF = hms(TOT_S - WINDOW), hms(TOT_S + WINDOW)
T_WIN_ON_HM, T_WIN_OFF_HM = hm(TOT_S - WINDOW), hm(TOT_S + WINDOW)
T_SUP_ON, T_SUP_OFF = hms(TOT_S - SUP_BEFORE), hms(TOT_S + SUP_AFTER)
T_IN_EARLIEST = hms(TOT_S - WINDOW - IN_LEAD)
T_REC_HM = hm(START_S + RECOVERY_MIN * 60)
T_REC_A, T_REC_B = hm(TOT_S + 15 * 60), hm(TOT_S + 25 * 60)
