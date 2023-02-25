/**
 * 1910called, an internet phone stack for upcycling with Pi.
 * Copyright (C) 2023 mo-g
 * 
 * 1910called is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 * 
 * 1910called is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with 1910called  If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * Note - this program will initially contain methods and assumptions that will
 * be transferred to more specific models, config and interfaces as development
 * progresses. This will start ugly and clean up as we work out the final
 * architecture.
 */

import { RTPHeader, RTPPacket } from './Libraries/ecma-rtp/index.mjs';
import gpio from 'rpi-gpio';
import speaker from "speaker";


const configFile = "./config.js";

/**
* The next constants should be moved into the config file.
*/

const ioPin = {
    clicker: 0,
    state: 0,
    earpiece: 0
};

const audioDevices = {
    ringer: {
        alsaDevice: "hw0,0",
        latency: 0,
        channels: 1,
        bitDepth: 16,
        bitRate: 16000,
        input: false,
        output:true
    },
    handset: {
        alsaDevice: "hw0,1",
        latency: 0,
        channels: 1,
        bitDepth: 16,
        bitRate: 16000,
        input: true,
        output:true
    }
};

const tonePack = "uk_1924";


