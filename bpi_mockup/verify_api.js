import Buffer from 'buffer';

const CID = '001';
const SECRET = 'secret001';
const API_URL = 'http://localhost:8001/ext/bnis/?fungsi=vabilling';

class BnisEnc {
    static enc(string, key) {
        let result = '';
        const keyLen = key.length;
        for (let i = 0; i < string.length; i++) {
            const keyIdx = (i % keyLen - 1 + keyLen) % keyLen;
            const keyChar = key[keyIdx];
            const newCharCode = (string.charCodeAt(i) + keyChar.charCodeAt(0)) % 128;
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

    static decryptReal(string, cid, secret) {
        let b64 = string.replace(/-/g, '+').replace(/_/g, '/');
        while (b64.length % 4 !== 0) b64 += '=';
        const decoded = Buffer.Buffer.from(b64, 'base64').toString('binary');
        let result = this.dec(decoded, cid);
        result = this.dec(result, secret);
        return result;
    }

    static encrypt(jsonData, cid, secret) {
        const timestampStr = String(Math.floor(Date.now() / 1000)).split('').reverse().join('');
        const dataStr = timestampStr + '.' + JSON.stringify(jsonData);
        return this.doubleEncrypt(dataStr, cid, secret);
    }
}

async function test() {
    const payload = {
        type: 'createbilling',
        trx_id: 'TRX-12345',
        trx_amount: '100000',
        customer_name: 'John Doe',
        virtual_account: '988123456789',
        datetime_expired: '2026-12-31T23:59:59+0700',
        description: 'Test Billing'
    };

    const encryptedData = BnisEnc.encrypt(payload, CID, SECRET);

    console.log('Sending request to mockup...');
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ client_id: CID, data: encryptedData })
        });

        const body = await response.json();
        console.log('Response body:', JSON.stringify(body, null, 2));

        if (body.data) {
            const decrypted = BnisEnc.decryptReal(body.data, CID, SECRET);
            console.log('Decrypted Response:', decrypted);
        }
    } catch (e) {
        console.error('Fetch error:', e.message);
    }
}

test();
