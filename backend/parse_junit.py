import xml.etree.ElementTree as ET
r = ET.parse("/tmp/junit.xml").getroot()
print(f"Tests: {r.attrib.get('tests', '?')}, Failures: {r.attrib.get('failures', '?')}, Errors: {r.attrib.get('errors', '?')}, Skipped: {r.attrib.get('skipped', '?')}")
