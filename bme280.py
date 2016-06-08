import time
from i2cdev import I2CDev
from util import sb, ss, b2us, b2ss

ADDR_0x76 = 0x76
ADDR_0x77 = 0x77

REG_ID = 0xD0
REG_RESET = 0xE0
REGS_CAL = range(0x88, 0xA0) + [0xA1] + range(0xE1, 0xE8)
REG_CTRL_HUM = 0xF2
REG_STATUS = 0xF3
REG_CTRL_MEAS = 0xF4
REG_CONFIG = 0xF5
REGS_DATA = range(0xf7, 0xff)

class BME280(I2CDev):
    def __init__(self, i2c, addr = ADDR_0x76):
        super(BME280, self).__init__(i2c, addr)

    def get_values(self):
        return (self.__lastT, self.__lastP, self.__lastH)

    def get_temperature(self):
        return self.__lastT

    def get_humidity(self):
        return self.__lastH

    def get_pressure(self):
        return self.__lastP

    def read_calibration_data(self):
        cv = []
        for r in REGS_CAL:
            cv.append(self.read_byte_data(r))
        self.__T1 = b2us(cv[1], cv[0])
        self.__T2 = b2ss(cv[3], cv[2])
        self.__T3 = b2ss(cv[5], cv[4])
        self.__P1 = b2us(cv[7], cv[6])
        self.__P2 = b2ss(cv[9], cv[8])
        self.__P3 = b2ss(cv[11], cv[10])
        self.__P4 = b2ss(cv[13], cv[12])
        self.__P5 = b2ss(cv[15], cv[14])
        self.__P6 = b2ss(cv[17], cv[16])
        self.__P7 = b2ss(cv[19], cv[18])
        self.__P8 = b2ss(cv[21], cv[20])
        self.__P9 = b2ss(cv[23], cv[22])
        self.__H1 = cv[24]
        self.__H2 = b2ss(cv[26], cv[25])
        self.__H3 = cv[27]
        self.__H4 = ss((cv[28] << 4) | (0x0F & cv[29]))
        self.__H5 = ss((cv[30] << 4) | (0x0F & (cv[29] >> 4)))
        self.__H6 = sb(cv[31])

    def read_data(self):
        rd = []
        for r in REGS_DATA:
            rd.append(self.read_byte_data(r))
        rp = (rd[0] << 12) | (rd[1] << 4) | (rd[2] >> 4)
        rt = (rd[3] << 12) | (rd[4] << 4) | (rd[5] >> 4)
        rh = (rd[6] << 8) | rd[7]
        return (rt, rp, rh)

    def show_calibration_data(self):
        print("dig_T1 = %d;" % self.__T1)
        print("dig_T2 = %d;" % self.__T2)
        print("dig_T3 = %d;" % self.__T3)
        print("dig_P1 = %d;" % self.__P1)
        print("dig_P2 = %d;" % self.__P2)
        print("dig_P3 = %d;" % self.__P3)
        print("dig_P4 = %d;" % self.__P4)
        print("dig_P5 = %d;" % self.__P5)
        print("dig_P6 = %d;" % self.__P6)
        print("dig_P7 = %d;" % self.__P7)
        print("dig_P8 = %d;" % self.__P8)
        print("dig_P9 = %d;" % self.__P9)
        print("dig_H1 = %d;" % self.__H1)
        print("dig_H2 = %d;" % self.__H2)
        print("dig_H3 = %d;" % self.__H3)
        print("dig_H4 = %d;" % self.__H4)
        print("dig_H5 = %d;" % self.__H5)
        print("dig_H6 = %d;" % self.__H6)                                 

    def compensate_t(self, rt):
        var1 = (((rt >> 3) - (self.__T1 << 1)) * self.__T2) >> 11;
        var2 = (((((rt >> 4) - self.__T1) * ((rt >> 4) - self.__T1)) >> 12) * self.__T3) >> 14;
        self.__t_fine = var1 + var2;
        return (self.__t_fine * 5 + 128) >> 8;

    def compensate_p(self, rp):
        var1 = self.__t_fine - 128000;
        var2 = var1 * var1 * self.__P6;
        var2 = var2 + ((var1 * self.__P5) << 17);
        var2 = var2 + (self.__P4 << 35);
        var1 = ((var1 * var1 * self.__P3) >> 8) + ((var1 * self.__P2) << 12);
        var1 = ((1 << 47) + var1) * self.__P1 >> 33;
        if var1 == 0:
            return 0
        p = 1048576 - rp;
        p = (((p << 31) - var2) * 3125) / var1;
        var1 = (self.__P9 * (p >> 13) * (p >> 13)) >> 25;
        var2 = (self.__P8 * p) >> 19;
        p = ((p + var1 + var2) >> 8) + (self.__P7 << 4);
        return p

    def compensate_h(self, rh):
        v_x1_u32r = self.__t_fine - 76800;
        v_x1_u32r = ((((rh << 14) - (self.__H4 << 20) - (self.__H5 * v_x1_u32r)) + 16384) >> 15) * (((((((v_x1_u32r * self.__H6) >> 10) * (((v_x1_u32r * self.__H3) >> 11) + 32768)) >> 10) + 2097152) * self.__H2 + 8192) >> 14)
        v_x1_u32r = v_x1_u32r - (((((v_x1_u32r >> 15) * (v_x1_u32r >> 15)) >> 7) * self.__H1) >> 4)
        v_x1_u32r = 0 if v_x1_u32r < 0 else v_x1_u32r
        v_x1_u32r = 419430400 if v_x1_u32r > 419430400 else v_x1_u32r
        return v_x1_u32r >> 12

    def update(self):
        (rt, rp, rh) = self.read_data()
        self.__lastT = self.compensate_t(rt) / 100.0
        self.__lastP = self.compensate_p(rp) / 25600.0
        self.__lastH = self.compensate_h(rh) / 1024.0
