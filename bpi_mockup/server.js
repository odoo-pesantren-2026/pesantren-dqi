import express from 'express';
import bodyParser from 'body-parser';
import { JSONFilePreset } from 'lowdb/node';
import path from 'path';

const app = express();
const port = process.env.PORT || 8001;

// Configuration (should match Odoo settings)
const CID = '001';
const SECRET = 'secret001';
const ODOO_URL = process.env.ODOO_URL || 'http://localhost:8069';
const DB_NAME = process.env.DB_NAME || 'pesantren-ubig-local';
const PARTNER_ID = process.env.PARTNER_ID || '001';

// Initialize lowdb
const defaultData = { billings: [] };
const db = await JSONFilePreset('db.json', defaultData);

app.use(bodyParser.json());

// =========================================================================
// BnisEnc - Ported from provider_bsi.py
// =========================================================================
class BnisEnc {
    static TIME_DIFF_LIMIT = 480; // 8 minutes

    static encrypt(jsonData, cid, secret) {
        const timestampStr = String(Math.floor(Date.now() / 1000)).split('').reverse().join('');
        const dataStr = timestampStr + '.' + JSON.stringify(jsonData);
        return this.doubleEncrypt(dataStr, cid, secret);
    }

    static decrypt(hashedString, cid, secret) {
        try {
            const parsedString = this.doubleDecrypt(hashedString, cid, secret);
            const dotIndex = parsedString.indexOf('.');
            if (dotIndex === -1) return null;

            const timestamp = parsedString.substring(0, dotIndex).split('').reverse().join('');
            const data = parsedString.substring(dotIndex + 1);

            if (this.tsDiff(parseInt(timestamp))) {
                return JSON.parse(data);
            }
            console.warn('BnisEnc: Timestamp difference exceeded limit');
            return null;
        } catch (error) {
            console.error('BnisEnc decrypt error:', error.message);
            return null;
        }
    }

    static tsDiff(ts) {
        return Math.abs(ts - Math.floor(Date.now() / 1000)) <= this.TIME_DIFF_LIMIT;
    }

    static doubleEncrypt(string, cid, secret) {
        let result = this.enc(string, cid);
        result = this.enc(result, secret);

        // Base64 encode (latin-1 equivalent in Node is 'binary')
        let b64 = Buffer.from(result, 'binary').toString('base64');
        b64 = b64.replace(/=+$/, '');
        return b64.replace(/\+/g, '-').replace(/\//g, '_');
    }

    static doubleDecrypt(string, cid, secret) {
        // Pad and decode
        let b64 = string.replace(/-/g, '+').replace(/_/g, '/');
        while (b64.length % 4 !== 0) {
            b64 += '=';
        }

        const decoded = Buffer.from(b64, 'base64').toString('binary');
        let result = this.dec(decoded, cid);
        result = this.dec(result, secret);
        return result;
    }

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
        if (keyLen === 0) return string;

        for (let i = 0; i < string.length; i++) {
            const keyIdx = (i % keyLen - 1 + keyLen) % keyLen;
            const keyChar = key[keyIdx];
            const newCharCode = ((string.charCodeAt(i) - keyChar.charCodeAt(0)) + 256) % 128;
            result += String.fromCharCode(newCharCode);
        }
        return result;
    }
}

// =========================================================================
// API Routes
// =========================================================================

// P2H VA API Endpoint
app.post('/ext/bnis/', async (req, res) => {
    const { fungsi } = req.query;
    if (fungsi !== 'vabilling') {
        return res.status(404).json({ status: '999', message: 'Function not found' });
    }

    const { client_id, data: encryptedData } = req.body;
    if (client_id !== CID) {
        return res.status(403).json({ status: '999', message: 'Invalid Client ID' });
    }

    const decrypted = BnisEnc.decrypt(encryptedData, CID, SECRET);
    if (!decrypted) {
        return res.status(400).json({ status: '999', message: 'Decryption failed or session expired' });
    }

    console.log('[BSI Mockup] Request:', decrypted);

    const { type, trx_id, trx_amount, customer_name, virtual_account, datetime_expired, description } = decrypted;
    let responseData = { status: '000', message: 'Success' };

    await db.read();
    const { billings } = db.data;

    if (type === 'createbilling') {
        // Check if trx_id already exists
        const existing = billings.find(b => b.trx_id === trx_id);
        if (existing) {
            responseData = { status: '999', message: 'Transaction ID already exists' };
        } else {
            const newBilling = {
                trx_id,
                trx_amount,
                customer_name,
                virtual_account,
                datetime_expired,
                description,
                status: 'pending',
                created_at: new Date().toISOString()
            };
            billings.push(newBilling);
            await db.write();
            responseData = { status: '000', message: 'Billing created', trx_id };
        }
    } else if (type === 'updatebilling') {
        const index = billings.findIndex(b => b.trx_id === trx_id);
        if (index === -1) {
            responseData = { status: '999', message: 'Transaction ID not found' };
        } else {
            billings[index] = { ...billings[index], trx_amount, customer_name, datetime_expired, description, updated_at: new Date().toISOString() };
            await db.write();
            responseData = { status: '000', message: 'Billing updated', trx_id };
        }
    } else if (type === 'deletebilling') {
        const index = billings.findIndex(b => b.trx_id === trx_id);
        if (index === -1) {
            responseData = { status: '999', message: 'Transaction ID not found' };
        } else {
            billings.splice(index, 1);
            await db.write();
            responseData = { status: '000', message: 'Billing deleted', trx_id };
        }
    } else {
        responseData = { status: '999', message: 'Unknown billing type' };
    }

    // Encrypt the response
    const encryptedResponse = BnisEnc.encrypt(responseData, CID, SECRET);
    res.json({ client_id: CID, data: encryptedResponse });
});

