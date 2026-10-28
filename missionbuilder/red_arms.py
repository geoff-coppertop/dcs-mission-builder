"""Explicit air-to-air loadouts for Red fighters.

pydcs can only load DCS's default payloads from a local DCS install, so without one every AI fighter
is saved with empty pylons. These are typical period fits, set pylon by pylon.
"""
from dcs.planes import MiG_21Bis, MiG_29A, MiG_29S

LOADOUTS = {
    MiG_21Bis.id: {1: MiG_21Bis.Pylon1.APU_60_2M_with_2_x_R_60M__AA_8_Aphid_B____IR_AAM,
                   2: MiG_21Bis.Pylon2.APU_13U_2_with_R_3R__AA_2_Atoll_C____Semi_Active_AAM,
                   3: MiG_21Bis.Pylon3.Fuel_Tank_800_L__21_,
                   4: MiG_21Bis.Pylon4.APU_13U_2_with_R_3R__AA_2_Atoll_C____Semi_Active_AAM,
                   5: MiG_21Bis.Pylon5.APU_60_2M_with_2_x_R_60M__AA_8_Aphid_B____IR_AAM_},
    MiG_29A.id: {1: MiG_29A.Pylon1.R_60M__AA_8_Aphid_B____IR_AAM, 2: MiG_29A.Pylon2.R_73__AA_11_Archer____Infra_Red,
                 3: MiG_29A.Pylon3.R_27R__AA_10_Alamo_A____Semi_Act_Rdr, 4: MiG_29A.Pylon4.Fuel_tank_1400L,
                 5: MiG_29A.Pylon5.R_27R__AA_10_Alamo_A____Semi_Act_Rdr, 6: MiG_29A.Pylon6.R_73__AA_11_Archer____Infra_Red,
                 7: MiG_29A.Pylon7.R_60M__AA_8_Aphid_B____IR_AAM},
    MiG_29S.id: {1: MiG_29S.Pylon1.R_73__AA_11_Archer____Infra_Red, 2: MiG_29S.Pylon2.R_73__AA_11_Archer____Infra_Red,
                 3: MiG_29S.Pylon3.R_27ER__AA_10_Alamo_C____Semi_Act_Extended_Range, 4: MiG_29S.Pylon4.Fuel_tank_1400L,
                 5: MiG_29S.Pylon5.R_27ER__AA_10_Alamo_C____Semi_Act_Extended_Range,
                 6: MiG_29S.Pylon6.R_73__AA_11_Archer____Infra_Red, 7: MiG_29S.Pylon7.R_73__AA_11_Archer____Infra_Red},
}


def arm(group):
    """Load the A2A fit for every unit in a Red fighter group; fails loudly for an unknown type."""
    for u in group.units:
        lo = LOADOUTS[u.unit_type.id]
        u.pylons.clear()
        for st, wpn in lo.items():
            u.load_pylon(wpn, st)
    return group
