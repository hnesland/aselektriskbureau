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


/**
 * Specify the Payload type of this audio stream. Current options are:
 *     Mulaw8K (8K μlaw LE), Alaw8K (8K Alaw LE), G7228K (8K G722 LE), G7298K (8K G729 LE)
 */


import alawmulaw from 'alawmulaw'; // For now, move to codec.mjs later.
import dgram from 'dgram';

const Payload = {
    Mulaw8K: 0,
    Alaw8K: 8,
    G7228K: 9,
    G7298K: 18
};

function findPayload(payloadNumber) {
    return Object.keys(Payload).find(key => Payload[key] === payloadNumber);
}

function significantBits (integerValue, bitLength) {
    return integerValue.toString(2).padStart(bitLength, '0');
}

function booleanBits (booleanValue, bitLength = 1) {
    return (booleanValue ? 1 : 0).toString(2).padStart(bitLength, '0');
}

function bufferBits(buffer) {
    return [...buffer].map((b) => b.toString(2).padStart(8, '0')).join('');
}

function binstringToHex(binstring, wordSize = 8) {
    const wordCount = Math.ceil(binstring.length / wordSize);
    var bytes = new Array();
  
    while (bytes.length < wordCount) {
        var bit = bytes.length * wordSize;
        bytes.push(binstring.substr(bit, wordSize));
    }

    var hexValue = new String();
    bytes.forEach(function (item, index) {
        hexValue += item.toString(16);
    });

    return hexValue;
  }

/**
 * This is a specific hardcoded header for Spin Doctor audio. It's not meant to be general purpose.
 * 
 * This is what we need to generate:
 * const rtpHeader = "8000";
 * var rtpSerial = 13; // 2 bytes, this is as good a starting number as any.
 * var rtpTimeStamp = 42; // 4 bytes, this is as good a starting number as any.
 * const ssrc = "00003827"; // Default used by the OEM Agent.
 */
class RTPHeader {
    constructor(payloadSize, payloadType = Payload.Mulaw8K, ssrc = 14375, csrcs = new Array(), extensions = new Array()) {
        this.payloadSize = payloadSize;
        // Byte 1 - RTP Format
        this.version = new Number(2);
        this.headerPadding = new Boolean(false);
        this.extension = new Boolean(extensions.length);
        this.csrcCount = csrcs.length; // 4 bits

        // Byte 2: Payload Format
        this.marker =  new Boolean(false);
        this.payloadType = payloadType;

        // Bytes 3-4: Serial Number - Randomise initial for future SRTP support. Cap at 25% of range.
        this.sequenceNo = Math.floor(Math.random() * (65534/4));

        // Bytes 5-8: Timestamp - Cap at 25% of range.
        this.timeStamp = Math.floor(Math.random() * (2147483647/4));

        // Bytes 9-12: SSRC - Imitate OEM Server to be safe.
        this.ssrc = ssrc; // If not set manually, use OEM default for server packet.

        // Bytes 13+
        this.csrcs = csrcs; // not currently in use, but might as well have it!
        this.extensions = extensions; // See above.
    }

    /**
     * Takes a dgram as a Buffer, and decodes it into a structured object
     * representing the RTP header of the packet sent by the badge.
     * 
     * Inspired by Array.from().
     */
    static from(packet) {
        var rtpFormat = bufferBits(packet.slice(0,1));
    
        var rtpVersion = parseInt(rtpFormat.slice(0,2), 2);
        if (rtpVersion !== 2) {
            throw "Not an RTP v2 Packet!";
        }

        var padding = !!+rtpFormat.slice(2,3);
        if (padding) {
            console.log("RTP Packet is padded, unsupported case!")
        }

        var extension = !!+rtpFormat.slice(3,4);
        var csrcCount = parseInt(rtpFormat.slice(4,8), 2);
        if (extension + csrcCount !== 0) {
            throw "Extension/CSRC present, unsupported header size!";
        } else {
            var lengthOfHeader = 12; // For now, assume a minimalist 12 byte header. We should handle extensions and multiple csrcs but it's not necessary yet.
        }

        var payloadFormat = bufferBits(packet.slice(1,2));
        var marker = !!+payloadFormat.slice(0,1);
        if (marker) {
            console.log("Payload Marker bit set. I have no idea what to do with that.");
        }
        var payloadType = parseInt(payloadFormat.slice(1,8), 2);

        // var payloadType = Payload[findPayload(payloadType)] // Brutish validation to check supported Payload type. Not sure we're there yet.
        var payloadSize = (packet.slice(lengthOfHeader).length);

        var sequenceNo = parseInt(packet.slice(2,4));
        var timeStamp = parseInt(packet.slice(4,8));
        var ssrc = parseInt(packet.slice(8,12));

        var header = new RTPHeader(payloadSize, payloadType, ssrc);
        header.forceHeader(sequenceNo, timeStamp);
        return header;
    }

