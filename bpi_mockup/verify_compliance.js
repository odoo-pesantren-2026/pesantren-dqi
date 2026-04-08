import fs from 'fs';

let config = {
    CID: '001',
    SECRET: 'secret001',
    ODOO_URL: 'http://localhost:8069',
    DB_NAME: 'pesantren-dqi',
    PARTNER_ID: '001'
};

try {
    const configData = JSON.parse(fs.readFileSync('config.json', 'utf8'));
    config = { ...config, ...configData };
} catch (error) {
    // console.warn('Could not load config.json, using defaults');
}
const BASE_URL = process.env.BASE_URL || 'http://localhost:8001';
const AUTH_URL = `${BASE_URL}/api/v1.0/access-token/b2b`;
const INQUIRY_URL = `${BASE_URL}/api/v1.0/transfer-va/inquiry`;
const PAYMENT_URL = `${BASE_URL}/api/v1.0/transfer-va/payment`;
const ADVICE_URL = `${BASE_URL}/api/v1.0/transfer-va/advice`;
const RECON_URL = `${BASE_URL}/api/bpi-bi-snap/reconciliation`;

async function testCompliance() {
    console.log('--- Starting API Compliance Test ---');

    // 1. Test Auth
    console.log('\n[1] Testing AUTH...');
    const authRes = await fetch(AUTH_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ grantType: 'client_credentials' })
    });
    const authData = await authRes.json();
    console.log('Response:', JSON.stringify(authData, null, 2));
    if (authData.responseCode === '2000000' && authData.responseMessage === 'Auth Success') {
        console.log('✅ AUTH compliant');
    } else {
        console.error('❌ AUTH non-compliant');
    }

    // 2. Test Inquiry
    console.log('\n[2] Testing INQUIRY...');
    const inqRes = await fetch(INQUIRY_URL, {
        method: 'POST',
        headers: { 
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + authData.accessToken
        },
        body: JSON.stringify({
            partnerServiceId: 'SBI0001',
            customerNo: '111222333444'
        })
    });
    const inqData = await inqRes.json();
    console.log('Response:', JSON.stringify(inqData, null, 2));
    if (inqData.responseCode === '2002400' && 
        inqData.responseMessage === 'Success' && 
        typeof inqData.virtualAccountData.totalAmount.value === 'string') {
        console.log('✅ INQUIRY compliant');
    } else {
        console.error('❌ INQUIRY non-compliant');
    }

    // 3. Test Payment (Invalid amount)
    console.log('\n[3] Testing PAYMENT (Invalid Amount)...');
    const payErrRes = await fetch(PAYMENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            customerNo: '111222333444',
            paymentRequestId: 'REQ-001',
            paidAmount: { value: '1000', currency: 'IDR' }
        })
    });
    const payErrData = await payErrRes.json();
    console.log('Response:', JSON.stringify(payErrData, null, 2));
    if (payErrData.responseCode === '4042513') {
        console.log('✅ PAYMENT Invalid Amount handling compliant');
    } else {
        console.error('❌ PAYMENT Invalid Amount handling non-compliant');
    }

    // 4. Test Payment (Success)
    console.log('\n[4] Testing PAYMENT (Success)...');
    const payRes = await fetch(PAYMENT_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            customerNo: '111222333444',
            paymentRequestId: 'PAY-001',
            paidAmount: { value: '150000', currency: 'IDR' }
        })
    });
    const payData = await payRes.json();
    console.log('Response:', JSON.stringify(payData, null, 2));
    if (payData.responseCode === '2002500' && payData.responseMessage === 'Success' && !payData.virtualAccountData) {
        console.log('✅ PAYMENT compliant');
    } else {
        console.error('❌ PAYMENT non-compliant');
    }

    // 5. Test Advice
    console.log('\n[5] Testing ADVICE...');
    const advRes = await fetch(ADVICE_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            paymentRequestId: 'PAY-001',
            customerNo: '111222333444'
        })
    });
    const advData = await advRes.json();
    console.log('Response:', JSON.stringify(advData, null, 2));
    if (advData.responseCode === '2002500') {
        console.log('✅ ADVICE compliant');
    } else {
        console.error('❌ ADVICE non-compliant');
    }

    // 6. Test Reconciliation
    console.log('\n[6] Testing RECONCILIATION...');
    const reconRes = await fetch(RECON_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            action: 'rekonsiliasi',
            kodeBPI: config.PARTNER_ID,
            data: []
        })
    });
    const reconData = await reconRes.json();
    console.log('Response:', JSON.stringify(reconData, null, 2));
    if (Array.isArray(reconData) && reconData[0].rc === true) {
        console.log('✅ RECONCILIATION compliant');
    } else {
        console.error('❌ RECONCILIATION non-compliant');
    }

    console.log('\n--- Compliance Test Finished ---');
}

testCompliance().catch(err => console.error('Test failed:', err));