// =========================================================================
// SNAP BI Standard Endpoints (used by Test Wizard)
// =========================================================================

// 1. Auth: POST /api/v1.0/access-token/b2b
app.post('/api/v1.0/access-token/b2b', (req, res) => {
    console.log('[SNAP BI] Auth request');
    res.json({
        responseCode: '2000000',
        responseMessage: 'Successful',
        accessToken: 'mock-access-token-' + Math.random().toString(36).substring(7),
        expiresIn: 900,
        tokenType: 'BearerToken'
    });
});

// 2. Inquiry: POST /api/v1.0/transfer-va/inquiry
app.post('/api/v1.0/transfer-va/inquiry', async (req, res) => {
    const { customerNo, partnerServiceId } = req.body;
    console.log(`[SNAP BI] Inquiry request for: ${customerNo}`);

    await db.read();
    const va = db.data.virtual_accounts.find(v => v.customerNo === customerNo);

    if (va) {
        res.json({
            responseCode: '2002400',
            responseMessage: 'Successful',
            virtualAccountData: {
                partnerServiceId: partnerServiceId || 'SBI0001',
                customerNo: va.customerNo,
                virtualAccountNo: (partnerServiceId || 'SBI0001') + va.customerNo,
                virtualAccountName: va.virtualAccountName,
                totalAmount: {
                    value: parseFloat(va.totalAmount.value),
                    currency: va.totalAmount.currency
                },
                virtualAccountEmail: va.virtualAccountEmail,
                virtualAccountPhone: va.virtualAccountPhone,
                trxId: 'INQ-' + Date.now(),
                additionalInfo: { billerId: '1234' }
            }
        });
    } else {
        res.json({
            responseCode: '4042412',
            responseMessage: 'Bill not found',
        });
    }
});

// 3. Payment: POST /api/v1.0/transfer-va/payment
app.post('/api/v1.0/transfer-va/payment', async (req, res) => {
    const { customerNo, paymentRequestId, paidAmount } = req.body;
    console.log(`[SNAP BI] Payment notification for: ${customerNo}, amount: ${paidAmount?.value}`);

    await db.read();
    const va = db.data.virtual_accounts.find(v => v.customerNo === customerNo);

    if (va) {
        res.json({
            responseCode: '2002500',
            responseMessage: 'Successful',
            virtualAccountData: {
                partnerServiceId: 'SBI0001',
                customerNo: va.customerNo,
                virtualAccountNo: 'SBI0001' + va.customerNo,
                virtualAccountName: va.virtualAccountName,
                paidAmount: {
                    value: parseFloat(paidAmount?.value || 0),
                    currency: paidAmount?.currency || 'IDR'
                },
                paymentRequestId: paymentRequestId,
                additionalInfo: { billerId: '1234' }
            }
        });
    } else {
        res.json({
            responseCode: '4042512',
            responseMessage: 'Bill not found',
        });
    }
});

// Helper for UI/Debugging: List all billings
app.get('/billings', async (req, res) => {
    await db.read();
    res.json(db.data.billings);
});

