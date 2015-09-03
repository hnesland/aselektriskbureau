Mapping from Raspberry Pi (V1 B) to Breadboard (Smartduino kind)


Lp | BB  | L  | Raspberry Pi    | Raspberry Pi   | R   | BB
-- | --- | -- | --------------- | -------------- | --  | -----
1  | +5V | 1  | 3v3 Power       | 5v Power       | 2   | +3.3V
2  | B1  | 3  | BCM 2 (SDA)     | 5v Power       | 4   | B2
3  | B3  | 5  | BCM 3 (SCL)     | Ground         | 6   | B4
4  | B5  | 7  | BCM 4 (GPCLK0)  | BCM 14 (TXD)   | 8   | B6
5  | B14 | 9  | Ground          | BCM 15 (RXD)   | 10  | B8
6  | B9  | 11 | BCM 17          | BCM 18 (PCM_C) | 12  | B10
7  | B11 | 13 | BCM 27 (PCM_D)  | Ground         | 14  | B12
8  | B13 | 15 | BCM 22          | BCM 23         | 16  | --- (In place of B7)
9  | B15 | 17 | 3v3 Power       | BCM 24         | 18  | B16
10 | B17 | 19 | BCM 10 (MOSI)   | Ground         | 20  | B18
11 | B19 | 21 | BCM 9 (MISO)    | BCM 25         | 22  | B20
12 | B21 | 23 | BCM 11 (SCLK)   | BCM 8 (CE0)    | 24  | B22
13 | B23 | 25 | Ground          | BCM 7 (CE1)    | 26  | B24
                                                      
14 | B25 | 27 | BCM 0 (ID_SD)   | BCM 1 (ID_SC)  | 28  | B26
15 | B27 | 29 | BCM 5           | Ground         | 30  | GND
                                                      
16 |     | 31 | BCM 6           | BCM 12         | 32  | 
17 |     | 33 | BCM 13          | Ground         | 34  | 
18 |     | 35 | BCM 19 (MISO)   | BCM 16         | 36  |  
19 |     | 37 | BCM 26          | BCM 20 (MOSI)  | 38  | 
20 |     | 39 | Ground          | BCM 21 (SCLK)  | 40  | 



Notes:

1. I had to cut two routes on Smartduino Breadboards because they were shorted connecting Pin 9 with Pin 16. nd B7 with B14. I suspect cutting one line (on backside leading to B14) would be sufficient and would lead to Pin 16 remaining connected to B14 allowing access to BCM23.

