    /**
     * Return header as buffer so it can be prepended to an audio stream.
     * 
     * Currently returns hex string - need to fix that!
     */
    toBuffer () {
        // Byte 1 - RTP Format
        var version = significantBits(this.version, 2);
        var headerPadding = booleanBits(this.headerPadding);
        var extension = booleanBits(this.extension);
        var csrcCount = significantBits(this.csrcCount, 4)
        var rtpFormat = version + headerPadding + extension + csrcCount;
        console.log(rtpFormat.length, rtpFormat); ///////////////////////////////////////////////////////////////

        // Byte 2: Payload Format
        var marker = booleanBits(this.marker);
        var payloadType = significantBits(this.payloadType, 7);
        var payloadFormat = marker + payloadType;
        console.log(payloadFormat.length, payloadFormat); ///////////////////////////////////////////////////////////////

        // Bytes 3-4: Serial Number - Randomise initial for future SRTP support. Cap at 25% of range.
        var sequenceNo = significantBits(this.sequenceNo, 16);

        // Bytes 5-8: Timestamp - Cap at 25% of range.
        var timeStamp = significantBits(this.timeStamp, 32);

        // Bytes 9-12: SSRC - Imitate OEM Server to be safe.
        var ssrc = significantBits(this.ssrc, 32);

        // Bytes 13+ not yet implemented
        // loop over this.csrcs;
        // loop over this.extensions; // See above.

        var combinedHeader = binstringToHex(rtpFormat + payloadFormat + sequenceNo + timeStamp + ssrc);
        console.log(combinedHeader.length, combinedHeader); ///////////////////////////////////////////////////////////////
        return combinedHeader;
    }

    /**
     * Represent header in human-readable format for display and logging.
     */
    toString () {
        return "RTPHeader.toString() not implemented.";
    }

    /**
     * Update header with latest sequence and timestamp
     */
    incrementHeader() {
        this.sequenceNo += 1;
        this.timeStamp += this.payloadSize;
    }

    /**
     * Explicitly set sequence and timestamp.
     * 
     * Warning: This is only meant to be called by RTPHeader.from(). It can be used to manually create an arbitrary
     * packet, but that's potentially dangerous as it allows to send duplicate or conflicting audio packets!
     */
    forceHeader(sequenceNo, timeStamp) {
        this.sequenceNo = sequenceNo;
        this.timeStamp = timeStamp;
    }
}

/**
 * Again - values specifically hardcoded for Spin Doctor.
 */
 class RTPPacket {
    constructor(header, payload = undefined) {
        this.header = header;

        if (this.header.payloadType == Payload.Mulaw8K) {
            this._payload = alawmulaw.mulaw.decode(payload); // For now, brute force the transcode, since we know we're working in mulaw.
        } else {
            console.log(this.header);
            throw "Not Mulaw, unsure what to do!";
        }
    }

    /**
     * Takes a dgram as a Buffer, and decodes it into a structured object
     * representing the RTP packet (including Header) of the packet sent by the badge.
     * 
     * Inspired by Array.from().
     */
    static from(packet) {
        var header = RTPHeader.from(packet);
        var payload = packet.slice(header.payloadSize * -1);
        return new RTPPacket(header, payload);
    }

    set payload (payload) {

    }

    get payload () {
        return this._payload;
    }

    /**
     * Transcode media to desired codec. Will presumably also need to handle
     * sample rate conversion? Don't think we can alter interval sizes here.
     * 
     * - Need to define codecs/profiles in some sensible way in this library.
     * - Need to update the header after transcoding?
     */
    transcode(codec) {

    }

    /**
     * Return the packet, ready to send.
     */
    toBuffer() {

    }

    /**
     * Represent the packet as a string form. Needs work.
     */
    toString() {
        var headerString = this.header.toString();

        return headerString, "RTPPacket.toString() not implemented.";
    }
}

