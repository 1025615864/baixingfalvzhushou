const fs = require('fs');
const path = 'd:\\Git\\baixingfalvzhushou\\backend\\tests\\test_api.py';
let c = fs.readFileSync(path, 'utf8');
c = c.replace(/hash_password\("Test123456"\)/g, 'hash_password(TEST_PASSWORD)');
c = c.replace(/"password": "Test123456a"/g, '"password": TEST_PASSWORD');
c = c.replace(/"password": "Test123456"/g, '"password": TEST_PASSWORD');
fs.writeFileSync(path, c);
console.log('Done');