// One-Click Dashboard for easy simulation
app.get('/dashboard', async (req, res) => {
    await db.read();
    const { billings } = db.data;

    const html = `
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BSI Mockup Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Inter', sans-serif; background: #f4f7f6; color: #333; margin: 0; padding: 20px; }
            .container { max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            h1 { color: #008080; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between; }
            .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
            .badge-pending { background: #fff3cd; color: #856404; }
            .badge-settlement { background: #d4edda; color: #155724; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #eee; }
            th { background: #f8f9fa; color: #666; font-size: 13px; }
            .btn { cursor: pointer; border: none; padding: 8px 16px; border-radius: 6px; font-weight: 600; font-size: 13px; transition: all 0.2s; }
            .btn-pay { background: #008080; color: white; }
            .btn-pay:hover { background: #006666; transform: translateY(-1px); }
            .btn-pay:disabled { background: #ccc; cursor: not-allowed; }
            .status-text { font-size: 12px; opacity: 0.8; }
            .footer { margin-top: 30px; font-size: 12px; color: #999; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>
                BSI Smart Billing Simulator
                <span style="font-size: 14px; font-weight: normal; color: #999;">Mockup Dashboard</span>
            </h1>
            
            <p>List of all billings registered from Odoo. Click <b>"Pay"</b> to simulate a bank payment and push notification to Odoo.</p>

            <table>
                <thead>
                    <tr>
                        <th>Order ID</th>
                        <th>Santri Name</th>
                        <th>Amount</th>
                        <th>VA Number</th>
                        <th>Status</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
                    ${billings.length === 0 ? '<tr><td colspan="6" style="text-align:center; padding: 40px; color: #999;">No billings registered yet. Visit Odoo and click "Kirim Billing BSI".</td></tr>' : ''}
                    ${billings.map(b => `
                        <tr>
                            <td><strong>${b.trx_id}</strong></td>
                            <td>${b.customer_name}</td>
                            <td>Rp${parseInt(b.trx_amount).toLocaleString('id-ID')}</td>
                            <td><code>${b.virtual_account}</code></td>
                            <td><span class="badge badge-${b.status}">${b.status}</span></td>
                            <td>
                                <button class="btn btn-pay" 
                                    onclick="payBilling('${b.trx_id}')" 
                                    ${b.status !== 'pending' ? 'disabled' : ''}>
                                    ${b.status === 'pending' ? 'Pay Now' : 'Paid'}
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>

            <div class="footer">
                BSI Mockup Server running on port 8001 | Configuration: CID=${CID}
            </div>
        </div>

        <script>
            async function payBilling(trxId) {
                if (!confirm('Simulate payment for ' + trxId + '? This will also notify Odoo.')) return;
                
                try {
                    const response = await fetch('/simulate/payment', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ trx_id: trxId })
                    });
                    const result = await response.json();
                    
                    if (response.ok) {
                        alert('✅ Success! Odoo has been notified.\\n\\nResponse: ' + JSON.stringify(result.odoo_response));
                        location.reload();
                    } else {
                        alert('❌ Error: ' + (result.message || 'Unknown error'));
                    }
                } catch (err) {
                    alert('❌ Connection failed: ' + err.message);
                }
            }
        </script>
    </body>
    </html>
    `;
    res.send(html);
});

// Simulation: Record payment and NOTIFY ODOO
app.post('/simulate/payment', async (req, res) => {
    const { trx_id } = req.body;
    await db.read();
    const billing = db.data.billings.find(b => b.trx_id === trx_id);
    if (!billing) return res.status(404).json({ message: 'Billing not found' });

    console.log(`[BSI Mockup] Simulating payment for: ${trx_id}`);

    // Update internal state
    billing.status = 'settlement';
    billing.paid_at = new Date().toISOString();
    await db.write();

    // Prepare notification to Odoo (SNAP BI Standard)
    // customerNo is usually the suffix of the VA number
    const customerNo = billing.virtual_account.replace(PARTNER_ID, '').padStart(3, '0');
    const payment_id = 'SIM-PAY-' + Date.now();
    const timestamp = new Date().toISOString().replace(/\.\d{3}Z$/, '+07:00');

    const notificationPayload = {
        customerNo: customerNo,
        partnerServiceId: PARTNER_ID,
        paymentRequestId: payment_id,
        paidAmount: {
            value: parseFloat(billing.trx_amount),
            currency: 'IDR'
        },
        trxDateTime: timestamp,
        additionalInfo: {
            trx_id: billing.trx_id,
            simulated: true
        }
    };

    console.log(`[BSI Mockup] Pushing notification to Odoo: ${ODOO_URL}/api/v1.0/transfer-va/payment`);

    try {
        const response = await fetch(`${ODOO_URL}/api/v1.0/transfer-va/payment?db=${DB_NAME}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Partner-Id': PARTNER_ID,
                'X-External-Id': payment_id,
                'X-Timestamp': timestamp,
                'X-Signature': 'simulated-signature-for-mockup' // Odoo skips verification in mockup mode
            },
            body: JSON.stringify(notificationPayload)
        });

        // Read body as text first to handle potential non-JSON errors
        const textResponse = await response.text();
        let result;
        try {
            result = JSON.parse(textResponse);
        } catch (e) {
            console.error('[BSI Mockup] Odoo returned non-JSON response:', textResponse.substring(0, 500));
            throw new Error(`Odoo returned invalid JSON: ${textResponse.substring(0, 50)}...`);
        }

        console.log('[BSI Mockup] Odoo Response:', result);

        res.json({
            message: 'Payment simulated and pushed to Odoo',
            billing,
            odoo_response: result
        });
    } catch (error) {
        console.error('[BSI Mockup] Notification failed:', error.message);
        res.status(500).json({
            message: 'Payment simulated locally but Odoo notification failed',
            error: error.message,
            billing
        });
    }
});

app.listen(port, '0.0.0.0', () => {
    console.log(`[BSI Mockup] Server running on port ${port}`);
    console.log(`[BSI Mockup] Using Client ID: ${CID}`);
});
