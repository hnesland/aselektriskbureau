/**
 * ecma-rotarydialler, A Raspberry Pi library for mechanical rotary diallers, written in ECMAScript
 * Copyright (C) 2023 mo-g
 * 
 * ecma-rotarydialler is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 * 
 * ecma-rotarydialler is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with ecma-rotarydialler.  If not, see <https://www.gnu.org/licenses/>.
 */


import gpio from 'rpi-gpio';


const translatedPulse = {
    1:1,
    2:2,
    3:3,
    4:4,
    5:5,
    6:6,
    7:7,
    8:8,
    9:9,
    10:0
};


/**
 * Represents the dialler of a hardware phone, accessed through rpi-gpio.
 * 
 * First thing, can I use the interrupts and callback on that library to avoid having
 * to listen on a loop for changes?
 */
class Dialler {
    constructor ({clickPin = 0,
                  statePin = 0,
                  clickTimeout = 0,
                  dialTimeout = 0,
                  callback = function () {throw "Callback not set!";}} = {}) {
        this.clickPin = gpio.setup(clickPin, ["DIR_IN", "EDGE_RISING"], function () {});
        this.statePin = gpio.setup(statePin, ["DIR_IN", "EDGE_BOTH"], function () {});
        this.clickTimeout = clickTimeout;
        this.dialTimeout = dialTimeout;
    };

};

export { Dialler}
