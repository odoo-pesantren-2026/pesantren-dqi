import Buffer from 'buffer';

// Configuration
const CID = '001';
const SECRET = 'secret001';

class BnisEnc {
    static enc(string, key) {
        let result = '';
        const keyLen = key.length;
        if (keyLen === 0) return string;
        for (let i = 0; i < string.length; i++) {
            const keyIdx = (i % keyLen - 1 + keyLen) % keyLen;
            const keyChar = key[keyIdx];
            const newCharCode = (string.charCodeAt(i) + keyChar.charCodeAt(0)) % 128;
            result += String.fromCharCode(newCharCode);
        }
        return result;
    }

    static dec(string, key) {
        let result = '';
        const keyLen = key.length;
        for (let i = 0; i < string.length; i++) {
            const keyIdx = (i % keyLen - 1 + keyLen) % keyLen;
            const keyChar = key[keyIdx];
            const newCharCode = ((string.charCodeAt(i) - keyChar.charCodeAt(0)) + 256) % 128;
            result += String.fromCharCode(newCharCode);
        }
        return result;
    }

    static doubleEncrypt(string, cid, secret) {
        let result = this.enc(string, cid);
        result = this.enc(result, secret);
        let b64 = Buffer.Buffer.from(result, 'binary').toString('base64');
        b64 = b64.replace(/=+$/, '');
        return b64.replace(/\+/g, '-').replace(/\//g, '_');
    }

    static doubleDecrypt(string, cid, secret) {
        let b64 = string.replace(/-/g, '+').replace(/_/g, '/');
        while (b64.length % 4 !== 0) b64 += '=';
        const decoded = Buffer.Buffer.from(b64, 'base64').toString('binary');
        let result = this.dec(decoded, cid);
        result = this.dec(result, secret);
        return result;
    }
}

// Test
const original = "Hello World!";
const encrypted = BnisEnc.doubleEncrypt(original, CID, SECRET);
const decrypted = BnisEnc.doubleDecrypt(encrypted, CID, SECRET);

console.log('Original:', original);
console.log('Encrypted:', encrypted);
console.log('Decrypted:', decrypted);

if (original === decrypted) {
    console.log('SUCCESS: Encryption/Decryption logic works.');
} else {
    console.log('FAILURE: Mismatch.');
}
