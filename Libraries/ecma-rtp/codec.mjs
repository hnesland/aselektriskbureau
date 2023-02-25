/**
 * ecma-rtp, an RTP Library for Spin Doctor
 * Copyright (C) 2021-2022 The Combadge Project by mo-g
 * 
 * ecma-rtp is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 * 
 * ecma-rtp is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with ecma-rtp.  If not, see <https://www.gnu.org/licenses/>.
 */


import alawmulaw from 'alawmulaw';


/**
 * Superclass to represent an audio Codec.
 */
class Codec {
    constructor () {
        this.samples = []
    }

    transcode () {

    }

    /**
     * We need to do some testing to see how resampling options affect STT because
     * 
     * Cubic without Low Pass Filter:
     * generate: 0.283ms
     * transcode: 0.144ms
     * resample: 0.442ms
     * 
     * Cubic with LPF:
     * generate: 0.375ms
     * transcode: 0.123ms
     * resample: 6.605ms
     * 
     * That's on 20ms audio on an i5 9500. Interestingly it scales x2 per x10 duration,
     * so it's not terrible - but if we can shave time off, so much the better
     */
    resample (samples) {
        var floatSamples=Float32Array.from(Float32Array.from(samples).map(x=>x/0x8000));
        console.time('resample')
        var newSamples = waveResampler.resample(floatSamples, 16000, 8000, {method: "cubic", LPF: false}); // RETURNS A FLOAT64 NOT AN INT16 READ THE DOCS
        var samples1616=Int16Array.from(newSamples.map(x => (x>0 ? x*0x7FFF : x*0x8000)));
        return new Buffer.from(samples1616.buffer);
    }

    set samples (samples) {
        this.samples.push(this.transcode(samples));
    }

    get samples () {
        return this.samples.pop;
    }
}

/**
 * Represents mulaw (as used by Combadges)
 */
class μLaw extends Codec {
    constructor ({sourceRate = 16000,
                  sourceDepth = 16,
                  targetRate = 8000,
                  targetDepth = 8} = {}) {
        super();
    }



    transcode (samples, callback) {
        if (samples instanceof Uint8Array) {
            return alawmulaw.mulaw.decode(samples);
        } else if (samples instanceof Int16Array) {
            return alawmulaw.mulaw.encode(samples);
        }
    }
}

export { μLaw }
