import xml.etree.ElementTree as ET

tree = ET.parse(r'D:\SNBI_Bridge_App\SNBI_Bridge_App\database\2025NJ_ElementData.xml')
root = tree.getroot()
print(root.tag)  # Should print: FHWAELEMENT

for fhwaed in root.findall('FHWAED'):
    struc = fhwaed.find('STRUCNUM').text
    en = fhwaed.find('EN').text
    print(f"Bridge: {struc}, Element: {en}")