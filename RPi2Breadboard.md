Mapping from Raspberry Pi (V1 B) to Breadboard (Smartduino kind)

RC - Ribbon Cable
BB - Symbol on Breadboard
Raspberry PI - Meaning on Raspberry PI

The 15 wide ribbon cable is attached so it is centered and two pins are free on either side (of RPi B)

| L  | BB  | Pin | Raspberry Pi    | Raspberry Pi   | Pin | BB    | R  |
| ---| --- | --- | --------------- | -------------- | --- | ----- | ---|
| 1  | +5V |     |                 |                |     | +3.3V | 1  |
| 2  | B1  | 1   | 3v3 Power       | 5v Power       | 2   | B2    | 2  |
| 3  | B3  | 3   | BCM 2 (SDA)     | 5v Power       | 4   | B4    | 3  |
| 4  | B5  | 5   | BCM 3 (SCL)     | Ground         | 6   | B6    | 4  |
| 5  | B14 | 7   | BCM 4 (GPCLK0)  | BCM 14 (TXD)   | 8   | B8    | 5  |
| 6  | B9  | 9   | Ground          | BCM 15 (RXD)   | 10  | B10   | 6  |
| 7  | B11 | 11  | BCM 17          | BCM 18 (PCM_C) | 12  | B12   | 7  |
| 8  | B13 | 13  | BCM 27 (PCM_D)  | Ground         | 14  | --(L5)| 8  |
| 9  | B15 | 15  | BCM 22          | BCM 23         | 16  | B16   | 9  |
| 10 | B17 | 17  | 3v3 Power       | BCM 24         | 18  | B18   | 10 |
| 11 | B19 | 19  | BCM 10 (MOSI)   | Ground         | 20  | B20   | 11 |
| 12 | B21 | 21  | BCM 9 (MISO)    | BCM 25         | 22  | B22   | 12 |
| 13 | B23 | 23  | BCM 11 (SCLK)   | BCM 8 (CE0)    | 24  | B24   | 13 |
| 14 | B25 | 25  | Ground          | BCM 7 (CE1)    | 26  | B26   | 14 |
| 15 | B27 |     |                 |                |     | GND   | 15 |

Notes: 

1. I had to cut two routes on Smartduino Breadboards because they were shorted connecting Pin 9 with Pin 16. nd B7 with B14. I suspect cutting one line (on backside leading to B14) would be sufficient and would lead to Pin 16 remaining connected to B14 allowing access to BCM23.

















