import xml.etree.ElementTree as ET

NS = {'xacml': 'urn:oasis:names:tc:xacml:3.0:core:schema:wd-17'}

def get_role_from_request(request_file):
    tree = ET.parse(request_file)
    root = tree.getroot()

    attr = root.find(
        ".//xacml:Attribute[@AttributeId='role']/xacml:AttributeValue",
        NS
    )
    return attr.text if attr is not None else None


def evaluate_policy(role):
    # Mô phỏng policy.xml của bạn
    if role == "manager":
        return "Permit"
    elif role == "guest":
        return "Deny"
    else:
        return "NotApplicable"


if __name__ == "__main__":
    request_file = "request_1.xml"  # đổi file để test
    role = get_role_from_request(request_file)
    decision = evaluate_policy(role)

    print("=== TEST CASE RESULT ===")
    print("Input role:", role)
    print("Decision:", decision)
