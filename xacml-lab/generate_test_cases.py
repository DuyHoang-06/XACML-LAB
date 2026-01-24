import xml.etree.ElementTree as ET
import os

# Namespace XACML
NS = {'xacml': 'urn:oasis:names:tc:xacml:3.0:core:schema:wd-17'}

# =========================
# 1. PARSE POLICY
# =========================
def parse_policy(policy_file):
    tree = ET.parse(policy_file)
    root = tree.getroot()

    rules = []
    for rule in root.findall('xacml:Rule', NS):
        rule_id = rule.get('RuleId')
        effect = rule.get('Effect')

        attr_value = None
        match = rule.find('.//xacml:AttributeValue', NS)
        if match is not None:
            attr_value = match.text

        rules.append({
            'rule_id': rule_id,
            'role': attr_value,
            'effect': effect
        })

    return rules


# =========================
# 2. DFS TRAVERSAL (LOGIC)
# =========================
def dfs_generate_test_cases(rules):
    test_cases = []

    def dfs(rule_index):
        if rule_index == len(rules):
            return

        rule = rules[rule_index]

        # Path: Policy → Rule → Condition
        test_cases.append({
            'role': rule['role'],
            'expected': rule['effect']
        })

        dfs(rule_index + 1)

    dfs(0)
    return test_cases


# =========================
# 3. BUILD REQUEST.XML
# =========================
def build_request_xml(role):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Request>
  <Attributes Category="subject">
    <Attribute AttributeId="role">
      <AttributeValue>{role}</AttributeValue>
    </Attribute>
  </Attributes>
</Request>
"""


# =========================
# 4. MAIN
# =========================
if __name__ == "__main__":
    policy_file = "policy.xml"
    output_dir = "generated_requests"
    os.makedirs(output_dir, exist_ok=True)

    rules = parse_policy(policy_file)
    test_cases = dfs_generate_test_cases(rules)

    for i, tc in enumerate(test_cases, 1):
        role = tc['role']
        content = build_request_xml(role)

        file_path = f"{output_dir}/request_{i}.xml"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[OK] Generated {file_path} | role={role} | expected={tc['expected']}")
