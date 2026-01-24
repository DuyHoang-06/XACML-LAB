import xml.etree.ElementTree as ET

# Đọc file XACML Policy
tree = ET.parse("policy.xml")
root = tree.getroot()

# Namespace của XACML (phải có, nếu không sẽ không parse đúng)
ns = {'xacml': 'urn:oasis:names:tc:xacml:3.0:core:schema:wd-17'}

# Lấy tất cả các Rule
rules = root.findall('xacml:Rule', ns)

print("📜 Danh sách các Rule trong policy:")
for rule in rules:
    rule_id = rule.get('RuleId')
    effect = rule.get('Effect')

    # Tìm phần AttributeValue trong Target (nếu có)
    match_value = rule.find('.//xacml:AttributeValue', ns)
    if match_value is not None:
        attr_value = match_value.text
    else:
        attr_value = "—"

    print(f"→ RuleId: {rule_id} | Effect: {effect} | AttributeValue: {attr_value}")