/**
 * Should provide a source and sink for RTP Packets. For now, hardcode to the correct values for Combadge audio.
 * 
 * Down the line, we should generalise this to allow the library to be reused elsewhere -
 * (since I wouldn't be writing it if there was another approachable JS RTP library)
 */
class RTPServer {
    constructor(listenAddress, portNumber, consumer = undefined) {
        this.sampleCount = new Number(160); // At 8 bits/sample, this can be used for both incrementing the timestamp AND counting bytes.
        this.header = new RTPHeader(this.sampleCount);
        this._consumer = undefined;

        if (portNumber % 2 != 0) {
            throw `RTP Ports must be even. Odd-numbered ports are reserved for RTCP. Invalid port ${portNumber} passed.`;
        }

        if (consumer) {
            this.consumer = consumer;
        }

        this.udpServer = dgram.createSocket('udp4');
        this.udpServer.bind(portNumber, listenAddress)
        this.udpServer.on('listening', () => {
            const address = this.udpServer.address();
            console.log(`RTP Server spawned at ${address.address}:${address.port}`);
        });
        this.udpServer.on('message', (message, clientInfo) => {  
            var packet = RTPPacket.from(message);
            this.receivePacket(packet);
        });
        /*
        this.transcoding = true;
        var floatSamples=Float32Array.from(Float32Array.from(this.recSamples).map(x=>x/0x8000));
        var newSamples = waveResampler.resample(floatSamples, 8000, 16000); // RETURNS A FLOAT64 NOT AN INT16 READ THE DOCS
        var samples1616=Int16Array.from(newSamples.map(x => (x>0 ? x*0x7FFF : x*0x8000)));
        var wav16buffer = new Buffer.from(samples1616.buffer);
        console.log("Result:", model.stt(wav16buffer));
        this.transcoding = false;
        */
    }

    /**
     * Function to pass in a function to receive audio from the server.
     */
    set consumer (consumer) {
        if (!(consumer instanceof Function)) {
            throw "Must pass a function.";
        }
    }

    get consumer () {
        return this._consumer;
    }

    /** Do something with the packet, then forward it to the Consumer if set, or cache it if not. */
    receivePacket (packet) {

    }

    /**
     * Send audio to a remote device. We'll be explicit about target, rather than just using send() from the responder
     * because otherwise I can already see an exploit where a snooper sends 0-length packets to ensure they're always the most recent address.
     * socket.send(msg[, offset, length][, port][, address][, callback])
     */
    sendPacket (packet, address, port) {
        packetData = packet.toBuffer()
        this.udpServer.send(packetData, 0, packetData.length, port, address)
    }

    /**
     * Return a completed media packet without transcoding.
     */
    sendCopy(bytes) {
        var headerConstruct = this.header.getHeader();
        var headerBuffer = new Buffer.from(headerConstruct, 'hex');
        var completeBuffer = Buffer.concat([headerBuffer, bytes]);
        this.header.updateHeader();
        return completeBuffer;
    }

    /**
     * Return a decoded media array without transcoding.
     */
    receiveCopy(bytes) {
        var headerSection = bytes.subarray(0,12)
        var mediaSection = bytes.subarray(headerLength)

        var headerValues = this.header.decode(headerSection);

        return mediaSection;
    }
}

export { Payload, RTPHeader, RTPPacket, RTPServer };